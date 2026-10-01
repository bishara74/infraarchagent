"""Read first-scan counts without relabelling historical tfsec evidence."""

from collections.abc import Mapping
from typing import Any


def first_scan_counts(report: Mapping[str, Any]) -> dict[str, int | None]:
    final = report.get("final", report)
    tools = (
        ("checkov", "trivy", "terraform")
        if "first_scan_trivy_high_or_critical" in final
        else ("checkov", "tfsec")
    )
    return {
        tool: final.get(f"first_scan_{tool}_high_or_critical")
        for tool in (*tools, "combined")
    }
