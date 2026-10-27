"""NFR-01: evidence coverage and status decisions are explicit, never inferred."""

import copy
import json

import pytest

from scripts.phase10_evidence import ROOT, render, validate
from scripts.traceability import identifiers

pytestmark = pytest.mark.req("NFR-01")


def register():
    return json.loads((ROOT / "docs/evals/phase10-requirements.json").read_text())


def test_index_has_all_specification_ids_and_no_unsupported_status():
    data = register()
    requirements = identifiers((ROOT / "docs/spec/03-requirements.tex").read_text())
    validate(data, requirements, ROOT)
    assert len(data["rows"]) == 59
    text = render(data)
    assert "not met" in text and "unverified" in text
    assert "annotation or collection count is not" in text


@pytest.mark.parametrize(
    "change", ["missing", "no_evidence", "pr03_pass", "nfr04_pass"]
)
def test_index_rejects_missing_evidence_and_premature_acceptance(change):
    data = copy.deepcopy(register())
    requirements = {row["id"] for row in data["rows"]}
    if change == "missing":
        data["rows"].pop()
    elif change == "no_evidence":
        data["rows"][0]["evidence"] = []
    else:
        identity = "PR-03" if change == "pr03_pass" else "NFR-04"
        next(row for row in data["rows"] if row["id"] == identity)["status"] = "met"
    with pytest.raises(ValueError):
        validate(data, requirements, ROOT)


def test_current_index_distinguishes_new_verification_from_prior_execution():
    text = render(register())
    assert "(phase10b-verification/README.md)" in text
    assert "(phase10-verification/README.md)" in text
    assert "(phase10b-traceability/traceability.md)" in text
