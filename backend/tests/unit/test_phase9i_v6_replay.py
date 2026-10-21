"""PR-01/FR-V-03: offline migration reporting preserves scenario and guard units."""

from copy import deepcopy

import pytest

from scripts.phase9i_v6_replay import (
    configuration_blocks,
    final_scenario,
    removed_fields,
    summarize,
)

pytestmark = pytest.mark.req("PR-01", "FR-V-03", "NFR-01")


def test_final_scenarios_use_metadata_and_ignore_prompt_text():
    assert (
        final_scenario(
            {"measurement": "pr01", "prompt_index": 2, "prompt": "not a static site"}
        )
        == "final-2"
    )
    assert final_scenario({"measurement": "pr03", "prompt": "anything"}) == "final-0"


def test_removed_field_audit_is_recursive_and_excludes_computed_outputs():
    child = {"attributes": {"old": {"optional": True}}, "block_types": {}}
    old = {
        "attributes": {"computed_only": {"computed": True}},
        "block_types": {"nested": {"block": child}},
    }
    new = {
        "attributes": {},
        "block_types": {"nested": {"block": {"attributes": {}, "block_types": {}}}},
    }
    assert list(
        removed_fields({"computed_only": "x", "nested": [{"old": "x"}]}, old, new)
    ) == [("nested.old", "argument")]
    assert list(
        removed_fields({"dynamic": [{"nested": {"content": [{"old": "x"}]}}]}, old, new)
    ) == [("nested.old", "argument")]


def observation(valid, blockers):
    return {
        "validation": "valid" if valid else "invalid",
        "scan_outcome": "clean",
        "profiles": {
            p: {
                "checks_passed": valid and not blockers,
                "remaining_blocking": blockers,
                "excepted": [],
            }
            for p in ("strict", "contextual-v1", "contextual-v2")
        },
    }


def test_rejected_candidate_gains_are_not_retained_deltas():
    old = observation(False, 1)
    candidate = observation(True, 0)
    row = {
        "before": old,
        "candidate": candidate,
        "retained": deepcopy(old),
        "reason": "terraform_regression",
    }
    result = summarize([row])
    assert result["candidate"]["validation"] == {"valid": 1}
    assert result["deltas"]["valid"] == 0
    assert all(
        v == {"passes": 0, "blockers": 0} for v in result["deltas"]["profiles"].values()
    )
    row["retained"] = candidate
    row["reason"] = "improved"
    result = summarize([row])
    assert result["deltas"]["valid"] == 1
    assert all(
        v == {"passes": 1, "blockers": -1}
        for v in result["deltas"]["profiles"].values()
    )


def test_inventory_flattens_named_data_sources_in_both_serializations():
    body = {"current": {"state": "available"}}
    for data in (
        {"data": [{"aws_availability_zones": body}]},
        {"data": {"aws_availability_zones": body}},
    ):
        assert configuration_blocks(data, "data") == [
            (("aws_availability_zones", "current"), {"state": "available"})
        ]


async def test_frozen_observations_require_identical_bytes_and_changes_run_natively(
    monkeypatch,
):
    from unittest.mock import AsyncMock

    from scripts.phase9i_v6_replay import MigrationObserver, Observer

    observer = object.__new__(MigrationObserver)
    old = observation(False, 1)
    native_result = observation(True, 0)
    observer.frozen = {"unchanged": ("prior_native_offline", old)}
    observer.fresh_keys = {"changed"}
    files = {"terraform/main.tf": "original"}
    item = {"key": "unchanged", "package": {"files": files}}
    native = AsyncMock(return_value=native_result)
    monkeypatch.setattr(Observer, "observe", native)
    assert await observer.observe(item, dict(files)) == old
    native.assert_not_awaited()
    with pytest.raises(AssertionError):
        await observer.observe(item, {"terraform/main.tf": "different"})
    item["key"] = "changed"
    assert await observer.observe(item, files) == native_result
    native.assert_awaited_once()
