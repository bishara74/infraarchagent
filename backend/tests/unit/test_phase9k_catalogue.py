"""FR-A-01 / PR-01 / NFR-01: fake-only catalogue capture and cost projections."""

from decimal import Decimal

import httpx
import pytest

from app.core.public_catalogue import CatalogueError, digest, load_snapshot
from scripts.phase9_budget import BudgetGuard, CreditSnapshot
from scripts.phase9k_catalogue import (
    broad_usage,
    candidates,
    capture,
    estimate,
    pinned_sonnet,
    recommendation,
)
from tests.phase9k_fixtures import ARCHITECT, BASELINE, fake_snapshot

pytestmark = pytest.mark.req("FR-A-01", "PR-01", "NFR-01")
FAKE_SONNET = "anthropic/TEST-ONLY-sonnet-2099.1"


def with_candidate(snapshot):
    model = {**snapshot["payload"]["models"][-1], "id": FAKE_SONNET, "created": 999}
    snapshot["payload"]["models"].append(model)
    snapshot["payload"]["endpoints"][FAKE_SONNET] = snapshot["payload"]["endpoints"][
        ARCHITECT
    ]
    return snapshot


def usage():
    return [
        {
            "folder": "TEST-ONLY-evidence",
            "results_sha256": "a" * 64,
            "run_id": "fake",
            "scenario_id": scenario,
            "cost_usd": Decimal("10"),
            "calls": [
                {
                    "model": BASELINE + ":nitro",
                    "input_tokens": 100,
                    "output_tokens": 200,
                    "reasoning_tokens": 50,
                },
                {
                    "model": BASELINE + ":nitro",
                    "input_tokens": 50,
                    "output_tokens": 100,
                    "reasoning_tokens": 40,
                },
            ],
        }
        for scenario in range(1, 11)
    ]


async def test_capture_anonymous_atomic_allowlisted_and_no_live_model_defaults(
    tmp_path,
):
    fake = with_candidate(fake_snapshot(tmp_path / "fixture.json"))
    requested = []

    def reply(request):
        requested.append(request)
        assert not {"authorization", "x-api-key", "cookie"} & set(request.headers)
        if request.url.path.endswith("/models"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {**m, "secret": "do-not-save"}
                        for m in fake["payload"]["models"]
                    ]
                },
            )
        identity = request.url.path.removeprefix("/api/v1/models/").removesuffix(
            "/endpoints"
        )
        return httpx.Response(
            200,
            json={
                "data": {
                    "endpoints": [
                        {**e, "api_key": "do-not-save"}
                        for e in fake["payload"]["endpoints"][identity]
                    ]
                }
            },
        )

    path = tmp_path / "captured.json"
    snapshot = await capture(
        path, [BASELINE + ":nitro"], transport=httpx.MockTransport(reply)
    )
    assert load_snapshot(path) == snapshot
    assert len(requested) == 3
    assert "do-not-save" not in path.read_text()
    assert snapshot["sha256"] == digest(snapshot["payload"])
    assert recommendation(snapshot) == FAKE_SONNET
    assert candidates(snapshot)[0]["json_schema_declared"]
    assert len(snapshot["source_urls"]) == 3


async def test_capture_failure_never_replaces_existing_snapshot(tmp_path):
    path = tmp_path / "snapshot.json"
    original = fake_snapshot(path)
    with pytest.raises(CatalogueError):
        await capture(
            path,
            [BASELINE],
            transport=httpx.MockTransport(lambda r: httpx.Response(403)),
        )
    assert load_snapshot(path) == original


@pytest.mark.parametrize(
    "identity",
    [
        "~anthropic/sonnet-latest",
        "anthropic/TEST-ONLY-sonnet-latest",
        "anthropic/TEST-ONLY-sonnet-2099:free",
        "test-only/not-sonnet",
    ],
)
def test_recommendation_excludes_aliases_and_variants(identity):
    assert not pinned_sonnet({"id": identity})


def test_cost_uses_explicit_model_not_recommendation_and_counts_output_once(tmp_path):
    snapshot = with_candidate(fake_snapshot(tmp_path / "snapshot.json"))
    selected = next(m for m in snapshot["payload"]["models"] if m["id"] == ARCHITECT)
    selected["pricing"] = {"prompt": "0.001", "completion": "0.002"}
    report = estimate(snapshot, ARCHITECT, usage=usage())
    assert report["explicit_architect_model"] == ARCHITECT
    assert report["recommended_architect_model"] == FAKE_SONNET
    assert report["recommendation_advisory"]
    assert (
        report["per_run"]["architect_usd"] == 0.75
    )  # 150 input, 300 output; no +90 reasoning
    assert report["smoke_6_9_10"]["architect_usd"] == 2.25
    assert report["round_20"]["architect_usd"] == 15
    assert report["per_run"]["extra_usd"] == pytest.approx(
        0.75 - (150 * 0.000123 + 300 * 0.000456)
    )
    with pytest.raises(CatalogueError, match="Explicit ARCHITECT_MODEL"):
        estimate(snapshot, "", usage=usage())


def test_estimate_missing_price_capability_and_endpoint_evidence_refuses(tmp_path):
    snapshot = fake_snapshot(tmp_path / "snapshot.json")
    snapshot["payload"]["models"][-1]["pricing"] = {}
    with pytest.raises(CatalogueError, match="pricing"):
        estimate(snapshot, ARCHITECT, usage=usage())
    snapshot["payload"]["endpoints"][ARCHITECT] = []
    with pytest.raises(CatalogueError, match="endpoint"):
        estimate(snapshot, ARCHITECT, usage=usage())


def test_credit_guard_uses_estimate_before_any_measured_cost():
    guard = BudgetGuard(Decimal("2"), 20, estimated_run_cost=Decimal("3"))
    assert guard.highest == 0
    assert guard.threshold() == 6
    assert guard.reason(CreditSnapshot(remaining=Decimal("5")))
    assert guard.reason(CreditSnapshot(remaining=Decimal("7"))) is None
    guard.observe(Decimal("4"))
    assert guard.threshold() == 8


def test_recorded_usage_totals_without_real_metadata():
    rows = broad_usage()
    assert len(rows) == 40
    assert sum(c["input_tokens"] for r in rows for c in r["calls"]) == 64871
    assert sum(c["output_tokens"] for r in rows for c in r["calls"]) == 31582


def test_inspection_command_does_not_load_dotenv_or_settings(tmp_path):
    import os
    import subprocess
    from pathlib import Path

    snapshot_path = tmp_path / "snapshot.json"
    fake_snapshot(snapshot_path)
    backend = Path(__file__).resolve().parents[2]
    script = """
import sys

def guard(event, args):
    if event == 'open' and str(args[0]).endswith('.env'):
        raise AssertionError('dotenv read')
sys.addaudithook(guard)
from scripts import phase9k_catalogue
assert 'app.core.config' not in sys.modules
sys.argv = ['catalogue', 'inspect', '--snapshot', sys.argv[1]]
phase9k_catalogue.main()
assert 'app.core.config' not in sys.modules
"""
    env = {"PATH": os.environ.get("PATH", "/usr/bin"), "PYTHONPATH": str(backend)}
    result = subprocess.run(
        [str(backend / ".venv/bin/python"), "-c", script, str(snapshot_path)],
        env=env,
        cwd=backend,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert '"recommendation_advisory": true' in result.stdout


def test_advisory_listing_handles_unserved_candidate_without_selecting_it(tmp_path):
    snapshot = with_candidate(fake_snapshot(tmp_path / "snapshot.json"))
    snapshot["payload"]["endpoints"][FAKE_SONNET] = []
    assert candidates(snapshot)[0]["eligible"] is False
    assert recommendation(snapshot) is None
    with pytest.raises(CatalogueError, match="endpoint"):
        estimate(snapshot, FAKE_SONNET, usage=usage())


@pytest.mark.parametrize("symlink", [False, True])
def test_snapshot_loader_refuses_dotenv_before_any_read(tmp_path, monkeypatch, symlink):
    from pathlib import Path

    path = tmp_path / ".env"
    if symlink:
        link = tmp_path / "snapshot.json"
        link.symlink_to(path)
        path = link
    monkeypatch.setattr(
        Path, "read_text", lambda *a, **k: pytest.fail("Dotenv read attempted")
    )
    with pytest.raises(CatalogueError, match="make catalogue-snapshot"):
        load_snapshot(path)
