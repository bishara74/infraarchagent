"""FR-S-01/04 and NFR-01 scanner parser, retry, and environment tests."""

import json
import shutil
from pathlib import Path

import pytest

from app.domain.enums import Variant
from app.scanners.checkov_parser import parse_checkov
from app.scanners.runner import (
    ProcessToolRunner,
    RecordedToolRunner,
    ToolFailure,
    ToolResult,
)
from app.scanners.scan import Scanner
from app.scanners.tfsec_parser import parse_tfsec

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/security"


def files(state: str) -> dict[str, str]:
    root = FIXTURES / state
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def recorded(state: str, repeat: int = 1) -> RecordedToolRunner:
    outputs = {
        tool: [
            ToolResult((FIXTURES / f"{tool}-{state}.json").read_text(), "", 0, 0.1)
            for _ in range(repeat)
        ]
        for tool in ("checkov", "tfsec")
    }
    return RecordedToolRunner(outputs, recorded_root=(FIXTURES / state).resolve())


@pytest.mark.req("FR-S-01", "FR-S-04")
async def test_recorded_vulnerable_and_fixed_scans() -> None:
    vulnerable = await Scanner(recorded("vulnerable")).scan(
        files("vulnerable"), Variant.SECURITY
    )
    assert any(v.rule_id == "CKV_AWS_16" and v.blocking for v in vulnerable.violations)
    assert any(v.tool == "tfsec" and v.blocking for v in vulnerable.violations)
    assert all(v.file_path in files("vulnerable") for v in vulnerable.violations)
    assert any(v.line_start and v.line_end for v in vulnerable.violations)
    fixed = await Scanner(recorded("fixed")).scan(files("fixed"), Variant.SECURITY)
    assert not any(v.blocking for v in fixed.violations)


@pytest.mark.req("FR-S-01")
def test_checkov_list_and_tfsec_banner_shapes() -> None:
    root = (FIXTURES / "vulnerable").resolve()
    paths = set(files("vulnerable"))
    checkov = (FIXTURES / "checkov-vulnerable.json").read_text()
    assert parse_checkov(checkov, root, paths)
    reports = json.loads(checkov)
    assert isinstance(reports, list)
    assert len(parse_checkov(json.dumps(reports[0]), root, paths)) == len(
        parse_checkov(json.dumps([reports[0]]), root, paths)
    )
    tfsec = (FIXTURES / "tfsec-vulnerable.json").read_text()
    assert parse_tfsec("tfsec is joining the Trivy family\n" + tfsec, root, paths)
    with pytest.raises(ValueError):
        parse_tfsec("unexpected banner\n" + tfsec, root, paths)
    with pytest.raises(ValueError):
        parse_checkov("broken", root, paths)


@pytest.mark.req("FR-S-01")
async def test_one_whole_scan_retry_and_two_failures() -> None:
    runner = recorded("fixed", repeat=2)
    runner.results["tfsec"][0] = ToolFailure("tfsec", "timeout")
    result = await Scanner(runner).scan(files("fixed"), Variant.SECURITY)
    assert result.tool_status == {"checkov": "ok", "tfsec": "ok"}
    assert runner.calls.count("checkov") == runner.calls.count("tfsec") == 2
    failed = recorded("fixed", repeat=2)
    failed.results["tfsec"] = [ToolFailure("tfsec", "timeout")] * 2
    with pytest.raises(ToolFailure, match="tfsec: timeout"):
        await Scanner(failed).scan(files("fixed"), Variant.SECURITY)


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
    not shutil.which("checkov") or not shutil.which("tfsec"),
    reason="local scanners are not installed",
)
async def test_real_scanners_run_offline_on_both_fixtures() -> None:
    scanner = Scanner(ProcessToolRunner(120))
    vulnerable = await scanner.scan(files("vulnerable"), Variant.SECURITY)
    assert any(v.rule_id == "CKV_AWS_16" for v in vulnerable.violations)
    assert any(v.tool == "tfsec" and v.blocking for v in vulnerable.violations)
    fixed = await scanner.scan(files("fixed"), Variant.SECURITY)
    assert not any(v.blocking for v in fixed.violations)
