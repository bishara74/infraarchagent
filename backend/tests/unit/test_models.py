import pytest
from pydantic import ValidationError

from app.domain.enums import Variant
from app.domain.models import DeploymentPlan, IaCPackage, Violation


def test_violation_fingerprint_and_tool() -> None:
    violation = Violation(
        rule_id="CKV_1",
        severity="HIGH",
        file_path="main.tf",
        resource="aws_s3_bucket.example",
        message="unsafe",
        tool="checkov",
    )
    assert violation.fingerprint() == (
        "CKV_1",
        "main.tf",
        "aws_s3_bucket.example",
    )
    with pytest.raises(ValidationError):
        Violation.model_validate({**violation.model_dump(), "tool": "other"})


def test_package_validates_paths_at_construction() -> None:
    package = IaCPackage(variant=Variant.COST, files={"main.tf": "resource {}"})
    assert package.files["main.tf"] == "resource {}"
    with pytest.raises(ValidationError):
        IaCPackage(variant=Variant.COST, files={"../outside": "bad"})
    with pytest.raises(ValidationError):
        IaCPackage(variant=Variant.COST, files={"Main.tf": "a", "main.tf": "b"})


def test_deployment_plan_is_permissive_in_phase_zero() -> None:
    plan = DeploymentPlan(services=["ec2"], dependencies={"web": ["db"]})
    assert plan.services == ["ec2"]
    assert plan.file_types == []
