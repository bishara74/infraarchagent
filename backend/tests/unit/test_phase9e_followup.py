"""FR-S-03/FR-V-04: nested evidence and bounded safe attempt feedback."""

import json
from uuid import uuid4

import pytest

from app.agents.security.feedback import attempt_feedback
from app.core.logging import RedactingFilter
from app.domain.review import security_iterations
from scripts.phase9d_quality import quality_snapshot, quality_table, recompute_quality

pytestmark = pytest.mark.req("FR-S-03", "FR-V-04", "NFR-01")
CANARY = "sk-ant-api03-CANARY-7f3c9e2a1b4d5e6f"


def report():
    iterations = [
        {
            "fixes": [
                {"file": "terraform/main.tf", "schema_context_chars": 11689},
                {"file": "helm/app.yaml", "schema_context_chars": 0},
            ],
            "verification": {
                "outcome": "rolled_back",
                "reasons": ["terraform_regression"],
                "error_classes": ["Unsupported argument"],
            },
        },
        {"fixes": [{"file": "terraform/main.tf"}]},
    ]
    return {
        "sessions": [{"iterations": iterations[:1]}, {"iterations": iterations[1:]}],
        "iterations": iterations,
    }


def test_nested_sessions_precede_legacy_alias_and_preserve_missing():
    raw = report()
    assert len(list(security_iterations(raw))) == 2
    assert len(list(security_iterations({"iterations": raw["iterations"]}))) == 2
    compact = quality_snapshot(
        {"status": "pending_review", "security_report": raw}, RedactingFilter()
    )
    stats, _ = quality_table([compact])
    assert stats["schema_context_chars"]["security"]["count"] == 2
    assert stats["security_context_coverage"]["terraform"] == {
        "total": 2,
        "positive": 1,
        "zero": 0,
        "missing": 1,
        "reasons": {"unknown": 2},
    }
    assert stats["security_context_coverage"]["other"]["zero"] == 1
    assert len(stats["security_outcomes_by_class"]) == 1
    assert (
        list(security_iterations({"sessions": [], "iterations": raw["iterations"]}))
        == []
    )


def test_corrected_compact_round_trip_keeps_coverage_and_readiness(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    saved = tmp_path / "saved"
    saved.mkdir()
    run_id = str(uuid4())
    (results / "results.json").write_text(
        json.dumps({"runs": [{"run_id": run_id, "measurement": "pr01"}]})
    )
    (saved / (run_id + ".json")).write_text(
        json.dumps(
            {
                "packages": [
                    {
                        "variant": "security",
                        "status": "pending_review",
                        "security_report": report(),
                    }
                ],
                "missing_variants": ["cost", "performance"],
            }
        )
    )
    one, two = tmp_path / "one", tmp_path / "two"
    recompute_quality(results, saved, one)
    recompute_quality(results, one / "quality", two)
    assert json.loads((one / "quality.json").read_text()) == json.loads(
        (two / "quality.json").read_text()
    )


def test_feedback_is_complete_bounded_json_with_no_source_or_secrets():
    record = {
        "outcome": "rolled_back",
        "reasons": ["terraform_regression"],
        "error_classes": ["Missing required argument " + CANARY] * 100,
        "source": "DO-NOT-COPY",
        "diff": "DO-NOT-COPY",
    }
    text = attempt_feedback(
        record,
        [{"file": "terraform/main.tf", "accepted": False, "reason": CANARY}],
        RedactingFilter(),
    )
    assert len(text) <= 4000 and CANARY not in text and "DO-NOT-COPY" not in text
    assert json.loads(text)["reasons"] == ["terraform_regression"]
    assert attempt_feedback({"outcome": "accepted"}, [], RedactingFilter()) == ""
