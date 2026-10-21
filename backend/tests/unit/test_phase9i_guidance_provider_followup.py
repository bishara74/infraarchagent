"""FR-G-02/FR-V-03: required-first guidance and schema-only measurements."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.core.logging import RedactingFilter
from app.domain.enums import Variant
from app.domain.validation import RemediationReport
from app.pipeline.orchestrator import PipelineOrchestrator
from app.security.generation import generation_context
from app.validation.schema_context import generator_schema_guidance
from scripts.benchmark import normalized_event
from scripts.phase9d_quality import compact_snapshot, quality_snapshot, quality_table
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
