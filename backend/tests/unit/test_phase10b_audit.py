"""FR-S-02/07: exposure counter-audit keeps unknowns and profile history honest."""

from copy import deepcopy

import pytest

from scripts.phase10b_audit import exposure_flip, inventory, render, summarize

pytestmark = pytest.mark.req("FR-S-02", "FR-S-07", "NFR-01")


def audit():
    return {
        "plan": {"classification": "public"},
        "original": {
            "classification": "public",
            "resources": [{"resource": "aws_lb.edge", "classification": "public"}],
        },
        "retained": {
            "classification": "internal",
            "resources": [{"resource": "aws_lb.edge", "classification": "internal"}],
        },
    }


def test_same_resource_public_to_internal_only():
    source = audit()
    assert exposure_flip(source) is True
    other = deepcopy(source)
    other["retained"]["resources"][0]["resource"] = "aws_lb.other"
    assert exposure_flip(other) is False
    other["plan"]["classification"] = "absent"
    assert exposure_flip(other) is False
    source["original"]["classification"] = "unknown"
    assert exposure_flip(source) is None
    assert exposure_flip(None) is None


def test_corrected_rates_subtract_affected_passes_and_preserve_unknown_range():
    rows = [
        {
            "folder": "sample",
            "audit": audit(),
            "passes": {"strict": True},
            "affected": True,
        },
        {
            "folder": "sample",
            "audit": None,
            "passes": {"strict": True},
            "affected": None,
        },
        {
            "folder": "sample",
            "audit": audit(),
            "passes": {"strict": False},
            "affected": True,
        },
    ]
    summary = summarize(rows)[0]
    strict = summary["profiles"]["strict"]
    assert strict["published_passes"] == 2
    assert strict["affected_passes"] == 1
    assert strict["corrected_pass_range"] == [0, 1]
    assert summary["profiles"]["contextual-v2"]["published_passes"] is None
    report = render({"folders": [summary], "packages": []})
    assert "unavailable" in report and "incomplete" in report
    assert "43/120" not in report  # No hard-coded corpus claim in the renderer.


def test_missing_architecture_is_unknown_not_zero(tmp_path):
    path = "docs/evals/phase9-bench-real-synthetic/quality/run/cost.json"

    class Evidence:
        paths = {path}

        def json(self, name):
            assert name == path
            return {
                "status": "checks_passed",
                "profile_assessments": {"strict": {"checks_passed": True}},
            }

    rows, sources = inventory(Evidence(), tmp_path)
    assert not sources
    assert rows[0]["affected"] is None
    assert rows[0]["passes"]["contextual-v2"] is None
