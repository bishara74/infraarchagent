"""Collect test identifiers, not test success; reproduce the thesis TC matrix."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from scripts.phase9_common import (
    BACKEND,
    ROOT,
    collection_environment,
    evidence_directory,
    safe_main,
    write_json,
)
from scripts.phase9_report import summary

ID = re.compile(
    r"\b(?P<stem>FR-[A-Z]+|NFR|PR|UC)-(?P<first>\d{2})(?P<suffix>(?:(?:--|\.\.|–|/|-)\d{2})*)\b"
)


def identifiers(text: str) -> set[str]:
    found = set()
    for match in ID.finditer(text):
        stem, first = match["stem"], int(match["first"])
        found.add(f"{stem}-{first:02}")
        for separator, number in re.findall(r"(--|\.\.|–|/|-)(\d{2})", match["suffix"]):
            last = int(number)
            for value in [last] if separator == "/" else range(first, last + 1):
                found.add(f"{stem}-{value:02}")
            first = last
    return found


def playwright_tests(suites: list[dict], parents: tuple[str, ...] = ()) -> list[dict]:
    rows = []
    for suite in suites:
        titles = (*parents, suite.get("title", ""))
        for spec in suite.get("specs", []):
            title = " > ".join((*titles, spec["title"]))
            for test in spec.get("tests", []):
                rows.append(
                    {
                        "framework": "playwright",
                        "file": "frontend/e2e/" + spec["file"],
                        "node_id": spec["id"] + ":" + test.get("projectName", ""),
                        "title": title,
                        "ids": sorted(identifiers(title)),
                    }
                )
        rows.extend(playwright_tests(suite.get("suites", []), titles))
    return rows


def build_report(requirements: set[str], tests: list[dict], mapping: dict) -> dict:
    unique = {(test["framework"], test["node_id"]): test for test in tests}
    expanded = {
        group: set().union(*(identifiers(value) for value in values))
        for group, values in mapping["groups"].items()
    }
    rows, invalid = [], []
    for test in unique.values():
        for value in test["ids"]:
            if not isinstance(value, str) or value not in requirements:
                invalid.append(
                    {
                        "framework": test["framework"],
                        "file": test["file"],
                        "problem": "unknown or malformed requirement annotation",
                    }
                )
    for requirement in sorted(requirements):
        covered = [test for test in unique.values() if requirement in test["ids"]]
        rows.append(
            {
                "requirement": requirement,
                "tests": covered,
                "counts": {
                    framework: sum(t["framework"] == framework for t in covered)
                    for framework in ("pytest", "vitest", "playwright")
                },
                "tc_groups": sorted(
                    group for group, ids in expanded.items() if requirement in ids
                ),
            }
        )
    return {
        "requirements": rows,
        "uncovered": [row["requirement"] for row in rows if not row["tests"]],
        "invalid_annotations": invalid,
        "evidence": "Collection only; no passing-test claim.",
    }


def collect(directory: Path) -> tuple[list[dict], list[str]]:
    tests, failures = [], []
    commands = [
        (
            "pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                "-p",
                "scripts.pytest_traceability",
                "--traceability-output",
                str(directory / "pytest.json"),
            ],
            BACKEND,
        ),
        ("vitest", ["node_modules/.bin/vitest", "list", "--json"], ROOT / "frontend"),
        (
            "playwright",
            ["node_modules/.bin/playwright", "test", "--list", "--reporter=json"],
            ROOT / "frontend",
        ),
        (
            "playwright-perf",
            [
                "node_modules/.bin/playwright",
                "test",
                "--list",
                "--reporter=json",
                "--grep",
                "@perf",
            ],
            ROOT / "frontend",
        ),
    ]
    for name, command, cwd in commands:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=collection_environment(),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode:
                failures.append(name)
                continue
            if name == "pytest":
                tests.extend(json.loads((directory / "pytest.json").read_text()))
            elif name == "vitest":
                values = json.loads(result.stdout)
                tests.extend(
                    {
                        "framework": "vitest",
                        "file": str(Path(value["file"]).relative_to(ROOT)),
                        "node_id": str(Path(value["file"]).relative_to(ROOT))
                        + ":"
                        + value["name"],
                        "title": value["name"],
                        "ids": sorted(identifiers(value["name"])),
                    }
                    for value in values
                )
            else:
                values = json.loads(result.stdout)
                if values.get("errors"):
                    failures.append(name)
                else:
                    tests.extend(playwright_tests(values.get("suites", [])))
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
            failures.append(name)
    for test in tests:
        file = Path(test["file"])
        if file.is_absolute():
            test["file"] = str(file.relative_to(ROOT))
    return tests, failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    directory = evidence_directory("traceability", args.output_dir)
    source = re.sub(
        r"(?<!\\)%[^\n]*", "", (ROOT / "docs/spec/03-requirements.tex").read_text()
    )
    tests, failures = collect(directory)
    report = build_report(
        identifiers(source),
        tests,
        json.loads((ROOT / "docs/traceability-map.json").read_text()),
    )
    report["collection_failures"] = failures
    write_json(directory / "traceability.json", report)
    lines = ["| Requirement | Test files / counts | TC groups |", "|---|---|---|"]
    for row in report["requirements"]:
        files = (
            ", ".join(sorted({test["file"] for test in row["tests"]})) or "Uncovered"
        )
        counts = ", ".join(f"{key}: {value}" for key, value in row["counts"].items())
        lines.append(
            f"| {row['requirement']} | {files}; {counts} | "
            f"{', '.join(row['tc_groups']) or 'No TC mapping'} |"
        )
    lines.extend(
        [
            "",
            "Uncovered IDs: " + (", ".join(report["uncovered"]) or "None"),
            "Collection failures: " + (", ".join(failures) or "None"),
            report["evidence"],
        ]
    )
    (directory / "traceability.md").write_text("\n".join(lines) + "\n")
    summary(
        directory / "summary.md",
        "Requirement traceability",
        "INCOMPLETE" if failures else "PASS",
        [
            report["evidence"],
            f"Requirements: {len(report['requirements'])}; "
            f"uncovered: {len(report['uncovered'])}.",
            "Uncovered IDs: " + (", ".join(report["uncovered"]) or "None"),
            "TC mappings follow the thesis matrix; absent mappings stay unassigned.",
        ],
    )
    print(directory)
    if failures or report["invalid_annotations"]:
        raise SystemExit(2)


if __name__ == "__main__":
    safe_main(main)
