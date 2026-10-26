"""NFR-01/FR-A-05: replay v1 and measure the English-clause correction by layer."""

import json
from pathlib import Path

import pytest

from app.security.lesson_filter import screen
from tests.unit.test_phase9l_corpus import CORPUS, evaluate

pytestmark = pytest.mark.req("NFR-01", "FR-A-05")
EXTRA = json.loads(
    (Path(__file__).parents[1] / "fixtures/phase9m-filter-corpus.json").read_text()
)["cases"]


@pytest.mark.parametrize(
    "case", [*CORPUS["cases"], *EXTRA], ids=lambda case: case["id"]
)
def test_v2_corpus_preserves_attacks_and_accepts_english(case):
    row = next(row for row in evaluate("2", [case])["cases"] if row["id"] == case["id"])
    assert row["cumulative_blocked"] == case["blocked"], row


def test_v1_replay_keeps_original_layer_counts_and_author_false_positive():
    report = evaluate("1")
    assert [
        report[k]
        for k in (
            "total",
            "structured_blocked",
            "filter_independent_blocked",
            "filter_after_structure_blocked",
            "cumulative_blocked",
        )
    ] == [46, 10, 29, 28, 38]
    assert screen(EXTRA[0]["text"], version="1")["reasons"][0]["id"] == "code"
    assert screen(EXTRA[0]["text"])["passed"]


def test_unknown_filter_version_cannot_silently_select_latest():
    with pytest.raises(ValueError, match="Unknown lesson filter version"):
        screen("Prefer private subnets.", version="3")
