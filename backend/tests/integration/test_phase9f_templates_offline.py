"""FR-V-03: all supporting templates validate against real offline providers."""

import shutil

import pytest

from app.agents.security.verification import TerraformVerifier
from app.security.templates import build_template
from app.validation.tools import DEFAULT_MIRROR
from app.validation.workspace import ValidationWorkspace
from tests.unit.test_security_templates import template_input


@pytest.mark.req("FR-S-02", "FR-V-03", "NFR-01")
@pytest.mark.scanners
@pytest.mark.parametrize("version", ["5.100.0", "6.68.0"])
async def test_all_support_templates_with_offline_provider(version):
    archive = (
        DEFAULT_MIRROR
        / "registry.terraform.io/hashicorp/aws"
        / f"terraform-provider-aws_{version}_linux_amd64.zip"
    )
    if not shutil.which("terraform") or not archive.is_file():
        pytest.skip("installed Terraform and mirrored pinned AWS provider required")
    workspace = ValidationWorkspace()
    try:
        with workspace.activate():
            for kind in ("kms", "access_logs", "flow_logs", "monitoring"):
                files, findings = template_input(version, kind)
                candidate, record = build_template(files, findings, "terraform", kind)
                assert record["status"] == "proposed", record
                checks = await TerraformVerifier().checks(candidate)
                assert not [c for c in checks if c.status in {"failed", "skipped"}], (
                    kind
                )
    finally:
        workspace.close()


@pytest.mark.req("FR-S-02", "FR-S-03", "NFR-01")
@pytest.mark.scanners
@pytest.mark.parametrize("version", ["5.100.0", "6.68.0"])
@pytest.mark.parametrize("kind", ["kms", "access_logs", "flow_logs", "monitoring"])
async def test_support_templates_real_scanners(version, kind):
    from app.domain.enums import Variant
    from app.scanners.runner import ProcessToolRunner
    from app.scanners.scan import Scanner

    if not all(shutil.which(name) for name in ("terraform", "checkov", "trivy")):
        pytest.skip("installed offline scanners required")
    files, findings = template_input(version, kind)
    candidate, record = build_template(files, findings, "terraform", kind)
    assert record["status"] == "proposed"
    scanner = Scanner(ProcessToolRunner())
    before = await scanner.scan(files, Variant.SECURITY)
    after = await scanner.scan(candidate, Variant.SECURITY)
    baseline = {v.fingerprint() for v in before.violations if v.blocking}
    introduced = [
        v for v in after.violations if v.blocking and v.fingerprint() not in baseline
    ]
    # These are visible strict blockers on an SSE-S3 log destination, never
    # acceptance exemptions; section 4 supplies only a separate assessment.
    documented_log_destination_blockers = {
        "CKV_AWS_145",
        "AWS-0132",
        "CKV_AWS_18",
        "AWS-0089",
        "CKV_AWS_144",
    }
    unexpected = [
        v
        for v in introduced
        if not (
            kind == "access_logs" and v.rule_id in documented_log_destination_blockers
        )
    ]
    assert not unexpected, [(v.rule_id, v.resource) for v in unexpected]
    if kind in {"kms", "access_logs"}:
        assert not [v for v in introduced if v.rule_id == "AWS-0090"]
    if kind == "kms":
        assert not [v for v in introduced if v.rule_id == "AWS-0132"]
