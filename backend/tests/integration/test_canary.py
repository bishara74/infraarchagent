import logging
from uuid import UUID

import httpx
import pytest
from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import Settings, get_settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import AgentName, AgentState, LLMProvider, Variant
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
