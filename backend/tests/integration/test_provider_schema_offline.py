"""FR-V-03: real provider export is offline and requires no cloud credentials."""

import shutil

import pytest

from app.validation.provider_schema import ProviderSchemaIndex
from app.validation.tools import DEFAULT_MIRROR
from scripts import provider_schema


@pytest.mark.req("FR-V-03", "NFR-01")
@pytest.mark.scanners
async def test_real_offline_provider_export(tmp_path, monkeypatch):
    archive = (
        DEFAULT_MIRROR
        / "registry.terraform.io/hashicorp/random"
        / "terraform-provider-random_3.9.1_linux_amd64.zip"
    )
    if not shutil.which("terraform") or not archive.is_file():
        pytest.skip("installed Terraform and mirrored random 3.9.1 required")
    monkeypatch.setattr(provider_schema, "PINS", {"random": ("3.9.1",)})
    assert await provider_schema.export_schemas(DEFAULT_MIRROR, tmp_path) == 0
    index = ProviderSchemaIndex("random", "3.9.1", directory=tmp_path)
    assert index.available
    assert index.resource_schema("random_password")["attributes"]["length"]["required"]
