"""FR-G-05: Checkov is the pass measure; all tool counts remain visible."""

import json
from pathlib import Path

import pytest
from pydantic import SecretStr

from app.core.config import Settings, get_settings
from app.domain.enums import Severity
from app.domain.models import Violation
from app.scanners.runner import RecordedToolRunner, ToolFailure, ToolResult
from app.scanners.scan import Scanner, ScanResult
from scripts import eval_security


@pytest.mark.req("FR-G-05")
async def test_scan_only_reports_separate_and_combined_high_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "packages" / "model" / "three_tier" / "security"
    (folder / "terraform").mkdir(parents=True)
    (folder / "terraform/main.tf").write_text("terraform {}\n")

    class FakeScanner(Scanner):
        def __init__(self, runner: object) -> None:
            pass

        async def scan(
            self, files: dict[str, str], variant: object, *, iteration: int = 0
        ) -> ScanResult:
            return ScanResult(
                [
                    Violation(
                        rule_id="AWS-0080",
                        severity=Severity.HIGH,
                        file_path="terraform/main.tf",
                        resource="db",
                        message="unsafe",
                        tool="trivy",
                        blocking=True,
                    )
                ],
                {"checkov": "ok", "trivy": "ok", "terraform": "ok"},
            )

    monkeypatch.setattr(eval_security, "Scanner", FakeScanner)
    output = await eval_security.run_evaluation(
        get_settings(), packages=[folder], output_root=tmp_path
    )
    result = json.loads((output / "results.json").read_text())
    case = result["cases"][0]
    assert case["first_scan_checkov_high_or_critical"] == 0
    assert case["first_scan_trivy_high_or_critical"] == 1
    assert case["first_scan_combined_high_or_critical"] == 1
    assert case["fr_g_05_pass"] is True
    assert result["aggregate"]["model"]["fr_g_05_pass"] is True
    assert "Trivy HIGH/CRITICAL 1" in (output / "summary.md").read_text()


@pytest.mark.req("FR-G-05", "FR-S-01")
async def test_evaluation_retains_checkov_measure_when_trivy_cannot_parse(
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

    class PartialScanner(Scanner):
        def __init__(self, runner: object) -> None:
            self.runner = RecordedToolRunner(
                {
                    "checkov": [ToolResult(checkov_json, "", 1, 0)],
                    "trivy": [ToolResult("invalid Terraform", "", 1, 0)],
                    "terraform": [ToolResult('{"diagnostics":[]}', "", 0, 0)],
                }
            )

        async def scan(
            self, files: dict[str, str], variant: object, *, iteration: int = 0
        ) -> ScanResult:
            raise ToolFailure("trivy", "invalid_json")

    monkeypatch.setattr(eval_security, "Scanner", PartialScanner)
    output = await eval_security.run_evaluation(
        get_settings(), packages=[folder], output_root=tmp_path
    )
    case = json.loads((output / "results.json").read_text())["cases"][0]
    assert case["scanner_errors"] == {"trivy": "invalid_json"}
    assert case["first_scan_checkov_high_or_critical"] == 1
    assert case["first_scan_trivy_high_or_critical"] is None
    assert case["first_scan_combined_high_or_critical"] is None
    assert case["fr_g_05_pass"] is False
    remediation_output = await eval_security.run_evaluation(
        get_settings(), packages=[folder], remediate=True, output_root=tmp_path
    )
    summary = (remediation_output / "summary.md").read_text()
    assert "## Remediation results" in summary
    assert "scan_error" in summary


@pytest.mark.req("FR-S-01", "FR-G-05")
async def test_evaluation_reports_syntax_limited_scan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "packages" / "model" / "three_tier" / "security"
    (folder / "terraform").mkdir(parents=True)
    (folder / "terraform/main.tf").write_text('locals "x" { a = 1 }\n')

    class SyntaxScanner:
        def __init__(self, runner: object) -> None:
            pass

        async def scan(
            self, files: dict[str, str], variant: object, *, iteration: int = 0
        ) -> ScanResult:
            return ScanResult(
                [
                    Violation(
                        rule_id="TERRAFORM_SYNTAX",
                        severity=Severity.CRITICAL,
                        file_path="terraform/main.tf",
                        resource="",
                        message="Extraneous label for locals",
                        title="Extraneous label for locals",
                        line_start=1,
                        tool="terraform",
                        blocking=True,
                    )
                ],
                {"checkov": "ok", "trivy": "ok", "terraform": "syntax_limited"},
                True,
            )

    monkeypatch.setattr(eval_security, "Scanner", SyntaxScanner)
    output = await eval_security.run_evaluation(
        get_settings(), packages=[folder], output_root=tmp_path
    )
    result = json.loads((output / "results.json").read_text())
    case = result["cases"][0]
    assert case["syntax_limited"] is True
    assert case["scanner_errors"] == {}
    assert case["syntax_findings"][0]["file_path"] == "terraform/main.tf"
    assert case["top_rule_ids"] == ["TERRAFORM_SYNTAX"]
    assert case["first_scan_trivy_high_or_critical"] == 0
    assert case["first_scan_terraform_high_or_critical"] == 1
    assert case["first_scan_combined_high_or_critical"] == 1
    assert "syntax-limited" in (output / "summary.md").read_text()
    assert result["aggregate"]["model"]["syntax_limited_count"] == 1


@pytest.mark.req("FR-S-04", "FR-G-05")
async def test_remediation_summary_uses_report_reason_and_fixing_model_price(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "packages" / "generator-model" / "three_tier" / "security"
    (folder / "terraform").mkdir(parents=True)
    (folder / "terraform/main.tf").write_text("terraform {}\n")

    class FakeScanner(Scanner):
        def __init__(self, runner: object) -> None:
            pass

        async def scan(
            self, files: dict[str, str], variant: object, *, iteration: int = 0
        ) -> ScanResult:
            return ScanResult(
                [
                    Violation(
                        rule_id=rule,
                        severity=Severity.HIGH,
                        file_path="terraform/main.tf",
                        resource="db",
                        message="unsafe",
                        tool="trivy",
                        blocking=True,
                    )
                    for rule in ("AWS-0080", "aws-rds-public")
                ],
                {"checkov": "ok", "trivy": "ok", "terraform": "ok"},
            )

    async def fake_remediate(*args: object) -> tuple[dict[str, object], str]:
        return (
            {
                "fixing_model": "fixer-model",
                "fix_passes": 2,
                "iterations": [
                    {
                        "fixes": [
                            {
                                "file": "terraform/main.tf",
                                "accepted": True,
                                "reason": None,
                                "input_tokens": 1000,
                                "output_tokens": 1000,
                            }
                        ]
                    },
                    {
                        "fixes": [
                            {
                                "file": "terraform/main.tf",
                                "accepted": False,
                                "reason": "schema:file.content.missing",
                                "input_tokens": 0,
                                "output_tokens": 1000,
                            }
                        ]
                    },
                ],
                "final": {
                    "outcome": "exhausted",
                    "reason": "no progress",
                    "remaining_blocking": [{"severity": "HIGH"}],
                },
            },
            "",
        )

    monkeypatch.setattr(eval_security, "Scanner", FakeScanner)
    monkeypatch.setattr(eval_security, "_remediate", fake_remediate)
    settings = Settings.model_construct(
        database_url=SecretStr("unused"),
        migration_database_url=SecretStr("unused"),
        test_database_url=SecretStr("unused"),
        test_migration_database_url=SecretStr("unused"),
        llm_model="generator-model",
    )
    output = await eval_security.run_evaluation(
        settings,
        packages=[folder],
        remediate=True,
        price_in={"generator-model": 1000, "fixer-model": 2},
        price_out={"generator-model": 1000, "fixer-model": 3},
        output_root=tmp_path,
    )
    result = json.loads((output / "results.json").read_text())
    case = result["cases"][0]
    assert case["generator_model"] == "generator-model"
    assert case["fixing_model"] == "fixer-model"
    assert case["first_scan_blocking_count"] == 2
    assert case["blocking_after_count"] == 1
    assert case["fix_passes"] == 2
    assert case["stop_reason"] == "no progress"
    assert case["blocking_after_by_severity"] == {"HIGH": 1}
    assert case["fixes_accepted"] == 1
    assert case["fixes_rejected_by_reason"] == {"schema:file.content.missing": 1}
    assert case["estimated_cost"] == pytest.approx(0.008)
    aggregate = result["fixing_aggregate"]["fixer-model"]
    assert aggregate["total_reduction_percent"] == 50
    assert aggregate["clean_rate"] == 0
    assert aggregate["mean_remaining"] == 1
    summary = (output / "summary.md").read_text()
    assert "## Remediation results" in summary
    assert "schema:file.content.missing:1" in summary
    assert "no progress" in summary
    assert "## Fixing model aggregates" in summary
    unknown_price = await eval_security.run_evaluation(
        settings,
        packages=[folder],
        remediate=True,
        price_in={"generator-model": 1000},
        price_out={"generator-model": 1000},
        output_root=tmp_path,
    )
    unpriced = json.loads((unknown_price / "results.json").read_text())
    assert unpriced["cases"][0]["estimated_cost"] is None


@pytest.mark.req("FR-S-01", "FR-S-04")
async def test_progress_retains_recovered_timeout_and_limits_packages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "model" / "plan" / "security"
    folder.mkdir(parents=True)
    (folder / "main.tf").write_text("locals {}")
    runner = RecordedToolRunner(
        {
            "checkov": [
                ToolResult('{"passed":0,"failed":0,"resource_count":0}', "", 0, 0)
            ]
            * 2,
            "terraform": [ToolResult('{"diagnostics":[]}', "", 0, 0)] * 2,
            "trivy": [
                ToolFailure("trivy", "timeout"),
                ToolResult('{"Results":[]}', "", 0, 0),
            ],
        }
    )
    monkeypatch.setattr(eval_security, "ProcessToolRunner", lambda _: runner)
    settings = Settings.model_construct()
    output = await eval_security.run_evaluation(
        settings,
        packages=[folder, tmp_path / "must-not-be-read"],
        packages_limit=1,
        output_root=tmp_path,
    )
    case = json.loads((output / "results.json").read_text())["cases"][0]
    assert case["scanner_errors"] == {}
    assert case["scan_timeouts"][0]["tool"] == "trivy"
    assert case["scan_timeouts"][0]["iteration"] == 0
    assert case["scan_timeouts"][0]["attempt"] == 1
    assert runner.calls.count("checkov") == runner.calls.count("trivy") == 2
    stderr = capsys.readouterr().err
    assert "package=model/plan/security status=started" in stderr
    assert "iteration=0 attempt=1 tool=trivy" in stderr
    assert "status=timeout" in stderr
    assert "status=finished" in stderr
    with pytest.raises(ValueError, match="packages_limit"):
        await eval_security.run_evaluation(settings, packages_limit=0)
