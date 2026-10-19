"""FR-UI-06/07 presentation and FR-S-09 target ordering."""

import pytest

from app.domain.enums import PackageStatus, RunStatus
from app.domain.review import package_presentation, retry_targets


@pytest.mark.req("FR-UI-06", "FR-UI-07")
@pytest.mark.parametrize("status", list(PackageStatus))
@pytest.mark.parametrize("run_status", list(RunStatus))
def test_presentation_for_every_state(status, run_status):
    result = package_presentation(run_status, status, {}, None, None, None)
    labelled = status in {
        PackageStatus.ENGINEER_APPROVED,
        PackageStatus.CHECKS_PASSED,
        PackageStatus.REJECTED,
    }
    assert result["downloadable"] == labelled
    assert result["readiness_label"] == (
        status.value if labelled or status == PackageStatus.PENDING_REVIEW else None
    )
    assert result["review_available"] == (
        status == PackageStatus.PENDING_REVIEW
        and run_status not in {RunStatus.CREATED, RunStatus.RUNNING}
    )
    assert result["review_reasons"] == (
        ["validation_error"]
        if status
        in {
            PackageStatus.PENDING_REVIEW,
            PackageStatus.ENGINEER_APPROVED,
            PackageStatus.REJECTED,
        }
        else []
    )


@pytest.mark.req("FR-S-09")
def test_targets_have_category_priority_and_unique_existing_paths():
    files = {path: "" for path in ("a.tf", "b.tf", "c.tf", "d.tf")}
    security = {
        "final": {
            "remaining_blocking": [
                {"file_path": p} for p in ("b.tf", "a.tf", "missing")
            ]
        }
    }
    validation = {
        "failed_checks_for_remediation": [
            {"file_path": p} for p in (None, "b.tf", "c.tf")
        ]
    }
    assert retry_targets(files, security, validation, ["d.tf", "a.tf"]) == [
        "a.tf",
        "b.tf",
        "c.tf",
        "d.tf",
    ]


@pytest.mark.req("FR-S-07", "FR-S-09")
@pytest.mark.parametrize(
    "result,reason", [("invalid", "validation_failed"), ("error", "validation_error")]
)
def test_current_review_reasons(result, reason):
    derived = package_presentation(
        RunStatus.PARTIAL_SUCCESS,
        PackageStatus.PENDING_REVIEW,
        {},
        {"final": {"outcome": "exhausted"}},
        {"summary": {"result": result}},
        "review retry aborted: scanner failed",
    )
    assert derived["review_reasons"] == [
        "unresolved_security_findings",
        reason,
        "retry_aborted",
    ]
