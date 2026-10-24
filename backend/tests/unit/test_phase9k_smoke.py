"""PR-01 / FR-A-01 / NFR-01: smoke and scripted client rehearsal."""

import json
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.core.config import get_settings
from app.core.generator_settings import GeneratorSettings
from app.core.public_catalogue import provenance
from app.domain.agent_selection import ROLES
from scripts import run_phase9_benchmarks as runner
from scripts.phase9_common import evidence_directory
from scripts.phase9i_broad import registered_scenarios, scenario_digest, smoke_schedule
from scripts.phase9k_catalogue import estimate
from scripts.phase9k_routing import status_preflight
from tests.phase9k_fixtures import ARCHITECT, BASELINE, FIXER, fake_snapshot
from tests.unit.test_phase9i_broad_report import committed_broad as committed_broad
from tests.unit.test_phase9k_catalogue import usage

pytestmark = pytest.mark.req("PR-01", "FR-A-01", "FR-P-04", "NFR-01")


def test_smoke_keeps_registration_and_exact_scenario_order():
    data, raw, _ = registered_scenarios()
    slots = smoke_schedule(data, scenario_digest(raw))
    assert [s["scenario_id"] for s in slots] == [6, 9, 10]
    assert [s["sequence"] for s in slots] == [1, 2, 3]
    assert {s["scenario_sha256"] for s in slots} == {
        "285bcb48c0d569bf06bd6b06d3a5cef52e28c0970ba6662ddc5380fafb6c288f"
    }
    assert all(
        s["prompt"]
        == next(p["prompt"] for p in data["scenarios"] if p["id"] == s["scenario_id"])
        for s in slots
    )


@pytest.mark.parametrize("mode", ["real", "stub"])
def test_smoke_cli_sets_three_run_cap(monkeypatch, mode):
    import sys

    captured = []

    async def run(args):
        captured.append(args)

    monkeypatch.setattr(runner, "run", run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["benchmark", mode, "--broad", "--broad-smoke", "--budget-usd", "2"],
    )
    runner.main()
    assert captured[0].max_runs == 3
    assert captured[0].runs_per_scenario == 1


@pytest.mark.parametrize("failure", [None, "snapshot", "preference"])
async def test_scripted_experiment_client_rehearsal_is_offline_and_auditable(
    tmp_path, monkeypatch, failure
):
    """Client plumbing fixture, not scanner/LLM quality or deployed infrastructure."""
    path = tmp_path / "snapshot.json"
    snapshot = fake_snapshot(path)
    selections = {
        role: {
            "model": ARCHITECT
            if role == "architect"
            else FIXER
            if role == "fixer"
            else BASELINE + ":nitro",
            "thinking_mode": "medium" if role == "architect" else "low",
            "provider_order": [] if role == "architect" else ["test-fast"],
        }
        for role in ROLES
    }
    output = tmp_path / "rehearsal"
    monkeypatch.setenv("API_KEY", "phase9k-scripted-key-only")
    monkeypatch.setattr(
        runner,
        "evidence_directory",
        lambda name, **kwargs: evidence_directory(
            name, output=output, tools={"scope": "scripted-http-client-only"}, **kwargs
        ),
    )
    monkeypatch.setattr(
        runner, "estimate", lambda s, model, **kwargs: estimate(s, model, usage=usage())
    )
    posts, requests = [], []
    current = [None]

    def reply(request):
        requests.append(str(request.url))
        assert request.url.host == "127.0.0.1"
        if request.url.path.endswith("/settings"):
            return httpx.Response(
                200,
                json=GeneratorSettings.from_settings(get_settings()).model_dump(
                    mode="json"
                ),
            )
        if request.url.path.endswith("/preflight"):
            if failure == "preference":
                return httpx.Response(400, json={"error": "invalid_benchmark_config"})
            assert request.headers["x-api-key"] == "phase9k-scripted-key-only"
            return httpx.Response(
                200, json={"selections": selections, "snapshot": provenance(snapshot)}
            )
        if request.url.path.endswith("/health"):
            return httpx.Response(
                200,
                json={
                    "provider_mirror_present": True,
                    "scanners": {
                        n: {"available": True}
                        for n in ("checkov", "trivy", "terraform")
                    },
                },
            )
        if request.method == "POST":
            posts.append(json.loads(request.content))
            current[0] = str(uuid4())
            return httpx.Response(202, json={"run_id": current[0]})
        if request.url.path.endswith("/results"):
            telemetry = [
                {
                    "kind": "llm",
                    "id": str(uuid4()),
                    "call_id": str(uuid4()),
                    "role": role,
                    "served_by": "Test Backup"
                    if role == "generator_cost"
                    else "Test Fast",
                    "finish_reason": "stop",
                    "elapsed_seconds": 0.001,
                    "reasoning_tokens": 1,
                    "input_tokens": 10,
                    "output_tokens": 10,
                }
                for role in ROLES
            ]
            return httpx.Response(
                200,
                json={
                    "run": {
                        "status": "success",
                        "provider": "stub",
                        "model": "stub",
                        "agent_models": {
                            role: {**s, "provider": "stub", "request_style": "legacy"}
                            for role, s in selections.items()
                        },
                    },
                    "telemetry": telemetry,
                    "plan": {
                        "services": [{"name": "ingress", "aws_service": "alb"}],
                        "network": {
                            "public_services": [],
                            "private_services": ["ingress"],
                        },
                    },
                    "packages": [
                        {
                            "variant": v,
                            "status": "checks_passed",
                            "retry_in_progress": False,
                            "validation_report": {"summary": {"result": "valid"}},
                            "files": {
                                "terraform/main.tf": (
                                    'resource "aws_lb" "app" { internal = true }'
                                )
                            },
                            "original_files": {
                                "terraform/main.tf": (
                                    'resource "aws_lb" "app" { internal = true }'
                                )
                            },
                        }
                        for v in ("cost", "performance", "security")
                    ],
                },
            )
        events = [
            {
                "seq": i,
                "kind": "run_status" if i == 3 else "agent_state",
                "agent": "orchestrator" if i == 3 else "architect",
                "status": status,
                "variant": None,
                "timestamp": f"2026-10-24T00:00:0{i}+00:00",
                "payload": {},
            }
            for i, status in enumerate(("running", "completed", "success"), 1)
        ]
        return httpx.Response(
            200, text="".join("data: " + json.dumps(e) + "\n\n" for e in events)
        )

    def public_reply(request):
        assert request.url.host == "openrouter.ai"
        assert (
            "authorization" not in request.headers
            and "x-api-key" not in request.headers
        )
        return httpx.Response(
            200,
            json={
                "data": {
                    "endpoints": [
                        {"provider_name": "Test Fast", "tag": "test-fast", "status": 0}
                    ]
                }
            },
        )

    async def checked_status(*args, **kwargs):
        return await status_preflight(
            *args, transport=httpx.MockTransport(public_reply), **kwargs
        )

    monkeypatch.setattr(runner, "status_preflight", checked_status)
    original_client = httpx.AsyncClient

    def client(*args, **kwargs):
        kwargs.setdefault("transport", httpx.MockTransport(reply))
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client)
    if failure == "snapshot":
        path.unlink()

    async def execute():
        await runner.run(
            SimpleNamespace(
                mode="stub",
                broad=True,
                broad_smoke=True,
                runs_per_scenario=1,
                smoke=False,
                architect_model=ARCHITECT,
                architect_thinking="medium",
                provider_preference="Test Fast",
                architect_provider_preference=None,
                force=False,
                catalogue_snapshot=path,
                max_runs=3,
                command="suite",
                base_url="http://127.0.0.1:9999",
                timeout=10,
            )
        )

    if failure:
        with pytest.raises(SystemExit) as stopped:
            await execute()
        assert stopped.value.code == 2
        manifest = json.loads((output / "environment.json").read_text())
        data = json.loads((output / "results.json").read_text())
        assert not posts
        assert manifest["explicit_architect_model"] == ARCHITECT
        assert manifest["provider_preferences"]["fixer"] == "Test Fast"
        assert all(r["execution_status"] == "not_started" for r in data["runs"])
        return
    await execute()
    data = json.loads((output / "results.json").read_text())
    manifest = json.loads((output / "environment.json").read_text())
    assert [r["scenario_id"] for r in data["runs"]] == [6, 9, 10]
    assert len(posts) == 3 and all(r["complete"] for r in data["runs"])
    assert all(r["provider_routing"]["any_fallback"] for r in data["runs"])
    assert (
        manifest["explicit_architect_model"] == ARCHITECT
        and manifest["recommendation_advisory"]
    )
    assert manifest["broad_smoke"] and manifest["planned_runs"] == 3
    assert (
        manifest["experiment_cost"]["baseline_runs"] == 10
    )  # explicitly synthetic baseline fixture
    assert len(list((output / "architecture").glob("*/plan.json"))) == 3
    assert len(list((output / "architecture").glob("*/cost.json"))) == 3
    assert all(
        p["config"]["agent_models"]["architect"]["model"] == ARCHITECT for p in posts
    )
    assert all("architect" not in p["config"]["provider_preferences"] for p in posts)
    assert "phase9k-scripted-key-only" not in (output / "environment.json").read_text()


def test_smoke_evidence_loader_verifies_three_registered_slots(
    committed_broad, monkeypatch
):
    from scripts.phase9i_broad_report import load_broad
    from tests.unit.test_phase9i_broad_report import FOLDER

    evidence, _ = committed_broad
    original = evidence.json
    data, raw, _ = registered_scenarios()
    rows = [
        {
            **s,
            "mode": "real",
            "run_id": None,
            "complete": False,
            "execution_status": "not_started",
        }
        for s in smoke_schedule(data, scenario_digest(raw))
    ]

    def changed(path):
        result = original(path)
        if path.endswith("environment.json"):
            result.update(broad_smoke=True, runs_per_scenario=1, planned_runs=3)
        if path.endswith("results.json"):
            result["runs"] = rows
        return result

    monkeypatch.setattr(evidence, "json", changed)
    result = load_broad(evidence, FOLDER)
    assert [r["scenario_id"] for r in result["rows"]] == [6, 9, 10]
    assert result["environment"]["broad_smoke"]
