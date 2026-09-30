import pytest

from app.domain.directive_checks import check_directive
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan


def plan(*, rds: bool = False, s3: bool = False) -> DeploymentPlan:
    storage = []
    if rds:
        storage.append(
            {
                "name": "db",
                "kind": "relational_db",
                "aws_service": "rds",
                "attached_to": ["web"],
            }
        )
    if s3:
        storage.append(
            {
                "name": "assets",
                "kind": "object_storage",
                "aws_service": "s3",
                "attached_to": ["web"],
            }
        )
    return DeploymentPlan.model_validate(
        {
            "cloud_provider": "aws",
            "services": [{"name": "web", "aws_service": "ECS", "purpose": "Serve"}],
            "dependencies": [],
            "network": {
                "public_services": ["web"],
                "private_services": [],
                "ingress": [],
                "notes": "VPC",
            },
            "storage": storage,
            "file_types": ["terraform", "kubernetes"],
            "ambiguities": [],
        }
    )


def report(
    variant: Variant, terraform: str, deployment: DeploymentPlan
) -> dict[str, bool]:
    checks = check_directive(variant, {"terraform/main.tf": terraform}, deployment)
    assert all(check.detail for check in checks)
    return {check.name: check.passed for check in checks}


@pytest.mark.req("FR-G-03")
def test_cost_pass_and_fail_each_heuristic() -> None:
    good = report(
        Variant.COST,
        'instance_type = "t3.micro"\ninstance_class = "db.t4g.small"',
        plan(),
    )
    assert all(good.values())
    bad = report(Variant.COST, 'instance_type = "m5.large"\nmulti_az = true', plan())
    assert bad == {"small instance classes": False, "single-AZ preference": False}


@pytest.mark.req("FR-G-04")
def test_performance_conditional_multi_az_and_autoscaling() -> None:
    good = report(
        Variant.PERFORMANCE,
        'multi_az = true\nresource "aws_autoscaling_group" "web" {}',
        plan(rds=True),
    )
    assert all(good.values())
    bad = report(Variant.PERFORMANCE, "resource {}", plan(rds=True))
    assert bad == {"relational DB multi-AZ": False, "autoscaling construct": False}
    assert "relational DB multi-AZ" not in report(Variant.PERFORMANCE, "", plan())
    hpa = check_directive(
        Variant.PERFORMANCE,
        {
            "terraform/main.tf": "",
            "k8s/autoscale.yaml": "kind: HorizontalPodAutoscaler",
        },
        plan(),
    )
    assert hpa[0].passed


@pytest.mark.req("FR-G-05")
def test_security_conditional_encryption_and_public_access_checks() -> None:
    good = report(
        Variant.SECURITY,
        "\n".join(
            (
                "storage_encrypted = true",
                'resource "aws_s3_bucket_server_side_encryption_configuration" "x" {}',
                'resource "aws_s3_bucket_public_access_block" "x" {}',
                'ingress { from_port = 443 to_port = 443 cidr_blocks = ["0.0.0.0/0"] }',
                'actions = ["s3:GetObject"]',
            )
        ),
        plan(rds=True, s3=True),
    )
    assert all(good.values())
    bad = report(
        Variant.SECURITY,
        'ingress { from_port = 80 to_port = 80 cidr_blocks = ["0.0.0.0/0"] }\n'
        'actions = ["*"]',
        plan(rds=True, s3=True),
    )
    assert len(bad) == 5
    assert not any(bad.values())
    plain = report(Variant.SECURITY, "", plan())
    assert "RDS storage encryption" not in plain
    assert "S3 encryption" not in plain


@pytest.mark.req("FR-G-05")
def test_iam_json_wildcard_is_reported() -> None:
    checks = report(Variant.SECURITY, '{"Action":"*"}', plan())
    assert not checks["IAM wildcard actions"]
    checks = report(Variant.SECURITY, 'Action = "*"', plan())
    assert not checks["IAM wildcard actions"]


@pytest.mark.req("FR-G-05")
def test_standalone_ingress_rule_is_reported() -> None:
    checks = report(
        Variant.SECURITY,
        'resource "aws_security_group_rule" "http" { '
        'type = "ingress" from_port = 80 to_port = 80 '
        'cidr_blocks = ["0.0.0.0/0"] }',
        plan(),
    )
    assert not checks["public ingress port"]
