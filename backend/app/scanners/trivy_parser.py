"""Parse the emitted embedded-check IDs and file locations in Trivy JSON."""

import json
from pathlib import Path

from app.domain.enums import Severity
from app.domain.models import Violation
from app.scanners.paths import scanner_path


def parse_trivy(output: str, root: Path, files: set[str]) -> list[Violation]:
    try:
        data = json.loads(output)
        if not isinstance(data, dict):
            raise ValueError
        results = data.get("Results", [])
        if not isinstance(results, list):
            raise ValueError
        violations = []
        for result in results:
            if not isinstance(result, dict):
                raise ValueError
            entries = result.get("Misconfigurations")
            if entries is None:
                entries = []
            if not isinstance(entries, list):
                raise ValueError
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError
                if entry.get("Status") != "FAIL":
                    continue
                rule_id = entry.get("AVDID") or entry["ID"]
                if not isinstance(rule_id, str) or not rule_id:
                    raise ValueError
                cause = entry.get("CauseMetadata") or {}
                violations.append(
                    Violation(
                        tool="trivy",
                        rule_id=rule_id,
                        severity=Severity(entry["Severity"]),
                        file_path=scanner_path(result["Target"], root, files),
                        resource=str(cause.get("Resource") or ""),
                        line_start=cause.get("StartLine") or None,
                        line_end=cause.get("EndLine") or None,
                        title=str(entry.get("Title") or "")[:200],
                        message=str(entry.get("Message") or entry.get("Title") or "")[
                            :1000
                        ],
                        guide_url=str(entry["PrimaryURL"])[:500]
                        if entry.get("PrimaryURL")
                        else None,
                    )
                )
        return violations
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise ValueError("invalid Trivy JSON") from error
