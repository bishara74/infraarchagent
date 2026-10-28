"""FR-S-02/03/07: replay preserves independent rejection denominators."""

import pytest

from scripts.phase10e_replay import recorded_rejections

pytestmark = pytest.mark.req("FR-S-02", "FR-S-03", "FR-S-07")


def test_recorded_gate_counts_do_not_claim_other_rejections_disappear():
    package = {
        "security_report": {
            "sessions": [
                {
                    "iterations": [
                        {
                            "verification": {
                                "reasons": ["plan_conformance_regression"],
                                "error_classes": ["one", "two"],
                                "partial_groups": [
                                    {"reason": "plan_conformance_regression"}
                                ],
                                "catalogue": [
                                    {"reason": "plan_conformance_regression"}
                                ],
                            }
                        },
                        {
                            "verification": {
                                "reasons": [
                                    "plan_conformance_regression",
                                    "new_blocking_findings",
                                ]
                            }
                        },
                    ]
                }
            ]
        },
        "validation_report": {
            "remediation": {
                "rounds": [{"reason": "plan_conformance_regression"}],
                "deterministic_repairs": [{"reason": "plan_conformance_regression"}],
            }
        },
    }
    assert recorded_rejections(package) == {
        "security_iterations_with_conformance_reason": 2,
        "security_iterations_conformance_only": 1,
        "security_error_class_counts": 3,
        "partial_groups_rejections": 1,
        "catalogue_rejections": 1,
        "rounds_rejections": 1,
        "deterministic_repairs_rejections": 1,
    }


def test_missing_report_and_accepted_iterations_are_not_rejections():
    assert recorded_rejections({}) == {}
    assert (
        recorded_rejections(
            {
                "security_report": {
                    "iterations": [
                        {"verification": {"outcome": "accepted", "reasons": []}}
                    ]
                }
            }
        )
        == {}
    )
