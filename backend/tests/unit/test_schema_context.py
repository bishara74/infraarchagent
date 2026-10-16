"""FR-S-03/09, FR-V-03: scanner and repair prompts share bounded schemas."""

import hashlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.agents.security.fix import FixAgent
from app.domain.plan import DeploymentPlan
from app.pipeline.demo_stub import DEMO_PLAN
from app.validation.schema_context import generator_schema_context, schema_context
from app.validation.workspace import ValidationWorkspace

pytestmark = pytest.mark.req("FR-S-03", "FR-S-09", "FR-V-03", "NFR-01")


@pytest.fixture
def schemas(tmp_path):
    providers = {}
    for version, required_type in [("5.100.0", "string"), ("6.68.0", "number")]:
        block = {
            "attributes": {
                "name": {"type": required_type, "required": True},
                "id": {"type": "string", "computed": True},
                "label": {"type": "string", "optional": True},
            },
            "block_types": {
                "rule": {
                    "nesting_mode": "list",
                    "min_items": 1,
                    "max_items": 2,
                    "block": {
                        "attributes": {"port": {"type": "number", "required": True}},
                        "block_types": {},
                    },
                }
            },
        }
        raw = json.dumps(
            {
                "resource_schemas": {"aws_widget": block, "aws_vpc": block},
                "data_source_schemas": {
                    "aws_identity": {
                        "attributes": {"id": {"computed": True, "type": "string"}},
                        "block_types": {},
                    }
                },
            }
        ).encode()
        (tmp_path / f"aws-{version}.json").write_bytes(raw)
        providers[f"aws/{version}"] = {"index_sha256": hashlib.sha256(raw).hexdigest()}
    (tmp_path / "manifest.json").write_text(
        json.dumps({"format_version": 1, "providers": providers})
    )
    return tmp_path


def files():
    return {
        "terraform/main.tf": """resource "aws_widget" "main" {
 label = "VALUE_MUST_NOT_APPEAR"
 rule {
  prto = 42
 }
}
locals { example = "VALUE_MUST_NOT_APPEAR" }
""",
        "terraform/providers.tf": """terraform {
 required_providers {
  aws = { source = "hashicorp/aws", version = "~> 5.100" }
 }
}
""",
    }


def test_context_version_nested_required_names_and_no_values(schemas):
    failures = [
        {
            "file_path": "terraform/main.tf",
            "line_start": 4,
            "message": "Unsupported argument",
        }
    ]
    context = schema_context(
        "terraform/main.tf", files(), failures=failures, directory=schemas
    )
    entry = next(e for e in json.loads(context) if e.get("type") == "aws_widget")
    assert entry["version"] == "5.100.0"
    assert entry["schema"]["required"] == {"name": "string"}
    assert entry["diagnostic_context"]["block_path"] == ["rule"]
    assert entry["diagnostic_context"]["schema"]["required"] == {"port": "number"}
    assert entry["diagnostic_context"]["nearest_arguments"] == ["port"]
    assert "VALUE_MUST_NOT_APPEAR" not in context
    assert '"kind":"local"' in context
    for cap in (1, 64, 512, 16000):
        bounded = schema_context(
            "terraform/main.tf", files(), directory=schemas, limit=cap
        )
        assert len(bounded) <= cap
        if bounded:
            json.loads(bounded)


def test_resolved_version_wins_and_wrong_namespace_not_grounded(schemas):
    workspace = ValidationWorkspace()
    try:
        workspace.resolved["terraform"] = {"aws": "6.68.0"}
        with workspace.activate():
            context = schema_context("terraform/main.tf", files(), directory=schemas)
        entry = json.loads(context)[0]
        assert entry["version"] == "6.68.0"
        assert entry["schema"]["required"]["name"] == "number"
        other = files()
        other["terraform/providers.tf"] = other["terraform/providers.tf"].replace(
            "hashicorp/aws", "other/aws"
        )
        assert not any(
            "schema" in e
            for e in json.loads(
                schema_context("terraform/main.tf", other, directory=schemas)
            )
        )
    finally:
        workspace.close()


def test_nearest_types_and_generator_cap(schemas):
    source = {"terraform/main.tf": 'resource "aws_widgit" "main" {}\n'}
    context = json.loads(schema_context("terraform/main.tf", source, directory=schemas))
    assert "aws_widget" in context[0]["nearest_types"]
    context = generator_schema_context(directory=schemas)
    assert len(context) <= 6000
    assert {v for e in json.loads(context) for v in e["versions"]} == {
        "5.100.0",
        "6.68.0",
    }


async def test_scanner_only_fix_receives_schema_and_size(schemas, monkeypatch):
    from app.agents.security import fix

    original = fix.schema_context
    monkeypatch.setattr(
        fix, "schema_context", lambda *a, **kw: original(*a, **kw, directory=schemas)
    )
    source = files()
    adapter = SimpleNamespace(
        complete_json=AsyncMock(
            return_value=SimpleNamespace(
                data={
                    "file": {
                        "path": "terraform/main.tf",
                        "content": source["terraform/main.tf"],
                    },
                    "new_files": {},
                },
                response=SimpleNamespace(
                    input_tokens=1, output_tokens=1, cached_input_tokens=None
                ),
            )
        )
    )
    value = dict(DEMO_PLAN)
    value["file_types"] = ["terraform"]
    proposal = await FixAgent(adapter, schema_context_max_chars=1500).propose(
        path="terraform/main.tf",
        files=source,
        findings=[],
        plan=DeploymentPlan.model_validate(value),
        directive="security",
        remaining=30,
    )
    prompt = adapter.complete_json.call_args.args[0]
    assert "<provider_schema" in prompt and "5.100.0" in prompt
    assert 0 < proposal.schema_context_chars <= 1500
