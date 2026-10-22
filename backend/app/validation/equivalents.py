"""D-56: only documented, value-preserving Terraform equivalences."""

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any

from lark import Tree

from app.security.terraform import TerraformPackage
from app.validation.file_paths import repair_file_paths
from app.validation.idioms import json_spans
from app.validation.v6_equivalents import repair_v6_equivalents


def repair_equivalents(
    files: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    files, records = repair_v6_equivalents(files)
    files, path_records = repair_file_paths(files)
    records.extend(path_records)
    package = TerraformPackage(files)
    result = dict(files)
    for path, doc in package.documents.documents.items():
        if doc.parse_error or not package.module_safe(str(PurePosixPath(path).parent)):
            continue
        edits: list[tuple[int, int, str, str, str]] = []
        source = files[path]
        if path.endswith(".tf.json"):
            spans = json_spans(source)
            for parts, start, end, value in spans:
                if len(parts) < 4 or parts[0] != "resource":
                    continue
                typ, name, old = str(parts[1]), str(parts[2]), str(parts[-1])
                resource = package.get(str(PurePosixPath(path).parent), f"{typ}.{name}")
                if resource is None or package.schema(resource) is None:
                    continue
                parent = next((v for p, a, b, v in spans if p == parts[:-1]), None)
                if not isinstance(parent, dict):
                    continue
                new = (
                    "db_name"
                    if typ == "aws_db_instance" and len(parts) == 4 and old == "name"
                    else "cidr_block"
                    if typ in {"aws_route_table", "aws_default_route_table"}
                    and "route" in parts[3:-1]
                    and old in {"cidr_ipv4", "cidr_blocks"}
                    else None
                )
                if not new or new in parent:
                    continue
                if (
                    new == "cidr_block"
                    and {"cidr_ipv4", "cidr_blocks"} <= parent.keys()
                ):
                    continue
                if old == "cidr_blocks":
                    if not isinstance(value, list) or len(value) != 1:
                        continue
                    child_span = next(
                        ((a, b) for p, a, b, v in spans if p == (*parts, 0)), None
                    )
                    if child_span is None:
                        continue
                    edits.append(
                        (
                            start,
                            end,
                            source[child_span[0] : child_span[1]],
                            "route_cidr",
                            f"{typ}.{name}",
                        )
                    )
                key = source.rfind(json.dumps(old), 0, start)
                edits.append(
                    (
                        key,
                        key + len(json.dumps(old)),
                        json.dumps(new),
                        "db_name" if new == "db_name" else "route_cidr",
                        f"{typ}.{name}",
                    )
                )
        elif doc.tree is not None:
            for node in doc.tree.find_data("block"):
                head = re.match(
                    r'resource\s+"([\w-]+)"\s+"([\w-]+)"\s*\{',
                    source[node.meta.start_pos : node.meta.end_pos],
                )
                if not head:
                    continue
                typ, name = head.groups()
                resource = package.get(str(PurePosixPath(path).parent), f"{typ}.{name}")
                if resource is None or package.schema(resource) is None:
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
                scopes = [(body, "root")]
                for child in body.children:
                    if isinstance(child, Tree) and child.data == "block":
                        label = re.match(
                            r"(route|condition)\s*\{",
                            source[child.meta.start_pos : child.meta.end_pos],
                        )
                        nested = next(
                            (
                                n
                                for n in child.children
                                if isinstance(n, Tree) and n.data == "body"
                            ),
                            None,
                        )
                        if label and nested is not None:
                            scopes.append((nested, label[1]))
                for scope, kind in scopes:
                    attributes = {}
                    for attr in scope.children:
                        if isinstance(attr, Tree) and attr.data == "attribute":
                            text = source[attr.meta.start_pos : attr.meta.end_pos]
                            match = re.match(r"([\w-]+)\s*=", text)
                            if match:
                                attributes[match[1]] = attr
                    pairs = (
                        [("name", "db_name", "db_name")]
                        if typ == "aws_db_instance" and kind == "root"
                        else [
                            ("cidr_ipv4", "cidr_block", "route_cidr"),
                            ("cidr_blocks", "cidr_block", "route_cidr"),
                        ]
                        if typ in {"aws_route_table", "aws_default_route_table"}
                        and kind == "route"
                        else []
                    )
                    if all(k in attributes for k in ("cidr_ipv4", "cidr_blocks")):
                        continue
                    for old, new, repair in pairs:
                        if old not in attributes or new in attributes:
                            continue
                        attr = attributes[old]
                        text = source[attr.meta.start_pos : attr.meta.end_pos]
                        replacement = new + text[len(old) :]
                        if old == "cidr_blocks":
                            tuples = list(attr.find_data("tuple"))
                            if len(tuples) != 1:
                                continue
                            expressions = [
                                n
                                for n in tuples[0].children
                                if isinstance(n, Tree) and n.data == "expr_term"
                            ]
                            if len(expressions) != 1:
                                continue
                            expr = expressions[0]
                            replacement = (
                                new
                                + " = "
                                + source[expr.meta.start_pos : expr.meta.end_pos]
                            )
                        edits.append(
                            (
                                attr.meta.start_pos,
                                attr.meta.end_pos,
                                replacement,
                                repair,
                                resource.address,
                            )
                        )
                    if (
                        typ in {"aws_lb_listener_rule", "aws_alb_listener_rule"}
                        and kind == "condition"
                        and "path_pattern" in attributes
                    ):
                        attr = attributes["path_pattern"]
                        text = source[attr.meta.start_pos : attr.meta.end_pos]
                        if (
                            re.match(r"path_pattern\s*=\s*\{", text)
                            and len(list(attr.find_data("object"))) == 1
                        ):
                            edits.append(
                                (
                                    attr.meta.start_pos,
                                    attr.meta.end_pos,
                                    re.sub(
                                        r"path_pattern\s*=\s*",
                                        "path_pattern ",
                                        text,
                                        count=1,
                                    ),
                                    "listener_path_pattern",
                                    resource.address,
                                )
                            )
        for start, end, replacement, kind, name in sorted(edits, reverse=True):
            result[path] = result[path][:start] + replacement + result[path][end:]
            records.append(
                {
                    "file": path,
                    "kind": kind,
                    "name": name,
                    "line": source.count("\n", 0, start) + 1,
                    "before_hash": hashlib.sha256(source.encode()).hexdigest(),
                    "after_hash": hashlib.sha256(result[path].encode()).hexdigest(),
                }
            )
    return result, records
