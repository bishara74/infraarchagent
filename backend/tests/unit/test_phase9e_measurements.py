"""FR-V-04/PR-05: measured stages, conservative attribution and safe evidence."""

import json

import pytest

from app.domain.validation import ValidationCheck
from app.validation.workspace import ValidationWorkspace
from scripts.benchmark import normalized_event, timings
from scripts.phase9e_metrics import measurement, measurement_summary
from scripts.phase9e_rehearsal import verification_rehearsal
from tests.unit.test_phase9e_gate import Runner

pytestmark = pytest.mark.req("FR-V-04", "PR-05", "NFR-01")


def failure(key="a", scope="resource.aws_vpc.main"):
    check = ValidationCheck(
        check_id="terraform.validate",
        category="terraform",
        tool="terraform",
        status="failed",
        message="Missing required argument",
        file_path="terraform/main.tf",
        line_start=1,
        diagnostic_key=key * 64,
    )
    check._origin_scope = scope
    return check


def test_hidden_errors_are_unknown_and_new_resources_are_attributable():
    workspace = ValidationWorkspace()
    files = {"terraform/main.tf": 'resource "aws_vpc" "main" {}\n'}
    try:
        workspace.observe([failure()], "generated", files)
        workspace.observe(
            [failure("b"), failure("c", "resource.aws_vpc.added")],
            "security_fix",
            {
                "terraform/main.tf": files["terraform/main.tf"]
                + 'resource "aws_vpc" "added" {}\n'
            },
        )
        annotated = workspace.annotate(
            (failure("b"), failure("c", "resource.aws_vpc.added"))
        )
        assert [c.origin for c in annotated] == ["unknown", "security_fix"]
        assert "_origin_scope" not in annotated[0].model_dump()
    finally:
        workspace.close()


def test_generated_and_repair_origins_require_observed_complete_baseline():
    workspace = ValidationWorkspace()
    try:
        workspace.observe([failure()], "generated", {})
        assert workspace.annotate((failure(),))[0].origin == "generated"
        workspace.observe([], "repair", {})
        workspace.observe([failure()], "repair", {})
        assert workspace.annotate((failure(),))[0].origin == "repair"
    finally:
        workspace.close()


def test_measurement_allowlist_and_timing_rows_have_no_new_thresholds():
    raw = {
        "stage": "generation_gate",
        "phase": "generation",
        "duration_seconds": 3.25,
        "init_runs": 1,
        "secret": "CANARY",
        "reasons": ["CANARY"],
    }
    event = normalized_event(
        {
            "seq": 1,
            "kind": "stage_notice",
            "agent": "generator_cost",
            "variant": "cost",
            "status": "generating",
            "timestamp": "2026-10-16T00:00:00+00:00",
            "payload": {"measurement": raw},
        }
    )
    row = timings("fixture", [event])[0]
    assert row["seconds"] == 3.25 and row["threshold_seconds"] is None
    assert "CANARY" not in json.dumps(event)
    assert measurement({"stage": "CANARY"}) is None


def test_deadline_only_denominator_and_multiple_causes_remain_distinct():
    records = [
        dict(
            stage="security_iteration_verification",
            phase="security",
            duration_seconds=n,
            fix_started=True,
            candidate_created=candidate,
            deadline_only=only,
            reasons=reasons,
        )
        for n, candidate, only, reasons in [
            (1, True, True, ["iteration_deadline"]),
            (2, True, False, ["iteration_deadline", "terraform_regression"]),
            (3, False, False, ["iteration_deadline"]),
            (4, True, False, []),
        ]
    ]
    summary, table = measurement_summary(records)
    assert summary["iterations"] == {
        "attempted_fix_iterations": 4,
        "deadline_only_rollbacks": 1,
        "deadline_before_candidate": 1,
        "multiple_cause_deadline_rollbacks": 1,
        "validity_regression_rollbacks": 1,
    }
    assert summary["durations"]["security_iteration_verification"] == {
        "count": 4,
        "median": 2.5,
        "p90": 4,
        "max": 4,
    }
    assert "four initial / nine post-security" in table


async def test_scripted_rehearsal_uses_private_workspaces_and_initialization_reuse():
    runner = Runner()
    result = await verification_rehearsal(runner=runner)
    assert len(result["records"]) == 6
    assert result["summary"]["iterations"]["attempted_fix_iterations"] == 6
    assert result["summary"]["iterations"]["deadline_only_rollbacks"] == 0
    init = [call for call in runner.calls if call[1][1] == "init"]
    assert len(init) == 3
    assert len({str(call[2]) for call in init}) == 3
    assert result["summary"]["initialization"]["init_runs"] == 3
    assert result["summary"]["initialization"]["init_reused"] >= 6
