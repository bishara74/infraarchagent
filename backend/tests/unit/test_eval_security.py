"""FR-G-05: Checkov is the pass measure; all tool counts remain visible."""

import json
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.domain.enums import Severity
from app.domain.models import Violation
from app.scanners.runner import RecordedToolRunner, ToolFailure, ToolResult
from app.scanners.scan import ScanResult
from scripts import eval_security


@pytest.mark.req("FR-G-05")
async def test_scan_only_reports_separate_and_combined_high_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "packages" / "model" / "three_tier" / "security"
    (folder / "terraform").mkdir(parents=True)
    (folder / "terraform/main.tf").write_text("terraform {}\n")

    class FakeScanner:
        def __init__(self, runner: object) -> None:
            pass

        async def scan(self, files: dict[str, str], variant: object) -> ScanResult:
            return ScanResult(
                [
                    Violation(
                        rule_id="aws-rds-encrypt",
                        severity=Severity.HIGH,
                        file_path="terraform/main.tf",
                        resource="db",
                        message="unsafe",
                        tool="tfsec",
                        blocking=True,
                    )
                ],
                {"checkov": "ok", "tfsec": "ok"},
            )

    monkeypatch.setattr(eval_security, "Scanner", FakeScanner)
    output = await eval_security.run_evaluation(
        get_settings(), packages=[folder], output_root=tmp_path
    )
    result = json.loads((output / "results.json").read_text())
    case = result["cases"][0]
    assert case["first_scan_checkov_high_or_critical"] == 0
    assert case["first_scan_tfsec_high_or_critical"] == 1
    assert case["first_scan_combined_high_or_critical"] == 1
    assert case["fr_g_05_pass"] is True
    assert result["aggregate"]["model"]["fr_g_05_pass"] is True
    assert "tfsec HIGH/CRITICAL 1" in (output / "summary.md").read_text()


@pytest.mark.req("FR-G-05", "FR-S-01")
async def test_evaluation_retains_checkov_measure_when_tfsec_cannot_parse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "packages" / "model" / "three_tier" / "security"
    (folder / "terraform").mkdir(parents=True)
    (folder / "terraform/main.tf").write_text("terraform {}\n")
    checkov_json = json.dumps(
        {
            "results": {
                "failed_checks": [
                    {
                        "check_id": "CKV_AWS_16",
                        "file_path": "/terraform/main.tf",
                        "resource": "db",
                        "check_name": "RDS encryption",
                        "file_line_range": [1, 1],
                    }
                ]
            }
        }
    )

    class PartialScanner:
        def __init__(self, runner: object) -> None:
            self.runner = RecordedToolRunner(
                {
                    "checkov": [ToolResult(checkov_json, "", 1, 0)],
                    "tfsec": [ToolResult("invalid Terraform", "", 1, 0)],
                }
            )

        async def scan(self, files: dict[str, str], variant: object) -> ScanResult:
            raise ToolFailure("tfsec", "invalid_json")

    monkeypatch.setattr(eval_security, "Scanner", PartialScanner)
    output = await eval_security.run_evaluation(
        get_settings(), packages=[folder], output_root=tmp_path
    )
    case = json.loads((output / "results.json").read_text())["cases"][0]
    assert case["scanner_errors"] == {"tfsec": "invalid_json"}
    assert case["first_scan_checkov_high_or_critical"] == 1
    assert case["first_scan_tfsec_high_or_critical"] is None
    assert case["first_scan_combined_high_or_critical"] is None
    assert case["fr_g_05_pass"] is False
