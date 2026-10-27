"""FR-P-04/NFR-01: replay counts preserve historical attempt denominators."""

import pytest

from app.core.logging import RedactingFilter
from scripts.phase9d_quality import quality_snapshot
from scripts.phase10d_replay import export_counts, load_baseline

pytestmark = pytest.mark.req("FR-P-04", "FR-S-07", "NFR-01")


def test_export_counts_distinguish_attempts_and_error_classes():
    def historical_snapshot(package, redactor):
        return {
            "phase9e": {
                "security_iteration_repairs": [
                    {
                        "outcome": "rolled_back",
                        "reasons": [],
                        "error_classes": ["one", "two"],
                    }
                ],
                "repair_rounds": [
                    {
                        "outcome": "rejected",
                        "reason": "unknown",
                        "error_classes": ["one", "two", "three"],
                    }
                ],
            }
        }

    result = export_counts([{}], historical_snapshot)
    assert result == {
        "empty_rollback_attempts": 1,
        "empty_rollback_error_classes": 2,
        "unknown_repair_attempts": 1,
        "unknown_repair_error_classes": 3,
    }


def test_current_empty_accepted_reasons_are_not_rollback_anomalies():
    package = {
        "security_report": {
            "iterations": [{"verification": {"outcome": "accepted", "reasons": []}}]
        }
    }
    assert all(v == 0 for v in export_counts([package], quality_snapshot).values())


def test_baseline_is_loaded_from_the_frozen_diagnosis_revision():
    baseline = load_baseline("backend/scripts/phase9e_metrics.py")
    assert "plan_conformance_regression" not in baseline.REASONS
    assert (
        baseline.measurement(
            {
                "stage": "security_iteration_verification",
                "reasons": ["plan_conformance_regression"],
            }
        )["reasons"]
        == []
    )
    assert quality_snapshot(
        {
            "security_report": {
                "iterations": [
                    {"verification": {"reasons": ["plan_conformance_regression"]}}
                ]
            }
        },
        RedactingFilter(),
    )["phase9e"]["security_iteration_repairs"][0]["reasons"] == [
        "plan_conformance_regression"
    ]
