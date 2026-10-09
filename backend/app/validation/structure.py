"""Deterministic structural checks, with no external services."""

import ipaddress
import re
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from app.domain.package_layout import required_types_missing
from app.domain.plan import DeploymentPlan, FileType
from app.domain.validation import Category, CheckStatus, ValidationCheck
from app.validation.documents import (
    Document,
    PackageDocuments,
    blocks,
    code_text,
    mapping,
    normalize_name,
)

DOCKER_INSTRUCTIONS = {
    "FROM",
    "RUN",
    "CMD",
    "LABEL",
    "MAINTAINER",
    "EXPOSE",
    "ENV",
    "ADD",
    "COPY",
    "ENTRYPOINT",
    "VOLUME",
    "USER",
    "WORKDIR",
    "ARG",
    "ONBUILD",
    "STOPSIGNAL",
    "HEALTHCHECK",
    "SHELL",
}
TASK_META = {
    "name",
    "when",
    "register",
    "tags",
    "become",
    "become_user",
    "delegate_to",
    "ignore_errors",
    "ignore_unreachable",
    "changed_when",
    "failed_when",
    "notify",
    "vars",
    "environment",
    "loop",
    "loop_control",
    "with_items",
    "with_dict",
    "with_fileglob",
    "until",
    "retries",
    "delay",
    "no_log",
    "run_once",
    "check_mode",
    "any_errors_fatal",
    "throttle",
    "timeout",
    "collections",
}
WORKLOADS = {
    "Deployment",
    "StatefulSet",
    "DaemonSet",
    "ReplicaSet",
    "Job",
    "CronJob",
    "Pod",
}


def finding(
    doc: Document,
    check_id: str,
    condition: bool,
    message: str,
    *,
    token: str | None = None,
    line: int | None = None,
    status: CheckStatus | None = None,
    category: Category = "structure",
) -> ValidationCheck:
    return ValidationCheck(
        check_id=check_id,
        category=category,
        tool="builtin",
        status=status or ("passed" if condition else "failed"),
        file_path=doc.path,
        line_start=line or doc.line(token),
        message=message,
    )


def balanced(text: str) -> bool:
    depth = 0
    for char in text:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def block_bodies(text: str, keyword: str) -> list[tuple[int, str]]:
    bodies = []
    for match in re.finditer(r"\b" + keyword + r"\b[^{}]*\{", text):
        depth = 1
        index = match.end()
        while index < len(text) and depth:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        bodies.append((match.start(), text[match.end() : index - 1]))
    return bodies


def target_hostname(target: str) -> str:
    clean = target.strip("\"'")
    try:
        return urlsplit(clean if "://" in clean else "//" + clean).hostname or ""
    except ValueError:
        return ""


def nginx_targets(
    package: PackageDocuments, plan: DeploymentPlan
) -> list[ValidationCheck]:
    resolved = {normalize_name(service.name) for service in plan.services}
    for doc in package.of_kind(FileType.KUBERNETES):
        for item in doc.yaml_documents:
            data = item.data
            if isinstance(data, dict) and data.get("kind") == "Service":
                name = mapping(data.get("metadata")).get("name")
                if isinstance(name, str):
                    resolved.add(normalize_name(name))
    for doc in package.of_kind(FileType.TERRAFORM):
        for labels, attributes in blocks(doc.data, "resource"):
            if labels[0] == "helm_release":
                name = attributes.get("name")
                if isinstance(name, str) and "${" not in name:
                    resolved.add(normalize_name(name))
    for doc in package.of_kind(FileType.NGINX):
        text = code_text(
            doc.source, hash_comments=True, mask_strings=False, slash_comments=False
        )
        resolved.update(
            normalize_name(name)
            for name in re.findall(r"\bupstream\s+([\w.-]+)\s*\{", text)
        )
        resolved.update(
            normalize_name(target_hostname(host))
            for host in re.findall(
                r"#\s*external-host:\s*(\S+)",
                code_text(doc.source, slash_comments=False),
            )
        )
    checks = []
    for doc in package.of_kind(FileType.NGINX):
        text = code_text(
            doc.source, hash_comments=True, mask_strings=False, slash_comments=False
        )
        masked = code_text(doc.source, hash_comments=True, slash_comments=False)
        for match in re.finditer(r"\bproxy_pass\s+([^;\s]+)\s*;", text):
            if not re.match(r"\bproxy_pass\b", masked[match.start() :]):
                continue
            line = text.count("\n", 0, match.start()) + 1
            target = match.group(1)
            if "$" in target:
                checks.append(
                    finding(
                        doc,
                        "nginx.proxy_pass",
                        True,
                        "Variable proxy_pass target cannot be resolved statically",
                        line=line,
                        status="warning",
                    )
                )
                continue
            host = target_hostname(target)
            try:
                ipaddress.ip_address(host)
                is_ip = True
            except ValueError:
                is_ip = False
            ok = is_ip or "." in host or normalize_name(host) in resolved
            message = (
                "proxy_pass target resolved"
                if ok
                else f"Unresolved bare proxy_pass target in {doc.path}:{line}"
            )
            checks.append(finding(doc, "nginx.proxy_pass", ok, message, line=line))
    return checks


def tasks(doc: Document, items: object) -> list[ValidationCheck]:
    if not isinstance(items, list):
        return [
            finding(doc, "ansible.tasks", False, "Tasks must be a list", token="tasks")
        ]
    checks = []
    for task in items:
        if not isinstance(task, dict):
            checks.append(
                finding(doc, "ansible.task_module", False, "Task must be a mapping")
            )
            continue
        nested = next(
            (task[key] for key in ("block", "rescue", "always") if key in task), None
        )
        if nested is not None:
            for key in ("block", "rescue", "always"):
                if key in task:
                    checks.extend(tasks(doc, task[key]))
            continue
        module = any(
            isinstance(key, str)
            and key not in TASK_META
            and not key.startswith("with_")
            for key in task
        )
        checks.append(
            finding(
                doc,
                "ansible.task_module",
                module,
                "Task declares a module" if module else "Task has no module key",
                token=str(task.get("name", "tasks")),
            )
        )
    return checks


def structural_checks(
    package: PackageDocuments, plan: DeploymentPlan
) -> list[ValidationCheck]:
    checks = []
    for missing in required_types_missing(package.files, plan.file_types):
        checks.append(
            ValidationCheck(
                check_id="package.required_files",
                category="structure",
                tool="builtin",
                status="failed",
                message=f"Missing required {missing.value} files",
            )
        )
    identities = set()
    for doc in package.documents.values():
        kind = doc.kind
        if doc.parse_error:
            checks.append(
                finding(
                    doc,
                    "document.parse",
                    False,
                    "Document could not be parsed",
                    line=doc.error_line or 1,
                )
            )
            continue
        if kind == FileType.KUBERNETES:
            for item in doc.yaml_documents:
                data = item.data
                ok = (
                    isinstance(data, dict)
                    and all(
                        isinstance(data.get(key), str) and data[key]
                        for key in ("apiVersion", "kind")
                    )
                    and isinstance(data.get("metadata"), dict)
                    and isinstance(data["metadata"].get("name"), str)
                    and bool(data["metadata"].get("name"))
                    and isinstance(data["metadata"].get("namespace", "default"), str)
                )
                checks.append(
                    finding(
                        doc,
                        "k8s.manifest",
                        bool(ok),
                        "Manifest requires apiVersion, kind and metadata.name",
                        line=item.line,
                    )
                )
                if not ok:
                    continue
                identity = (
                    data["metadata"].get("namespace", "default"),
                    data["kind"],
                    data["metadata"]["name"],
                )
                checks.append(
                    finding(
                        doc,
                        "k8s.duplicate",
                        identity not in identities,
                        "Kubernetes identity must be unique in its namespace",
                        line=item.line,
                    )
                )
                identities.add(identity)
                if data["kind"] in WORKLOADS:
                    spec = mapping(data.get("spec"))
                    if data["kind"] == "CronJob":
                        spec = mapping(mapping(spec.get("jobTemplate")).get("spec"))
                    pod = (
                        spec
                        if data["kind"] == "Pod"
                        else mapping(mapping(spec.get("template")).get("spec"))
                    )
                    containers = (
                        pod.get("containers") if isinstance(pod, dict) else None
                    )
                    valid = (
                        isinstance(containers, list)
                        and bool(containers)
                        and all(
                            isinstance(c, dict) and c.get("name") and c.get("image")
                            for c in containers
                        )
                    )
                    checks.append(
                        finding(
                            doc,
                            "k8s.containers",
                            bool(valid),
                            "Workload containers require name and image",
                            line=item.positions.get(("spec",), item.line),
                        )
                    )
        elif kind == FileType.HELM:
            if PurePosixPath(doc.path).name == "Chart.yaml":
                data = doc.data
                ok = isinstance(data, dict) and all(
                    data.get(key) for key in ("apiVersion", "name", "version")
                )
                checks.append(
                    finding(
                        doc,
                        "helm.chart",
                        bool(ok),
                        "Chart requires apiVersion, name and version",
                    )
                )
                root = str(PurePosixPath(doc.path).parent)
                checks.append(
                    finding(
                        doc,
                        "helm.templates",
                        any(
                            path.startswith(root + "/templates/")
                            for path in package.files
                        ),
                        "Chart requires templates",
                    )
                )
            elif PurePosixPath(doc.path).name in {"values.yaml", "values.yml"}:
                checks.append(
                    finding(
                        doc,
                        "helm.values",
                        isinstance(doc.data, dict),
                        "Values must be a YAML mapping",
                    )
                )
        elif kind == FileType.DOCKERFILE:
            instructions = []
            continued = False
            for line, text in enumerate(doc.source.splitlines(), 1):
                clean = text.strip()
                if not clean or clean.startswith("#"):
                    continue
                if not continued:
                    keyword = clean.split()[0].upper()
                    instructions.append(keyword)
                    checks.append(
                        finding(
                            doc,
                            "dockerfile.instruction",
                            keyword in DOCKER_INSTRUCTIONS,
                            "Dockerfile instruction must be recognized",
                            line=line,
                        )
                    )
                continued = clean.endswith("\\")
            checks.append(
                finding(
                    doc,
                    "dockerfile.from",
                    "FROM" in instructions,
                    "Dockerfile requires FROM",
                )
            )
        elif kind == FileType.JENKINS:
            text = code_text(doc.source)
            checks.append(
                finding(
                    doc,
                    "jenkins.braces",
                    balanced(text),
                    "Jenkins braces must be balanced",
                )
            )
            pipelines = block_bodies(text, "pipeline")
            checks.append(
                finding(
                    doc,
                    "jenkins.pipeline",
                    bool(pipelines)
                    and all(
                        re.search(r"\bagent\b", body)
                        and re.search(r"\bstages\s*\{", body)
                        for _, body in pipelines
                    ),
                    "Declarative pipeline requires agent and stages",
                )
            )
            for offset, body in block_bodies(text, "stage"):
                checks.append(
                    finding(
                        doc,
                        "jenkins.steps",
                        bool(re.search(r"\bsteps\s*\{", body)),
                        "Each stage requires steps",
                        line=text.count("\n", 0, offset) + 1,
                    )
                )
        elif kind == FileType.ANSIBLE:
            path = doc.path
            if "/roles/" in path:
                if "/tasks/" in path or "/handlers/" in path:
                    checks.extend(tasks(doc, doc.data))
            elif "inventory" in PurePosixPath(path).name:
                continue
            elif isinstance(doc.data, dict):
                # Group vars, host vars and role defaults are supporting mappings.
                if not any(
                    part in {"group_vars", "host_vars", "vars"}
                    for part in PurePosixPath(path).parts
                ):
                    checks.append(
                        finding(
                            doc,
                            "ansible.playbook",
                            False,
                            "Playbook must be a list of plays",
                        )
                    )
            elif isinstance(doc.data, list):
                for play in doc.data:
                    ok = isinstance(play, dict) and bool(play.get("hosts"))
                    checks.append(
                        finding(
                            doc,
                            "ansible.playbook",
                            bool(ok),
                            "Each play requires hosts",
                            token="hosts",
                        )
                    )
                    if isinstance(play, dict):
                        for key in ("tasks", "pre_tasks", "post_tasks", "handlers"):
                            if key in play:
                                checks.extend(tasks(doc, play[key]))
            else:
                checks.append(
                    finding(
                        doc,
                        "ansible.playbook",
                        False,
                        "Playbook must be a list of plays",
                    )
                )
        elif kind == FileType.NGINX:
            text = code_text(doc.source, hash_comments=True, slash_comments=False)
            checks.append(
                finding(
                    doc, "nginx.braces", balanced(text), "Nginx braces must be balanced"
                )
            )
            checks.append(
                finding(
                    doc,
                    "nginx.server",
                    bool(re.search(r"\bserver\s*\{", text)),
                    "Nginx requires a server block",
                )
            )
        elif kind == FileType.PROMETHEUS:
            data = doc.data
            if (
                isinstance(data, dict)
                and "groups" in data
                and "scrape_configs" not in data
            ):
                checks.append(
                    finding(
                        doc,
                        "prometheus.rules",
                        isinstance(data["groups"], list),
                        "Rule groups must be a list",
                    )
                )
            else:
                configs = data.get("scrape_configs") if isinstance(data, dict) else None
                checks.append(
                    finding(
                        doc,
                        "prometheus.scrape_configs",
                        isinstance(configs, list),
                        "scrape_configs must be a list",
                        token="scrape_configs",
                    )
                )
                if isinstance(configs, list):
                    for config in configs:
                        checks.append(
                            finding(
                                doc,
                                "prometheus.job_name",
                                isinstance(config, dict)
                                and bool(config.get("job_name")),
                                "Each scrape config requires job_name",
                                token="job_name",
                            )
                        )
        elif kind == FileType.GRAFANA:
            data = doc.data
            panels = data.get("panels") if isinstance(data, dict) else None
            checks.append(
                finding(
                    doc,
                    "grafana.panels",
                    isinstance(panels, list),
                    "Dashboard requires panels",
                    token="panels",
                )
            )

            def panel_checks(items: list[object], panel_doc: Document = doc) -> None:
                for panel in items:
                    valid = isinstance(panel, dict) and bool(panel.get("type"))
                    checks.append(
                        finding(
                            panel_doc,
                            "grafana.panel_type",
                            bool(valid),
                            "Each panel requires a type",
                            token="type",
                        )
                    )
                    if isinstance(panel, dict) and isinstance(
                        panel.get("panels"), list
                    ):
                        panel_checks(panel["panels"])

            if isinstance(panels, list):
                panel_checks(panels)
    checks.extend(nginx_targets(package, plan))
    return checks
