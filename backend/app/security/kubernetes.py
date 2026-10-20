"""D-56: missing-only pod defaults, with source-preserving bounded edits.

Helm inspection is authorised by real rendered objects, never by treating Go
templates as YAML. Unsupported bindings remain unchanged. No runtime claim is
made: image users, write paths and capacity requirements cannot be inferred.
"""

import copy
import hashlib
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any

import yaml  # type: ignore[import-untyped]
from yaml.nodes import (  # type: ignore[import-untyped]
    MappingNode,
    Node,
    ScalarNode,
    SequenceNode,
)

KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Job"}
CONTROLS = {
    "identity": ("CKV_K8S_23", "CKV_K8S_40", "KSV-0012", "KSV-0118"),
    "escalation": ("CKV_K8S_20", "KSV-0001"),
    "filesystem": ("CKV_K8S_22", "KSV-0014"),
    "capabilities": ("CKV_K8S_37", "KSV-0003", "KSV-0004", "KSV-0106"),
    "seccomp": ("CKV_K8S_31", "KSV-0104"),
    "resources": ("CKV_K8S_10", "CKV_K8S_11", "CKV_K8S_12", "CKV_K8S_13"),
}
SECURITY = {
    "runAsNonRoot": True,
    "runAsUser": 10001,
    "runAsGroup": 10001,
    "allowPrivilegeEscalation": False,
    "readOnlyRootFilesystem": True,
    "capabilities": {"drop": ["ALL"]},
    "seccompProfile": {"type": "RuntimeDefault"},
}
RESOURCES = {
    "requests": {"cpu": "100m", "memory": "128Mi"},
    "limits": {"cpu": "500m", "memory": "512Mi"},
}
ACTION = re.compile(r"{{[\s\S]*?}}")


def _static_structure(source: str) -> bool:
    controls: list[tuple[re.Match[str], str]] = []
    for match in ACTION.finditer(source):
        control = re.match(
            r"-?\s*(if|range|with|else|end|define|block)\b", match.group()[2:-2]
        )
        if control:
            controls.append((match, control[1]))
    if not controls:
        return True
    if any(control not in {"if", "end"} for _, control in controls):
        return False
    leading = [m for m, c in controls if c == "if"]
    trailing = [m for m, c in controls if c == "end"]
    if (
        len(leading) != len(trailing)
        or not leading
        or leading[-1].end() > trailing[0].start()
    ):
        return False
    # Only complete document wrappers; branches inside YAML remain unsupported.
    return (
        not ACTION.sub("", source[: leading[-1].end()]).strip()
        and not ACTION.sub("", source[trailing[0].start() :]).strip()
    )


def _hash(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()


def _project(source: str) -> str:
    def mask(match: re.Match[str]) -> str:
        text = match.group()
        start = source.rfind("\n", 0, match.start()) + 1
        standalone = not source[start : match.start()].strip()
        return "".join("\n" if c == "\n" else " " if standalone else "x" for c in text)

    return ACTION.sub(mask, source)


def _pairs(node: Node | None) -> dict[str, Node]:
    if not isinstance(node, MappingNode) or (node.flow_style and node.value):
        raise ValueError("unsupported_mapping")
    pairs = {}
    for key, value in node.value:
        if not isinstance(key, ScalarNode) or key.value in pairs or key.value == "<<":
            raise ValueError("ambiguous_mapping")
        pairs[key.value] = value
    return pairs


def _plain(node: Node, source: str) -> Any:
    text = source[node.start_mark.index : node.end_mark.index]
    if "{{" in text or re.search(r"[&*][\w-]+", text):
        raise ValueError("unresolved_binding")
    return yaml.safe_load(text)


def _value(node: Node, source: str) -> Any:
    if isinstance(node, MappingNode):
        return {k: _value(v, source) for k, v in _pairs(node).items()}
    if isinstance(node, SequenceNode):
        return [_value(v, source) for v in node.value]
    return _plain(node, source)


def _insert(
    node: Node, text: str, edits: list[tuple[int, int, str]], source: str
) -> None:
    _pairs(node)
    if node.flow_style:
        start = source.rfind("\n", 0, node.start_mark.index) + 1
        line = source[start : node.start_mark.index]
        indent = " " * (len(line) - len(line.lstrip()) + 2)
        edits.append(
            (
                node.start_mark.index,
                node.end_mark.index,
                "\n" + "\n".join(indent + line for line in text.splitlines()),
            )
        )
        return
    end = _offset(node, source)
    # Mapping end points at the next sibling's first token, not its indentation.
    start = source.rfind("\n", 0, end) + 1
    offset = start if not source[start:end].strip() else end
    prefix = "\n" if offset and source[offset - 1] != "\n" else ""
    indent = " " * node.start_mark.column
    edits.append(
        (
            offset,
            offset,
            prefix + "".join(indent + line + "\n" for line in text.splitlines()),
        )
    )


def _offset(node: Node, source: str) -> int:
    """Keep insertions inside trailing whole-document Helm conditional guards."""
    last = node
    while True:
        if isinstance(last, MappingNode) and last.value:
            last = last.value[-1][1]
        elif isinstance(last, SequenceNode) and last.value:
            last = last.value[-1]
        else:
            break
    for action in ACTION.finditer(source, last.end_mark.index, node.end_mark.index):
        if re.match(r"{{-?\s*end\b", action.group()):
            return source.rfind("\n", 0, action.start()) + 1
    return int(node.end_mark.index)


def _dump(data: Any) -> str:
    return str(yaml.safe_dump(data, sort_keys=False, default_flow_style=False)).rstrip()


def _edit_order(item: tuple[int, tuple[int, int, str]]) -> tuple[int, int, bool, int]:
    index, (start, _, replacement) = item
    text = replacement.lstrip("\n")
    indent = len(text) - len(text.lstrip(" "))
    # Indentless sequences still belong inside their preceding mapping key.
    mapping = not text.lstrip().startswith(("-", "{{"))
    return start, -indent, mapping, index


def _add_missing(
    node: Node,
    additions: dict[str, Any],
    source: str,
    edits: list[tuple[int, int, str]],
    expressions: dict[tuple[str, ...], str],
    prefix: tuple[str, ...] = (),
) -> None:
    pairs = _pairs(node)
    missing = {}
    for key, value in additions.items():
        if key in pairs:
            if isinstance(value, dict):
                _add_missing(
                    pairs[key], value, source, edits, expressions, (*prefix, key)
                )
            continue
        missing[key] = value
    if missing:
        text = _dump(missing)
        for key in missing:
            path = (*prefix, key)
            if path in expressions:
                replacement = expressions[path]
                pattern = re.compile(
                    r"(?ms)^" + re.escape(key) + r":.*?(?=^[^\s-][^:\n]*:|\Z)"
                )
                text = pattern.sub(
                    (key + ": " + replacement + "\n").replace("\\", "\\\\"), text
                ).rstrip()
        _insert(node, text, edits, source)


def _quantity(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None

    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(m|Ki|Mi|Gi|Ti|k|M|G|T)?", str(value))
    if not match:
        return None
    scales: dict[str | None, Decimal | int] = {
        None: 1,
        "m": Decimal(".001"),
        "Ki": 1024,
        "Mi": 1024**2,
        "Gi": 1024**3,
        "Ti": 1024**4,
        "k": 1000,
        "M": 1000**2,
        "G": 1000**3,
        "T": 1000**4,
    }
    try:
        return Decimal(match[1]) * scales[match[2]]
    except InvalidOperation:
        return None


def _bind_values(
    node: Node,
    additions: dict[str, Any],
    base: str,
    prefix: tuple[str, ...] = (),
) -> dict[tuple[str, ...], str]:
    expressions = {}
    pairs = _pairs(node)
    for key, value in additions.items():
        path = (*prefix, key)
        if key in pairs and isinstance(value, dict):
            expressions.update(_bind_values(pairs[key], value, base, path))
        elif key not in pairs:
            expression = "{{ toYaml " + base + "." + ".".join(path)
            if isinstance(value, (dict, list)):
                expression += " | nindent " + str(node.start_mark.column + 2)
            expressions[path] = expression + " }}"
    return expressions


def _defaults(
    container: dict[str, Any], pod: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    own = container.get("securityContext", {})
    inherited = pod.get("securityContext", {})
    if not isinstance(own, dict) or not isinstance(inherited, dict):
        raise ValueError("unresolved_security_context")
    effective = {**inherited, **own}
    security: dict[str, Any] = {}
    skips = []
    root = effective.get("runAsUser") == 0 or effective.get("runAsNonRoot") is False
    unresolved_identity = any(
        key in effective and type(effective[key]) is not expected
        for key, expected in (
            ("runAsUser", int),
            ("runAsGroup", int),
            ("runAsNonRoot", bool),
        )
    )
    privileged = own.get("privileged") is True
    capabilities = own.get("capabilities", {})
    if not isinstance(capabilities, dict):
        raise ValueError("unresolved_capabilities")
    for key, value in SECURITY.items():
        if key in effective:
            if key == "capabilities" and not privileged and capabilities == {}:
                security[key] = {"drop": ["ALL"]}
            elif key == "seccompProfile" and not privileged and effective[key] == {}:
                security[key] = {"type": "RuntimeDefault"}
            continue
        if key in {"runAsNonRoot", "runAsUser", "runAsGroup"} and (
            root or unresolved_identity
        ):
            skips.append("explicit_or_unresolved_identity")
            continue
        if key == "allowPrivilegeEscalation" and (
            privileged or "SYS_ADMIN" in capabilities.get("add", [])
        ):
            skips.append("explicit_privilege_requirement")
            continue
        if key == "capabilities" and privileged:
            skips.append("explicit_privilege_requirement")
            continue
        if key == "seccompProfile" and privileged:
            skips.append("explicit_privilege_requirement")
            continue
        security[key] = copy.deepcopy(value)
    resources = container.get("resources", {})
    if not isinstance(resources, dict):
        raise ValueError("unresolved_resources")
    additions: dict[str, Any] = {}
    for resource in ("cpu", "memory"):
        request_map, limit_map = (
            resources.get("requests", {}),
            resources.get("limits", {}),
        )
        if not isinstance(request_map, dict) or not isinstance(limit_map, dict):
            skips.append("unresolved_resources")
            continue
        request = _quantity(request_map.get(resource, RESOURCES["requests"][resource]))
        limit = _quantity(limit_map.get(resource, RESOURCES["limits"][resource]))
        if request is None or limit is None or request > limit:
            skips.append("inconsistent_or_unresolved_resources")
            continue
        for field in ("requests", "limits"):
            if resource not in resources.get(field, {}):
                additions.setdefault(field, {})[resource] = RESOURCES[field][resource]
    return {
        **({"securityContext": security} if security else {}),
        **({"resources": additions} if additions else {}),
    }, sorted(set(skips))


def _path(node: Node, *parts: str) -> Node:
    for part in parts:
        node = _pairs(node)[part]
    return node


def _known_identity(context: Any) -> bool:
    return isinstance(context, dict) and all(
        key not in context or type(context[key]) is expected
        for key, expected in (
            ("runAsUser", int),
            ("runAsGroup", int),
            ("runAsNonRoot", bool),
        )
    )


def values_document(source: str) -> dict[str, Any]:
    """Reject duplicate keys/aliases rather than append to ambiguous values."""
    seen: set[int] = set()

    def inspect(node: Node) -> None:
        if id(node) in seen:
            raise ValueError("ambiguous_values_alias")
        seen.add(id(node))
        if isinstance(node, MappingNode):
            keys: set[str] = set()
            for key, child in node.value:
                if (
                    not isinstance(key, ScalarNode)
                    or key.value in keys
                    or key.value == "<<"
                ):
                    raise ValueError("ambiguous_values_mapping")
                keys.add(key.value)
                inspect(child)
        elif isinstance(node, SequenceNode):
            for child in node.value:
                inspect(child)

    node = yaml.compose(source, Loader=yaml.SafeLoader)
    if node is not None:
        inspect(node)
    data = yaml.safe_load(source) or {}
    if not isinstance(data, dict):
        raise ValueError("unsupported_values_document")
    return data


def repair_pods(
    files: dict[str, str],
    rendered: dict[str, list[dict[str, Any]]] | None = None,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Pure edits. Helm requires authoritative output grouped by source path."""
    result = dict(files)
    records: list[dict[str, Any]] = []
    values_additions: dict[str, dict[str, Any]] = defaultdict(dict)
    for path, source in sorted(files.items()):
        helm = path.startswith("helm/") and "/templates/" in path
        if not path.endswith((".yaml", ".yml")) or not (
            helm or path.startswith("k8s/")
        ):
            continue
        if helm and (rendered is None or path not in rendered):
            continue
        if helm and ".Values.infraarchSecurity." in source:
            continue
        edits: list[tuple[int, int, str]] = []
        local_records: list[dict[str, Any]] = []
        values_before = copy.deepcopy(values_additions)
        try:
            if not _static_structure(source):
                raise ValueError("dynamic_template_structure")
            projected = _project(source) if helm else source
            nodes = list(yaml.compose_all(projected, Loader=yaml.SafeLoader))
            for index, node in enumerate(nodes):
                if node is None:
                    continue
                fields = _pairs(node)
                kind = _plain(fields["kind"], source) if "kind" in fields else None
                if kind not in KINDS:
                    continue
                if re.search(
                    r"[&*][\w-]+", source[node.start_mark.index : node.end_mark.index]
                ):
                    raise ValueError("ambiguous_alias")
                pod_node = _path(node, "spec", "template", "spec")
                pod_fields = _pairs(pod_node)
                if helm:
                    assert rendered is not None
                    matches = [d for d in rendered[path] if d.get("kind") == kind]
                    if len(matches) != 1:
                        raise ValueError("ambiguous_render_binding")
                    document = matches[0]
                    pod = document["spec"]["template"]["spec"]
                else:
                    document = _value(node, source)
                    pod = document["spec"]["template"]["spec"]
                if (
                    pod.get("os", {}).get("name") == "windows"
                    or pod.get("nodeSelector", {}).get("kubernetes.io/os") == "windows"
                ):
                    continue
                workload = str(document.get("metadata", {}).get("name", kind))[:128]
                wid = "w" + _hash(f"{path}:{index}:{kind}")[:12]
                root = path.split("/templates/", 1)[0]
                value_path = root + "/values.yaml"
                volume_fragments: list[str] = []
                consumers = [*pod.get("containers", []), *pod.get("initContainers", [])]
                inherited = pod.get("securityContext", {})
                # Never introduce inherited identity conflicting with a consumer.
                safe_identity = _known_identity(inherited) and all(
                    _known_identity(c.get("securityContext", {}))
                    and c.get("securityContext", {}).get("runAsUser") != 0
                    and c.get("securityContext", {}).get("runAsNonRoot") is not False
                    and c.get("securityContext", {}).get("privileged") is not True
                    for c in consumers
                )
                pod_defaults = {}
                if (
                    safe_identity
                    and inherited.get("runAsUser") != 0
                    and inherited.get("runAsNonRoot") is not False
                ):
                    pod_defaults = {
                        key: copy.deepcopy(SECURITY[key])
                        for key in (
                            "runAsNonRoot",
                            "runAsUser",
                            "runAsGroup",
                            "seccompProfile",
                        )
                        if key not in inherited
                    }
                if pod_defaults:
                    pod_additions = {"securityContext": pod_defaults}
                    pod_expressions = (
                        _bind_values(
                            pod_node, pod_additions, f".Values.infraarchSecurity.{wid}"
                        )
                        if helm
                        else {}
                    )
                    _add_missing(
                        pod_node, pod_additions, source, edits, pod_expressions
                    )
                    if helm:
                        values_additions[value_path].setdefault(wid, {})[
                            "securityContext"
                        ] = pod_defaults
                    local_records.append(
                        {
                            "file": path,
                            "kind": "kubernetes_pod_defaults",
                            "name": workload,
                            "workload": workload,
                            "container": "pod",
                            "catalogue_entry": "pod_identity_seccomp",
                            "rule_ids": [
                                "CKV_K8S_23",
                                "CKV_K8S_40",
                                "KSV-0012",
                                "KSV-0118",
                                "KSV-0104",
                            ],
                            "changed_fields": [
                                "pod.securityContext." + key for key in pod_defaults
                            ],
                            "override_location": value_path
                            + ":infraarchSecurity."
                            + wid
                            + ".securityContext"
                            if helm
                            else path,
                            "runtime_compatibility": "unverified",
                        }
                    )
                for group in ("containers", "initContainers"):
                    sequence = pod_fields.get(group)
                    if sequence is None:
                        continue
                    if not isinstance(sequence, SequenceNode) or sequence.flow_style:
                        raise ValueError("dynamic_containers")
                    rendered_containers = pod.get(group, [])
                    for cindex, container_node in enumerate(sequence.value):
                        cfields = _pairs(container_node)
                        name_node = cfields["name"]
                        name_source = source[
                            name_node.start_mark.index : name_node.end_mark.index
                        ]
                        if helm and "{{" in name_source:
                            if len(sequence.value) != len(rendered_containers):
                                raise ValueError("ambiguous_container_binding")
                            cname = rendered_containers[cindex].get("name")
                        else:
                            cname = _plain(name_node, source)
                        matches = [
                            c for c in rendered_containers if c.get("name") == cname
                        ]
                        if len(matches) != 1 or not isinstance(cname, str):
                            raise ValueError("ambiguous_container_binding")
                        container = matches[0]
                        additions, skips = _defaults(container, pod)
                        # Existing templated maps are intentionally not overwritten.
                        for field in list(additions):
                            if field in cfields:
                                try:
                                    _value(cfields[field], source)
                                except (ValueError, yaml.YAMLError):
                                    del additions[field]
                                    skips.append("unsupported_template_binding")
                        cid = ("i" if group == "initContainers" else "c") + str(cindex)
                        base = f".Values.infraarchSecurity.{wid}.{cid}"
                        expressions: dict[tuple[str, ...], str] = {}
                        defaults = copy.deepcopy(additions)
                        if helm:
                            expressions = _bind_values(container_node, additions, base)
                        writable = (
                            additions.get("securityContext", {}).get(
                                "readOnlyRootFilesystem"
                            )
                            is True
                        )
                        mounts = container.get("volumeMounts", [])
                        if not isinstance(mounts, list) or any(
                            not isinstance(m, dict)
                            or not isinstance(m.get("mountPath"), str)
                            for m in mounts
                        ):
                            writable = False
                            skips.append("unresolved_mounts")
                        if writable and any(
                            m["mountPath"] == "/"
                            or m["mountPath"] == "/tmp"
                            or m["mountPath"].startswith("/tmp/")
                            for m in mounts
                        ):
                            writable = False
                            skips.append("existing_or_overlapping_mount")
                        volume_name = "infraarch-tmp-" + wid[1:] + "-" + cid
                        volume_names = {
                            v.get("name")
                            for v in pod.get("volumes", [])
                            if isinstance(v, dict)
                        }
                        if writable and volume_name in volume_names:
                            writable = False
                            skips.append("volume_name_collision")
                        if writable:
                            mount = {"name": volume_name, "mountPath": "/tmp"}
                            if "volumeMounts" in cfields:
                                # Extend static sequences without reserialising them.
                                seq = cfields["volumeMounts"]
                                if not isinstance(seq, SequenceNode) or seq.flow_style:
                                    raise ValueError("unsupported_mounts")
                                offset = source.rfind("\n", 0, _offset(seq, source)) + 1
                                text = "".join(
                                    " " * seq.start_mark.column + line + "\n"
                                    for line in _dump([mount]).splitlines()
                                )
                                edits.append((offset, offset, text))
                            else:
                                additions["volumeMounts"] = [mount]
                            volume = {"name": volume_name, "emptyDir": {}}
                            if helm:
                                defaults["writablePaths"] = ["/tmp"]
                                mount_text = (
                                    "{{ range $i, $path := "
                                    + base
                                    + ".writablePaths }}\n  - name: "
                                    + volume_name
                                    + "-{{ $i }}\n"
                                    + "    mountPath: {{ $path | quote }}\n{{ end }}"
                                )
                                if "volumeMounts" in cfields:
                                    raise ValueError(
                                        "existing_mount_template_extension"
                                    )
                                expressions[("volumeMounts",)] = "\n" + mount_text
                                vtext = (
                                    "{{ range $i, $path := "
                                    + base
                                    + ".writablePaths }}\n- name: "
                                    + volume_name
                                    + "-{{ $i }}\n  emptyDir: {}\n{{ end }}"
                                )
                            else:
                                vtext = _dump([volume])
                            volume_fragments.append(vtext)
                        if not additions and not skips:
                            continue
                        _add_missing(
                            container_node, additions, source, edits, expressions
                        )
                        if helm and additions:
                            values_additions[value_path].setdefault(wid, {})[cid] = (
                                defaults
                            )
                        local_records.append(
                            {
                                "file": path,
                                "kind": "kubernetes_pod_defaults",
                                "name": workload,
                                "workload": workload,
                                "container": cname[:128],
                                "catalogue_entry": "pod_security",
                                "rule_ids": sorted(
                                    {r for rules in CONTROLS.values() for r in rules}
                                ),
                                "changed_fields": sorted(additions),
                                "skipped_reasons": sorted(set(skips)),
                                "outcome": "skipped" if not additions else None,
                                "reason": ",".join(sorted(set(skips))) or None,
                                "override_location": value_path
                                + ":infraarchSecurity."
                                + wid
                                + "."
                                + cid
                                if helm
                                else path,
                                "runtime_compatibility": "unverified",
                            }
                        )
                if volume_fragments:
                    vtext = "\n".join(volume_fragments)
                    if "volumes" in pod_fields:
                        seq = pod_fields["volumes"]
                        if not isinstance(seq, SequenceNode) or seq.flow_style:
                            raise ValueError("unsupported_volumes")
                        offset = source.rfind("\n", 0, _offset(seq, source)) + 1
                        text = "".join(
                            " " * seq.start_mark.column + line + "\n"
                            for line in vtext.splitlines()
                        )
                        edits.append((offset, offset, text))
                    else:
                        _insert(
                            pod_node,
                            "volumes:\n"
                            + "\n".join("  " + line for line in vtext.splitlines()),
                            edits,
                            source,
                        )
            content = source
            for _, (start, end, replacement) in sorted(
                enumerate(edits),
                key=_edit_order,
                reverse=True,
            ):
                content = content[:start] + replacement + content[end:]
            if content != source:
                if not helm:
                    for candidate_node in yaml.compose_all(
                        content, Loader=yaml.SafeLoader
                    ):
                        if candidate_node is not None:
                            _value(candidate_node, content)
                result[path] = content
                for record in local_records:
                    record.update(before_hash=_hash(source), after_hash=_hash(content))
            for record in local_records:
                record.update(before_hash=_hash(source), after_hash=_hash(content))
            records.extend(local_records)
        except (
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            yaml.YAMLError,
            RecursionError,
        ) as error:
            # No partial edits or values survive an ambiguous document/file.
            values_additions = values_before
            reason = (
                str(error)
                if isinstance(error, ValueError)
                and re.fullmatch(r"[a-z_]{1,64}", str(error))
                else "unsupported_document_structure"
            )
            records.append(
                {
                    "file": path,
                    "kind": "kubernetes_pod_defaults",
                    "name": "unresolved",
                    "outcome": "skipped",
                    "reason": reason,
                    "before_hash": _hash(source),
                    "after_hash": _hash(source),
                }
            )
            continue
    for path, additions in values_additions.items():
        if not additions:
            continue
        old = files.get(path, "")
        try:
            existing = values_document(old)
            if not isinstance(existing, dict) or "infraarchSecurity" in existing:
                # Preserve any operator-owned catalogue namespace.
                raise ValueError("existing_catalogue_values")
            content = (
                old
                + ("\n" if old and not old.endswith("\n") else "")
                + "\n# D-56: runtime compatibility unverified.\n"
                + "# Operator overrides supported.\n"
                + _dump({"infraarchSecurity": additions})
                + "\n"
            )
            result[path] = content
        except (ValueError, yaml.YAMLError):
            for record in list(records):
                if record.get("override_location", "").startswith(path + ":"):
                    result[record["file"]] = files[record["file"]]
                    records.remove(record)
    return result, records
