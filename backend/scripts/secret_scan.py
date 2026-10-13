"""Offline heuristic credential scan. Findings never contain matched values."""

import argparse
import json
import math
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

from scripts.phase9_common import ROOT, evidence_directory, safe_main, write_json
from scripts.phase9_report import summary

PRUNED = {
    ".git",
    "node_modules",
    ".venv",
    ".cache",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "coverage",
    ".vite",
    ".terraform",
    ".terraform-data",
}
PATTERNS = (
    ("openrouter", re.compile(r"\bsk-or-[A-Za-z0-9_-]{16,}")),
    ("anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}")),
    ("openai", re.compile(r"\bsk-(?!or-|ant-)[A-Za-z0-9_-]{16,}")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "private_key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
        ),
    ),
)
ASSIGNMENT = re.compile(
    r"""\b(?:[A-Z][A-Z0-9_]*_)?API_KEY[ \t]*=[ \t]*"""
    r"""(?:"([^"\r\n]*)"|'([^'\r\n]*)'|([^\s#'";]+))"""
)
TOKEN = re.compile(r"[A-Za-z0-9_+/=-]{16,}")


def excluded(path: Path) -> bool:
    return (
        any(part in PRUNED or part.endswith(".egg-info") for part in path.parts)
        or (path.name.startswith(".env") and path.name != ".env.example")
        or path.suffix in {".pyc", ".pyo", ".tsbuildinfo"}
    )


def matches(content: bytes, allowed: set[str]) -> list[tuple[int, str]]:
    if b"\0" in content:
        return []
    text = content.decode("utf-8", errors="replace")
    found = set()
    for name, pattern in PATTERNS:
        for match in pattern.finditer(text):
            if match.group() not in allowed:
                found.add((text.count("\n", 0, match.start()) + 1, name))
    for match in ASSIGNMENT.finditer(text):
        value = next(value for value in match.groups() if value is not None)
        if value in allowed or not TOKEN.fullmatch(value):
            continue
        entropy = -sum(
            (count / len(value)) * math.log2(count / len(value))
            for count in Counter(value).values()
        )
        if entropy >= 3:
            found.add((text.count("\n", 0, match.start()) + 1, "api_key_assignment"))
    return sorted(found)


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, timeout=60
    )
    if result.returncode:
        raise RuntimeError("Git scan failed")
    return result.stdout


def scan(root: Path, allowed: set[str]) -> tuple[list[dict], list[dict]]:
    findings, errors = [], []
    for directory, names, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        names[:] = [
            name
            for name in names
            if not excluded((parent / name).relative_to(root))
            and not (parent / name).is_symlink()
        ]
        for name in sorted(files):
            path = parent / name
            relative = path.relative_to(root)
            if excluded(relative) or path.is_symlink() or not path.is_file():
                continue
            try:
                for line, pattern in matches(path.read_bytes(), allowed):
                    findings.append(
                        {
                            "file": str(relative),
                            "line": line,
                            "commit": None,
                            "pattern": pattern,
                        }
                    )
            except OSError:
                errors.append(
                    {"file": str(relative), "commit": None, "pattern": "read_error"}
                )
    cache = {}
    try:
        commits = git(root, "rev-list", "--all", "--reflog").decode().splitlines()
        for commit in dict.fromkeys(commits):
            for record in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
                if not record:
                    continue
                metadata, raw_path = record.split(b"\t", 1)
                mode, kind, blob = metadata.decode().split()
                path = Path(os.fsdecode(raw_path))
                if kind != "blob" or mode == "120000" or excluded(path):
                    continue
                if blob not in cache:
                    cache[blob] = matches(git(root, "cat-file", "blob", blob), allowed)
                for line, pattern in cache[blob]:
                    findings.append(
                        {
                            "file": str(path),
                            "line": line,
                            "commit": commit,
                            "pattern": pattern,
                        }
                    )
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        errors.append({"file": ".", "commit": None, "pattern": "history_scan_error"})
    return findings, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    directory = evidence_directory("secret-scan", args.output_dir)
    allowed = set(
        json.loads((ROOT / "docs/secret-scan-allowlist.json").read_text())[
            "exact_values"
        ]
    )
    findings, errors = scan(args.root.resolve(), allowed)
    write_json(
        directory / "findings.json",
        {
            "findings": findings,
            "errors": errors,
            "limitations": "Heuristic scan; excludes binary content and pruned paths.",
        },
    )
    for finding in findings + errors:
        print(
            f"{finding['file']}:{finding.get('line', '?')} "
            f"{finding['commit'] or 'working-tree'} {finding['pattern']}"
        )
    summary(
        directory / "summary.md",
        "Secret scan — NFR-01",
        "INCOMPLETE" if errors else "FAIL" if findings else "PASS",
        [
            f"Findings: {len(findings)}; scan errors: {len(errors)}.",
            "All refs/reflogs scanned; paths excluded before retrieval.",
            "Only locations/patterns retained. D-42 documents limitations.",
        ],
    )
    print(directory)
    raise SystemExit(2 if errors else 1 if findings else 0)


if __name__ == "__main__":
    safe_main(main)
