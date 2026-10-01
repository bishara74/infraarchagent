"""FR-S-01/02, NFR-01: recordings, syntax boundaries and offline scanners."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app.scanners.runner import ProcessToolRunner, scanner_environment
from tests.unit.test_scanners import FIXTURES, files

CORPUS = json.loads((FIXTURES / "terraform-diagnostics.json").read_text())["cases"]
TOOLS_AVAILABLE = all(shutil.which(tool) for tool in ("checkov", "trivy", "terraform"))


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("tool", ["checkov", "trivy", "terraform"])
async def test_all_subprocess_environments_are_minimal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tool: str
) -> None:
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    fake = binary_dir / tool
    fake.write_text(
        "#!/usr/bin/env python3\nimport json,os\nprint(json.dumps(dict(os.environ)))\n"
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{binary_dir}:/usr/bin:/bin")
    for key in (
        "LLM_API_KEY",
        "DATABASE_URL",
        "AWS_ACCESS_KEY_ID",
        "TRIVY_TOKEN",
        "CHECKOV_API_KEY",
        "TF_CLI_ARGS",
        "NO_PROXY",
        "HTTPS_PROXY",
    ):
        monkeypatch.setenv(key, "canary-key")
    result = await ProcessToolRunner(5).run(tool, tmp_path)
    env = json.loads(result.stdout)
    assert "canary-key" not in result.stdout
    assert env["HTTPS_PROXY"] == env["https_proxy"] == "http://127.0.0.1:9"
    assert env["NO_PROXY"] == env["no_proxy"] == ""
    assert env["HOME"] == str(tmp_path)
    if tool == "checkov":
        assert env["CHECKOV_PARALLELIZATION_TYPE"] == "none"
    if tool == "terraform":
        assert env["CHECKPOINT_DISABLE"] == "1"
        assert env["TF_DATA_DIR"] == str(tmp_path / ".terraform-data")


@pytest.mark.scanners
@pytest.mark.req("FR-S-01", "NFR-01")
@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="local scanners are not installed")
@pytest.mark.parametrize("remote", [False, True])
def test_real_scanners_with_network_namespace_and_fresh_cache(
    tmp_path: Path, remote: bool
) -> None:
    if (
        not shutil.which("unshare")
        or subprocess.run(["unshare", "-Urn", "true"], capture_output=True).returncode
    ):
        pytest.skip("network namespaces unavailable")
    script = """
import asyncio,json,sys
from app.scanners.runner import ProcessToolRunner
from app.scanners.scan import Scanner
from app.domain.enums import Variant
async def main():
    files=json.load(open(sys.argv[1]))
    runner=ProcessToolRunner(30)
    first=await Scanner(runner).scan(files,Variant.SECURITY)
    second=await Scanner(runner).scan(files,Variant.SECURITY)
    key=lambda v:(v.tool,v.rule_id,v.file_path,v.resource,
                  v.line_start,v.line_end,v.severity.value)
    assert sorted(map(key,first.violations)) == sorted(map(key,second.violations))
    assert any(v.rule_id == "AWS-0080" for v in first.violations)
    assert any(v.rule_id == "CKV_AWS_16" for v in first.violations)
    if "terraform/modules.tf" in files:
        assert any(v.rule_id == "EXTERNAL_MODULE_NOT_SCANNED" for v in first.violations)
    print(json.dumps([v.model_dump(mode="json") for v in first.violations]))
asyncio.run(main())
"""
    package = tmp_path / "files.json"
    package.write_text(json.dumps(files("remote_module" if remote else "vulnerable")))
    env = scanner_environment(tmp_path, "trivy")
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    completed = subprocess.run(
        ["unshare", "-Urn", sys.executable, "-c", script, str(package)],
        env=env,
        capture_output=True,
        text=True,
        timeout=75,
    )
    assert completed.returncode == 0, completed.stderr
    assert "downloading" not in completed.stderr.lower()
    assert "failed to download" not in completed.stderr.lower()
    assert "error" not in completed.stderr.lower()


@pytest.mark.scanners
@pytest.mark.req("FR-S-01")
@pytest.mark.skipif(not shutil.which("trivy"), reason="Trivy is not installed")
async def test_trivy_scans_helm_without_helm_and_does_not_download_checks(
    tmp_path: Path,
) -> None:
    shutil.copytree(FIXTURES / "helm", tmp_path, dirs_exist_ok=True)
    output = await ProcessToolRunner(30).run("trivy", tmp_path)
    assert output.exit_code == 0
    results = json.loads(output.stdout)["Results"]
    assert any(
        result["Type"] == "helm"
        and any(
            entry["ID"] == "KSV-0017" for entry in result.get("Misconfigurations", [])
        )
        for result in results
    )
    assert not (tmp_path / ".trivy-cache/policy/content").exists()
    assert not output.stderr


@pytest.mark.scanners
@pytest.mark.req("FR-S-01", "NFR-01")
@pytest.mark.skipif(not shutil.which("trivy"), reason="Trivy is not installed")
def test_embedded_checks_debug_evidence_in_network_namespace(tmp_path: Path) -> None:
    if (
        not shutil.which("unshare")
        or subprocess.run(["unshare", "-Urn", "true"], capture_output=True).returncode
    ):
        pytest.skip("network namespaces unavailable")
    completed = subprocess.run(
        [
            "unshare",
            "-Urn",
            "trivy",
            "config",
            str(FIXTURES / "vulnerable"),
            "--format",
            "json",
            "--exit-code",
            "0",
            "--skip-check-update",
            "--skip-version-check",
            "--disable-telemetry",
            "--cache-dir",
            str(tmp_path / "cache"),
            "--debug",
        ],
        env=scanner_environment(tmp_path, "trivy"),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Embedded checks are loaded" in completed.stderr
    assert "count=563" in completed.stderr
    assert "No downloadable checks were loaded" in completed.stderr
    errors = [line for line in completed.stderr.splitlines() if "\tERROR\t" in line]
    # Trivy logs this successful fresh-cache fallback as ERROR. It is not a
    # download failure; ignoring every ERROR would hide a real regression.
    assert len(errors) == 1 and "Falling back to embedded checks" in errors[0]
    assert "cache does not exist" in errors[0]
    assert "Downloading" not in completed.stderr
    assert not (tmp_path / "cache/policy/content").exists()
