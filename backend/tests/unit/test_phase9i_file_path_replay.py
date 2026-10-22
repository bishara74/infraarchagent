"""PR-01/FR-V-03: path-only observations preserve baseline and scenario units."""

from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from scripts.phase9i_file_path_replay import (
    Observer,
    PathObserver,
    observational_model_ast,
    retained_files,
)
from scripts.phase9i_replay import digest
from scripts.phase9i_v6_replay import summarize
from tests.unit.test_phase9i_v6_equivalents import provider
from tests.unit.test_phase9i_v6_replay import observation

pytestmark = pytest.mark.req("PR-01", "FR-V-03", "NFR-01")


def test_baseline_is_prior_retained_v6_bytes_without_live_path_rules(monkeypatch):
    files = {
        **provider(),
        "terraform/main.tf": 'resource "aws_eip" "one" { vpc = true }\n'
        'locals { values = file("helm/app/values.yaml") }',
        "helm/app/values.yaml": "replicaCount: 2\n",
    }
    from app.validation.v6_equivalents import repair_v6_equivalents

    after, _ = repair_v6_equivalents(files)
    item = {"package": {"files": files}}
    previous = {
        "before_sha256": digest(files),
        "candidate_sha256": digest(after),
        "retained_sha256": digest(after),
        "reason": "improved",
    }
    monkeypatch.setattr(
        "scripts.phase9i_file_path_replay.repair_file_paths",
        lambda _: pytest.fail("live path rules must not reconstruct historical bytes"),
    )
    assert retained_files(item, previous) == after
    assert 'file("helm/app/values.yaml")' in after["terraform/main.tf"]
    broken = {**previous, "retained_sha256": "wrong"}
    with pytest.raises(AssertionError):
        retained_files(item, broken)
    previous["retained_sha256"] = digest(files)
    previous["reason"] = "no_improvement"
    assert retained_files(item, previous) == files


def test_model_proof_allows_only_the_additive_repair_kind():
    before = """class DeterministicRepair:
    kind: Literal["db_name", "route_cidr"]
class ValidationCheck:
    status: str
"""
    after = before.replace('"db_name",', '"terraform_file_path", "db_name",')
    assert observational_model_ast(before) == observational_model_ast(after)
    assert observational_model_ast(before) != observational_model_ast(
        after.replace('"route_cidr"', '"different"')
    )
    assert observational_model_ast(before) != observational_model_ast(
        after.replace("status: str", "status: int")
    )


async def test_identity_reuse_requires_same_prior_retained_bytes(monkeypatch):
    observer = object.__new__(PathObserver)
    files = {"terraform/main.tf": "old"}
    old = observation(False, 1)
    observer.baselines = {"identity": files}
    observer.previous_rows = {"identity": {"retained": old}}
    observer.fresh_keys = {"changed"}
    native = AsyncMock(return_value=observation(True, 1))
    monkeypatch.setattr(Observer, "observe", native)
    assert await observer.observe({"key": "identity"}, dict(files)) == old
    native.assert_not_awaited()
    with pytest.raises(AssertionError):
        await observer.observe({"key": "identity"}, {"terraform/main.tf": "new"})
    assert await observer.observe({"key": "changed"}, files) == observation(True, 1)
    native.assert_awaited_once()


def test_rejected_valid_candidate_and_security_blockers_do_not_create_pass_gains():
    old, candidate = observation(False, 2), observation(True, 2)
    row = {
        "before": old,
        "candidate": candidate,
        "retained": deepcopy(old),
        "reason": "no_improvement",
    }
    result = summarize([row])
    assert result["deltas"]["valid"] == 0
    row.update(retained=candidate, reason="improved")
    result = summarize([row])
    assert result["deltas"]["valid"] == 1
    assert all(
        p == {"passes": 0, "blockers": 0} for p in result["deltas"]["profiles"].values()
    )
