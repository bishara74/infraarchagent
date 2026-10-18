"""Checkov's single-framework object and multi-framework list JSON forms."""

import json
import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from app.domain.models import Violation
from app.domain.paths import validate_relative_path
from app.scanners.paths import scanner_path


class CheckovPathError(ValueError):
    """Valid report JSON whose location cannot be mapped without ambiguity."""


def checkov_path(
    raw: object, root: Path, files: set[str], framework: object
) -> tuple[str, bool]:
    try:
        return scanner_path(raw, root, files, allow_report_relative=True), False
    except ValueError:
        pass
    if not isinstance(raw, str) or framework != "helm":
        raise CheckovPathError("scanner location unmappable")
    reported = raw.lstrip("/")
    try:
        validate_relative_path(reported)
    except ValueError:
        raise CheckovPathError("scanner location unmappable") from None
    matches = []
    for chart in sorted(
        p for p in files if p.startswith("helm/") and p.endswith("/Chart.yaml")
    ):
        try:
            metadata = yaml.safe_load((root / chart).read_text())
            name = metadata.get("name") if isinstance(metadata, dict) else None
            if not isinstance(name, str) or not re.fullmatch(
                r"[a-z0-9][a-z0-9-]*", name
            ):
                continue
            parent = str(Path(chart).parent)
            prefix = parent + "/" + name + "/templates/"
            if reported.startswith(prefix):
                candidate = parent + "/templates/" + reported[len(prefix) :]
                if candidate in files:
                    matches.append(candidate)
        except (OSError, yaml.YAMLError):
            continue
    if len(matches) != 1:
        raise CheckovPathError("scanner location unmappable")
    return matches[0], True


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
                path, rendered = checkov_path(
                    entry.get("file_path") or entry.get("file_abs_path"),
                    root,
                    files,
                    report.get("check_type"),
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
                        line_start=int(lines[0]) if lines and not rendered else None,
                        line_end=int(lines[1])
                        if len(lines) > 1 and not rendered
                        else None,
                        tool="checkov",
                    )
                )
        return violations
    except CheckovPathError:
        raise
    except (TypeError, ValueError, KeyError, IndexError) as error:
        raise ValueError("invalid Checkov JSON") from error
