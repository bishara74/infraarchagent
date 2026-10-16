"""Only the two author-approved, source-preserving Terraform idiom repairs."""

import json
import re
from typing import Any

import hcl2
from lark import Tree
from lark.exceptions import LarkError

# Recognize AWS field tokens, never arbitrary Terraform expressions.
FLOW_FIELDS = frozenset(
    (
        "version account-id interface-id srcaddr dstaddr srcport dstport protocol "
        "packets bytes start end action log-status vpc-id subnet-id instance-id "
        "tcp-flags type pkt-srcaddr pkt-dstaddr region az-id sublocation-type "
        "sublocation-id pkt-src-aws-service pkt-dst-aws-service flow-direction "
        "traffic-path ecs-cluster-arn ecs-cluster-name ecs-container-instance-arn "
        "ecs-container-instance-id ecs-container-id ecs-second-container-id ecs- "
        "service-name ecs-task-definition-arn ecs-task-arn ecs-task-id reject- "
        "reason encryption-status resource-id transit-gateway-id tgw-attachment-id "
        "tgw-src-vpc-account-id tgw-dst-vpc-account-id tgw-src-vpc-id tgw-dst-vpc- "
        "id tgw-src-subnet-id tgw-dst-subnet-id tgw-src-eni tgw-dst-eni tgw-src-az- "
        "id tgw-dst-az-id tgw-pair-attachment-id packets-lost-no-route packets- "
        "lost-blackhole packets-lost-mtu-exceeded packets-lost-ttl-expired "
    ).split()
)
FIELD = re.compile(r"(?<!\$)\$\{([a-z][a-z0-9-]*)\}")


def escape_fields(value: str) -> str:
    return FIELD.sub(lambda m: "$" + m[0] if m[1] in FLOW_FIELDS else m[0], value)


def json_spans(source: str) -> list[tuple[tuple[str | int, ...], int, int, Any]]:
    decoder = json.JSONDecoder()
    result = []

    def visit(position: int, path: tuple[str | int, ...]) -> int:
        while source[position].isspace():
            position += 1
        value, end = decoder.raw_decode(source, position)
        result.append((path, position, end, value))
        cursor = position + 1
        if isinstance(value, dict):
            for key in value:
                while source[cursor].isspace() or source[cursor] == ",":
                    cursor += 1
                _, cursor = decoder.raw_decode(source, cursor)
                while source[cursor].isspace() or source[cursor] == ":":
                    cursor += 1
                cursor = visit(cursor, (*path, key))
        elif isinstance(value, list):
            for index in range(len(value)):
                while source[cursor].isspace() or source[cursor] == ",":
                    cursor += 1
                cursor = visit(cursor, (*path, index))
        return end

    visit(0, ())
    return result


def remove_empty_json_rules(source: str) -> str:
    # Recompute comma boundaries after each deletion; unrelated bytes survive.
    for name in ("ingress", "egress"):
        for path, start, end, value in json_spans(source):
            if path != (name,):
                continue
            if value == {} or (
                isinstance(value, list) and value and all(v == {} for v in value)
            ):
                key = source.rfind('"' + name + '"', 0, start)
                right = end
                while right < len(source) and source[right].isspace():
                    right += 1
                if source[right : right + 1] == ",":
                    source = source[:key] + source[right + 1 :]
                else:
                    left = key - 1
                    while left >= 0 and source[left].isspace():
                        left -= 1
                    source = (
                        source[: left if source[left : left + 1] == "," else key]
                        + source[end:]
                    )
            elif isinstance(value, list) and any(v == {} for v in value):
                source = (
                    source[:start]
                    + json.dumps([v for v in value if v != {}])
                    + source[end:]
                )
            break
    return source


def repair_idioms(files: dict[str, str]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    result = dict(files)
    records: list[dict[str, Any]] = []
    for path, source in sorted(files.items()):
        if not path.startswith("terraform/") or not path.endswith((".tf", ".tf.json")):
            continue
        edits = []
        try:
            if path.endswith(".json"):
                for parts, start, end, value in json_spans(source):
                    if len(parts) == 3 and parts[:2] == (
                        "resource",
                        "aws_default_security_group",
                    ):
                        replacement = remove_empty_json_rules(source[start:end])
                        if replacement != source[start:end]:
                            edits.append(
                                (
                                    start,
                                    end,
                                    replacement,
                                    "empty_default_security_group_rule",
                                    str(parts[2]),
                                )
                            )
                    elif (
                        len(parts) == 4
                        and parts[:2] == ("resource", "aws_flow_log")
                        and parts[3] == "log_format"
                        and isinstance(value, str)
                    ):
                        replacement = escape_fields(value)
                        if replacement != value:
                            edits.append(
                                (
                                    start,
                                    end,
                                    json.dumps(replacement),
                                    "flow_log_placeholders",
                                    str(parts[2]),
                                )
                            )
            else:
                tree = hcl2.parses_to_tree(source)
                for resource in tree.find_data("block"):
                    header = re.match(
                        r'resource\s+"(aws_default_security_group|aws_flow_log)"\s+"([\w-]+)"\s*\{',
                        source[resource.meta.start_pos : resource.meta.end_pos],
                    )
                    if not header:
                        continue
                    body = next(
                        (
                            n
                            for n in resource.children
                            if isinstance(n, Tree) and n.data == "body"
                        ),
                        None,
                    )
                    if body is None:
                        continue
                    for child in body.children:
                        if not isinstance(child, Tree):
                            continue
                        start, end = child.meta.start_pos, child.meta.end_pos
                        text = source[start:end]
                        if (
                            header[1] == "aws_default_security_group"
                            and child.data == "block"
                        ):
                            if re.fullmatch(
                                r"(?:ingress|egress)\s*\{\s*(?:(?:\#[^\n]*|//[^\n]*|/\*[\s\S]*?\*/)\s*)*\}",
                                text,
                            ):
                                edits.append(
                                    (
                                        start,
                                        end,
                                        "",
                                        "empty_default_security_group_rule",
                                        header[2],
                                    )
                                )
                        elif (
                            header[1] == "aws_flow_log"
                            and child.data == "attribute"
                            and re.match(r"log_format\s*=", text)
                        ):
                            replacement = escape_fields(text)
                            if replacement != text:
                                edits.append(
                                    (
                                        start,
                                        end,
                                        replacement,
                                        "flow_log_placeholders",
                                        header[2],
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
                    }
                )
        except (ValueError, TypeError, IndexError, LarkError):
            continue
    return result, records
