"""One-statement results snapshots, persisted plans and generation failures."""

from uuid import uuid4

import httpx
import pytest
from sqlalchemy import event

from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import (
    AgentName,
    AgentState,
    LLMProvider,
    PackageStatus,
    RunStatus,
    Variant,
)
from app.events.kinds import plan_created_payload
from app.main import create_app
from tests.unit.test_generators import plan


@pytest.mark.req("FR-UI-06", "FR-UI-07", "FR-G-07")
async def test_results_one_statement_plan_and_failed_variant(db_engines):
    engine, _ = db_engines
    app = create_app(get_settings(), engine)
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            row = await RunRepository(session).create(
                "Deploy AWS web app", LLMProvider.STUB, 3
            )
            run_id = row.run_id
            for variant in Variant:
                await PackageRepository(session).create(run_id, variant)
            await PackageRepository(session).save_files(
                run_id, Variant.COST, {"terraform/main.tf": "terraform {}"}
            )
    writer = app.state.writer
    await writer.run_transition(run_id, RunStatus.RUNNING, message="started")
    await writer.package_transition(
        run_id, Variant.COST, PackageStatus.GENERATED, message="generated"
    )
    await writer.package_transition(
        run_id,
        Variant.PERFORMANCE,
        PackageStatus.FAILED,
        message="failed",
        error="package generation failed",
    )
    expected_plan = plan()
    await app.state.event_log.append(
        run_id,
        AgentName.ARCHITECT,
        AgentState.COMPLETED,
        payload=plan_created_payload(expected_plan),
    )
    statements = []

    def count(_conn, _cursor, statement, _params, _context, _many):
        statements.append(statement)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        event.listen(engine.sync_engine, "before_cursor_execute", count)
        try:
            response = await client.get(f"/api/pipeline/{run_id}/results")
        finally:
            event.remove(engine.sync_engine, "before_cursor_execute", count)
        assert response.status_code == 200
        assert len(statements) == 1 and statements[0].lstrip().upper().startswith(
            "SELECT"
        )
        data = response.json()
        assert data["plan"] == expected_plan.model_dump(mode="json")
        assert [p["variant"] for p in data["packages"]] == ["cost"]
        assert data["missing_variants"] == [
            {"variant": "performance", "error": "package generation failed"}
        ]
        assert data["run"]["status"] == "running"
        assert set(data) == {"run", "plan", "packages", "missing_variants"}
        assert (
            "ResultsResponse"
            in (await client.get("/openapi.json")).json()["components"]["schemas"]
        )
        assert (await client.get("/api/pipeline/bad/results")).status_code == 400
        assert (await client.get(f"/api/pipeline/{uuid4()}/results")).status_code == 404


@pytest.mark.req("FR-UI-06")
async def test_results_without_plan_or_packages_is_current_snapshot(db_engines):
    engine, _ = db_engines
    app = create_app(get_settings(), engine)
    async with make_session_factory(engine)() as session:
        async with session.begin():
            run = await RunRepository(session).create(
                "Deploy AWS web app", LLMProvider.STUB, 3
            )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        data = (await client.get(f"/api/pipeline/{run.run_id}/results")).json()
    assert data["plan"] is None and data["packages"] == data["missing_variants"] == []
