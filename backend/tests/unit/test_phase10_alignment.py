"""FR-G-03/04/05: reproducible observations preserve denominators and limits."""

import pytest

from scripts.phase10_alignment import inventory, measure

pytestmark = pytest.mark.req("FR-G-03", "FR-G-04", "FR-G-05", "NFR-01")


def test_real_committed_directive_corpus_keeps_unknown_classes_separate():
    report = measure()
    assert len(report["packages"]) == 12
    assert all(row["model"] != "stub" for row in report["packages"])
    assert report["rates"]["cost_micro_literal"] == {
        "numerator": 2,
        "denominator": 4,
        "no_literal_class": 2,
    }
    assert report["rates"]["performance_literal_multi_az"]["numerator"] == 3
    assert report["rates"]["performance_autoscaling"]["numerator"] == 3
    assert report["rates"]["performance_both"]["numerator"] == 2
    assert report["rates"]["security_zero_first_checkov_high_or_critical"] == {
        "numerator": 0,
        "denominator": 4,
        "unknown": 0,
    }
    assert report["inputs"] and all(
        len(value) == 64 for value in report["inputs"].values()
    )


def test_inventory_includes_original_and_added_api_data_surfaces():
    endpoints, tables = inventory()
    assert ("GET", "/api/health", "health") in endpoints
    assert ("POST", "/api/lessons", "lessons") in endpoints
    assert ("GET", "/api/pipeline/{run_id}/download-all", "pipeline") in endpoints
    assert {
        "pipeline_runs",
        "generated_packages",
        "agent_events",
        "users",
        "lesson_sets",
    } <= set(tables)
    assert len(endpoints) == 46 and len(tables) == 14
