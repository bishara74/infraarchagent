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


async def test_two_cohort_summary_separates_acceptance_from_removed_gate(
    tmp_path, monkeypatch
):
    from scripts import phase10e_replay as replay
    from tests.unit.test_phase10b_conformance import files, plan

    (tmp_path / "docs/evals").mkdir(parents=True)
    monkeypatch.setattr(replay, "ROOT", tmp_path)
    monkeypatch.setattr(replay, "COHORTS", (("final2", "one", 1), ("final3", "two", 1)))

    class Observer:
        identity = {}

    monkeypatch.setattr(replay, "Observer", lambda cache: Observer())
    item = {
        "run_id": "synthetic",
        "scenario": 1,
        "round": 1,
        "variant": "security",
        "plan": plan().model_dump(mode="json"),
        "package": {"original_files": files(), "files": files({"internal": True})},
    }
    monkeypatch.setattr(replay, "inventory", lambda *args: ([item], []))
    outcomes = iter(["accepted", "new_blocking_findings"])

    class Paired:
        def __init__(self, observer):
            self.rows, self.groups, self.missing = [], [], []

        async def package(self, item):
            self.rows.append(
                {
                    "before": "plan_conformance_regression",
                    "after": next(outcomes),
                    "before_sha256": "before",
                    "candidate_sha256": "after",
                }
            )
            return {"reconstruction": "complete"}

    monkeypatch.setattr(replay, "Replay", Paired)
    result = await replay.run(tmp_path / "docs/evals/result", tmp_path / ".cache")
    combined = result["combined"]
    assert combined["paired_guard_rejections_removed"] == 2
    assert combined["available_candidate_decisions"] == {
        "before": {"plan_conformance_regression": 2},
        "after": {"accepted": 1, "new_blocking_findings": 1},
    }
    assert combined["final_retained_packages_flagged"] == 2
