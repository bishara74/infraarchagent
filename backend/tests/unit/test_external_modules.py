"""FR-S-01/02, NFR-01: recordings, syntax boundaries and offline scanners."""

import json
import shutil
from pathlib import Path

import pytest

from app.domain.enums import Variant
from app.scanners.external_modules import external_module_findings
from app.scanners.runner import ProcessToolRunner
from app.scanners.trivy_parser import parse_trivy
from app.security.policy import classify
from tests.unit.test_scanners import FIXTURES, files, recorded_output

CORPUS = json.loads((FIXTURES / "terraform-diagnostics.json").read_text())["cases"]
TOOLS_AVAILABLE = all(shutil.which(tool) for tool in ("checkov", "trivy", "terraform"))


@pytest.mark.req("FR-S-01", "NFR-01")
def test_remote_module_advisories_are_located_and_never_expose_sources() -> None:
    source = """# module "fake" { source = "remote/fake" }
locals {
 text = <<EOT
module "fake" { source = "remote/fake" }
EOT
}
module "local" { source = "./local" }
module "registry" {
 source = "terraform-aws-modules/vpc/aws"
}
module "git" {
 source = "git::https://user:canary-key@example.com/module.git"
}
module "http" { source = "https://example.com/module.zip" }
"""
    findings = external_module_findings({"terraform/main.tf": source})
    assert [(f.resource, f.line_start) for f in findings] == [
        ("module.registry", 9),
        ("module.git", 12),
        ("module.http", 14),
    ]
    for variant in Variant:
        classified = classify(findings, variant)
        assert all(
            not f.blocking and f.advisory_reason == "external_module_not_scanned"
            for f in classified
        )
        assert "canary-key" not in json.dumps(
            [f.model_dump(mode="json") for f in classified]
        )


@pytest.mark.scanners
@pytest.mark.req("FR-S-01", "NFR-01")
@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="local scanners are not installed")
async def test_remote_module_failure_keeps_local_findings(tmp_path: Path) -> None:
    from app.scanners.scan import Scanner

    package = files("remote_module")
    result = await Scanner(ProcessToolRunner(30)).scan(package, Variant.SECURITY)
    assert any(v.rule_id == "AWS-0080" and v.blocking for v in result.violations)
    external = next(
        v for v in result.violations if v.rule_id == "EXTERNAL_MODULE_NOT_SCANNED"
    )
    assert (external.file_path, external.line_start, external.resource) == (
        "terraform/modules.tf",
        2,
        "module.remote",
    )
    assert not external.blocking
    assert all(v.rule_id != "TERRAFORM_SYNTAX" for v in result.violations)


@pytest.mark.req("FR-S-01")
def test_invalid_module_strings_do_not_break_syntax_remediation() -> None:
    assert (
        external_module_findings(
            {"terraform/main.tf": r'module "bad" { source = "git::\q" }'}
        )
        == []
    )


@pytest.mark.req("FR-S-01")
def test_recorded_helm_and_remote_module_coverage() -> None:
    for state in ("helm", "remote_module"):
        raw = recorded_output("trivy", state)
        findings = parse_trivy(raw, FIXTURES / state, set(files(state)))
        assert any(
            f.rule_id == ("KSV-0017" if state == "helm" else "AWS-0080")
            for f in findings
        )
    assert (
        external_module_findings(files("remote_module"))[0].resource == "module.remote"
    )
