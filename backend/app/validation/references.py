"""Deterministic references, scoped to the package and Terraform module."""

import posixpath
import re
from pathlib import PurePosixPath
from typing import Any

from app.domain.plan import FileType
from app.domain.validation import CheckStatus, ValidationCheck
from app.validation.documents import (
    Document,
    PackageDocuments,
    blocks,
    code_text,
    helm_expression,
    helm_template_resources,
    mapping,
    walk,
)
from app.validation.structure import WORKLOADS, finding


def safe_reference(base: str, target: str) -> str | None:
    if (
        not target
        or target.startswith("/")
        or "\\" in target
        or re.match(r"^[A-Za-z]:", target)
    ):
        return None
    normalized = posixpath.normpath(posixpath.join(base, target))
    return None if normalized == ".." or normalized.startswith("../") else normalized


def glob_match(path: str, pattern: str) -> bool:
    regex = (
        re.escape(pattern)
        .replace(r"\*\*/", r"(?:[^/]+/)*")
        .replace(r"\*\*", r".*")
        .replace(r"\*", r"[^/]*")
        .replace(r"\?", r"[^/]")
    )
    return re.fullmatch(regex, path) is not None


def source_line(doc: Document, token: str) -> int:
    text = code_text(doc.source, hash_comments=True, mask_strings=False)
    return next(
        (index for index, line in enumerate(text.splitlines(), 1) if token in line), 1
    )


def terraform_references(package: PackageDocuments) -> list[ValidationCheck]:
    scopes: dict[str, list[Document]] = {}
    for doc in package.of_kind(FileType.TERRAFORM):
        if doc.path.endswith((".tf", ".tf.json")) and not doc.parse_error:
            scopes.setdefault(str(PurePosixPath(doc.path).parent), []).append(doc)
    checks = []
    for scope, documents in scopes.items():
        declared_vars = {
            labels[0] for doc in documents for labels, _ in blocks(doc.data, "variable")
        }
        declared_modules = {
            labels[0]: (doc, body)
            for doc in documents
            for labels, body in blocks(doc.data, "module")
        }
        declared_locals: set[str] = set()
        for doc in documents:
            raw = mapping(doc.data).get("locals", [])
            for local in raw if isinstance(raw, list) else [raw]:
                if isinstance(local, dict):
                    declared_locals.update(local)
        for _name, (doc, module) in declared_modules.items():
            source = module.get("source")
            if isinstance(source, str) and source.startswith(("./", "../")):
                target = safe_reference(scope, source)
                exists = target is not None and any(
                    str(PurePosixPath(path).parent) == target
                    and path.endswith((".tf", ".tf.json"))
                    for path in package.files
                )
                checks.append(
                    finding(
                        doc,
                        "terraform.local_module",
                        exists,
                        "Local module source must exist inside the package",
                        line=source_line(doc, source),
                        category="reference",
                    )
                )
        for doc in documents:
            seen: set[str] = set()
            for reference, line in sorted(
                doc.reference_locations.items(), key=lambda item: (item[1], item[0])
            ):
                parts = reference.split(".")
                family, name = parts[:2]
                output = parts[2] if len(parts) > 2 else None
                known = name in (
                    declared_vars
                    if family == "var"
                    else declared_locals
                    if family == "local"
                    else declared_modules
                )
                token = f"{family}.{name}"
                if token not in seen:
                    seen.add(token)
                    checks.append(
                        finding(
                            doc,
                            f"terraform.{family}_ref",
                            known,
                            f"{token} is {'declared' if known else 'not declared'}",
                            line=line,
                            category="reference",
                        )
                    )
                if known and family == "module" and output:
                    module = declared_modules[name][1]
                    source = module.get("source")
                    if isinstance(source, str) and source.startswith(("./", "../")):
                        target = safe_reference(scope, source)
                        child = scopes.get(target or "", [])
                        if child:
                            outputs = {
                                labels[0]
                                for document in child
                                for labels, _ in blocks(document.data, "output")
                            }
                            exists = output in outputs
                            state = "declared" if exists else "not declared"
                            checks.append(
                                finding(
                                    doc,
                                    "terraform.module_output",
                                    exists,
                                    f"{reference} is {state}",
                                    line=line,
                                    category="reference",
                                )
                            )
    return checks


def kubernetes_references(package: PackageDocuments) -> list[ValidationCheck]:
    entries = []
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for doc in package.of_kind(FileType.KUBERNETES):
        if doc.parse_error:
            continue
        for item in doc.yaml_documents:
            data = mapping(item.data)
            metadata = mapping(data.get("metadata"))
            namespace = metadata.get("namespace", "default")
            kind = data.get("kind")
            name = metadata.get("name")
            if (
                isinstance(namespace, str)
                and isinstance(kind, str)
                and isinstance(name, str)
            ):
                entries.append((doc, item, data, namespace))
                index[(namespace, kind, name)] = data
    dynamic_kinds: set[str] = set()
    helm_keys: set[tuple[str, str, str]] = set()
    for doc in package.of_kind(FileType.HELM):
        if "/templates/" not in doc.path or not doc.path.endswith((".yaml", ".yml")):
            continue
        for data in helm_template_resources(doc.source):
            kind = data.get("kind")
            metadata = mapping(data.get("metadata"))
            name = metadata.get("name")
            namespace = metadata.get("namespace")
            if not isinstance(kind, str) or helm_expression(kind):
                continue
            if (
                helm_expression(name)
                or helm_expression(namespace)
                or "namespace" not in metadata
            ):
                dynamic_kinds.add(kind)
            elif isinstance(name, str) and isinstance(namespace, str):
                helm_key = (namespace, kind, name)
                if helm_key not in index:
                    index[helm_key] = data
                    helm_keys.add(helm_key)
    checks = []

    def unresolved_status(exists: bool, kind: str) -> CheckStatus | None:
        return "warning" if not exists and kind in dynamic_kinds else None

    def target_message(exists: bool, kind: str, ordinary: str) -> str:
        if unresolved_status(exists, kind):
            return f"Helm {kind} name or namespace cannot be resolved statically"
        return ordinary

    def pod_labels(data: dict[str, Any]) -> dict[str, Any]:
        spec = mapping(data.get("spec"))
        if data.get("kind") == "Pod":
            return mapping(mapping(data.get("metadata")).get("labels"))
        if data.get("kind") == "CronJob":
            spec = mapping(mapping(spec.get("jobTemplate")).get("spec"))
        return mapping(
            mapping(mapping(spec.get("template")).get("metadata")).get("labels")
        )

    for doc, item, data, namespace in entries:
        for path, value in walk(data):
            key = path[-1]
            target_kind = None
            name = None
            warning = False
            if key in {"configMapRef", "configMapKeyRef"} or (
                key == "configMap" and "volumes" in path
            ):
                target_kind = "ConfigMap"
                name = mapping(value).get("name")
            elif key in {"secretRef", "secretKeyRef"}:
                target_kind = "Secret"
                name = mapping(value).get("name")
                warning = True
            elif key == "claimName" and "volumes" in path:
                target_kind = "PersistentVolumeClaim"
                name = value
            if target_kind:
                exists = (
                    (namespace, target_kind, name) in index
                    if isinstance(name, str)
                    else False
                )
                check_id = {
                    "ConfigMap": "k8s.configmap_ref",
                    "Secret": "k8s.secret_ref",
                    "PersistentVolumeClaim": "k8s.pvc_ref",
                }[target_kind]
                checks.append(
                    finding(
                        doc,
                        check_id,
                        exists,
                        target_message(
                            exists,
                            target_kind,
                            f"{target_kind} reference must resolve in its namespace",
                        )
                        if not warning or exists
                        else "Secret may be supplied outside the package",
                        line=item.positions.get(path, item.line),
                        category="reference",
                        status="warning"
                        if not exists and (warning or target_kind in dynamic_kinds)
                        else None,
                    )
                )
            if data.get("kind") == "Ingress" and key in {"backend", "defaultBackend"}:
                backend = mapping(value)
                service = mapping(backend.get("service"))
                service_name = service.get("name", backend.get("serviceName"))
                port = mapping(service.get("port"))
                service_port = port.get(
                    "name", port.get("number", backend.get("servicePort"))
                )
                target = (
                    index.get((namespace, "Service", service_name))
                    if isinstance(service_name, str)
                    else None
                )
                exists = target is not None
                checks.append(
                    finding(
                        doc,
                        "k8s.ingress_service",
                        exists,
                        target_message(
                            exists,
                            "Service",
                            "Ingress backend Service must exist in its namespace",
                        ),
                        line=item.positions.get(path, item.line),
                        category="reference",
                        status=unresolved_status(exists, "Service"),
                    )
                )
                if target:
                    ports = mapping(target.get("spec")).get("ports", [])
                    valid = isinstance(ports, list) and any(
                        isinstance(entry, dict)
                        and service_port in (entry.get("name"), entry.get("port"))
                        for entry in ports
                    )
                    dynamic_port = (
                        namespace,
                        "Service",
                        service_name,
                    ) in helm_keys and any(
                        helm_expression(value) for _, value in walk(ports)
                    )
                    checks.append(
                        finding(
                            doc,
                            "k8s.ingress_port",
                            valid,
                            "Helm Service port cannot be resolved statically"
                            if not valid and dynamic_port
                            else "Ingress port must match a Service port",
                            line=item.positions.get(path, item.line),
                            category="reference",
                            status="warning" if not valid and dynamic_port else None,
                        )
                    )
            if (
                data.get("kind") == "HorizontalPodAutoscaler"
                and key == "scaleTargetRef"
            ):
                target = mapping(value)
                kind = target.get("kind")
                name = target.get("name")
                exists = (
                    isinstance(kind, str)
                    and isinstance(name, str)
                    and kind in WORKLOADS
                    and (namespace, kind, name) in index
                )
                checks.append(
                    finding(
                        doc,
                        "k8s.hpa_target",
                        exists,
                        target_message(
                            exists,
                            kind,
                            "HPA target must identify an existing workload",
                        )
                        if isinstance(kind, str)
                        else "HPA target must identify an existing workload",
                        line=item.positions.get(path, item.line),
                        category="reference",
                        status=unresolved_status(exists, kind)
                        if isinstance(kind, str)
                        else None,
                    )
                )
        if data.get("kind") == "Service":
            selector = mapping(mapping(data.get("spec")).get("selector"))
            if selector:
                matches = any(
                    ns == namespace
                    and kind in WORKLOADS
                    and all(
                        pod_labels(workload).get(key) == value
                        for key, value in selector.items()
                    )
                    for (ns, kind, _), workload in index.items()
                )
                checks.append(
                    finding(
                        doc,
                        "k8s.service_selector",
                        matches,
                        "Service selector must match a workload in its namespace",
                        line=item.positions.get(("spec", "selector"), item.line),
                        category="reference",
                        status="warning"
                        if not matches and dynamic_kinds.intersection(WORKLOADS)
                        else None,
                    )
                )
    return checks


def helm_references(package: PackageDocuments) -> list[ValidationCheck]:
    checks = []
    for chart in package.of_kind(FileType.HELM):
        if PurePosixPath(chart.path).name != "Chart.yaml" or chart.parse_error:
            continue
        root = str(PurePosixPath(chart.path).parent)
        data = mapping(chart.data)
        dependencies = data.get("dependencies", [])
        for dependency in dependencies if isinstance(dependencies, list) else []:
            if not isinstance(dependency, dict):
                continue
            name = dependency.get("name")
            repository = dependency.get("repository", "")
            vendored = isinstance(name, str) and any(
                path.startswith(root + "/charts/" + name + "/")
                or re.fullmatch(
                    re.escape(root + "/charts/" + name) + r"-[^/]+\.tgz", path
                )
                for path in package.files
            )
            remote = isinstance(repository, str) and repository.startswith(
                ("http://", "https://", "oci://")
            )
            checks.append(
                finding(
                    chart,
                    "helm.dependency",
                    vendored,
                    "Dependency is vendored"
                    if vendored
                    else "Remote dependency not validated offline"
                    if remote
                    else "Helm dependency must be vendored",
                    token="dependencies",
                    category="reference",
                    status="warning" if remote and not vendored else None,
                )
            )
        values: Any = next(
            (
                doc.data
                for doc in package.of_kind(FileType.HELM)
                if doc.path in {root + "/values.yaml", root + "/values.yml"}
                and not doc.parse_error
            ),
            {},
        )
        for template in package.of_kind(FileType.HELM):
            if not template.path.startswith(root + "/templates/"):
                continue
            template_code = list(
                "".join("\n" if char == "\n" else " " for char in template.source)
            )
            for expression in re.finditer(r"{{-?([\s\S]*?)-?}}", template.source):
                template_code[expression.start(1) : expression.end(1)] = code_text(
                    expression.group(1)
                )
            for match in re.finditer(
                r"\.Values((?:\.[A-Za-z_][\w-]*)+)", "".join(template_code)
            ):
                current = values
                exists = True
                for part in match.group(1).strip(".").split("."):
                    if not isinstance(current, dict) or part not in current:
                        exists = False
                        break
                    current = current[part]
                checks.append(
                    finding(
                        template,
                        "helm.values_ref",
                        exists,
                        "Values path exists"
                        if exists
                        else "Values path missing; a template default may be intended",
                        line=template.source.count("\n", 0, match.start()) + 1,
                        category="reference",
                        status="warning" if not exists else None,
                    )
                )
    return checks


def inventory_groups(package: PackageDocuments) -> tuple[set[str], bool]:
    groups = {"all", "ungrouped"}
    present = False
    for doc in package.documents.values():
        name = PurePosixPath(doc.path).name
        if not doc.path.startswith("ansible/") or not (
            "inventory" in name
            or "/inventory/" in doc.path
            or name in {"hosts", "hosts.ini", "hosts.yaml", "hosts.yml"}
        ):
            continue
        present = True
        if isinstance(doc.data, dict):
            groups.update(str(key) for key in doc.data)
            for path, _value in walk(doc.data):
                if len(path) >= 2 and path[-2] == "children":
                    groups.add(str(path[-1]))
        else:
            groups.update(
                re.findall(
                    r"^\s*\[([^\]:]+)(?::(?:vars|children))?\]\s*$",
                    doc.source,
                    re.MULTILINE,
                )
            )
    return groups, present


def ansible_references(package: PackageDocuments) -> list[ValidationCheck]:
    groups, present = inventory_groups(package)
    checks = []
    for doc in package.of_kind(FileType.ANSIBLE):
        if "/roles/" in doc.path or not isinstance(doc.data, list) or doc.parse_error:
            continue
        for play in doc.data:
            if not isinstance(play, dict) or "hosts" not in play:
                continue
            hosts = play["hosts"]
            if present and isinstance(hosts, str):
                symbolic = "{{" in hosts or "*" in hosts or "~" in hosts
                requested = [name for name in re.split(r"[:,&!\s]+", hosts) if name]
                checks.append(
                    finding(
                        doc,
                        "ansible.inventory_group",
                        all(name in groups for name in requested),
                        "Inventory groups must exist"
                        if not symbolic
                        else "Inventory expression cannot be resolved statically",
                        token="hosts",
                        category="reference",
                        status="warning" if symbolic else None,
                    )
                )
            roles = play.get("roles", [])
            for role in roles if isinstance(roles, list) else []:
                name = role if isinstance(role, str) else mapping(role).get("role")
                target = (
                    safe_reference("ansible/roles", name)
                    if isinstance(name, str)
                    else None
                )
                exists = target is not None and any(
                    path.startswith(target + "/") for path in package.files
                )
                checks.append(
                    finding(
                        doc,
                        "ansible.role_ref",
                        exists,
                        "Referenced role must exist inside the package",
                        token="roles",
                        category="reference",
                    )
                )
        for path, value in walk(doc.data):
            if path[-1] in {"include_role", "import_role"}:
                name = mapping(value).get("name")
                target = (
                    safe_reference("ansible/roles", name)
                    if isinstance(name, str)
                    else None
                )
                checks.append(
                    finding(
                        doc,
                        "ansible.role_ref",
                        target is not None
                        and any(
                            path.startswith(target + "/") for path in package.files
                        ),
                        "Included role must exist inside the package",
                        token=str(path[-1]),
                        category="reference",
                    )
                )
    return checks


def prometheus_references(package: PackageDocuments) -> list[ValidationCheck]:
    checks = []
    for doc in package.of_kind(FileType.PROMETHEUS):
        if doc.parse_error:
            continue
        rules = mapping(doc.data).get("rule_files", [])
        seen = set()
        for rule in rules if isinstance(rules, list) else []:
            if not isinstance(rule, str) or rule in seen:
                continue
            seen.add(rule)
            target = safe_reference(str(PurePosixPath(doc.path).parent), rule)
            exists = target is not None and any(
                glob_match(path, target) for path in package.files
            )
            checks.append(
                finding(
                    doc,
                    "prometheus.rule_file",
                    exists,
                    "Rule-file path or glob must match files inside the package",
                    token=rule,
                    category="reference",
                )
            )
    return checks


def reference_checks(package: PackageDocuments) -> list[ValidationCheck]:
    from app.validation.workspace import current_workspace

    workspace = current_workspace()
    if workspace:
        checks = workspace.cache_index(
            "references", package.files, lambda: _reference_checks(package)
        )
        return [c.model_copy() for c in checks]
    return _reference_checks(package)


def _reference_checks(package: PackageDocuments) -> list[ValidationCheck]:
    return [
        *terraform_references(package),
        *kubernetes_references(package),
        *helm_references(package),
        *ansible_references(package),
        *prometheus_references(package),
    ]
