"""FR-S-01/02, NFR-01: recordings, syntax boundaries and offline scanners."""

import json
import shutil

import pytest

from app.security.reports import first_scan_counts
from tests.unit.test_scanners import FIXTURES

CORPUS = json.loads((FIXTURES / "terraform-diagnostics.json").read_text())["cases"]
TOOLS_AVAILABLE = all(shutil.which(tool) for tool in ("checkov", "trivy", "terraform"))


@pytest.mark.req("FR-S-01", "FR-G-05")
def test_legacy_report_counts_keep_actual_tool_attribution() -> None:
    legacy = {
        "first_scan_checkov_high_or_critical": 2,
        "first_scan_tfsec_high_or_critical": 3,
        "first_scan_combined_high_or_critical": 5,
    }
    assert first_scan_counts({"final": legacy}) == {
        "checkov": 2,
        "tfsec": 3,
        "combined": 5,
    }
    current = {
        **legacy,
        "first_scan_trivy_high_or_critical": None,
        "first_scan_terraform_high_or_critical": 1,
    }
    assert first_scan_counts(current) == {
        "checkov": 2,
        "trivy": None,
        "terraform": 1,
        "combined": 5,
    }
