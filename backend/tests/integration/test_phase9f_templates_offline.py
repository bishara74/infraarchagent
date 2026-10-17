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
