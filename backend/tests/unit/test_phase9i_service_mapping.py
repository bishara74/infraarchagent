"""FR-G-02/FR-V-03: advertised and observed services have indexed guidance."""

import json
from pathlib import Path

import pytest

from app.domain.plan import ARCHITECT_AWS_SERVICES, DeploymentPlan
from app.security.generation import (
    HTTP_API_TYPES,
    REST_API_TYPES,
    generation_context,
    hosting_resource_types,
    plan_resource_types,
    service_resource_types,
)
from app.validation.provider_schema import PINS, ProviderSchemaIndex
from tests.unit.test_secure_generation import plan

pytestmark = pytest.mark.req("FR-G-02", "FR-V-03", "NFR-01")
ROOT = Path(__file__).resolve().parents[3]


def test_architect_vocabulary_has_resources_in_both_pinned_indexes():
    schema = DeploymentPlan.model_json_schema()
    indexes = [ProviderSchemaIndex("aws", v) for v in PINS["aws"]]
    assert all(i.available for i in indexes), "Both pinned AWS indexes are required"
    missing = []
    for model in ("Service", "Storage"):
        labels = schema["$defs"][model]["properties"]["aws_service"]["examples"]
        assert set(labels) == set(ARCHITECT_AWS_SERVICES)
        for label in labels:
            # Plain monitoring is self-hosted; test its documented EKS context.
            types = service_resource_types(label, hosting_types={"aws_eks_cluster"})
            if not types or not any(
                all(i.resource_schema(t) for i in indexes) for t in types
            ):
                missing.append(f"{model}.{label}")
            for resource_type in types:
                if not all(i.resource_schema(resource_type) for i in indexes):
                    missing.append(f"{model}.{label}: {resource_type}")
    assert not missing, f"Unmapped/non-indexed Architect services: {sorted(missing)}"


def test_every_saved_broad_and_final_plan_service_is_covered():
    baseline = json.loads(
        (ROOT / "docs/evals/phase9i-service-mapping-offline/baseline.json").read_text()
    )
    indexes = [ProviderSchemaIndex("aws", v) for v in PINS["aws"]]
    missing = []
    assert len(baseline["plans"]) == 48
    extra = json.loads(
        (
            ROOT / "docs/evals/phase9i-v6-migrations-offline/service-labels.json"
        ).read_text()
    )
    assert len(extra["plans"]) == 20
    baseline["plans"].extend(extra["plans"])
    for item in baseline["plans"]:
        labels = item["selection"]["services"]
        value = plan(*labels)
        data = value.model_dump(mode="json")
        data["storage"] = [
            {"name": f"storage-{i}", **storage, "attached_to": []}
            for i, storage in enumerate(item["selection"]["storage"])
        ]
        value = DeploymentPlan.model_validate(data)
        hosting = hosting_resource_types(value)
        for label in labels + [s["aws_service"] for s in item["selection"]["storage"]]:
            types = service_resource_types(label, hosting_types=hosting)
            if not types or not all(
                all(i.resource_schema(t) for i in indexes) for t in types
            ):
                missing.append(f"{item['cohort']}/{item['run_id']}: {label}")
        context = generation_context(value)
        assert 0 < context.schema_chars <= 4500
        assert context.checklist_chars <= 1500 and len(context.text) <= 6000
    assert not missing, f"Unmapped/non-indexed saved-plan services: {sorted(missing)}"


@pytest.mark.parametrize(
    "label,expected",
    [
        (
            "AWS Lambda",
            {"aws_lambda_function", "aws_lambda_permission", "aws_iam_role"},
        ),
        ("API Gateway", REST_API_TYPES | HTTP_API_TYPES),
        ("Amazon API Gateway REST API", REST_API_TYPES),
        ("Amazon API Gateway HTTP API", HTTP_API_TYPES),
        ("apigatewayv2", HTTP_API_TYPES),
        ("DynamoDB", {"aws_dynamodb_table"}),
        ("subnet", {"aws_subnet", "aws_route_table_association"}),
        (
            "ssm",
            {"aws_ssm_association", "aws_ssm_document", "aws_iam_instance_profile"},
        ),
        ("elasticloadbalancingv2", {"aws_lb", "aws_lb_listener"}),
        ("Amazon Route 53", {"aws_route53_zone", "aws_route53_record"}),
        ("Amazon RDS Aurora", {"aws_rds_cluster", "aws_rds_cluster_instance"}),
    ],
)
def test_service_aliases_select_core_types(label, expected):
    assert service_resource_types(label) == expected


@pytest.mark.parametrize("host", ["EC2", "EKS", "ECS Fargate"])
def test_monitoring_inherits_hosting_without_inventing_managed_workspaces(host):
    value = plan(host, "Prometheus", "Grafana")
    hosting = hosting_resource_types(value)
    for label in ("prometheus", "grafana"):
        assert service_resource_types(label, hosting_types=hosting) == hosting
        assert not service_resource_types(label)
    assert "aws_prometheus_workspace" not in plan_resource_types(value)
    assert "aws_grafana_workspace" not in plan_resource_types(value)
    assert service_resource_types("Amazon Managed Service for Prometheus") == {
        "aws_prometheus_workspace"
    }
    assert service_resource_types("Amazon Managed Grafana") == {
        "aws_grafana_workspace",
        "aws_iam_role",
    }


def test_storage_service_precedes_generic_kind_and_unknown_labels_do_not_match():
    value = plan("lambda")
    data = value.model_dump(mode="json")
    data["storage"] = [
        {
            "name": "warehouse",
            "kind": "relational_db",
            "aws_service": "Redshift",
            "attached_to": [],
        },
        {
            "name": "cache",
            "kind": "cache",
            "aws_service": "elasticache",
            "attached_to": [],
        },
        {
            "name": "records",
            "kind": "nosql_db",
            "aws_service": "dynamodb",
            "attached_to": [],
        },
    ]
    types = plan_resource_types(DeploymentPlan.model_validate(data))
    assert {
        "aws_redshift_cluster",
        "aws_elasticache_replication_group",
        "aws_dynamodb_table",
    } <= types
    assert "aws_db_instance" not in types
    assert not service_resource_types("notlambda other-service")
    assert "CANARY" not in generation_context(plan("Lambda CANARY")).text
    # Free-form compatibility is retained outside the advertised vocabulary.
    assert plan("future-service").services[0].aws_service == "future-service"


def test_coverage_fails_with_unmapped_service_list(monkeypatch):
    from app.security.generation import SERVICE_TYPES

    monkeypatch.setitem(SERVICE_TYPES, "lambda", set())
    with pytest.raises(
        AssertionError,
        match=r"Unmapped/non-indexed Architect services:.*Service.lambda",
    ):
        test_architect_vocabulary_has_resources_in_both_pinned_indexes()


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("object_storage", "aws_s3_bucket"),
        ("relational_db", "aws_db_instance"),
        ("nosql_db", "aws_dynamodb_table"),
        ("block_volume", "aws_ebs_volume"),
        ("cache", "aws_elasticache_replication_group"),
    ],
)
def test_generic_storage_kind_fallback(kind, expected):
    data = plan("future-service").model_dump(mode="json")
    data["storage"] = [
        {
            "name": "storage",
            "kind": kind,
            "aws_service": "unspecified",
            "attached_to": [],
        }
    ]
    assert expected in plan_resource_types(DeploymentPlan.model_validate(data))
