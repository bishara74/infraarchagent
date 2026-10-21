"""FR-V-03: native offline validation verifies the documented v6 migrations."""

import shutil

import pytest

from app.agents.security.verification import TerraformVerifier, failure_count
from app.validation.tools import DEFAULT_MIRROR
from app.validation.v6_equivalents import repair_v6_equivalents
from tests.unit.test_phase9i_v6_equivalents import provider


@pytest.mark.req("FR-V-03", "NFR-01")
@pytest.mark.scanners
async def test_real_v6_equivalents_remove_three_native_errors():
    archive = (
        DEFAULT_MIRROR
        / "registry.terraform.io/hashicorp/aws"
        / "terraform-provider-aws_6.68.0_linux_amd64.zip"
    )
    if not shutil.which("terraform") or not archive.is_file():
        pytest.skip("installed Terraform and mirrored AWS 6.68.0 required")
    files = {
        **provider(),
        "terraform/main.tf": """resource "aws_eip" "nat" {
  vpc = true
}
resource "aws_ssm_association" "one" {
  name = "AWS-RunShellScript"
  instance_id = "i-0123456789abcdef0"
  parameters = { commands = "echo test" }
}
resource "aws_cloudwatch_log_group" "flow" {
  name = "offline-test"
}
resource "aws_flow_log" "flow" {
  log_group_name = aws_cloudwatch_log_group.flow.name
  iam_role_arn = "arn:aws:iam::123456789012:role/flow"
  vpc_id = "vpc-0123456789abcdef0"
  traffic_type = "ALL"
}
""",
    }
    verifier = TerraformVerifier()
    before = await verifier.checks(files)
    assert failure_count(before) == 3
    candidate, records = repair_v6_equivalents(files)
    assert len(records) == 3
    assert repair_v6_equivalents(candidate) == (candidate, [])
    after = await verifier.checks(candidate)
    assert failure_count(after) == 0
    assert any(c.status == "passed" for c in after)
