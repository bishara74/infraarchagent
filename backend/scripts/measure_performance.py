"""Wrap installed timing suites with Phase 9 raw evidence and safe metadata."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

from app.core.config import Settings
from scripts.phase9_common import BACKEND, evidence_directory, safe_main, write_json
from scripts.phase9_report import summary
from scripts.run_verification import verification_environment


def junit_counts(path: Path) -> dict[str, int]:
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = {
        name: sum(int(suite.get(name, 0)) for suite in suites)
        for name in ("tests", "failures", "errors", "skipped")
    }
    total["passed"] = (
        total["tests"] - total["failures"] - total["errors"] - total["skipped"]
    )
    return total


def run(kind: str, directory: Path, *, runner=subprocess.run) -> dict:
    # Explicit environment settings only, including in verification's parent.
    settings = Settings(_env_file=None)
    env = verification_environment(settings)
    env["INFRAARCH_PHASE9_OUTPUT_DIR"] = str(directory.resolve())
    if kind == "backend":
        command = [
            sys.executable,
            "-m",
            "scripts.run_verification",
            "pytest",
            "-q",
            "-m",
            "perf",
            "--junitxml",
            str(directory / "results.xml"),
            "-o",
            "junit_family=xunit1",
        ]
    else:
        command = [
            sys.executable,
            "-m",
            "scripts.run_verification",
            "e2e",
            "--grep",
            "@perf",
            "--reporter=list,json",
        ]
        env["PLAYWRIGHT_JSON_OUTPUT_FILE"] = str(directory / "playwright.json")
    summary(
        directory / "summary.md",
        "Quiet-machine timing suite",
        "INCOMPLETE",
        ["Timing suite started."],
    )
    try:
        result = runner(
            command,
            cwd=BACKEND,
            env=env,
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
    except subprocess.TimeoutExpired:
        from types import SimpleNamespace

        result = SimpleNamespace(
            returncode=2, stdout="", stderr="Timing suite observation timeout.\n"
        )
    (directory / "console.txt").write_text(result.stdout + result.stderr)
    counts = None
    try:
        if kind == "backend":
            counts = junit_counts(directory / "results.xml")
        else:
            stats = json.loads((directory / "playwright.json").read_text())["stats"]
            counts = {
                "passed": stats["expected"],
                "failures": stats["unexpected"],
                "skipped": stats["skipped"],
                "flaky": stats["flaky"],
            }
    except (OSError, ValueError, KeyError, ElementTree.ParseError):
        pass
    report = {
        "kind": kind,
        "returncode": result.returncode,
        "counts": counts,
        "mode": "stub",
        "quiet_machine": "Operator must confirm; not inferred.",
    }
    write_json(directory / "results.json", report)
    summary(
        directory / "summary.md",
        "Quiet-machine timing suite",
        "PASS"
        if result.returncode == 0 and counts is not None
        else "FAIL"
        if counts
        else "INCOMPLETE",
        [
            json.dumps(report),
            "Raw console and test reports retain measured samples.",
            "Stub evidence; author benchmarks supply real-provider timings.",
        ],
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["backend", "ui"])
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    directory = evidence_directory(
        "backend-perf" if args.kind == "backend" else "pr02",
        args.output_dir,
        mode="stub",
        provider="stub",
        model="stub",
    )
    report = run(args.kind, directory)
    print(directory)
    raise SystemExit(report["returncode"])


if __name__ == "__main__":
    safe_main(main)
