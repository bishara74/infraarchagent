"""D-56: version-bound AWS v6 migrations from the documented upgrade guide."""

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any

from lark import Tree

from app.security.terraform import Resource, TerraformPackage
from app.validation.idioms import json_spans


def replacement(
    package: TerraformPackage, resource: Resource, old: str
) -> tuple[str, Any, str] | None:
    """Only known, unambiguous equivalents; never change provider constraints."""
    version = package.version(resource.module)
    schema = package.schema(resource)
    if not version or not version.startswith("6.") or schema is None:
        return None
    body = resource.body
    value = body.get(old)
    if old in schema.get("attributes", {}):
        return None
    result: tuple[str, Any, str] | None = None
    if resource.type == "aws_eip" and old == "vpc" and value is True:
        result = ("domain", "vpc", "eip_v6_domain")
    elif (
        resource.type == "aws_ssm_association"
        and old == "instance_id"
        and isinstance(value, str)
        and value.strip()
        and value != "*"
        and "dynamic" not in body
    ):
        result = (
            "targets",
            [{"key": "InstanceIds", "values": [value]}],
            "ssm_v6_targets",
        )
    elif (
        resource.type == "aws_flow_log"
        and old == "log_group_name"
        and body.get("log_destination_type", "cloud-watch-logs") == "cloud-watch-logs"
        and isinstance(value, str)
        and re.fullmatch(r"\$\{aws_cloudwatch_log_group\.[\w-]+\.name\}", value)
    ):
        target = package.resolve(resource.module, value)
        if target is not None and target.type == "aws_cloudwatch_log_group":
            result = (
                "log_destination",
                value.removesuffix(".name}") + ".arn}",
                "flow_log_v6_destination",
            )
    if result is None or result[0] in body:
        return None
    supported = schema.get(
        "block_types" if result[0] == "targets" else "attributes", {}
    )
    if result[0] not in supported:
        return None
    return result


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous_json")
        result[key] = value
    return result


def repair_v6_equivalents(
    files: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Produce source-preserving proposals for the existing candidate guard."""
    package = TerraformPackage(files)
    result, records = dict(files), []
    ambiguous_modules = set()
    for path, doc in package.documents.documents.items():
        if path.endswith(".tf.json") and not doc.parse_error:
            try:
                json.loads(doc.source, object_pairs_hook=_unique_object)
            except ValueError:
                ambiguous_modules.add(str(PurePosixPath(path).parent))
    for path, doc in package.documents.documents.items():
        module = str(PurePosixPath(path).parent)
        if (
            doc.parse_error
            or not package.module_safe(module)
            or module in ambiguous_modules
        ):
            continue
        source = files[path]
        edits: list[tuple[int, int, str, str, str]] = []
        if path.endswith(".tf.json"):
            spans = json_spans(source)
            for parts, start, end, _ in spans:
                if len(parts) != 4 or parts[0] != "resource":
                    continue
                resource = package.get(module, f"{parts[1]}.{parts[2]}")
                if resource is None:
                    continue
                old = str(parts[3])
                change = replacement(package, resource, old)
                if change is None:
                    continue
                new, value, kind = change
                key = source.rfind(json.dumps(old), 0, start)
                if key < 0:
                    continue
                edits.extend(
                    [
                        (
                            key,
                            key + len(json.dumps(old)),
                            json.dumps(new),
                            kind,
                            resource.address,
                        ),
                        (start, end, json.dumps(value), kind, resource.address),
                    ]
                )
        elif doc.tree is not None:
            for node in doc.tree.find_data("block"):
                head = re.match(
                    r'resource\s+"([\w-]+)"\s+"([\w-]+)"\s*\{',
                    source[node.meta.start_pos : node.meta.end_pos],
                )
                if not head:
                    continue
                resource = package.get(module, ".".join(head.groups()))
                if resource is None:
                    continue
                body = next(
                    (
                        n
                        for n in node.children
                        if isinstance(n, Tree) and n.data == "body"
                    ),
                    None,
                )
                if body is None:
                    continue
                attributes = [
                    n
                    for n in body.children
                    if isinstance(n, Tree) and n.data == "attribute"
                ]
                for attr in attributes:
                    text = source[attr.meta.start_pos : attr.meta.end_pos]
                    match = re.match(r"([\w-]+)\s*=", text)
                    if not match:
                        continue
                    old = match[1]
                    if (
                        sum(
                            bool(
                                re.match(
                                    rf"{old}\s*=",
                                    source[n.meta.start_pos : n.meta.end_pos],
                                )
                            )
                            for n in attributes
                        )
                        != 1
                    ):
                        continue
                    change = replacement(package, resource, old)
                    if change is None:
                        continue
                    new, value, kind = change
                    if new == "targets":
                        # Keep the exact original expression rather than serializing
                        # hcl2's interpolation representation back into a string.
                        expression = text[match.end() :].strip()
                        rendered = (
                            'targets {\n    key = "InstanceIds"\n    values = ['
                            + expression
                            + "]\n  }"
                        )
                        if node.meta.line == node.meta.end_line:
                            rendered = "\n  " + rendered + "\n"
                    elif new == "log_destination":
                        rendered = "log_destination = " + value[2:-1]
                    else:
                        rendered = 'domain = "vpc"'
                    edits.append(
                        (
                            attr.meta.start_pos,
                            attr.meta.end_pos,
                            rendered,
                            kind,
                            resource.address,
                        )
                    )
        for start, end, rendered, _, _ in sorted(edits, reverse=True):
            result[path] = result[path][:start] + rendered + result[path][end:]
        for kind, address in sorted(
            {(kind, address) for _, _, _, kind, address in edits}
        ):
            start = min(a for a, _, _, k, n in edits if (k, n) == (kind, address))
            records.append(
                {
                    "file": path,
                    "kind": kind,
                    "name": address,
                    "line": source.count("\n", 0, start) + 1,
                    "before_hash": hashlib.sha256(source.encode()).hexdigest(),
                    "after_hash": hashlib.sha256(result[path].encode()).hexdigest(),
                }
            )
    return result, records
