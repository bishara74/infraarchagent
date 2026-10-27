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
@pytest.mark.req("UC-03")
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
    # Production lifespan checks the schema before serving requests.
    await app.state.schema_gate.refresh()
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
        auth_queries = [s for s in statements if "FROM users" in s]
        result_queries = [s for s in statements if "FROM users" not in s]
        assert len(auth_queries) == 1
        assert len(result_queries) == 1 and result_queries[
            0
        ].lstrip().upper().startswith("SELECT")
        data = response.json()
        assert data["plan"] == expected_plan.model_dump(mode="json")
        assert [p["variant"] for p in data["packages"]] == ["cost"]
        assert data["missing_variants"] == [
            {"variant": "performance", "error": "package generation failed"}
        ]
        assert data["run"]["status"] == "running"
        assert set(data) == {"run", "plan", "packages", "missing_variants", "telemetry"}
        assert data["telemetry"] is None
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


@pytest.mark.req("FR-UI-06", "FR-UI-07", "FR-S-09")
async def test_results_exact_fields_order_and_strict_openapi(db_engines):
    from tests.integration.test_pipeline_review import (
        add_pending_variant,
        client_for,
        pending_app,
    )

    app, run_id = await pending_app(db_engines[0])
    for variant in (Variant.SECURITY, Variant.PERFORMANCE):
        await add_pending_variant(app, run_id, variant)
    async with client_for(app) as client:
        data = (await client.get(f"/api/pipeline/{run_id}/results")).json()
        schema = (await client.get("/openapi.json")).json()
    assert set(data["run"]) == {
        "lessons",
        "id",
        "status",
        "input_text",
        "start_time",
        "end_time",
        "provider",
        "model",
        "max_iterations",
        "error_message",
        "policy_profile",
        "agent_models",
    }
    assert data["run"]["agent_models"] is None
    assert data["run"]["id"] == str(run_id)
    assert data["run"]["start_time"].endswith("Z") and data["run"]["end_time"].endswith(
        "Z"
    )
    assert [row["variant"] for row in data["packages"]] == [
        "cost",
        "performance",
        "security",
    ]
    for row in data["packages"]:
        assert set(row) == {
            "variant",
            "status",
            "iteration_count",
            "error",
            "files",
            "original_files",
            "security_report",
            "validation_report",
            "review_feedback",
            "review_decision",
            "profile_assessments",
        "plan_conflicts",
            "readiness_label",
            "downloadable",
            "review_available",
            "review_actions",
            "retry_in_progress",
            "review_reasons",
            "retry_targets",
        }
    for name in ("ResultsResponse", "RunResult", "PackageResult", "MissingVariant"):
        assert schema["components"]["schemas"][name]["additionalProperties"] is False
    request_schema = schema["paths"][
        "/api/pipeline/{run_id}/packages/{variant}/review"
    ]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert request_schema["additionalProperties"] is False
    assert request_schema["properties"]["target_files"]["maxItems"] == 5
    assert (
        "retry_in_progress"
        in schema["components"]["schemas"]["PackageResult"]["required"]
    )
    assert all(
        row["review_actions"] == ["approve", "retry", "reject"]
        for row in data["packages"]
    )
    assert all(row["retry_in_progress"] is False for row in data["packages"])


@pytest.mark.req("FR-UI-07", "FR-P-04", "FR-S-09")
@pytest.mark.parametrize("settlement", ["success", "abort", "restart"])
async def test_results_retry_marker_covers_intermediate_states_and_settlement(
    db_engines, settlement
):
    from tests.integration.test_pipeline_review import client_for, pending_app

    app, run_id = await pending_app(db_engines[0])
    async with app.state.session_factory() as session:
        async with session.begin():
            await app.state.writer.review_action(
                session, run_id, Variant.COST, "retry", None
            )
    async with client_for(app) as client:
        for target in (
            PackageStatus.SCANNING,
            PackageStatus.SCAN_CLEAN,
            PackageStatus.VALIDATING,
            PackageStatus.INVALID,
        ):
            await app.state.writer.package_transition(
                run_id, Variant.COST, target, message="retry test"
            )
            row = (await client.get(f"/api/pipeline/{run_id}/results")).json()[
                "packages"
            ][0]
            assert row["retry_in_progress"] is True
            assert "review_retry_started_at" not in row
        if settlement == "success":
            await app.state.writer.package_transition(
                run_id, Variant.COST, PackageStatus.PENDING_REVIEW, message="retry test"
            )
        elif settlement == "abort":
            await app.state.writer.abort_review_retry(
                run_id, Variant.COST, reason="review retry failed"
            )
        else:
            async with app.router.lifespan_context(app):
                pass
        row = (await client.get(f"/api/pipeline/{run_id}/results")).json()["packages"][
            0
        ]
        assert row["retry_in_progress"] is False
