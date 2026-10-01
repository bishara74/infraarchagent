"""FR-S-01/02, NFR-01: recordings, syntax boundaries and offline scanners."""

import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from app.domain.enums import Severity
from app.scanners.runner import ProcessToolRunner, scanner_versions
from app.scanners.terraform_parser import parse_terraform
from scripts.normalize_security_fixture import RECORDED_ROOT, normalize_capture
from tests.unit.test_scanners import FIXTURES, files, recorded_output

CORPUS = json.loads((FIXTURES / "terraform-diagnostics.json").read_text())["cases"]
TOOLS_AVAILABLE = all(shutil.which(tool) for tool in ("checkov", "trivy", "terraform"))


@pytest.mark.req("FR-S-01", "FR-S-02")
@pytest.mark.parametrize("case", CORPUS, ids=lambda case: case["name"])
def test_terraform_recorded_diagnostics(case: dict) -> None:
    root = Path("/tmp/portable-package")
    output = json.dumps(case["output"]).replace(RECORDED_ROOT, str(root))
    findings = parse_terraform(output, root, set(case["files"]))
    if case["expected"]:
        assert case["expected"] in {item.title for item in findings}
        assert all(
            item.tool == "terraform"
            and item.severity == Severity.CRITICAL
            and item.file_path in case["files"]
            and item.line_start
            for item in findings
        )
    else:
        assert findings == []
    assert "snippet" not in str([item.model_dump() for item in findings])


@pytest.mark.req("FR-S-01")
def test_terraform_formatting_warning_unknown_and_provider_schema_ignored() -> None:
    case = deepcopy(next(c for c in CORPUS if c["name"] == "unsupported"))
    for summary, severity, context in [
        ("Unrecognized summary", "error", None),
        ("Invalid expression", "warning", None),
        ("Unsupported block type", "error", 'provider "aws"'),
        ("Unsupported block type", "error", 'resource "terraform_data" "x"'),
    ]:
        diagnostic = case["output"]["diagnostics"][0]
        diagnostic.update(summary=summary, severity=severity)
        diagnostic["snippet"]["context"] = context
        assert (
            parse_terraform(
                json.dumps(case["output"]), Path(RECORDED_ROOT), set(case["files"])
            )
            == []
        )


@pytest.mark.req("FR-S-01", "NFR-01")
def test_terraform_unsafe_diagnostic_path_rejected() -> None:
    case = deepcopy(CORPUS[0])
    case["output"]["diagnostics"][0]["range"]["filename"] = "../escape.tf"
    with pytest.raises(ValueError):
        parse_terraform(
            json.dumps(case["output"]), Path("/tmp/package"), set(case["files"])
        )


@pytest.mark.req("NFR-01")
def test_version_probes_have_same_environment_and_terraform_first_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.scanners import runner

    seen = []

    def probe(args, **kwargs):
        seen.append(kwargs["env"])
        return subprocess.CompletedProcess(
            args,
            0,
            "Terraform v1.16.4\non linux_amd64\n"
            if args[0] == "terraform"
            else "Version 0.69.3\n",
            "",
        )

    monkeypatch.setattr(runner.shutil, "which", lambda tool: tool)
    monkeypatch.setattr(subprocess, "run", probe)
    monkeypatch.setenv("LLM_API_KEY", "canary-key")
    scanner_versions.cache_clear()
    try:
        assert scanner_versions()["terraform"]["version"] == "Terraform v1.16.4"
        assert len(seen) == 3
        assert all(
            "canary-key" not in json.dumps(env)
            and env["HTTPS_PROXY"] == "http://127.0.0.1:9"
            for env in seen
        )
    finally:
        scanner_versions.cache_clear()


@pytest.mark.scanners
@pytest.mark.req("FR-S-01", "FR-S-02")
@pytest.mark.skipif(not shutil.which("terraform"), reason="Terraform is not installed")
@pytest.mark.parametrize("case", CORPUS, ids=lambda case: case["name"])
async def test_real_terraform_diagnostics_match_recordings(
    tmp_path: Path, case: dict
) -> None:
    for name, source in case["files"].items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    output = await ProcessToolRunner(10).run("terraform", tmp_path)
    data = json.loads(output.stdout)
    if case["expected"]:
        assert case["expected"] in {d["summary"] for d in data["diagnostics"]}
    findings = parse_terraform(output.stdout, tmp_path, set(case["files"]))
    assert bool(findings) == bool(case["expected"])
    assert not (tmp_path / "terraform/.terraform").exists()


@pytest.mark.req("FR-S-01")
def test_normalize_trivy_relative_targets_and_terraform_diagnostics(
    tmp_path: Path,
) -> None:
    trivy = {
        "SchemaVersion": 2,
        "ArtifactType": "filesystem",
        "ArtifactName": ".",
        "Results": [{"Target": "terraform/main.tf"}],
    }
    normalized = json.loads(normalize_capture(json.dumps(trivy), tmp_path))
    assert normalized["ArtifactName"] == RECORDED_ROOT
    assert normalized["Results"][0]["Target"] == "terraform/main.tf"
    terraform = {
        "format_version": "1.0",
        "diagnostics": [{"range": {"filename": "main.tf"}}],
    }
    assert (
        json.loads(normalize_capture(json.dumps(terraform), tmp_path))["diagnostics"][
            0
        ]["range"]["filename"]
        == RECORDED_ROOT + "/terraform/main.tf"
    )


@pytest.mark.req("FR-S-01")
@pytest.mark.parametrize(
    "state",
    [
        "single_argument_block",
        "unclosed_block",
        "duplicate_argument",
        "missing_newline",
    ],
)
def test_dedicated_syntax_fixture_findings(state: str) -> None:
    raw = recorded_output("terraform", state)
    findings = parse_terraform(raw, FIXTURES / state, set(files(state)))
    assert findings and all(f.file_path == "terraform/main.tf" for f in findings)
