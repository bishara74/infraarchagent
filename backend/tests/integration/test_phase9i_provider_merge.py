"""FR-V-03: real offline Terraform validates a compatible provider consolidation."""

import shutil

import pytest

from app.agents.security.verification import TerraformVerifier, failure_count
from app.validation.provider_repairs import repair_required_providers
from app.validation.tools import DEFAULT_MIRROR


@pytest.mark.req("FR-V-03", "NFR-01")
@pytest.mark.scanners
async def test_real_provider_merge_removes_duplicate_configuration():
    archive = (
        DEFAULT_MIRROR
        / "registry.terraform.io/hashicorp/random"
        / "terraform-provider-random_3.9.1_linux_amd64.zip"
    )
    if not shutil.which("terraform") or not archive.is_file():
        pytest.skip("installed Terraform and mirrored random 3.9.1 required")
    files = {
        "terraform/a.tf": """terraform {
  required_providers {
    random = { source = "hashicorp/random", version = ">= 3.9, < 4" }
  }
}
resource "random_integer" "sample" {
  min = 1
  max = 2
}
""",
        "terraform/b.tf": """terraform {
  required_providers {
    random = { source = "hashicorp/random", version = "3.9.1" }
  }
}
""",
    }
    verifier = TerraformVerifier()
    before = await verifier.checks(files)
    assert failure_count(before) == 1
    assert any(
        c.message == "Duplicate required providers configuration" for c in before
    )
    candidate, records = repair_required_providers(files)
    assert records and repair_required_providers(candidate) == (candidate, [])
    after = await verifier.checks(candidate)
    assert failure_count(after) == 0
    assert any(
        c.check_id == "terraform.validate" and c.status == "passed" for c in after
    )
