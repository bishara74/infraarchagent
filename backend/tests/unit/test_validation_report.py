import pytest
from pydantic import ValidationError

from app.domain.enums import PackageStatus
from app.domain.validation import (
    ValidationCheck,
    ValidationReport,
    package_validation_status,
)


def check(status="passed", **kwargs):
    return ValidationCheck(
        check_id="test.structure",
        category="structure",
        tool="builtin",
        status=status,
        message="Safe diagnostic",
        **kwargs,
    )


@pytest.mark.req("FR-V-04", "NFR-01")
@pytest.mark.parametrize(
    "path", ["/tmp/foo", "../secret", "terraform/../foo", "C:/foo", "a\\b", "a//b"]
)
def test_rejects_unsafe_report_paths(path):
    with pytest.raises(ValidationError):
        check("failed", file_path=path)


@pytest.mark.req("FR-V-04")
@pytest.mark.parametrize(
    "kwargs",
    [
        {"line_start": 1},
        {"file_path": "terraform/main.tf", "line_start": 0},
        {"file_path": "terraform/main.tf", "line_start": 2, "line_end": 1},
        {"file_path": "terraform/main.tf", "line_end": 2},
        {"skip_reason": "tool_error"},
        {"message": "raw\noutput"},
    ],
)
def test_rejects_invalid_locations_and_check_fields(kwargs):
    values = dict(
        check_id="test.structure",
        category="structure",
        tool="builtin",
        status="passed",
        message="Safe diagnostic",
    )
    values.update(kwargs)
    with pytest.raises(ValidationError):
        ValidationCheck(**values)


@pytest.mark.req("FR-V-04")
def test_skips_require_a_reason_and_models_forbid_extra_fields():
    with pytest.raises(ValidationError):
        check("skipped")
    with pytest.raises(ValidationError):
        check(unexpected="field")
    with pytest.raises(ValidationError):
        check().message = "changed"


@pytest.mark.req("FR-V-03", "FR-V-04")
@pytest.mark.parametrize(
    "required,status,failure,expected",
    [
        (False, "skipped", False, "valid"),
        (True, "skipped", False, "error"),
        (True, "skipped", True, "invalid"),
        (True, "passed", False, "valid"),
        (True, "passed", True, "invalid"),
    ],
)
def test_central_outcome_precedence(required, status, failure, expected):
    checks = [
        ValidationCheck(
            check_id="terraform.validate",
            category="terraform",
            tool="terraform",
            status=status,
            message="Terraform outcome",
            skip_reason="mirror_missing" if status == "skipped" else None,
        ),
        check("warning"),
    ]
    if failure:
        checks.append(
            check("failed", file_path="kubernetes/app.yaml", line_start=2, line_end=4)
        )
    report = ValidationReport.build(checks, terraform_required=required)
    assert report.summary.result == expected
    assert (
        package_validation_status(report.summary.result)
        == {
            "valid": PackageStatus.VALID,
            "invalid": PackageStatus.INVALID,
            "error": PackageStatus.VALIDATION_ERROR,
        }[expected]
    )
    assert ValidationReport.model_validate_json(report.model_dump_json()) == report
    assert ValidationReport.model_validate(report.model_dump(mode="json")) == report


@pytest.mark.req("FR-V-04")
def test_sampling_preserves_all_failures_and_required_outcomes():
    checks = [check("warning", file_path=f"kubernetes/file{n}.yaml") for n in range(20)]
    checks.extend(
        [
            check("failed", file_path="terraform/main.tf", line_start=3),
            check("failed"),
            ValidationCheck(
                check_id="terraform.validate",
                category="terraform",
                tool="terraform",
                status="skipped",
                message="Mirror missing",
                skip_reason="mirror_missing",
            ),
        ]
    )
    report = ValidationReport.build(
        reversed(checks), terraform_required=True, max_nonfailures=2
    )
    assert report == ValidationReport.build(
        checks, terraform_required=True, max_nonfailures=2
    )
    assert report.summary.model_dump() == dict(
        passed=0, failed=2, warnings=20, skipped=1, result="invalid"
    )
    assert len(report.checks) == 5
    assert report.omitted_counts == {"warning": 18}
    assert len(report.failed_checks_for_remediation) == 1
    assert report.failed_checks_for_remediation[0].file_path == "terraform/main.tf"
    assert any(c.status == "failed" and c.file_path is None for c in report.checks)
    assert any(c.tool == "terraform" for c in report.checks)
    with pytest.raises(ValidationError):
        ValidationReport.model_validate(
            {**report.model_dump(), "failed_checks_for_remediation": ()}
        )


@pytest.mark.req("FR-V-04", "FR-V-05")
@pytest.mark.parametrize("reason", ["deadline", "internal_error"])
def test_stage_abort_overrides_partial_failures(reason):
    report = ValidationReport.build(
        [check("failed")], terraform_required=False, abort_reason=reason
    )
    assert report.summary.result == "error"
    assert report.abort_reason == reason


@pytest.mark.req("FR-V-03")
def test_missing_required_terraform_outcome_cannot_pass():
    assert ValidationReport.build([], terraform_required=True).summary.result == "error"


@pytest.mark.req("FR-V-04")
@pytest.mark.parametrize(
    "updates",
    [
        {"report_version": 2},
        {
            "summary": {
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "skipped": 0,
                "result": "invalid",
            }
        },
        {"omitted_counts": {"failed": 1}},
        {"omitted_counts": {"warning": -1}},
        {"tool_versions": {"unknown": "1"}},
        {"tool_versions": {"helm": "raw\noutput"}},
        {"tool_versions": {"helm": "x" * 101}},
    ],
)
def test_rejects_inconsistent_or_unsafe_report(updates):
    report = ValidationReport.build([], terraform_required=False)
    with pytest.raises(ValidationError):
        ValidationReport.model_validate({**report.model_dump(), **updates})


@pytest.mark.req("FR-V-03")
def test_builtin_check_cannot_impersonate_required_terraform():
    fake = ValidationCheck(
        check_id="terraform.validate",
        category="structure",
        tool="builtin",
        status="passed",
        message="Fake schema result",
    )
    assert (
        ValidationReport.build([fake], terraform_required=True).summary.result
        == "error"
    )
