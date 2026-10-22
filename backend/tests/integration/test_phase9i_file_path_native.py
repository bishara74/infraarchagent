"""FR-V-03: native provider validation verifies module-relative artifact reads."""

import shutil

import pytest

from app.agents.security.verification import TerraformVerifier, failure_count
from app.validation.file_paths import repair_file_paths
from app.validation.tools import DEFAULT_MIRROR
from tests.unit.test_phase9i_v6_equivalents import provider


@pytest.mark.req("FR-V-03", "NFR-01")
@pytest.mark.scanners
async def test_real_file_path_rebase_reads_same_package_artifact():
    archive = (
        DEFAULT_MIRROR
        / "registry.terraform.io/hashicorp/aws"
        / "terraform-provider-aws_6.68.0_linux_amd64.zip"
    )
    if not shutil.which("terraform") or not archive.is_file():
        pytest.skip("installed Terraform and mirrored AWS 6.68.0 required")
    files = {
        **provider(),
        "terraform/main.tf": """resource "aws_instance" "one" {
  ami = "ami-0123456789abcdef0"
  instance_type = "t3.micro"
  user_data = file("nginx/nginx.conf")
}
""",
        "nginx/nginx.conf": "events {}\n",
    }
    verifier = TerraformVerifier()
    before = await verifier.checks(files)
    assert failure_count(before) == 1
    after, records = repair_file_paths(files)
    assert len(records) == 1
    assert after["nginx/nginx.conf"] == files["nginx/nginx.conf"]
    checked = await verifier.checks(after)
    assert failure_count(checked) == 0
    assert any(c.status == "passed" for c in checked)
    assert repair_file_paths(after) == (after, [])
