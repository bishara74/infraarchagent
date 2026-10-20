"""FR-S-04/09: reporting counts occurrences and preserves introduced rules."""

import pytest

from scripts.phase9i_kubernetes_report import (
    identity_deltas,
    rule_deltas,
    stored_metrics,
    table_summary,
)

pytestmark = pytest.mark.req("FR-S-04", "FR-S-09", "FR-V-01")


def test_rule_deltas_count_occurrences_and_include_new_rules():
    before = {"blockers": [{"rule_id": "OLD"}, {"rule_id": "OLD"}]}
    after = {"blockers": [{"rule_id": "OLD"}, {"rule_id": "NEW"}]}
    assert rule_deltas(before, after) == [
        {"rule_id": "NEW", "before": 0, "after": 1, "delta": 1},
        {"rule_id": "OLD", "before": 2, "after": 1, "delta": -1},
    ]


def test_profile_table_keeps_validity_and_profile_pass_counts_separate():
    summary = {
        "final": {
            "per_prompt": {
                "ECS": {
                    "packages": 47,
                    "valid": 29,
                    "checks_passed": {
                        "strict": 5,
                        "contextual-v1": 6,
                        "contextual-v2": 7,
                    },
                }
            }
        }
    }
    assert table_summary(summary, "final")[-1] == "| ECS | 47 | 29 | 5 | 6 | 7 |"


def test_replacement_finding_is_visible_even_when_rule_count_is_unchanged():
    before = {
        "findings": [{"rule_id": "SAME", "file_path": "k8s/a.yaml", "resource": "old"}]
    }
    after = {
        "findings": [{"rule_id": "SAME", "file_path": "k8s/a.yaml", "resource": "new"}]
    }
    assert rule_deltas(before, after, "findings") == []
    assert identity_deltas(before, after) == {
        "introduced": [("SAME", "k8s/a.yaml", "new")],
        "removed": [("SAME", "k8s/a.yaml", "old")],
    }


def test_stored_metrics_do_not_backfill_experimental_assessments():
    profiles = {
        "strict": {"checks_passed": True},
        "contextual-v1": {"checks_passed": True},
    }
    package = {
        "validation_report": {"summary": {"result": "valid", "failed": 0}},
        "profile_assessments": profiles,
    }
    assert stored_metrics(package) == {
        "validation": "valid",
        "failed_checks": 0,
        "profiles": profiles,
    }
    assert "contextual-v2" not in stored_metrics(package)["profiles"]


def test_unknown_scan_does_not_claim_findings_removed_or_numeric_deltas():
    from scripts.phase9i_report import compare

    before = {
        "validation": "valid",
        "failed_checks": [],
        "scan_outcome": "clean",
        "blockers": [{"rule_id": "OLD", "file_path": "k8s/a.yaml", "resource": "app"}],
        "findings": [],
        "profiles": {
            p: {"remaining_blocking": 1}
            for p in ("strict", "contextual-v1", "contextual-v2")
        },
    }
    after = {
        **before,
        "scan_outcome": "unknown",
        "blockers": [],
        "profiles": {p: {"remaining_blocking": None} for p in before["profiles"]},
    }
    assert compare(before, after)["removed"] == []
    assert compare(before, after)["blocker_deltas"]["strict"] is None
    assert identity_deltas(before, after) == {
        "introduced": [],
        "removed": [],
        "known": False,
    }
