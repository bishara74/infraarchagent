import asyncio
import logging
from uuid import UUID

import httpx
import httpx2
import pytest
from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.agents.architect import ArchitectLLMFailure
from app.agents.generators.base import GeneratorLLMFailure
from app.core.config import Settings, get_settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import AgentName, AgentState, LLMProvider, Variant
from app.llm.anthropic import AnthropicAdapter
from app.llm.base import RetryPolicy
from app.llm.errors import LLMPermanentError
from app.llm.openai import OpenAIAdapter
from app.main import create_app


@pytest.mark.req("NFR-01")
async def test_secret_canary_stays_out_of_http_logs_and_database(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    db_session: AsyncSession,
    canary_key: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app_engine, _ = db_engines
    key = canary_key.require_llm_key()
    app = create_app(canary_key, app_engine)
    app.dependency_overrides[get_settings] = lambda: canary_key

    def fail(request: Request) -> None:
        raise RuntimeError(f"failure with {key}")

    app.add_api_route("/forced-error", fail)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        health = await client.get("/api/health")
        failure = await client.get("/forced-error")

    logging.getLogger("canary").warning("settings: %s", canary_key)
    run = await RunRepository(db_session).create("AWS web app", LLMProvider.STUB, 3)
    await PackageRepository(db_session).create(run.run_id, Variant.COST)
    await db_session.commit()
    event = await app.state.event_log.append(
        run.run_id,
        AgentName.ORCHESTRATOR,
        AgentState.RUNNING,
        payload={"stage": "started"},
    )
    assert isinstance(event.event_id, UUID)

    assert health.status_code == 200 and health.json()["llm_configured"] is True
    assert failure.status_code == 500
    for surface in (health.text, failure.text, caplog.text, repr(canary_key)):
        assert key not in surface
    async with app_engine.connect() as connection:
        for table in ("pipeline_runs", "generated_packages", "agent_events"):
            rows = await connection.scalars(text(f"SELECT t::text FROM {table} t"))
            assert all(key not in row for row in rows)


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
async def test_provider_error_does_not_expose_canary(
    provider: str,
    canary_key: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    key = canary_key.require_llm_key()
    caplog.set_level(logging.INFO)

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            401,
            headers={"x-canary": key},
            json={"error": {"type": "authentication_error", "message": key}},
        )

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        policy = RetryPolicy(1, 3, 5, 0, 100)
        adapter = (
            AnthropicAdapter("model", policy, key, http_client=client)
            if provider == "anthropic"
            else OpenAIAdapter("model", policy, key, http_client=client)
        )
        with pytest.raises(LLMPermanentError) as captured:
            await adapter.complete_json("prompt")
    assert key not in str(captured.value)
    assert key not in repr(captured.value)
    assert key not in caplog.text
    wrapped = ArchitectLLMFailure(captured.value.category)
    assert key not in wrapped.message
    assert key not in repr(wrapped)
    generator_error = GeneratorLLMFailure(Variant.SECURITY, captured.value.category)
    assert key not in str(generator_error)
    assert key not in repr(generator_error)
    assert key not in caplog.text


@pytest.mark.req("NFR-01", "FR-P-03")
async def test_pipeline_unexpected_error_redacts_canary_everywhere(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    canary_key: Settings,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, _ = db_engines
    key = canary_key.require_llm_key()
    app = create_app(canary_key, engine)

    class BombArchitect:
        def parse_input(self, text: str) -> None:
            return None

        async def generate_plan(self) -> None:
            raise RuntimeError(key)

    monkeypatch.setattr(
        app.state.runner.factory, "create_architect", lambda config: BombArchitect()
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/pipeline/run", json={"text": "Deploy an AWS web service"}
            )
            assert response.status_code == 202
            await asyncio.gather(*app.state.runner.tasks.values())
            stream = await client.get(response.json()["stream_url"])
    run_id = UUID(response.json()["run_id"])
    async with make_session_factory(engine)() as session:
        row = await RunRepository(session).get(run_id)
    assert row is not None and row.error_message == "internal error; see server logs"
    assert key not in stream.text
    assert key not in caplog.text
