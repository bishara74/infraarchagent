"""Native, offline syntax checks and whitespace-only HCL normalization."""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import hcl2
import yaml  # type: ignore[import-untyped]
from lark import Tree
from lark.exceptions import LarkError

from app.scanners.runner import CommandToolRunner, ProcessToolRunner, ToolFailure
from app.validation.documents import PackageDocuments
from app.validation.workspace import current_workspace


@dataclass(frozen=True)
class SyntaxIssue:
    path: str
    line: int
    message: str
    detail: str = ""
    column: int = 1

    def feedback(self, files: dict[str, str]) -> dict[str, Any]:
        lines = files[self.path].splitlines()
        excerpt = "\n".join(
            f"{n + 1}: {lines[n]}"
            for n in range(max(0, self.line - 3), min(len(lines), self.line + 2))
        )
        return {
            "file_path": self.path,
            "line_start": self.line,
            "column": self.column,
            "message": self.message,
            "detail": self.detail,
            "excerpt": excerpt,
        }


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def normalize_blocks(
    files: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Only insert newlines between independently parsed attribute spans.

    Lark's contextual lexer/grammar supplies complete attribute boundaries. We
    require an unchanged parse tree (including token values) after insertion;
    quoted whitespace, comments, heredocs and expressions are never rewritten.
    """
    result = dict(files)
    records: list[dict[str, Any]] = []
    for path, source in sorted(files.items()):
        if not path.startswith("terraform/") or not path.endswith(".tf"):
            continue
        try:
            tree = hcl2.parses_to_tree(source)
            positions: set[int] = set()
            locations = []
            for block in tree.find_data("block"):
                if block.meta.line != block.meta.end_line:
                    continue
                body = next(
                    (
                        c
                        for c in block.children
                        if isinstance(c, Tree) and c.data == "body"
                    ),
                    None,
                )
                if body is None:
                    continue
                children = [c for c in body.children if isinstance(c, Tree)]
                if len(children) < 2 or any(c.data != "attribute" for c in children):
                    continue
                positions.update(c.meta.start_pos for c in children)
                positions.add(block.meta.end_pos - 1)
                locations.append(block.meta.line)
            if not positions:
                continue
            normalized = source
            for position in sorted(positions, reverse=True):
                normalized = normalized[:position] + "\n" + normalized[position:]

            # Ignore separator trivia only, never whitespace inside a token.
            def signature(node: Tree[Any]) -> list[tuple[str, str]]:
                return [
                    (str(t.type), str(t))
                    for t in node.scan_values(lambda value: not isinstance(value, Tree))
                    if hasattr(t, "type") and t.type != "NL_OR_COMMENT"
                ]

            if signature(tree) != signature(hcl2.parses_to_tree(normalized)):
                continue
            result[path] = normalized
            records.extend(
                {
                    "file": path,
                    "kind": "multiline_arguments",
                    "name": "block",
                    "line": line,
                    "before_hash": _hash(source),
                    "after_hash": _hash(normalized),
                }
                for line in locations
            )
        except (LarkError, ValueError, TypeError):
            continue
    return result, records


async def native_syntax(
    files: dict[str, str],
    paths: set[str] | None = None,
    *,
    runner: CommandToolRunner | None = None,
) -> list[SyntaxIssue]:
    """No init, provider installation, evaluation or application environment."""
    runner = runner or ProcessToolRunner(10)
    workspace = current_workspace()
    cache = workspace.syntax_cache if workspace else {}
    issues = []
    for path, source in sorted(files.items()):
        if paths is not None and path not in paths:
            continue
        if not path.startswith("terraform/") or not path.endswith((".tf", ".tf.json")):
            continue
        key = (path, _hash(source))
        if key in cache:
            issues.extend(cache[key])
            continue
        found: list[SyntaxIssue] = []
        with TemporaryDirectory(prefix="infraarch-syntax-") as directory:
            root = Path(directory)
            target = root / Path(path).name
            target.write_text(source)
            if path.endswith(".tf"):
                checked = await runner.run_command(
                    "terraform",
                    ["terraform", "fmt", "-write=false", "-no-color", target.name],
                    root,
                )
                if checked.exit_code != 0:
                    text = checked.stderr or checked.stdout
                    for part in re.split(r"(?m)^Error: ", text)[1:]:
                        line = re.search(r"\bline (\d+)", part)
                        found.append(
                            SyntaxIssue(
                                path,
                                int(line[1]) if line else 1,
                                part.splitlines()[0],
                                part,
                            )
                        )
                    if not found:
                        raise ToolFailure("terraform", "invalid_json")
            else:
                # JSON decoding alone misses Terraform's JSON language structure.
                checked = await runner.run_command(
                    "terraform", ["terraform", "validate", "-json", "-no-color"], root
                )
                try:
                    data = json.loads(checked.stdout)
                    for diagnostic in data["diagnostics"]:
                        title = diagnostic["summary"]
                        if diagnostic["severity"] == "error" and any(
                            word in title.lower()
                            for word in (
                                "json",
                                "extraneous",
                                "missing property",
                                "invalid character",
                                "invalid expression",
                                "unclosed",
                                "unterminated",
                            )
                        ):
                            start = (diagnostic.get("range") or {}).get("start", {})
                            found.append(
                                SyntaxIssue(
                                    path,
                                    start.get("line", 1),
                                    title,
                                    diagnostic.get("detail", ""),
                                    start.get("column", 1),
                                )
                            )
                except (ValueError, KeyError, TypeError):
                    raise ToolFailure("terraform", "invalid_json") from None
        cache[key] = found
        issues.extend(found)
    for doc in PackageDocuments.parse(
        {p: s for p, s in files.items() if paths is None or p in paths}
    ).documents.values():
        if doc.parse_error and (paths is None or doc.path in paths):
            if any(issue.path == doc.path for issue in issues):
                continue
            # Parser exceptions contain exact JSON/YAML locations but must stay
            # private until the caller applies its configured secret redactor.
            detail = "Document could not be parsed"
            try:
                if doc.path.endswith(".json"):
                    json.loads(files[doc.path])
                else:
                    list(yaml.safe_load_all(files[doc.path]))
            except (ValueError, yaml.YAMLError) as error:
                detail = str(error)
            issues.append(SyntaxIssue(doc.path, doc.error_line or 1, detail))
    return issues
