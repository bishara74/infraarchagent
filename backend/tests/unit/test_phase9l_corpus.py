"""NFR-01: independently count structural/filter layers without safety claims."""

import json
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domain.lessons import LessonInput
from app.security.lesson_filter import screen
from tests.unit.test_phase9l_lessons import SAFE

CORPUS = json.loads(
    (Path(__file__).parents[1] / "fixtures/phase9l-injection-corpus.json").read_text()
)


def text_for(case):
    if "repeat" in case:
        return case["repeat"] * case["count"]
    if "parts" in case:
        return "".join(case["parts"])
    text = case["text"]
    return (
        text.encode().decode("unicode_escape") if case.get("decode_escapes") else text
    )


def evaluate():
    rows, rule_counts = [], Counter()
    for case in CORPUS["cases"]:
        value = text_for(case)
        try:
            lesson = LessonInput.model_validate({**SAFE, "text": value})
        except ValidationError:
            structured = False
            lesson = None
        else:
            structured = True
        # Run the independent filter on raw text too, even if layer 1 rejects it.
        independent = screen(value)
        filtered = screen(lesson.text) if lesson else independent
        reasons = [reason["id"] for reason in filtered["reasons"]]
        rule_counts.update(reasons)
        rows.append(
            {
                "id": case["id"],
                "class": case["class"],
                "structured_blocked": not structured,
                "filter_independent_blocked": not independent["passed"],
                "filter_after_structure_blocked": bool(
                    lesson and not filtered["passed"]
                ),
                "cumulative_blocked": not structured or not filtered["passed"],
                "expected_blocked": case["blocked"],
                "rules": reasons,
            }
        )
    return {
        "corpus_version": CORPUS["version"],
        "total": len(rows),
        "structured_blocked": sum(row["structured_blocked"] for row in rows),
        "filter_independent_blocked": sum(
            row["filter_independent_blocked"] for row in rows
        ),
        "filter_after_structure_blocked": sum(
            row["filter_after_structure_blocked"] for row in rows
        ),
        "cumulative_blocked": sum(row["cumulative_blocked"] for row in rows),
        "rules": dict(sorted(rule_counts.items())),
        "cases": rows,
        "limitations": (
            "Human approval is a separate authorization layer. Delimiters and "
            "deterministic output gates are regression-tested boundaries, not "
            "universal semantic injection detectors. Residual cases intentionally "
            "pass the syntactic filter."
        ),
    }


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda case: case["id"])
def test_injection_corpus_by_layer(case):
    row = next(row for row in evaluate()["cases"] if row["id"] == case["id"])
    assert row["cumulative_blocked"] == case["blocked"], row


@pytest.mark.req("NFR-01")
def test_corpus_reports_every_case_without_raw_payloads():
    report = evaluate()
    assert report["total"] == len(CORPUS["cases"])
    assert all("text" not in row and "parts" not in row for row in report["cases"])
    assert report["cumulative_blocked"] == sum(
        case["blocked"] for case in CORPUS["cases"]
    )
