"""FR-V-03: module-atomic duplicate declarations without expression evaluation."""

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

import hcl2
from lark import Tree
from lark.exceptions import LarkError

from app.validation.idioms import json_spans
from app.validation.workspace import current_workspace


@dataclass
class Declaration:
    path: str
    start: int
    end: int
    identity: tuple[str, str, str]
    # Each field owns its complete attribute or nested-block collection.
    fields: dict[str, tuple[str, Any, str]]
    json: bool = False


def signature(node: Tree[Any]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (str(token.type), str(token))
        for token in node.scan_values(lambda item: not isinstance(item, Tree))
        if hasattr(token, "type") and token.type != "NL_OR_COMMENT"
    )


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous_json")
        result[key] = value
    return result


def declarations(path: str, source: str) -> list[Declaration]:
    result = []
    if path.endswith(".tf.json"):
        # Do not let Python's last-key-wins policy conceal a conflict.
        json.loads(source, object_pairs_hook=unique)
        spans = json_spans(source)
        for parts, start, end, value in spans:
            if len(parts) != 3 or parts[0] not in {"resource", "data"}:
                continue
            if not all(isinstance(part, str) for part in parts):
                raise ValueError("unsupported_declaration")
            if not isinstance(value, dict) or "dynamic" in value:
                raise ValueError("unsupported_body")
            json_fields: dict[str, tuple[str, Any, str]] = {
                str(p[-1]): (
                    "json",
                    json.dumps(v, sort_keys=True, ensure_ascii=True),
                    source[a:b],
                )
                for p, a, b, v in spans
                if len(p) == 4 and p[:3] == parts
            }
            result.append(
                Declaration(
                    path,
                    start,
                    end,
                    (str(parts[0]), str(parts[1]), str(parts[2])),
                    json_fields,
                    True,
                )
            )
        return result
    tree = hcl2.parses_to_tree(source)
    body = next(n for n in tree.children if isinstance(n, Tree) and n.data == "body")
    for node in body.children:
        if not isinstance(node, Tree) or node.data != "block":
            continue
        match = re.match(
            r'(resource|data)\s+"([\w-]+)"\s+"([\w-]+)"\s*\{',
            source[node.meta.start_pos : node.meta.end_pos],
        )
        if match is None:
            continue
        inner = next(
            n for n in node.children if isinstance(n, Tree) and n.data == "body"
        )
        fields: dict[str, tuple[str, Any, str]] = {}
        if any(
            str(n.children[0]).strip() == "dynamic"
            for n in node.find_data("identifier")
        ):
            fields["__dynamic_body__"] = ("unsupported", (), "")
        for child in inner.children:
            if not isinstance(child, Tree) or child.data not in {"attribute", "block"}:
                continue
            raw = source[child.meta.start_pos : child.meta.end_pos]
            name = re.match(r"[\w-]+", raw)
            if name is None:
                raise ValueError("unsupported_field")
            kind, tokens = str(child.data), (signature(child),)
            key = name[0]
            if key in fields:
                old_kind, old_tokens, old_raw = fields[key]
                if kind != "block" or old_kind != "block":
                    raise ValueError("duplicate_attribute")
                tokens = (*old_tokens, *tokens)
                raw = old_raw + "\n" + raw
            fields[key] = (kind, tokens, raw)
        result.append(
            Declaration(
                path,
                node.meta.start_pos,
                node.meta.end_pos,
                (match[1], match[2], match[3]),
                fields,
            )
        )
    return result


def deletion(source: str, item: Declaration) -> tuple[int, int, str]:
    if not item.json:
        return item.start, item.end, ""
    key = source.rfind(json.dumps(item.identity[-1]), 0, item.start)
    if key < 0:
        raise ValueError("unsupported_key_escape")
    end = item.end
    while end < len(source) and source[end].isspace():
        end += 1
    if source[end : end + 1] == ",":
        return key, end + 1, ""
    left = key - 1
    while left >= 0 and source[left].isspace():
        left -= 1
    return (left if source[left : left + 1] == "," else key), item.end, ""


def repair_duplicates(
    files: dict[str, str],
    *,
    blocked: set[str] | None = None,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """One ambiguous/conflicting duplicate aborts this module's entire candidate."""
    result = dict(files)
    records: list[dict[str, Any]] = []
    modules: dict[str, list[str]] = defaultdict(list)
    for path in sorted(files):
        if path.startswith("terraform/") and path.endswith((".tf", ".tf.json")):
            modules[str(PurePosixPath(path).parent)].append(path)
    for paths in modules.values():
        try:
            groups: dict[tuple[str, str, str], list[Declaration]] = defaultdict(list)
            for path in paths:
                for item in declarations(path, files[path]):
                    groups[item.identity].append(item)
            edits: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
            touched: dict[str, list[Declaration]] = defaultdict(list)
            for items in groups.values():
                if len(items) < 2:
                    continue
                if any(
                    field[0] == "unsupported"
                    for item in items
                    for field in item.fields.values()
                ):
                    raise ValueError("dynamic_body")
                first = items[0]
                fields = dict(first.fields)
                for later in items[1:]:
                    if later.json != first.json:
                        raise ValueError("mixed_declaration_formats")
                    for name, field in later.fields.items():
                        if name in fields and fields[name][:2] != field[:2]:
                            raise ValueError("conflicting_duplicate")
                        fields.setdefault(name, field)
                    edits[later.path].append(deletion(files[later.path], later))
                    touched[later.path].append(later)
                added = {
                    key: value
                    for key, value in fields.items()
                    if key not in first.fields
                }
                if added:
                    if first.json:
                        addition = ("," if first.fields else "") + ",".join(
                            json.dumps(key) + ":" + value[2]
                            for key, value in added.items()
                        )
                    else:
                        addition = (
                            "\n"
                            + "\n".join(value[2] for value in added.values())
                            + "\n"
                        )
                    edits[first.path].append((first.end - 1, first.end - 1, addition))
                touched[first.path].append(first)
            candidate = {path: files[path] for path in paths}
            for path, changes in edits.items():
                # Adjacent JSON entry removals can share their comma. Rebuild
                # after each deletion instead by rejecting overlapping spans.
                ordered = sorted(changes)
                if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:], strict=False)):
                    raise ValueError("overlapping_edits")
                for start, end, text in reversed(ordered):
                    candidate[path] = (
                        candidate[path][:start] + text + candidate[path][end:]
                    )
                if not candidate[path].strip():
                    candidate[path] = "\n"
            # Reparse all files before publishing any module bytes.
            for path, source in candidate.items():
                declarations(path, source)
        except (ValueError, TypeError, AttributeError, StopIteration, LarkError):
            if blocked is not None:
                blocked.update(paths)
            continue
        workspace = current_workspace()
        for path, items in touched.items():
            if candidate[path] == files[path]:
                continue
            records.append(
                {
                    "file": path,
                    "kind": "duplicate_block",
                    "name": ",".join(
                        dict.fromkeys(".".join(i.identity) for i in items)
                    ),
                    "line": files[path].count("\n", 0, min(i.start for i in items)) + 1,
                    "before_hash": hashlib.sha256(files[path].encode()).hexdigest(),
                    "after_hash": hashlib.sha256(candidate[path].encode()).hexdigest(),
                    "origin": workspace.stage if workspace else "generated",
                }
            )
        result.update(candidate)
    return result, records
