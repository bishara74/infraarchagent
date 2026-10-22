"""D-56: rebase literal file inputs to an exact, existing package artifact.

Terraform documents file("${path.module}/...") reads at
https://developer.hashicorp.com/terraform/language/functions/file .
Only propose edits; the existing validity/security guard decides retention.
"""

import hashlib
import json
import posixpath
from collections.abc import Iterator
from pathlib import PurePosixPath
from typing import Any

import hcl2
from lark import Tree
from lark.exceptions import LarkError

from app.domain.paths import UnsafePathError, validate_file_map, validate_relative_path
from app.validation.documents import Document, PackageDocuments
from app.validation.idioms import json_spans


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous_json")
        result[key] = value
    return result


def _ambiguous(doc: Document) -> bool:
    if doc.parse_error:
        return True
    if doc.path.endswith(".tf.json"):
        try:
            json.loads(doc.source, object_pairs_hook=_unique)
        except ValueError:
            return True
    if doc.tree is not None:
        for body in doc.tree.find_data("body"):
            names = [
                str(node.children[0].children[0])
                for node in body.children
                if isinstance(node, Tree) and node.data == "attribute"
            ]
            if len(names) != len(set(names)):
                return True
    return False


def _rebased(files: dict[str, str], module: str, literal: str) -> str | None:
    # Exact canonical keys only: never search by basename or inspect the host FS.
    try:
        validate_relative_path(literal)
    except UnsafePathError:
        return None
    if any(part.startswith(".env") for part in PurePosixPath(literal).parts):
        return None
    if literal not in files or any(
        posixpath.join(base, literal) in files for base in (module, "terraform")
    ):
        return None
    relative = posixpath.relpath(literal, module)
    target = posixpath.normpath(posixpath.join(module, relative))
    if target != literal or target.startswith(("../", "/")):
        return None
    return "${path.module}/" + relative


def _calls(
    tree: Tree[Any], source: str, *, encoded: bool = False
) -> Iterator[tuple[int, int, str]]:
    for call in tree.find_data("function_call"):
        identifier = call.children[0]
        if not isinstance(identifier, Tree) or str(identifier.children[0]) != "file":
            continue
        arguments = [
            n for n in call.children if isinstance(n, Tree) and n.data == "arguments"
        ]
        if len(arguments) != 1:
            continue
        expressions = [
            n
            for n in arguments[0].children
            if isinstance(n, Tree) and n.data != "new_line_or_comment"
        ]
        if len(expressions) != 1 or expressions[0].data != "expr_term":
            continue
        children = expressions[0].children
        if (
            len(children) != 1
            or not isinstance(children[0], Tree)
            or children[0].data not in {"string", "template_string"}
        ):
            continue
        literal = children[0]
        raw = source[literal.meta.start_pos : literal.meta.end_pos]
        try:
            if encoded:
                raw = json.loads('"' + raw + '"')
            value = json.loads(raw)
        except ValueError:
            continue
        if isinstance(value, str):
            yield literal.meta.start_pos, literal.meta.end_pos, value


def _heredoc_calls(tree: Tree[Any], source: str) -> Iterator[tuple[int, int, str]]:
    # hcl2 keeps heredoc templates as opaque tokens. Parse a quoted copy to
    # distinguish actual interpolations from shell text, then map offsets back.
    for node in tree.iter_subtrees():
        if node.data not in {"heredoc_template", "heredoc_template_trim"}:
            continue
        raw = source[node.meta.start_pos : node.meta.end_pos]
        lines = raw.splitlines(keepends=True)
        if len(lines) < 2:
            continue
        body = "".join(lines[1:-1])
        encoded = json.dumps(body)
        boundaries = {1: 0}
        cursor = 1
        for offset, char in enumerate(body, 1):
            cursor += len(json.dumps(char)) - 2
            boundaries[cursor] = offset
        origin = node.meta.start_pos + len(lines[0])
        for start, end, value in _json_calls(encoded):
            if start in boundaries and end in boundaries:
                yield origin + boundaries[start], origin + boundaries[end], value


def _json_offsets(raw: str) -> dict[int, int]:
    """Decoded character boundaries to original JSON offsets, including surrogates."""
    cursor, offset = 1, 0
    result = {offset: cursor}
    while cursor < len(raw) - 1:
        end = cursor + 1
        if raw[cursor] == "\\":
            end = cursor + (6 if raw[cursor + 1] == "u" else 2)
            if (
                raw[cursor : cursor + 2] == "\\u"
                and 0xD800 <= int(raw[cursor + 2 : end], 16) <= 0xDBFF
                and raw[end : end + 2] == "\\u"
                and 0xDC00 <= int(raw[end + 2 : end + 6], 16) <= 0xDFFF
            ):
                end += 6
        offset += len(json.loads('"' + raw[cursor:end] + '"'))
        cursor = end
        result[offset] = cursor
    return result


def _json_calls(raw: str) -> list[tuple[int, int, str]]:
    prefix = "__value = "
    synthetic = prefix + raw
    try:
        tree = hcl2.parses_to_tree(synthetic)
        calls = [
            (start - len(prefix), end - len(prefix), value)
            for start, end, value in _calls(tree, synthetic, encoded=True)
        ]
        if calls:
            return calls
    except (LarkError, ValueError):
        pass
    # JSON-escaped newlines in a multiline interpolation are not HCL whitespace.
    # Parse the decoded template only if it remains one complete quoted string;
    # never turn literal text into injected HCL expressions or declarations.
    value = json.loads(raw)
    synthetic = prefix + '"' + value + '"'
    try:
        tree = hcl2.parses_to_tree(synthetic)
    except (LarkError, ValueError):
        return []
    quoted = [
        n
        for n in tree.find_data("string")
        if n.meta.start_pos == len(prefix) and n.meta.end_pos == len(synthetic)
    ]
    if len(quoted) != 1:
        return []
    offsets = _json_offsets(raw)
    calls = []
    for start, end, literal in _calls(quoted[0], synthetic):
        left, right = start - len(prefix) - 1, end - len(prefix) - 1
        if left in offsets and right in offsets:
            calls.append((offsets[left], offsets[right], literal))
    return calls


def repair_file_paths(
    files: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Keep artifact contents and expression types; log source-preserving edits."""
    try:
        validate_file_map(files)
    except ValueError:
        return files, []
    documents = PackageDocuments.parse(
        {
            p: s
            for p, s in files.items()
            if p.startswith("terraform/") and p.endswith((".tf", ".tf.json"))
        }
    )
    unsafe = {
        str(PurePosixPath(doc.path).parent)
        for doc in documents.documents.values()
        if _ambiguous(doc)
    }
    result, records = dict(files), []
    for path, doc in documents.documents.items():
        module = str(PurePosixPath(path).parent)
        if module in unsafe:
            continue
        source = doc.source
        edits: list[tuple[int, int, str, str]] = []
        if doc.tree is not None:
            calls = [*_calls(doc.tree, source), *_heredoc_calls(doc.tree, source)]
        else:
            calls = []
            for _, start, end, value in json_spans(source):
                if not isinstance(value, str):
                    continue
                calls.extend(
                    (a + start, b + start, literal)
                    for a, b, literal in _json_calls(source[start:end])
                )
        for start, end, literal in calls:
            replacement = _rebased(files, module, literal)
            if replacement is None:
                continue
            rendered = json.dumps(replacement)
            if path.endswith(".tf.json"):
                rendered = json.dumps(rendered)[1:-1]
            edits.append((start, end, rendered, literal))
        for start, end, rendered, _ in sorted(edits, reverse=True):
            result[path] = result[path][:start] + rendered + result[path][end:]
        for start, _, _, literal in sorted(edits):
            records.append(
                {
                    "file": path,
                    "kind": "terraform_file_path",
                    "name": literal,
                    "line": source.count("\n", 0, start) + 1,
                    "before_hash": hashlib.sha256(source.encode()).hexdigest(),
                    "after_hash": hashlib.sha256(result[path].encode()).hexdigest(),
                }
            )
    return result, records
