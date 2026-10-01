"""FR-S-01/04 and NFR-01 scanner parser, retry, and environment tests."""

import json
import shutil
from pathlib import Path

import pytest

from app.domain.enums import Severity, Variant
from app.scanners.checkov_parser import parse_checkov
from app.scanners.runner import (
    ProcessToolRunner,
    RecordedToolRunner,
    ToolFailure,
    ToolResult,
)
from app.scanners.scan import Scanner
from app.scanners.terraform_parser import parse_terraform
from app.scanners.trivy_parser import parse_trivy
from scripts.normalize_security_fixture import RECORDED_ROOT, normalize_capture

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/security"


def files(state: str, fixtures: Path = FIXTURES) -> dict[str, str]:
    root = fixtures / state
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def recorded(
    state: str, repeat: int = 1, fixtures: Path = FIXTURES
) -> RecordedToolRunner:
    outputs = {
        tool: [
            ToolResult(
                (
                    fixtures / f"{tool}-{state.replace(chr(95), chr(45))}.json"
                ).read_text(),
                "",
                0,
                0.1,
            )
            for _ in range(repeat)
        ]
        for tool in ("checkov", "trivy", "terraform")
    }
    return RecordedToolRunner(outputs, recorded_root=Path(RECORDED_ROOT))


def recorded_output(tool: str, state: str, fixtures: Path = FIXTURES) -> str:
    return (
        (fixtures / f"{tool}-{state.replace(chr(95), chr(45))}.json")
        .read_text()
        .replace(RECORDED_ROOT, str((fixtures / state).resolve()))
    )


@pytest.mark.req("FR-S-01", "FR-S-04")
async def test_recorded_vulnerable_and_fixed_scans() -> None:
    vulnerable = await Scanner(recorded("vulnerable")).scan(
        files("vulnerable"), Variant.SECURITY
    )
    assert any(v.rule_id == "CKV_AWS_16" and v.blocking for v in vulnerable.violations)
    assert any(v.tool == "trivy" and v.blocking for v in vulnerable.violations)
    assert all(v.file_path in files("vulnerable") for v in vulnerable.violations)
    assert any(v.line_start and v.line_end for v in vulnerable.violations)
    fixed = await Scanner(recorded("fixed")).scan(files("fixed"), Variant.SECURITY)
    assert not any(v.blocking for v in fixed.violations)


@pytest.mark.req("FR-S-01")
def test_checkov_and_trivy_shapes() -> None:
    root = (FIXTURES / "vulnerable").resolve()
    paths = set(files("vulnerable"))
    checkov = recorded_output("checkov", "vulnerable")
    assert parse_checkov(checkov, root, paths)
    reports = json.loads(checkov)
    assert isinstance(reports, list)
    assert len(parse_checkov(json.dumps(reports[0]), root, paths)) == len(
        parse_checkov(json.dumps([reports[0]]), root, paths)
    )
    trivy = recorded_output("trivy", "vulnerable")
    assert parse_trivy(trivy, root, paths)
    with pytest.raises(ValueError):
        parse_trivy("unexpected banner\n" + trivy, root, paths)
    with pytest.raises(ValueError):
        parse_checkov("broken", root, paths)
    assert (
        parse_checkov(
            '{"passed":0,"failed":0,"resource_count":0,"checkov_version":"3.3.21"}',
            root,
            paths,
        )
        == []
    )


@pytest.mark.req("FR-S-01")
async def test_recorded_fixtures_parse_after_copy(tmp_path: Path) -> None:
    copied = tmp_path / "portable-security-fixtures"
    shutil.copytree(FIXTURES, copied)
    package_root = copied / "vulnerable"
    paths = set(files("vulnerable", copied))
    assert parse_checkov(
        recorded_output("checkov", "vulnerable", copied), package_root, paths
    )
    assert parse_trivy(
        recorded_output("trivy", "vulnerable", copied), package_root, paths
    )
    result = await Scanner(recorded("vulnerable", fixtures=copied)).scan(
        files("vulnerable", copied), Variant.SECURITY
    )
    assert all(item.file_path in paths for item in result.violations)
    raw = recorded_output("trivy", "vulnerable", copied)
    assert RECORDED_ROOT in normalize_capture(raw, package_root)


@pytest.mark.req("FR-S-01")
async def test_one_whole_scan_retry_and_two_failures() -> None:
    runner = recorded("fixed", repeat=2)
    runner.results["trivy"][0] = ToolFailure("trivy", "timeout")
    result = await Scanner(runner).scan(files("fixed"), Variant.SECURITY)
    assert result.tool_status == {"checkov": "ok", "trivy": "ok", "terraform": "ok"}
    assert runner.calls.count("checkov") == runner.calls.count("trivy") == 2
    failed = recorded("fixed", repeat=2)
    failed.results["trivy"] = [ToolFailure("trivy", "timeout")] * 2
    with pytest.raises(ToolFailure, match="trivy: timeout"):
        await Scanner(failed).scan(files("fixed"), Variant.SECURITY)
    unparseable = recorded("fixed", repeat=2)
    unparseable.results["trivy"] = [
        ToolResult("Error: scan failed: no HCL location", "", 1, 0) for _ in range(2)
    ]
    with pytest.raises(ToolFailure, match="trivy: invalid_json"):
        await Scanner(unparseable).scan(files("fixed"), Variant.SECURITY)
    assert unparseable.calls.count("trivy") == 2


@pytest.mark.req("FR-S-01", "FR-S-02")
async def test_recorded_terraform_hcl_error_is_a_syntax_limited_finding() -> None:
    root = (FIXTURES / "syntax_error").resolve()
    raw = (FIXTURES / "terraform-syntax-error.json").read_text()
    output = raw.replace(RECORDED_ROOT, str(root))
    finding = parse_terraform(output, root, {"terraform/main.tf"})[0]
    assert finding.rule_id == "TERRAFORM_SYNTAX"
    assert finding.tool == "terraform"
    assert finding.severity == Severity.CRITICAL
    assert finding.file_path == "terraform/main.tf"
    assert finding.line_start == finding.line_end == 1
    assert finding.title.startswith("Extraneous label for locals")
    assert str(root) not in str(finding.model_dump())
    runner = RecordedToolRunner(
        {
            "checkov": [
                ToolResult('{"passed":0,"failed":0,"resource_count":0}', "", 0, 0)
            ],
            "trivy": [
                ToolResult((FIXTURES / "trivy-syntax-error.json").read_text(), "", 0, 0)
            ],
            "terraform": [ToolResult(raw, "", 1, 0)],
        },
        recorded_root=Path(RECORDED_ROOT),
    )
    scan = await Scanner(runner).scan(files("syntax_error"), Variant.SECURITY)
    assert scan.syntax_limited
    assert scan.tool_status["terraform"] == "syntax_limited"
    assert scan.violations[0].blocking


@pytest.mark.req("NFR-01")
async def test_subprocess_has_no_application_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = tmp_path / "checkov"
    fake.write_text(
        "#!/usr/bin/env python3\nimport json,os\nprint(json.dumps(dict(os.environ)))\n"
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:/usr/bin:/bin")
    monkeypatch.setenv("LLM_API_KEY", "canary-key")
    monkeypatch.setenv("DATABASE_URL", "canary-database")
    result = await ProcessToolRunner(5).run("checkov", tmp_path)
    environment = json.loads(result.stdout)
    assert "LLM_API_KEY" not in environment
    assert "DATABASE_URL" not in environment
    assert environment["HOME"] == str(tmp_path)


@pytest.mark.scanners
@pytest.mark.req("FR-S-01", "NFR-01")
@pytest.mark.skipif(
    any(not shutil.which(tool) for tool in ("checkov", "trivy", "terraform")),
    reason="local scanners are not installed",
)
async def test_real_scanners_run_offline_on_both_fixtures() -> None:
    scanner = Scanner(ProcessToolRunner(120))
    vulnerable = await scanner.scan(files("vulnerable"), Variant.SECURITY)
    assert any(v.rule_id == "CKV_AWS_16" for v in vulnerable.violations)
    assert any(v.tool == "trivy" and v.blocking for v in vulnerable.violations)
    fixed = await scanner.scan(files("fixed"), Variant.SECURITY)
    assert not any(v.blocking for v in fixed.violations)


@pytest.mark.scanners
@pytest.mark.req("FR-S-01", "FR-S-02")
@pytest.mark.skipif(
    any(not shutil.which(tool) for tool in ("checkov", "trivy", "terraform")),
    reason="local scanners are not installed",
)
async def test_real_terraform_hcl_error_is_fixable_finding(tmp_path: Path) -> None:
    scanner = Scanner(ProcessToolRunner(120))
    scan = await scanner.scan(files("syntax_error"), Variant.SECURITY)
    assert scan.syntax_limited
    assert scan.tool_status["terraform"] == "syntax_limited"
    assert len(scan.violations) == 1
    finding = scan.violations[0]
    assert finding.rule_id == "TERRAFORM_SYNTAX"
    assert finding.file_path == "terraform/main.tf"
    assert finding.line_start == 1
    assert finding.blocking
    checkov_root = tmp_path / "checkov"
    (checkov_root / "terraform").mkdir(parents=True)
    (checkov_root / "terraform/main.tf").write_text(
        (FIXTURES / "syntax_error/terraform/main.tf").read_text()
    )
    checkov = await ProcessToolRunner(120).run("checkov", checkov_root)
    assert json.loads(checkov.stdout)["parsing_errors"] == 0
