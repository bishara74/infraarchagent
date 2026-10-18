"""Retained late packages and failed attempts persist through EventLog and SSE."""

import asyncio
from uuid import UUID

import httpx
import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.domain.package_layout import package_structure_errors
from app.llm.base import LLMResponse
from app.main import create_app
from scripts.benchmark import normalized_event
from scripts.phase9c_metrics import generator_evidence
from tests.integration.test_pipeline_orchestrator import FakeSecurity, FakeValidation


@pytest.mark.req("FR-G-02", "FR-G-06", "FR-G-07", "PR-05", "NFR-01")
@pytest.mark.parametrize("case", ["failure", "late"])
async def test_generator_metrics_persist_without_raw_output(
    db_engines, caplog, monkeypatch, case
):
    settings = get_settings().model_copy(
        update={
            "api_key": None,
            "llm_api_key": None,
            "llm_max_attempts": 1,
        }
    )
    app = create_app(settings, db_engines[0])
    app.state.runner.security_stage = FakeSecurity()
    app.state.runner.validation_stage = FakeValidation()
    factory = app.state.runner.factory
    generators = factory.create_generators()
    cost = generators[0]
    now = [0.0]
    original = cost.llm_adapter.send_prompt

    async def send(prompt, **kwargs):
        if case == "failure":
            return LLMResponse("PRIVATE_INVALID_RESPONSE {bad}", 10, 8000)
        result = await original(prompt, **kwargs)
        # Return inside the 145-second work window; validation below still
        # deliberately overruns the full deadline to test truthful metrics.
        now[0] = 144.0
        return result

    monkeypatch.setattr(cost.llm_adapter, "send_prompt", send)
    if case == "late":
        cost._clock = lambda: now[0]
        cost.llm_adapter._clock = lambda: now[0]

        def validate(files, required):
            if now[0] == 144.0:
                now[0] = 151.0
            return package_structure_errors(files, required)

        monkeypatch.setattr(
            "app.agents.generators.base.package_structure_errors", validate
        )
    monkeypatch.setattr(factory, "create_generators", lambda config: generators)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        accepted = await client.post(
            "/api/pipeline/run",
            json={"text": "Deploy an AWS web service", "config": {"provider": "stub"}},
        )
        run_id = UUID(accepted.json()["run_id"])
        await asyncio.gather(*list(app.state.runner.tasks.values()))
        results = await client.get(f"/api/pipeline/{run_id}/results")
        stream = await client.get(f"/api/pipeline/{run_id}/stream")
    records = await app.state.event_log.list_after(run_id, None)
    events = [
        normalized_event(
            {
                "seq": r.seq,
                "kind": r.payload["kind"],
                "agent": r.agent_name.value,
                "variant": r.payload.get("variant"),
                "status": r.new_state,
                "timestamp": r.timestamp.isoformat(),
                "payload": r.payload,
            }
        )
        for r in records
    ]
    evidence = generator_evidence(events)
    assert evidence["generator_attempt_count"] == 3
    assert len(cost.last_run.attempt_details) == 1
    cost_package = next(
        (p for p in results.json()["packages"] if p["variant"] == "cost"), None
    )
    if case == "late":
        assert cost_package is not None
        assert cost_package["status"] == "production_ready"
        assert evidence["generator_deadlines"]["cost"] == {
            "deadline_exceeded": True,
            "overrun_seconds": 1.0,
            "generator_elapsed_seconds": 151.0,
        }
        assert cost.last_run.attempt_details[-1].deadline_exceeded
    else:
        assert cost_package is None
        assert evidence["failure_categories"] == {"cost": "invalid_response"}
        assert (
            evidence["generator_output_tokens_per_attempt"][0]["output_tokens"] == 8000
        )
    for surface in (results.text, stream.text, caplog.text):
        assert "PRIVATE_INVALID_RESPONSE" not in surface
    async with db_engines[0].connect() as connection:
        for table in ("pipeline_runs", "generated_packages", "agent_events"):
            rows = await connection.scalars(text(f"SELECT t::text FROM {table} t"))
            assert all("PRIVATE_INVALID_RESPONSE" not in row for row in rows)
