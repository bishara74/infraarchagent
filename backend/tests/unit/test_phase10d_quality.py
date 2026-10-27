"""FR-P-04/FR-V-04/NFR-01: keep recorded reason codes without source leakage."""

import json

import pytest

from app.core.logging import RedactingFilter
from scripts.phase9d_quality import compact_snapshot, quality_snapshot
from scripts.phase9e_metrics import measurement

pytestmark = pytest.mark.req("FR-P-04", "FR-V-04", "NFR-01")


@pytest.mark.parametrize(
    "reason",
    ["plan_conformance_regression", "security_control_removed", "future_guard_reason"],
)
def test_all_recorded_reason_codes_survive_export_and_reload(reason):
    package = {
        "status": "pending_review",
        "security_report": {
            "iterations": [
                {
                    "verification": {
                        "outcome": "rolled_back",
                        "reasons": [reason],
                        "error_classes": ["one", "two"],
                    }
                }
            ]
        },
        "validation_report": {
            "remediation": {
                "rounds": [
                    {"phase": "generation", "outcome": "rejected", "reason": reason}
                ]
            }
        },
    }
    snapshot = quality_snapshot(package, RedactingFilter())
    for result in (snapshot, compact_snapshot(snapshot, RedactingFilter())):
        assert result["phase9e"]["security_iteration_repairs"][0]["reasons"] == [reason]
        assert result["phase9e"]["repair_rounds"][0]["reason"] == reason
    observed = measurement(
        {
            "stage": "security_iteration_verification",
            "reason": reason,
            "reasons": [reason],
        }
    )
    assert observed["reason"] == reason and observed["reasons"] == [reason]


def test_accepted_iteration_may_have_no_rejection_reason():
    result = quality_snapshot(
        {
            "status": "pending_review",
            "security_report": {
                "iterations": [{"verification": {"outcome": "accepted", "reasons": []}}]
            },
        },
        RedactingFilter(),
    )
    assert result["phase9e"]["security_iteration_repairs"][0]["reasons"] == []


def test_arbitrary_reason_metadata_is_not_exported():
    canary = "sk-ant-api03-CANARY-7f3c9e2a1b4d5e6f"
    result = quality_snapshot(
        {
            "security_report": {
                "iterations": [
                    {
                        "verification": {
                            "outcome": "rolled_back",
                            "reasons": [canary, "/tmp/private-source"],
                        }
                    }
                ]
            }
        },
        RedactingFilter(),
    )
    assert canary not in json.dumps(result)
    assert "/tmp/private-source" not in json.dumps(result)
