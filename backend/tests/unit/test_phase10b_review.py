"""FR-S-07, FR-UI-05: current plan-conflict evidence follows open findings."""

import pytest

from app.domain.enums import PackageStatus, RunStatus
from app.domain.review import open_plan_conflicts, package_presentation

pytestmark = pytest.mark.req("FR-S-07", "FR-UI-05", "FR-UI-07")


def report():
    conflict = {
        "service": "edge",
        "resource": "aws_lb.edge",
        "file_path": "terraform/main.tf",
        "property": "exposure",
        "expected": "public",
        "assessment": "regression",
        "rule_ids": ["AWS-0053"],
    }
    finding = {
        "resource": "aws_lb.edge",
        "rule_id": "AWS-0053",
        "file_path": "terraform/main.tf",
    }
    return {
        "sessions": [
            {"iterations": [{"verification": {"plan_conformance": [conflict]}}]}
        ],
        "final": {"outcome": "exhausted", "remaining_blocking": [finding]},
    }


def test_open_finding_has_explicit_reason_and_bounded_evidence():
    security = report()
    view = package_presentation(
        RunStatus.SUCCESS,
        PackageStatus.PENDING_REVIEW,
        {},
        security,
        {"summary": {"result": "valid"}},
        None,
    )
    assert view["review_reasons"] == [
        "plan_conformance_conflict",
        "unresolved_security_findings",
    ]
    assert view["plan_conflicts"][0]["rule_id"] == "AWS-0053"
    assert view["readiness_label"] == "pending_review"


def test_later_fix_removes_explanation_without_rewriting_history():
    security = report()
    security["final"]["remaining_blocking"] = []
    assert open_plan_conflicts(security) == []
    assert security["sessions"][0]["iterations"][0]["verification"]["plan_conformance"]


def test_other_resource_or_rule_never_inherits_plan_conflict():
    security = report()
    security["final"]["remaining_blocking"][0]["resource"] = "aws_lb.other"
    assert open_plan_conflicts(security) == []
    assert open_plan_conflicts(None) == []
