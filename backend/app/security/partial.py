"""Deterministic dependency groups for guarded partial candidate acceptance."""

import asyncio
import json
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any

import hcl2
from lark import Tree
from lark.exceptions import LarkError

from app.domain.validation import ValidationCheck
from app.scanners.scan import ScanResult
from app.security.acceptance import CandidateGuard
from app.validation.documents import code_text


@dataclass
class RetainedCandidate:
    """Private checkpoint: source must never enter public report metadata."""

    files: dict[str, str]
    scan: ScanResult
    fixes: list[dict[str, Any]] = field(default_factory=list)


def retained_metrics(
    fixes: list[dict[str, Any]], before: dict[str, str], after: dict[str, str]
) -> None:
    for fix in fixes:
        paths = [fix["file"], *fix.get("edits", []), *fix.get("new_files", [])]
        fix["retained"] = fix["accepted"] and any(
            after.get(p) != before.get(p) for p in paths
        )
        fix["recovered_existing_proposal"] = fix["accepted"] and any(
            after.get(p) != before.get(p)
            for p in fix.get("normalized_existing_paths", [])
        )


@dataclass(frozen=True)
class Block:
    key: tuple[str, ...]
    start: int
    end: int
    value: Any
    definitions: frozenset[str]


def _definitions(key: tuple[str, ...], value: Any) -> frozenset[str]:
    kind, *labels = key
    if kind == "resource":
        return frozenset({".".join(labels)})
    if kind == "variable":
        return frozenset({"var." + labels[0]})
    if kind in {"data", "module"}:
        return frozenset({".".join(key)})
    if kind == "locals" and isinstance(value, dict):
        return frozenset("local." + k for k in value)
    return frozenset()


def top_blocks(path: str, source: str) -> dict[tuple[str, ...], Block]:
    result: dict[tuple[str, ...], Block] = {}
    if path.endswith(".tf.json"):
        data = json.loads(source)
        if not isinstance(data, dict):
            raise ValueError("unseparable document")
        for kind, value in data.items():
            entries: list[tuple[tuple[str, ...], Any]]
            if kind in {"resource", "data"}:
                entries = [
                    ((kind, typ, name), body)
                    for typ, named in value.items()
                    for name, body in named.items()
                ]
            elif kind in {"variable", "output", "module", "provider"}:
                entries = [((kind, name), body) for name, body in value.items()]
            else:
                entries = [((kind,), value)]
            for key, body in entries:
                result[key] = Block(key, 0, 0, body, _definitions(key, body))
        return result
    tree = hcl2.parses_to_tree(source)
    body = next(
        (c for c in tree.children if isinstance(c, Tree) and c.data == "body"), tree
    )
    for node in body.children:
        if not isinstance(node, Tree) or node.data != "block":
            continue
        raw = source[node.meta.start_pos : node.meta.end_pos]
        header = raw.split("{", 1)[0]
        match = re.fullmatch(r'\s*(\w+)\s*((?:"[^"\n]+"\s*)*)', header)
        if not match:
            raise ValueError("unseparable block")
        key = (match[1], *re.findall(r'"([^"\n]+)"', match[2]))
        if key in result:
            raise ValueError("duplicate block identity")
        local_names = {m[1]: None for m in re.finditer(r"(?m)^\s*([\w-]+)\s*=", raw)}
        result[key] = Block(
            key,
            node.meta.start_pos,
            node.meta.end_pos,
            raw,
            _definitions(key, local_names),
        )
    return result


@dataclass(frozen=True)
class Change:
    path: str
    key: tuple[str, ...] | None
    value: Any
    definitions: frozenset[str]
    references: frozenset[str]

    @property
    def label(self) -> str:
        return self.path + (":" + ".".join(self.key) if self.key else "")

    def apply(self, files: dict[str, str]) -> dict[str, str]:
        result = dict(files)
        if self.key is None:
            if self.value is None:
                result.pop(self.path, None)
            else:
                result[self.path] = self.value
            return result
        if self.path.endswith(".tf.json"):
            data = json.loads(result.get(self.path, "{}"))
            parent = data
            for key in self.key[:-1]:
                parent = parent.setdefault(key, {})
            if self.value is None:
                parent.pop(self.key[-1], None)
            else:
                parent[self.key[-1]] = self.value
            result[self.path] = json.dumps(data, indent=2) + "\n"
        else:
            source = result.get(self.path, "")
            old = top_blocks(self.path, source).get(self.key)
            if old:
                result[self.path] = (
                    source[: old.start] + (self.value or "") + source[old.end :]
                )
            elif self.value is not None:
                result[self.path] = source + "\n" + self.value + "\n"
        return result


def _references(value: Any) -> frozenset[str]:
    source = value if isinstance(value, str) else json.dumps(value)
    return frozenset(
        re.findall(
            r"\b(?:aws_[\w]+\.[\w-]+|var\.[\w-]+|local\.[\w-]+|module\.[\w-]+|data\.aws_[\w]+\.[\w-]+)",
            code_text(source, hash_comments=True, mask_strings=False),
        )
    )


def change_groups(
    before: dict[str, str], candidate: dict[str, str]
) -> list[list[Change]]:
    changes: list[Change] = []
    for path in sorted(before.keys() | candidate.keys()):
        if before.get(path) == candidate.get(path):
            continue
        old, new = before.get(path), candidate.get(path)
        try:
            if (
                not path.startswith("terraform/")
                or not path.endswith((".tf", ".tf.json"))
                or new is None
            ):
                raise ValueError("whole file group")
            originals = top_blocks(
                path, old or ("{}" if path.endswith(".json") else "")
            )
            proposed = top_blocks(path, new)
            for key in sorted(originals.keys() | proposed.keys()):
                a, b = originals.get(key), proposed.get(key)
                if a and b and a.value == b.value:
                    continue
                changes.append(
                    Change(
                        path,
                        key,
                        b.value if b else None,
                        (a.definitions if a else frozenset())
                        | (b.definitions if b else frozenset()),
                        _references(a.value if a else "")
                        | _references(b.value if b else ""),
                    )
                )
        except (LarkError, ValueError, TypeError, AttributeError):
            changes.append(
                Change(
                    path, None, new, frozenset(), _references((old or "") + (new or ""))
                )
            )
    # A changed declaration and every changed reference to it form one group.
    parent = list(range(len(changes)))

    def root(i: int) -> int:
        while parent[i] != i:
            i = parent[i]
        return i

    for i, change_a in enumerate(changes):
        for j, change_b in enumerate(changes[:i]):
            if PurePosixPath(change_a.path).parent == PurePosixPath(
                change_b.path
            ).parent and (
                change_a.definitions & change_b.references
                or change_b.definitions & change_a.references
                or (change_a.key and change_a.key[0] in {"terraform", "provider"})
                or (change_b.key and change_b.key[0] in {"terraform", "provider"})
            ):
                parent[root(i)] = root(j)
    groups: dict[int, list[Change]] = {}
    for i, change in enumerate(changes):
        groups.setdefault(root(i), []).append(change)
    return sorted(groups.values(), key=lambda g: tuple(c.label for c in g))


async def accept_groups(
    guard: CandidateGuard,
    before: dict[str, str],
    candidate: dict[str, str],
    checks: list[ValidationCheck],
    scan: ScanResult,
    limit: int,
    records: list[dict[str, Any]],
    checkpoint: RetainedCandidate,
) -> tuple[dict[str, str], list[ValidationCheck], ScanResult]:
    retained = dict(before)
    evaluated = 0
    for group in change_groups(before, candidate):
        record: dict[str, Any] = {"changes": [c.label for c in group]}
        records.append(record)
        if evaluated >= limit or guard.budget.expired():
            record.update(
                status="unevaluated",
                reason="group_limit" if evaluated >= limit else "iteration_deadline",
            )
            continue
        proposed = retained
        for change in group:
            proposed = change.apply(proposed)
        evaluated += 1
        try:
            result = await guard.evaluate(retained, proposed, checks, scan)
        except asyncio.CancelledError:
            record.update(status="unevaluated", reason="iteration_deadline")
            raise
        except TimeoutError:
            record.update(status="unevaluated", reason="iteration_deadline")
            continue
        record.update(
            status="discarded" if result.reason else "kept",
            reason=result.reason or "guards_passed",
            introduced_findings=result.introduced,
        )
        if not result.reason:
            retained, checks, scan = proposed, result.checks, result.scan
            checkpoint.files, checkpoint.scan = dict(retained), scan
            retained_metrics(checkpoint.fixes, before, retained)
    return retained, checks, scan
