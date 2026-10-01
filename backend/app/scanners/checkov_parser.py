"""Checkov's single-framework object and multi-framework list JSON forms."""

import json
from pathlib import Path

from app.domain.models import Violation
from app.scanners.paths import scanner_path


def parse_checkov(output: str, root: Path, files: set[str]) -> list[Violation]:
    try:
        data = json.loads(output)
        reports = data if isinstance(data, list) else [data]
        if not reports or any(not isinstance(report, dict) for report in reports):
            raise ValueError
        violations: list[Violation] = []
        for report in reports:
            if "results" not in report:
                # Checkov emits only a summary when no supported resource exists.
                if report.get("failed") == 0 and report.get("resource_count") == 0:
                    continue
                raise ValueError
            results = report["results"]
            failed = results["failed_checks"]
            if not isinstance(failed, list):
                raise ValueError
            for entry in failed:
                if not isinstance(entry, dict):
                    raise ValueError
                lines = entry.get("file_line_range") or []
                path = scanner_path(
                    entry.get("file_path") or entry.get("file_abs_path"),
                    root,
                    files,
                    allow_report_relative=True,
                )
                violations.append(
                    Violation(
                        rule_id=str(entry["check_id"]),
                        file_path=path,
                        resource=str(entry.get("resource") or ""),
                        message=str(entry.get("check_name") or "")[:1000],
                        title=str(entry.get("check_name") or "")[:200],
                        guide_url=(
                            str(entry["guideline"])[:500]
                            if entry.get("guideline")
                            else None
                        ),
                        line_start=int(lines[0]) if lines else None,
                        line_end=int(lines[1]) if len(lines) > 1 else None,
                        tool="checkov",
                    )
                )
        return violations
    except (TypeError, ValueError, KeyError, IndexError) as error:
        raise ValueError("invalid Checkov JSON") from error
