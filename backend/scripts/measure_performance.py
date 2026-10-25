"""Wrap installed timing suites with Phase 9 evidence and safe diagnostics."""

import argparse
import html
import json
import math
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

from pydantic import SecretStr, ValidationError

from app.core.config import Settings, get_settings
from app.core.logging import RedactingFilter
from scripts.phase9_common import BACKEND, evidence_directory, write_json
from scripts.phase9_report import summary
from scripts.run_verification import verification_environment


def junit_counts(path: Path) -> dict[str, int]:
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    if root.tag not in {"testsuite", "testsuites"} or not suites:
        raise ValueError("Missing JUnit test suites")
    total = {
        name: sum(int(suite.get(name, 0)) for suite in suites)
        for name in ("tests", "failures", "errors", "skipped")
    }
    total["passed"] = (
        total["tests"] - total["failures"] - total["errors"] - total["skipped"]
    )
    if total["tests"] == 0 or any(value < 0 for value in total.values()):
        raise ValueError("Missing or inconsistent JUnit counts")
    return total


def finish(
    directory: Path, report: dict, console: str, redactor: RedactingFilter
) -> dict:
    # Redact the complete structured report as well as the console: parametrized
    # test identifiers and report properties are not trusted diagnostic text.
    def clean(value):
        if isinstance(value, str):
            return redactor.redact(value)
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items()}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value

    report = clean(report)
    (directory / "console.txt").write_text(redactor.redact(console))
    write_json(directory / "results.json", report)
    summary(
        directory / "summary.md",
        "Quiet-machine timing suite",
        report["status"],
        [
            report["reason"],
            json.dumps(report),
            "Redacted console and test reports retain measured samples.",
            "Stub evidence; author benchmarks supply real-provider timings.",
        ],
    )
    return report


def captured(value: str | bytes | None) -> str:
    return (
        value.decode("utf-8", errors="replace")
        if isinstance(value, bytes)
        else value or ""
    )


def run(kind: str, directory: Path, *, runner=subprocess.run) -> dict:
    report = {
        "kind": kind,
        "returncode": 2,
        "counts": None,
        "status": "INCOMPLETE",
        "stage": "settings",
        "reason": "Verification settings unavailable.",
        "failed_tests": [],
        "measurements": [],
        "mode": "stub",
        "quiet_machine": "Operator must confirm; not inferred.",
    }
    redactor = RedactingFilter()
    try:
        # Use the same parent settings resolver as scripts.run_verification.
        # Verification bootstrap disables dotenv when explicitly requested.
        settings = get_settings()
        secrets = [
            value.get_secret_value()
            for name in Settings.model_fields
            if isinstance(value := getattr(settings, name), SecretStr)
        ]
        redactor = RedactingFilter(
            *secrets,
            *(html.escape(value, quote=True) for value in secrets),
            *(json.dumps(value)[1:-1] for value in secrets),
        )
        env = verification_environment(settings)
    except ValidationError as error:
        fields = sorted(
            {
                str(item["loc"][0]).upper()
                for item in error.errors(include_input=False, include_url=False)
                if item["loc"] and item["loc"][0] in Settings.model_fields
            }
        )
        report["reason"] = (
            "Invalid or missing verification settings: "
            + (", ".join(fields) if fields else "check declared setting fields")
            + "."
        )
        return finish(directory, report, report["reason"] + "\n", redactor)
    except OSError:
        report["reason"] = (
            "Cannot load verification settings; check settings file access."
        )
        return finish(directory, report, report["reason"] + "\n", redactor)
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
        raw_report = directory / "results.xml"
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
        raw_report = directory / "playwright.json"
        env["PLAYWRIGHT_JSON_OUTPUT_FILE"] = str(raw_report)
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
    except subprocess.TimeoutExpired as error:
        report.update(
            stage="timeout",
            reason="Timing suite exceeded its 1800-second observation timeout.",
        )
        if raw_report.exists():
            raw_report.write_text(redactor.redact(raw_report.read_text()))
        return finish(
            directory, report, captured(error.stdout) + captured(error.stderr), redactor
        )
    except OSError:
        report.update(
            stage="launch",
            reason="Cannot launch verification; "
            "check the installed interpreter and executables.",
        )
        return finish(directory, report, report["reason"] + "\n", redactor)
    report.update(returncode=result.returncode, stage="report")
    try:
        raw_report.write_text(redactor.redact(raw_report.read_text()))
        if kind == "backend":
            report["counts"] = junit_counts(raw_report)
            for case in ElementTree.parse(raw_report).getroot().iter("testcase"):
                identity = f"{case.get('classname', '')}::{case.get('name', '')}"
                for tag in ("failure", "error"):
                    for failure in case.findall(tag):
                        report["failed_tests"].append(
                            {
                                "id": identity,
                                "kind": tag,
                                "message": failure.get(
                                    "message", "Test failed; see console.txt."
                                ),
                            }
                        )
                for prop in case.findall("properties/property"):
                    if prop.get("name") == "pr04_seconds":
                        value = float(prop.get("value", "nan"))
                        if math.isfinite(value) and value >= 0:
                            report["measurements"].append(
                                {"id": identity, "pr04_seconds": value}
                            )
        else:
            stats = json.loads(raw_report.read_text())["stats"]
            report["counts"] = {
                "passed": int(stats["expected"]),
                "failures": int(stats["unexpected"]),
                "skipped": int(stats["skipped"]),
                "flaky": int(stats["flaky"]),
            }
    except (OSError, ValueError, KeyError, TypeError, ElementTree.ParseError):
        report.update(
            counts=None,
            reason=f"Verification exited {result.returncode}; {raw_report.name} "
            "is missing, unreadable or malformed. Check console.txt "
            "for prerequisite/collection errors.",
            returncode=result.returncode or 2,
        )
    else:
        counts = report["counts"]
        failed = counts["failures"] or counts.get("errors", 0)
        report.update(
            stage="tests",
            status="FAIL" if result.returncode or failed else "PASS",
            returncode=result.returncode or (1 if failed else 0),
            reason=(
                "Verification failed; see failed_tests and console.txt "
                "for failing tests or setup prerequisites."
            )
            if result.returncode or failed
            else "Timing suite passed.",
        )
    return finish(directory, report, result.stdout + result.stderr, redactor)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["backend", "ui"])
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    try:
        directory = evidence_directory(
            "backend-perf" if args.kind == "backend" else "pr02",
            args.output_dir,
            mode="stub",
            provider="stub",
            model="stub",
        )
    except (OSError, ValueError, RuntimeError) as error:
        print(
            f"Performance evidence setup failed ({type(error).__name__}); "
            "check --output-dir and local metadata tools.",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
    report = run(args.kind, directory)
    print((directory / "console.txt").read_text(), end="")
    print(f"{report['status']}: {report['reason']}")
    print(
        json.dumps({"counts": report["counts"], "measurements": report["measurements"]})
    )
    print(directory)
    raise SystemExit(report["returncode"])


if __name__ == "__main__":
    main()
