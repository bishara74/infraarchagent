from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.domain.plan import DeploymentPlan, FileType, plan_validation_errors


def valid_plan() -> dict[str, object]:
    return {
        "cloud_provider": "aws",
        "services": [
            {"name": "web", "aws_service": "ECS Fargate", "purpose": "Serve requests"},
            {"name": "db", "aws_service": "RDS", "purpose": "Store data"},
        ],
        "dependencies": [{"source": "web", "target": "db", "description": "SQL"}],
        "network": {
            "public_services": ["web"],
            "private_services": ["db"],
            "ingress": ["HTTPS 443 to web"],
            "notes": "VPC",
        },
        "storage": [
            {
                "name": "data",
                "kind": "relational_db",
                "aws_service": "RDS",
                "attached_to": ["db"],
            }
        ],
        "file_types": ["terraform"],
        "ambiguities": [],
    }


@pytest.mark.req("FR-A-01", "FR-A-02", "FR-A-03")
def test_valid_plan_and_frozen_model() -> None:
    plan = DeploymentPlan.model_validate(valid_plan())
    assert plan.file_types == [FileType.TERRAFORM]
    assert plan_validation_errors(valid_plan()) == []
    with pytest.raises(ValidationError):
        plan.cloud_provider = "aws"


@pytest.mark.req("FR-A-01", "FR-A-02", "FR-A-03")
@pytest.mark.parametrize(
    "change,expected",
    [
        (
            lambda p: p["dependencies"][0].update(target="missing"),
            "dependencies.0.target: unknown",
        ),
        (
            lambda p: p["dependencies"][0].update(target="web"),
            "cannot depend on itself",
        ),
        (lambda p: p["services"].append(deepcopy(p["services"][0])), "duplicate name"),
        (
            lambda p: p["network"]["public_services"].append("missing"),
            "network.public_services: unknown",
        ),
        (
            lambda p: p["network"]["private_services"].append("web"),
            "both public and private",
        ),
        (lambda p: p.update(file_types=[]), "terraform is required"),
        (lambda p: p["file_types"].append("terraform"), "duplicate value"),
        (lambda p: p.update(file_types=["terraform", "unknown"]), "file_types.1"),
        (lambda p: p.update(unexpected=True), "unexpected"),
        (lambda p: p.pop("ambiguities"), "ambiguities"),
        (lambda p: p["network"].update(notes="x" * 33000), "serialized JSON exceeds"),
        (lambda p: p["network"]["ingress"].append("x" * 201), "network.ingress.1"),
        (
            lambda p: p["storage"].append(deepcopy(p["storage"][0])),
            "storage: duplicate name",
        ),
        (
            lambda p: p["storage"][0]["attached_to"].append("missing"),
            "storage.0.attached_to: unknown",
        ),
    ],
)
def test_invalid_plan_reports_specific_problem(change: object, expected: str) -> None:
    plan = valid_plan()
    change(plan)  # type: ignore[operator]
    errors = plan_validation_errors(plan)
    assert any(expected in error for error in errors), errors
    with pytest.raises(ValidationError):
        DeploymentPlan.model_validate(plan)


@pytest.mark.req("FR-A-01")
def test_cycle_and_multiple_errors() -> None:
    plan = valid_plan()
    plan["services"].append({"name": "worker", "aws_service": "ECS", "purpose": "Work"})
    plan["dependencies"].extend(
        [
            {"source": "db", "target": "worker", "description": "A"},
            {"source": "worker", "target": "web", "description": "B"},
            {"source": "worker", "target": "missing", "description": "C"},
        ]
    )
    plan["file_types"] = []
    errors = plan_validation_errors(plan)
    assert any(
        "dependency cycle:" in error
        and all(name in error for name in ("web", "db", "worker"))
        for error in errors
    )
    assert any("unknown service" in error for error in errors)
    assert any("terraform is required" in error for error in errors)


@pytest.mark.req("FR-A-01")
@pytest.mark.parametrize("field", ["source", "target"])
def test_dependency_on_storage_gets_actionable_message(field: str) -> None:
    plan = valid_plan()
    plan["dependencies"][0][field] = "data"
    assert (
        f"dependencies.0.{field}: 'data' is a storage entry, not a service; "
        "link it with storage[].attached_to instead of dependencies"
    ) in plan_validation_errors(plan)


@pytest.mark.req("FR-A-01", "FR-A-02")
@pytest.mark.parametrize("field", ["source", "target"])
def test_dependency_on_file_type_gets_actionable_message(field: str) -> None:
    plan = valid_plan()
    plan["dependencies"][0][field] = "terraform"
    assert (
        f"dependencies.0.{field}: 'terraform' is a deployment tool / file type, "
        "not a service; remove it from dependencies"
    ) in plan_validation_errors(plan)
