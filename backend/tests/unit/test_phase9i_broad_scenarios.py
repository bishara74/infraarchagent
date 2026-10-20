"""PR-01/NFR-01: immutable broad scenario registration and anchor texts."""

import json

import pytest

from scripts.phase9_common import ROOT

pytestmark = pytest.mark.req("PR-01", "NFR-01")


def registration():
    return json.loads((ROOT / "docs/evals/scenarios/broad-v1.json").read_bytes())


def test_registered_ids_complexity_and_exact_default_order():
    data = registration()
    assert data["version"] == "broad-v1"
    assert [s["id"] for s in data["scenarios"]] == list(range(1, 11))
    assert [s["complexity"] for s in data["scenarios"]] == [
        1,
        2,
        2,
        3,
        3,
        4,
        4,
        4,
        5,
        5,
    ]
    assert all(s["name"] and s["prompt"] for s in data["scenarios"])
    assert data["schedule"] == {
        "default_runs_per_scenario": 2,
        "round_order": "alternating_forward_reverse",
        "default_order": list(range(1, 11)) + list(range(10, 0, -1)),
    }


@pytest.mark.parametrize("scenario,index", [(2, 2), (9, 0), (10, 1)])
def test_final_set_anchors_are_verbatim(scenario, index):
    original = json.loads((ROOT / "docs/phase9-prompts.json").read_bytes())
    assert (
        registration()["scenarios"][scenario - 1]["prompt"]
        == original["prompts"][index]
    )
