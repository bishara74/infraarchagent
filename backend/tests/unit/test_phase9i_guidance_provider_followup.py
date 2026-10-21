"""FR-G-02/FR-V-03: required-first guidance and guarded provider consolidation."""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.agents.budget import AgentBudget
from app.agents.deterministic import checked_one
from app.core.logging import RedactingFilter
from app.domain.enums import Variant
from app.domain.validation import RemediationReport
from app.pipeline.orchestrator import PipelineOrchestrator
from app.security.generation import generation_context
from app.validation.documents import PackageDocuments
from app.validation.provider_repairs import (
    intersect_constraints,
    repair_required_providers,
)
from app.validation.schema_context import generator_schema_guidance
from scripts.benchmark import normalized_event
from scripts.phase9d_quality import compact_snapshot, quality_snapshot, quality_table
from tests.unit.test_phase9i_deterministic import Engine, Scanner, Verifier, report
from tests.unit.test_secure_generation import plan

pytestmark = pytest.mark.req("FR-G-02", "FR-V-03", "FR-V-04", "NFR-01")


def schema(*, required="id", optional="extra", children=None):
    return {
        "attributes": {
            required: {"type": "string", "required": True},
            optional: {"type": "string", "optional": True},
        },
        "block_types": children or {},
    }


def block(child, mandatory=True):
    return {"nesting_mode": "list", "min_items": int(mandatory), "block": child}


def fake_index(monkeypatch, schemas):
    monkeypatch.setattr(
        "app.validation.schema_context.index_for",
        lambda *args: SimpleNamespace(resource_schema=schemas.get),
    )


def test_required_cores_for_every_type_precede_optional_content(monkeypatch):
    child = schema(children={"level4": block(schema())})
    nested = schema(
        children={"level2": block(schema(children={"level3": block(child)}))}
    )
    fake_index(monkeypatch, {"aws_a": nested, "aws_b": schema()})
    result = generator_schema_guidance(650, resource_types=("aws_a", "aws_b"))
    entries = {e["type"]: e for e in json.loads(result.text)}
    assert len(result.text) <= 650 and not result.omitted_required
    assert entries["aws_b"]["schema"]["required"] == {"id": "string"}
    current = entries["aws_a"]["schema"]
    for name in ("level2", "level3", "level4"):
        current = current["blocks"][name]
        assert current["required"] == {"id": "string"}
    # Empty optional sections carry no omitted content and need no JSON header.
    fake_index(
        monkeypatch,
        {"aws_a": {"attributes": {"id": {"required": True, "type": "string"}}}},
    )
    complete = generator_schema_guidance(400, resource_types=("aws_a",))
    assert json.loads(complete.text)[0]["truncated"] is False


def test_conditional_cores_are_atomic_and_never_displace_unconditional(monkeypatch):
    fake_index(
        monkeypatch,
        {
            "aws_a": schema(
                children={"optional_parent": block(schema(required="x" * 1000), False)}
            ),
            "aws_b": schema(
                children={
                    "optional_parent": block(
                        schema(children={"cookies": block(schema(required="forward"))}),
                        False,
                    )
                }
            ),
        },
    )
    result = generator_schema_guidance(600, resource_types=("aws_a", "aws_b"))
    entries = {e["type"]: e for e in json.loads(result.text)}
    assert not result.omitted_required and result.omitted_conditional == ("aws_a",)
    assert entries["aws_a"]["schema"]["blocks"] == {}
    parent = entries["aws_b"]["schema"]["blocks"]["optional_parent"]
    assert parent["if_used"] is True and "min" not in parent
    assert parent["blocks"]["cookies"]["required"] == {"forward": "string"}


def test_version_specific_required_fields_are_not_dropped(monkeypatch):
    monkeypatch.setattr(
        "app.validation.schema_context.index_for",
        lambda provider, version, directory: SimpleNamespace(
            resource_schema=lambda name: schema(
                required="old" if version.startswith("5") else "new"
            )
        ),
    )
    result = generator_schema_guidance(400, resource_types=("aws_a",))
    entry = json.loads(result.text)[0]
    assert entry["version_schema"]["5.100.0"]["required"] == {"old": "string"}
    assert entry["version_schema"]["6.68.0"]["required"] == {"new": "string"}


async def test_oversized_plan_continues_and_exports_same_overflow_signal(monkeypatch):
    value = plan("ECS", "EC2", "RDS", "EKS", "ALB", "CloudWatch", "CloudFront", "S3")
    fake_index(
        monkeypatch,
        {
            name: schema(required="required_" + "x" * 700)
            for name in (
                "aws_ecs_service",
                "aws_ecs_task_definition",
                "aws_instance",
                "aws_db_instance",
                "aws_eks_cluster",
                "aws_lb",
                "aws_lb_listener",
                "aws_cloudwatch_log_group",
                "aws_cloudfront_distribution",
                "aws_cloudfront_origin_access_control",
                "aws_s3_bucket",
                "aws_vpc",
                "aws_subnet",
                "aws_security_group",
                "aws_route_table",
                "aws_route_table_association",
                "aws_internet_gateway",
            )
        },
    )
    context = generation_context(value)
    assert context.schema_chars <= 4500 and len(context.text) <= 6000
    assert context.omitted_required
    included = [
        entry["type"] for entry in json.loads(context.text[: context.schema_chars])
    ]
    assert included[:2] == ["aws_ecs_service", "aws_ecs_task_definition"]
    assert all(
        len(entry["schema"]["required"]) == 1
        for entry in json.loads(context.text[: context.schema_chars])
    )
    metadata = RemediationReport(
        generator_schema_context_chars=9999, **context.metrics()
    ).model_dump(mode="json")
    package = {"validation_report": {"remediation": metadata}}
    snapshot = quality_snapshot(package, RedactingFilter())
    assert (
        compact_snapshot(snapshot, RedactingFilter())["phase9e"] == snapshot["phase9e"]
    )
    assert snapshot["phase9e"]["generator_schema_context_chars"] == 9999
    assert (
        snapshot["phase9e"]["generator_schema_only_context_chars"]
        == context.schema_chars
    )
    metrics, table = quality_table([snapshot], missing=0)
    assert metrics["generator_schema_overflow"]["overflow_packages"] == 1
    assert context.omitted_required[0] in table
    orchestrator = PipelineOrchestrator.__new__(PipelineOrchestrator)
    orchestrator.clock = lambda: 0
    orchestrator.run_id = uuid4()
    orchestrator.writer = SimpleNamespace(agent_state=AsyncMock())
    orchestrator._generation_failed = AsyncMock()
    generator = SimpleNamespace(
        variant=Variant.COST,
        generate=AsyncMock(
            side_effect=RuntimeError("stub stops after guidance publication")
        ),
    )
    assert await orchestrator._generate_inside(generator, value) == (Variant.COST, None)
    generator.generate.assert_awaited_once()
    assert (
        orchestrator.writer.agent_state.call_args.kwargs["metrics"] == context.metrics()
    )
    event = normalized_event(
        {
            "seq": 1,
            "kind": "agent_state",
            "agent": "generator_cost",
            "variant": "cost",
            "status": "running",
            "timestamp": "2026-10-21T12:00:00+00:00",
            "payload": {"metrics": {**context.metrics(), "untrusted": "CANARY"}},
        }
    )
    assert event["metrics"] == {
        k: v for k, v in context.metrics().items() if k != "generator_context_truncated"
    }
    assert "CANARY" not in json.dumps(event)


@pytest.mark.parametrize(
    "constraints,expected",
    [
        ([">= 5, < 7", "~> 6.2"], True),
        (["> 9, != 9.0.1", "< 10"], True),
        (["~> 5.1.0", ">= 5.2"], False),
        ([">= 6, <= 6", "!= 6"], False),
        (["> 6", "<= 6"], False),
        (["= 5.1", "5.1.0"], True),
        (["< 0"], False),
        ([""], True),
        (["1.0.0-beta"], False),
        (["~> 5", ">= 6"], False),
        (["> 5.0.0, < 5.0.2, != 5.0.1"], False),
    ],
)
def test_constraint_intersection_uses_bounds_not_mirror(constraints, expected):
    assert (intersect_constraints(constraints) is not None) is expected


def declarations(a=">= 5", b="< 7", source="hashicorp/aws"):
    return {
        "terraform/a.tf": 'terraform {\n required_version = ">= 1.0"\n'
        ' required_providers {\n aws = { source = "hashicorp/aws", version = "'
        + a
        + '" }\n }\n}\n# retain me\n',
        "terraform/b.tf": 'terraform {\n required_providers {\n aws = { source = "'
        + source
        + '", version = "'
        + b
        + '" }\n random = { source = "hashicorp/random", version = "3.9.1" }\n }\n}\n',
    }


@pytest.mark.parametrize("style", ["hcl", "json", "mixed"])
def test_merge_union_source_preservation_module_isolation_and_idempotence(style):
    files = declarations()
    if style != "hcl":
        files["terraform/b.tf.json"] = json.dumps(
            {
                "terraform": {
                    "required_version": ">= 1",
                    "required_providers": {
                        "aws": {"source": "hashicorp/aws", "version": "< 7"},
                        "random": {"source": "hashicorp/random", "version": "3.9.1"},
                    },
                },
                "output": {"x": {"value": "KEEP"}},
            }
        )
        del files["terraform/b.tf"]
    if style == "json":
        files["terraform/a.tf.json"] = (
            '{"terraform":{"required_providers":{"aws":'
            '{"source":"hashicorp/aws","version":">= 5"}},'
            '"required_version":">= 1"}}'
        )
        del files["terraform/a.tf"]
    files["terraform/child/main.tf"] = (
        'terraform { required_providers { aws = { source = "other/aws" } } }'
    )
    original = deepcopy(files)
    result, records = repair_required_providers(files)
    assert files == original and len(records) == 1
    assert result["terraform/child/main.tf"] == original["terraform/child/main.tf"]
    assert not any(
        doc.parse_error for doc in PackageDocuments.parse(result).documents.values()
    )
    assert repair_required_providers(result) == (result, [])
    assert ">= 5, < 7" in "".join(result.values())
    assert records[0]["before_hash"] != records[0]["after_hash"]
    if style != "json":
        assert "# retain me" in result["terraform/a.tf"]
        assert 'required_version = ">= 1.0"' in result["terraform/a.tf"]
    if style != "hcl":
        assert '"value": "KEEP"' in result["terraform/b.tf.json"]


@pytest.mark.parametrize(
    "a,b,source",
    [
        ("< 5", ">= 6", "hashicorp/aws"),
        (">= 5", "< 7", "other/aws"),
        ("1.0.0-beta", "< 7", "hashicorp/aws"),
    ],
)
def test_conflicts_leave_entire_module_for_llm(a, b, source):
    files = declarations(a, b, source)
    result, records = repair_required_providers(files)
    assert result == files and records[0]["outcome"] == "skipped"


@pytest.mark.parametrize(
    "mode,failed,accepted",
    [
        ("clean", False, True),
        ("clean", True, False),
        ("new_blocker", False, False),
        ("unavailable", False, False),
    ],
)
async def test_provider_proposal_uses_existing_validity_and_security_guards(
    mode, failed, accepted
):
    files = declarations()
    result, _, records = await checked_one(
        files,
        plan("S3"),
        Variant.COST,
        report(True),
        Engine(failed),
        SimpleNamespace(scanner=Scanner(mode), terraform_verifier=Verifier()),
        AgentBudget(30),
        repair_required_providers,
    )
    assert (result != files) is accepted
    assert records[0]["outcome"] == ("accepted" if accepted else "rejected")


def test_historical_metric_absence_remains_unknown():
    snapshot = quality_snapshot(
        {
            "validation_report": {
                "remediation": {"generator_schema_context_chars": 5503}
            }
        },
        RedactingFilter(),
    )
    assert "generator_schema_only_context_chars" not in snapshot["phase9e"]
    assert snapshot["phase9e"]["generator_schema_context_chars"] == 5503


def test_cloudfront_conditional_requirements_have_no_depth_cutoff():
    result = generator_schema_guidance(
        4500,
        resource_types=(
            "aws_cloudfront_distribution",
            "aws_cloudfront_origin_access_control",
            "aws_s3_bucket",
        ),
    )
    entry = json.loads(result.text)[0]["schema"]
    assert entry["blocks"]["origin"]["min"] == 1
    forwarded = entry["blocks"]["default_cache_behavior"]["blocks"]["forwarded_values"]
    assert forwarded["if_used"] is True
    assert forwarded["blocks"]["cookies"]["required"] == {"forward": "string"}


def test_aliases_union_and_unknown_properties_or_ambiguous_json_skip():
    files = declarations()
    files["terraform/a.tf"] = files["terraform/a.tf"].replace(
        'version = ">= 5"', 'version = ">= 5", configuration_aliases = [aws.first]'
    )
    files["terraform/b.tf"] = files["terraform/b.tf"].replace(
        'version = "< 7"',
        'version = "< 7", configuration_aliases = [aws.second, aws.first]',
    )
    result, records = repair_required_providers(files)
    assert (
        records
        and "configuration_aliases = [aws.first, aws.second]"
        in result["terraform/a.tf"]
    )
    assert repair_required_providers(result) == (result, [])
    files["terraform/b.tf"] = files["terraform/b.tf"].replace(
        'source = "hashicorp/aws"', 'source = "hashicorp/aws", unexpected = "PRESERVE"'
    )
    assert repair_required_providers(files)[0] == files
    files = declarations()
    files["terraform/c.tf.json"] = '{"terraform":{},"terraform":{}}'
    assert repair_required_providers(files)[0] == files


def test_multiple_blocks_in_one_file_and_malformed_modules_are_safe():
    original = declarations()
    files = {"terraform/main.tf": "\n".join(original.values())}
    result, records = repair_required_providers(files)
    assert len(records) == 1 and repair_required_providers(result) == (result, [])
    files["terraform/broken.tf"] = "terraform {"
    assert repair_required_providers(files) == (files, [])
