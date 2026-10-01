"""Unified diffs only for file paths whose bytes changed."""

from collections.abc import Mapping
from difflib import unified_diff


def package_diff(before: Mapping[str, str], after: Mapping[str, str]) -> str:
    chunks: list[str] = []
    for path in sorted(before.keys() | after.keys()):
        old = before.get(path)
        new = after.get(path)
        if old == new:
            continue
        chunks.extend(
            unified_diff(
                old.splitlines(keepends=True) if old is not None else [],
                new.splitlines(keepends=True) if new is not None else [],
                fromfile=f"a/{path}" if old is not None else "/dev/null",
                tofile=f"b/{path}" if new is not None else "/dev/null",
            )
        )
    return "".join(chunks)
