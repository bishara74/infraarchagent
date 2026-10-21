"""FR-V-03: atomic, source-preserving module provider consolidation proposals."""

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

import hcl2
from hcl2.utils import SerializationOptions
from lark import Tree

from app.validation.documents import PackageDocuments
from app.validation.idioms import json_spans

Version = tuple[int, int, int]
CLAUSE = re.compile(r"\s*(~>|>=|<=|!=|>|<|=)?\s*(\d+(?:\.\d+){0,2})\s*")


def intersect_constraints(constraints: list[str]) -> str | None:
    """Prove numeric conjunction satisfiability, independent of mirrored pins."""
    lower: Version = (0, 0, 0)
    upper: Version | None = None
    upper_inclusive = False
    excluded: set[Version] = set()
    if any(
        raw.strip() and any(not c.strip() for c in raw.split(","))
        for raw in constraints
    ):
        return None
    clauses = list(
        dict.fromkeys(
            c.strip() for raw in constraints for c in raw.split(",") if c.strip()
        )
    )
    for clause in clauses:
        match = CLAUSE.fullmatch(clause)
        if match is None:
            return None
        operator, raw = match.groups()
        parts = [int(p) for p in raw.split(".")]
        version: Version = tuple(parts + [0] * (3 - len(parts)))  # type: ignore[assignment]
        if operator == "!=":
            excluded.add(version)
            continue
        if operator in (None, "=", ">=", ">", "~>"):
            bound = (
                (version[0], version[1], version[2] + 1) if operator == ">" else version
            )
            lower = max(lower, bound)
        if operator in (None, "=", "<=", "<", "~>"):
            bound, inclusive = version, operator in (None, "=", "<=")
            if operator == "~>":
                bound = (
                    (version[0] + 1, 0, 0)
                    if len(parts) < 3
                    else (version[0], version[1] + 1, 0)
                )
            if upper is None or bound < upper or (bound == upper and not inclusive):
                upper, upper_inclusive = bound, inclusive
    while lower in excluded:
        lower = (lower[0], lower[1], lower[2] + 1)
    if upper is not None and (
        lower > upper or (lower == upper and not upper_inclusive)
    ):
        return None
    return ", ".join(clauses)


@dataclass
class Declaration:
    path: str
    start: int
    end: int
    providers: dict[str, Any]
    json_path: tuple[str | int, ...] | None = None


def _json_delete(source: str, declaration: Declaration) -> tuple[int, int, str]:
    assert declaration.json_path is not None
    key = source.rfind(json.dumps(str(declaration.json_path[-1])), 0, declaration.start)
    right = declaration.end
    while right < len(source) and source[right].isspace():
        right += 1
    if source[right : right + 1] == ",":
        return key, right + 1, ""
    left = key - 1
    while left >= 0 and source[left].isspace():
        left -= 1
    return (left if source[left : left + 1] == "," else key), declaration.end, ""


def _declarations(documents: PackageDocuments) -> list[Declaration]:
    declarations = []
    for path, doc in sorted(documents.documents.items()):
        if path.endswith(".tf.json"):
            # json.loads normally discards duplicate keys; never repair such input.
            def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError("ambiguous_json")
                    result[key] = value
                return result

            json.loads(doc.source, object_pairs_hook=unique)
            for parts, start, end, value in json_spans(doc.source):
                if (
                    parts
                    and parts[0] == "terraform"
                    and parts[-1] == "required_providers"
                    and all(isinstance(p, int) for p in parts[1:-1])
                ):
                    if not isinstance(value, dict):
                        raise ValueError("unsupported_declaration")
                    declarations.append(Declaration(path, start, end, value, parts))
        else:
            assert doc.tree is not None
            root_body = next(
                n for n in doc.tree.children if isinstance(n, Tree) and n.data == "body"
            )
            for node in root_body.children:
                if not isinstance(node, Tree) or node.data != "block":
                    continue
                if not re.match(
                    r"terraform\s*\{",
                    doc.source[node.meta.start_pos : node.meta.end_pos],
                ):
                    continue
                body = next(
                    n for n in node.children if isinstance(n, Tree) and n.data == "body"
                )
                for child in body.children:
                    if not isinstance(child, Tree) or child.data != "block":
                        continue
                    source = doc.source[child.meta.start_pos : child.meta.end_pos]
                    if re.match(r"required_providers\s*\{", source):
                        parsed = hcl2.serialize(
                            hcl2.transform(
                                hcl2.parses_to_tree("terraform {\n" + source + "\n}")
                            ),
                            serialization_options=SerializationOptions(
                                strip_string_quotes=True,
                                with_comments=False,
                                explicit_blocks=False,
                            ),
                        )
                        providers = parsed["terraform"][0]["required_providers"][0]
                        declarations.append(
                            Declaration(
                                path,
                                child.meta.start_pos,
                                child.meta.end_pos,
                                providers,
                            )
                        )
    return declarations


def _merge_providers(declarations: list[Declaration]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for declaration in declarations:
        for name, raw in declaration.providers.items():
            if not re.fullmatch(r"[A-Za-z_][\w-]*", name):
                raise ValueError("unsupported_declaration")
            body = {"version": raw} if isinstance(raw, str) else raw
            if not isinstance(body, dict) or set(body) - {
                "source",
                "version",
                "configuration_aliases",
            }:
                raise ValueError("unsupported_declaration")
            source = body.get("source", f"hashicorp/{name}")
            version = body.get("version", "")
            aliases = body.get("configuration_aliases", [])
            if (
                not isinstance(source, str)
                or not re.fullmatch(r"[\w.-]+/[\w.-]+(?:/[\w.-]+)?", source)
                or not isinstance(version, str)
                or not isinstance(aliases, list)
                or not all(
                    isinstance(a, str) and re.fullmatch(r"\$\{[\w-]+\.[\w-]+\}", a)
                    for a in aliases
                )
            ):
                raise ValueError("unsupported_declaration")
            groups[name].append(
                {"source": source, "version": version, "configuration_aliases": aliases}
            )
    merged = {}
    for name, entries in sorted(groups.items()):
        if len({entry["source"] for entry in entries}) != 1:
            raise ValueError("source_conflict")
        constraint = intersect_constraints([entry["version"] for entry in entries])
        if constraint is None:
            raise ValueError("incompatible_or_unsupported_constraints")
        aliases = sorted(
            {alias for entry in entries for alias in entry["configuration_aliases"]}
        )
        merged[name] = {
            "source": entries[0]["source"],
            **({"version": constraint} if constraint else {}),
            **({"configuration_aliases": aliases} if aliases else {}),
        }
    return merged


def repair_required_providers(
    files: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    result, records = dict(files), []
    modules: dict[str, dict[str, str]] = defaultdict(dict)
    for path, source in sorted(files.items()):
        if path.startswith("terraform/") and path.endswith((".tf", ".tf.json")):
            modules[str(PurePosixPath(path).parent)][path] = source
    for module, module_files in modules.items():
        documents = PackageDocuments.parse(module_files)
        if any(doc.parse_error for doc in documents.documents.values()):
            continue
        try:
            declarations = _declarations(documents)
            if len(declarations) < 2:
                continue
            record: dict[str, Any] = {
                "file": declarations[0].path,
                "kind": "required_providers_merge",
                "name": module,
            }
            merged = _merge_providers(declarations)
        except ValueError as error:
            records.append(
                {
                    "file": next(iter(module_files)),
                    "kind": "required_providers_merge",
                    "name": module,
                    "outcome": "skipped",
                    "reason": str(error)
                    if str(error)
                    in {
                        "unsupported_declaration",
                        "ambiguous_json",
                        "source_conflict",
                        "incompatible_or_unsupported_constraints",
                    }
                    else "unsupported_declaration",
                }
            )
            continue
        keeper = declarations[0]
        if keeper.json_path is not None:
            replacement = json.dumps(merged, separators=(",", ":"))
        else:
            lines = ["required_providers {"]
            for name, body in merged.items():
                fields = [
                    f"{key} = "
                    + (
                        "[" + ", ".join(a[2:-1] for a in value) + "]"
                        if key == "configuration_aliases"
                        else json.dumps(value)
                    )
                    for key, value in body.items()
                ]
                lines.append(f"    {name} = {{ " + ", ".join(fields) + " }")
            replacement = "\n".join([*lines, "  }"])
        edits: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
        edits[keeper.path].append((keeper.start, keeper.end, replacement))
        for declaration in declarations[1:]:
            edit = (
                _json_delete(files[declaration.path], declaration)
                if declaration.json_path is not None
                else (declaration.start, declaration.end, "")
            )
            edits[declaration.path].append(edit)
        candidate = dict(module_files)
        for path, changes in edits.items():
            for start, end, text in sorted(changes, reverse=True):
                candidate[path] = candidate[path][:start] + text + candidate[path][end:]
            if not candidate[path].strip():
                candidate[path] = "\n"
        # The existing validity/security guard makes the retention decision.
        for key, values in (("before_hash", module_files), ("after_hash", candidate)):
            record[key] = hashlib.sha256(
                json.dumps(values, sort_keys=True).encode()
            ).hexdigest()
        records.append(record)
        result.update(candidate)
    return result, records
