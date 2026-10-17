"""FR-G-02/FR-S-02: resource-specific security input without larger token budgets."""

import pytest

from app.agents.prompts.generator import build_system_prompt
from app.domain.plan import DeploymentPlan
from app.pipeline.demo_stub import DEMO_PLAN
from app.security.generation import generation_context, plan_resource_types


def plan(*services):
    data = dict(DEMO_PLAN)
    data["services"] = [
        {"name": f"service-{i}", "aws_service": service, "purpose": "serve"}
        for i, service in enumerate(services)
    ]
    data["network"] = {
        "public_services": [],
        "private_services": [],
        "ingress": [],
        "notes": "",
    }
    return DeploymentPlan.model_validate(data)


@pytest.mark.req("FR-G-02", "FR-S-02", "FR-V-03")
@pytest.mark.parametrize(
    "service,expected,excluded",
    [
        ("Amazon S3", "aws_s3_bucket", "aws_db_instance"),
        ("Amazon RDS PostgreSQL", "aws_db_instance", "aws_s3_bucket"),
        ("Amazon EC2", "aws_instance", "aws_eks_cluster"),
        ("Amazon EKS", "aws_eks_cluster", "aws_instance"),
    ],
)
def test_guidance_only_for_needed_resource_types(service, expected, excluded):
    value = plan(service)
    context = generation_context(value)
    assert expected in plan_resource_types(
        value
    ) and excluded not in plan_resource_types(value)
    assert expected in context.text and excluded not in context.text
    assert "5.100.0" in context.text and "6.68.0" in context.text
    assert len(context.text) <= 6000
    assert context.text in build_system_prompt(
        "secure", plan=value, max_output_tokens=8000
    )


@pytest.mark.req("FR-G-02", "FR-S-02", "PR-05", "NFR-01")
def test_context_cap_truncation_measurement_and_supporting_guidance():
    value = plan("EC2", "RDS", "S3", "ALB", "EKS", "ECS", "CloudWatch")
    context = generation_context(value)
    assert context.schema_chars <= 4500 and context.checklist_chars <= 1500
    assert len(context.text) <= 6000
    assert context.truncated
    for guidance in (
        "SSE-S3",
        "never self-logging",
        "monitoring.rds.amazonaws.com",
        "flow logs",
        "public subnet connectivity",
    ):
        assert guidance in context.text
    assert "8000 output tokens" in build_system_prompt("secure", plan=value)
    assert "16000 output tokens" in build_system_prompt(
        "secure", plan=value, max_output_tokens=16000
    )


@pytest.mark.req("FR-G-02", "NFR-01")
def test_untrusted_plan_text_is_not_copied_into_guidance():
    value = plan("S3 MALICIOUS_CANARY")
    assert "MALICIOUS_CANARY" not in generation_context(value).text
