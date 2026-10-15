"""NFR-01 optional shared API authentication and protected output surfaces."""

import asyncio
import io
import logging
import zipfile

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text

from app.core.config import ROOT
from app.main import create_app
from tests.integration.test_pipeline_review import (
    client_for,
    install_retry,
    pending_app,
    review_url,
    state,
)

API_CANARY = "phase7-api-canary-9bc654"
LLM_CANARY = "phase7-llm-canary-5abd93"


async def authenticated_app(engine, frontend_dist=None):
    seeded, run_id = await pending_app(engine)
    settings = seeded.state.settings.model_copy(
        update={"api_key": SecretStr(API_CANARY), "llm_api_key": SecretStr(LLM_CANARY)}
    )
    return create_app(settings, engine, frontend_dist=frontend_dist), run_id


@pytest.mark.req("NFR-01", "FR-UI-06", "FR-S-08", "FR-P-04")
async def test_every_pipeline_route_requires_header_but_health_is_open(db_engines):
    app, run_id = await authenticated_app(db_engines[0])
    routes = [
        ("POST", "/api/pipeline/run", {"text": "Deploy AWS web app"}),
        ("GET", f"/api/pipeline/{run_id}/results", None),
        ("POST", review_url(run_id), {"action": "approve"}),
        ("GET", f"/api/pipeline/{run_id}/download/cost", None),
        ("GET", f"/api/pipeline/{run_id}/stream", None),
    ]
    async with client_for(app) as client:
        assert (await client.get("/api/health")).status_code == 200
        for method, url, body in routes:
            responses = [
                await client.request(method, url, json=body, headers=headers)
                for headers in ({}, {"X-API-Key": "wrong"})
            ]
            query = await client.request(
                method, url, json=body, params={"api_key": API_CANARY}
            )
            assert all(response.status_code == 401 for response in [*responses, query])
            assert responses[0].json() == responses[1].json() == query.json()
            assert set(query.json()) == {"error", "message"}
        headers = {"X-API-Key": API_CANARY}
        assert (await client.get(routes[1][1], headers=headers)).status_code == 200
        assert (
            await client.post(
                review_url(run_id), json={"action": "approve"}, headers=headers
            )
        ).status_code == 200
        assert (await client.get(routes[3][1], headers=headers)).status_code == 200
        assert (await client.get(routes[4][1], headers=headers)).status_code == 200
        # Submission only needs to reach its handler; avoid running another pipeline.
        assert app.state.runner.reserve()
        while app.state.runner.reserve():
            pass
        assert (
            await client.post(routes[0][1], json=routes[0][2], headers=headers)
        ).status_code == 429
        while app.state.runner._reserved:
            app.state.runner.release()


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("configured", [False, True])
async def test_one_unset_key_warning_at_startup(db_engines, caplog, configured):
    app, _ = await pending_app(db_engines[0])
    settings = app.state.settings.model_copy(
        update={"api_key": SecretStr(API_CANARY) if configured else None}
    )
    app = create_app(settings, db_engines[0])
    caplog.clear()
    async with app.router.lifespan_context(app):
        warnings = [
            record for record in caplog.records if "API_KEY is unset" in record.message
        ]
        assert len(warnings) == (0 if configured else 1)


@pytest.mark.req("NFR-01", "FR-S-09", "FR-UI-06")
async def test_both_canaries_and_backend_paths_are_absent_from_new_surfaces(
    db_engines, monkeypatch, caplog
):
    app, run_id = await authenticated_app(db_engines[0])
    install_retry(app, monkeypatch)
    headers = {"X-API-Key": API_CANARY}
    feedback = f"Repair {API_CANARY} {LLM_CANARY} {ROOT}/backend/private.py"
    async with client_for(app) as client:
        retry = await client.post(
            review_url(run_id),
            json={"action": "retry", "feedback": feedback},
            headers=headers,
        )
        assert retry.status_code == 202
        await asyncio.gather(*app.state.runner.tasks.values())
        results = await client.get(f"/api/pipeline/{run_id}/results", headers=headers)
        stream = await client.get(f"/api/pipeline/{run_id}/stream", headers=headers)
        download = await client.get(
            f"/api/pipeline/{run_id}/download/cost", headers=headers
        )
    assert download.status_code == 200
    with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
        contents = "\n".join(archive.read(name).decode() for name in archive.namelist())
    _, package = await state(app, run_id)
    assert "[REDACTED]" in package.review_feedback
    async with app.state.engine.connect() as connection:
        rows = []
        for table in ("pipeline_runs", "generated_packages", "agent_events"):
            rows.extend(
                await connection.scalars(text(f"SELECT t::text FROM {table} t"))
            )
    for surface in (
        retry.text,
        results.text,
        stream.text,
        contents,
        caplog.text,
        *rows,
    ):
        assert API_CANARY not in surface and LLM_CANARY not in surface
        assert str(ROOT) not in surface


@pytest.mark.req("NFR-01")
async def test_unexpected_error_keeps_redacted_operator_traceback(
    db_engines, caplog, tmp_path
):
    app, _ = await authenticated_app(db_engines[0], frontend_dist=tmp_path / "missing")

    def fail():
        raise RuntimeError(f"{API_CANARY} {LLM_CANARY} {ROOT}/backend/private.py")

    app.add_api_route("/forced-error", fail)
    caplog.set_level(logging.ERROR)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/forced-error")
    assert response.json() == {
        "error": "internal_error",
        "message": "An unexpected error occurred.",
    }
    assert "Traceback (most recent call last)" in caplog.text
    assert "RuntimeError" in caplog.text and str(ROOT) in caplog.text
    assert API_CANARY not in caplog.text and LLM_CANARY not in caplog.text


@pytest.mark.req("NFR-01", "FR-V-04")
async def test_reports_and_events_are_sanitized_before_insert(db_engines, monkeypatch):
    from app.agents.validator import ValidatorAgent
    from app.domain.enums import AgentName, AgentState
    from app.domain.validation import ValidationCheck, ValidationReport

    app, run_id = await authenticated_app(db_engines[0])
    install_retry(app, monkeypatch)
    diagnostic = f"{API_CANARY} {LLM_CANARY} {ROOT}/backend/private.py"

    class Engine:
        async def validate(self, plan, files):
            return ValidationReport.build(
                [
                    ValidationCheck(
                        check_id="reference.test",
                        category="reference",
                        tool="builtin",
                        status="failed",
                        file_path="terraform/main.tf",
                        message=diagnostic,
                    ),
                    ValidationCheck(
                        check_id="reference.test",
                        category="reference",
                        tool="builtin",
                        status="failed",
                        file_path="terraform/main.tf",
                        message="aaaa reference",
                    ),
                ],
                terraform_required=False,
            )

    app.state.runner.validation_stage = ValidatorAgent(
        Engine(), app.state.session_factory, settings=app.state.settings
    )
    event = await app.state.event_log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        AgentState.RUNNING,
        message=diagnostic,
        payload={"diagnostic": diagnostic},
    )
    assert "[REDACTED]" in event.message
    async with client_for(app) as client:
        response = await client.post(
            review_url(run_id),
            json={"action": "retry"},
            headers={"X-API-Key": API_CANARY},
        )
    assert response.status_code == 202
    await asyncio.gather(*app.state.runner.tasks.values())
    _, row = await state(app, run_id)
    assert row.status == "pending_review"
    assert "[REDACTED]" in row.validation_report["checks"][0]["message"]
    async with app.state.engine.connect() as connection:
        for table in ("generated_packages", "agent_events"):
            rows = await connection.scalars(text(f"SELECT t::text FROM {table} t"))
            assert all(
                API_CANARY not in value
                and LLM_CANARY not in value
                and str(ROOT) not in value
                for value in rows
            )


@pytest.mark.req("NFR-01", "FR-P-04")
async def test_correct_header_allows_submission_and_sanitizes_input(
    db_engines, monkeypatch
):
    from app.agents.validator import ValidatorAgent
    from tests.integration.test_pipeline_review import validation_report
    from tests.integration.test_security_agent import ScriptedScanner

    app, _ = await authenticated_app(db_engines[0])
    app.state.runner.factory.scanner = ScriptedScanner([[], [], [], [], [], []])

    class Engine:
        async def validate(self, plan, files):
            return validation_report("valid")

    app.state.runner.validation_stage = ValidatorAgent(
        Engine(), app.state.session_factory, settings=app.state.settings
    )
    async with client_for(app) as client:
        response = await client.post(
            "/api/pipeline/run",
            json={"text": f"Deploy AWS web app {API_CANARY} {LLM_CANARY}"},
            headers={"X-API-Key": API_CANARY},
        )
        assert response.status_code == 202
        await asyncio.gather(*app.state.runner.tasks.values())
        data = (
            await client.get(
                f"/api/pipeline/{response.json()['run_id']}/results",
                headers={"X-API-Key": API_CANARY},
            )
        ).json()
    assert "[REDACTED]" in data["run"]["input_text"]
    assert API_CANARY not in str(data) and LLM_CANARY not in str(data)
