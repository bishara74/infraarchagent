"""D-56: parameterise image identities without asserting their trust or safety."""

import re
from typing import Any

import yaml  # type: ignore[import-untyped]
from yaml.nodes import SequenceNode  # type: ignore[import-untyped]

from app.security.kubernetes import (
    KINDS,
    _dump,
    _hash,
    _pairs,
    _path,
    _plain,
    _project,
    values_document,
)


def image_parts(image: str) -> dict[str, str] | None:
    if not image or re.search(r"\s|[{}\"']", image) or image.count("@") > 1:
        return None
    name, separator, digest = image.partition("@")
    repository, tag = name, ""
    if ":" in name.rsplit("/", 1)[-1]:
        repository, tag = name.rsplit(":", 1)
        if not tag:
            return None
    if not repository or (separator and not digest):
        return None
    return {"repository": repository, "tag": tag, "digest": digest}


def repair_image_values(
    files: dict[str, str],
    rendered: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    result, records = dict(files), []
    values_by_chart: dict[str, dict[str, Any]] = {}
    for path, source in sorted(files.items()):
        if path not in rendered or not path.startswith("helm/"):
            continue
        chart = path.split("/templates/", 1)[0]
        values_path = chart + "/values.yaml"
        try:
            values = values_document(files.get(values_path, ""))
            if not isinstance(values, dict) or "infraarchImages" in values:
                continue
            edits, additions, local_records = [], {}, []
            for index, node in enumerate(
                yaml.compose_all(_project(source), Loader=yaml.SafeLoader)
            ):
                if node is None:
                    continue
                fields = _pairs(node)
                kind = _plain(fields["kind"], source) if "kind" in fields else None
                if kind not in KINDS:
                    continue
                matches = [d for d in rendered[path] if d.get("kind") == kind]
                if len(matches) != 1:
                    continue
                document = matches[0]
                pod = document["spec"]["template"]["spec"]
                pod_node = _path(node, "spec", "template", "spec")
                for group in ("containers", "initContainers"):
                    sequence = _pairs(pod_node).get(group)
                    if not isinstance(sequence, SequenceNode):
                        continue
                    for cindex, container in enumerate(sequence.value):
                        fields = _pairs(container)
                        image_node = fields.get("image")
                        if image_node is None:
                            continue
                        if (
                            "{{"
                            in source[
                                image_node.start_mark.index : image_node.end_mark.index
                            ]
                        ):
                            continue
                        image = _plain(image_node, source)
                        name_node = fields["name"]
                        if (
                            "{{"
                            in source[
                                name_node.start_mark.index : name_node.end_mark.index
                            ]
                        ):
                            rendered_containers = pod.get(group, [])
                            if len(rendered_containers) != len(sequence.value):
                                continue
                            name = rendered_containers[cindex].get("name")
                        else:
                            name = _plain(name_node, source)
                        if not isinstance(image, str):
                            continue
                        found = [
                            c
                            for c in pod.get(group, [])
                            if c.get("name") == name and c.get("image") == image
                        ]
                        parts = image_parts(image)
                        if len(found) != 1 or parts is None:
                            continue
                        identifier = (
                            "i" + _hash(f"{path}:{index}:{group}:{cindex}")[:12]
                        )
                        base = ".Values.infraarchImages." + identifier
                        expression = (
                            '{{ printf "%s%s%s" '
                            + base
                            + '.repository (ternary (printf ":%s" '
                            + base
                            + '.tag) "" (ne '
                            + base
                            + '.tag "")) (ternary (printf "@%s" '
                            + base
                            + '.digest) "" (ne '
                            + base
                            + '.digest "")) | quote }}'
                        )
                        edits.append(
                            (
                                image_node.start_mark.index,
                                image_node.end_mark.index,
                                expression,
                            )
                        )
                        additions[identifier] = parts
                        local_records.append(
                            {
                                "file": path,
                                "kind": "kubernetes_image_values",
                                "name": str(name)[:128],
                                "workload": str(
                                    document.get("metadata", {}).get("name", kind)
                                )[:128],
                                "container": str(name)[:128],
                                "catalogue_entry": "image_configuration",
                                "rule_ids": ["CKV_K8S_14", "KSV-0013", "KSV-0125"],
                                "changed_fields": ["image"],
                                "override_location": values_path
                                + ":infraarchImages."
                                + identifier,
                                "reason": "identity_preserved_no_trust_claim",
                            }
                        )
            content = source
            for start, end, replacement in sorted(edits, reverse=True):
                content = content[:start] + replacement + content[end:]
            if content != source:
                result[path] = content
                values_by_chart.setdefault(values_path, {}).update(additions)
                for record in local_records:
                    record.update(before_hash=_hash(source), after_hash=_hash(content))
                records.extend(local_records)
        except (ValueError, TypeError, KeyError, yaml.YAMLError, RecursionError):
            continue
    for path, additions in values_by_chart.items():
        old = result.get(path, "")
        result[path] = (
            old
            + ("\n" if old and not old.endswith("\n") else "")
            + "\n# Existing image identities; trust remains an operator decision.\n"
            + _dump({"infraarchImages": additions})
            + "\n"
        )
    return result, records
