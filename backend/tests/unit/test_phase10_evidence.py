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
        if change == "nfr04_pass":
            data["author_clean_deployment_evidence"] = None
    with pytest.raises(ValueError):
        validate(data, requirements, ROOT)


def test_current_index_distinguishes_new_verification_from_prior_execution():
    text = render(register())
    assert "(phase10b-verification/README.md)" in text
    assert "(phase10-verification/README.md)" in text
    assert "(phase10b-traceability/traceability.md)" in text


@pytest.mark.req("NFR-04")
@pytest.mark.parametrize("status", ["met", "unverified"])
def test_deployment_prose_uses_reviewed_status_finding_and_evidence(status):
    data = register()
    deployment = next(row for row in data["rows"] if row["id"] == "NFR-04")
    deployment["status"] = status
    deployment["finding"] = "Reviewed deployment scope."
    deployment["evidence"] = ["docs/deployment.md"]
    data["author_clean_deployment_evidence"] = (
        "docs/evals/nfr04-clean-deployment-20261028/README.md"
        if status == "met"
        else None
    )
    validate(data, {row["id"] for row in data["rows"]}, ROOT)
    text = render(data)
    assert f"NFR-04: **{status}** — Reviewed deployment scope." in text
    assert "Evidence: [deployment.md](../../docs/deployment.md)." in text
    assert "NFR-04 remains unverified" not in text
