"""tfsec JSON parsing, including a known human-readable preamble if present."""

import json
import re
from pathlib import Path

from app.domain.enums import Severity
from app.domain.models import Violation
from app.scanners.paths import scanner_path

_SYNTAX_ERROR = re.compile(
    r"^Error: scan failed: (?P<path>.+):(?P<line>[1-9]\d*),\d+(?:-\d+)?: "
    r"(?P<message>.+)$",
    re.MULTILINE,
)


def _parse_syntax_error(output: str, root: Path, files: set[str]) -> Violation | None:
    match = _SYNTAX_ERROR.search(output)
    if match is None:
        return None
    raw_path = match.group("path")
    root_without_slash = str(root.resolve()).lstrip("/")
    if raw_path.startswith(root_without_slash + "/"):
        raw_path = "/" + raw_path
    path = scanner_path(raw_path, root, files)
    message = match.group("message")
    for prefix in (str(root.resolve()), root_without_slash):
        message = message.replace(prefix, "[package]")
    line = int(match.group("line"))
    return Violation(
        rule_id="TERRAFORM_SYNTAX",
        severity=Severity.CRITICAL,
        file_path=path,
        resource="",
        message=message[:1000],
        title=message[:200],
        line_start=line,
        line_end=line,
        tool="tfsec",
        blocking=True,
    )


def parse_tfsec(output: str, root: Path, files: set[str]) -> list[Violation]:
    syntax = _parse_syntax_error(output, root, files)
    if syntax is not None:
        return [syntax]
    try:
        start = output.find("{")
        if start < 0 or (
            start > 0 and "tfsec is joining the Trivy family" not in output[:start]
        ):
            raise ValueError
        data, end = json.JSONDecoder().raw_decode(output[start:])
        if output[start + end :].strip() or not isinstance(data, dict):
            raise ValueError
        results = data["results"]
        if not isinstance(results, list):
            raise ValueError
        violations: list[Violation] = []
        for item in results:
            if not isinstance(item, dict):
                raise ValueError
            location = item["location"]
            links = item.get("links") or []
            violations.append(
                Violation(
                    rule_id=str(item.get("long_id") or item["rule_id"]),
                    severity=Severity(str(item["severity"]).upper()),
                    file_path=scanner_path(location["filename"], root, files),
                    resource=str(item.get("resource") or ""),
                    message=str(
                        item.get("description") or item.get("rule_description") or ""
                    )[:1000],
                    title=str(item.get("rule_description") or "")[:200],
                    guide_url=str(links[0])[:500] if links else None,
                    line_start=int(location["start_line"])
                    if location.get("start_line")
                    else None,
                    line_end=int(location["end_line"])
                    if location.get("end_line")
                    else None,
                    tool="tfsec",
                )
            )
        return violations
    except (TypeError, ValueError, KeyError, IndexError) as error:
        raise ValueError("invalid tfsec JSON") from error
