# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""CLI watcher uses only the public API with an injectable HTTP transport."""

import asyncio

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.agents.validator import ValidatorAgent
from app.core.config import get_settings
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider
from app.main import create_app
from app.scanners.runner import RecordedToolRunner, ToolResult
from app.scanners.scan import Scanner
from app.validation.engine import ValidationEngine
from scripts.run_pipeline import watch_pipeline
from tests.unit.test_validation_engine import Clean, mirror


@pytest.mark.req("FR-P-04")
async def test_watcher_prints_terminal_summary_offline(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    engine, _ = db_engines
    settings = get_settings().model_copy(
        update={"llm_provider": LLMProvider.STUB, "llm_model": None}
    )
    app = create_app(settings, engine)
    app.state.runner.factory.scanner = Scanner(
        RecordedToolRunner(
            {
                "checkov": [
                    ToolResult('{"passed":0,"failed":0,"resource_count":0}', "", 0, 0)
                ]
                * 6,
                "trivy": [ToolResult('{"Results":[]}', "", 0, 0)] * 6,
                "terraform": [ToolResult('{"diagnostics":[]}', "", 0, 0)] * 6,
            }
        )
    )
    app.state.runner.validation_stage = ValidatorAgent(
        ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={}),
        make_session_factory(engine),
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            status, packages = await watch_pipeline(
                "Deploy an AWS web service", client=client, api_url="http://test"
            )
    assert status == "success"
    assert packages == {
        "cost": "checks_passed",
        "performance": "checks_passed",
        "security": "checks_passed",
    }
    output = capsys.readouterr().out
    assert "Run " in output
    assert "Final: success" in output


@pytest.mark.req("FR-P-04")
async def test_watcher_stops_after_cancelled_event(capsys):
    requests = []

    def response(request):
        requests.append(request.method)
        if request.method == "POST":
            return httpx.Response(
                202, json={"run_id": "run", "stream_url": "/api/pipeline/run/stream"}
            )
        return httpx.Response(
            200,
            text='id: 1\nevent: run_status\ndata: {"seq":1,"kind":"run_status",'
            '"agent":"orchestrator","status":"cancelled"}\n\n',
        )

    async with (
        asyncio.timeout(2),
        httpx.AsyncClient(transport=httpx.MockTransport(response)) as client,
    ):
        assert await watch_pipeline("Deploy an AWS web service", client=client) == (
            "cancelled",
            {},
        )
    assert requests == ["POST", "GET"]
    assert "Final: cancelled" in capsys.readouterr().out


@pytest.mark.req("NFR-01", "FR-P-04")
async def test_watcher_main_sets_environment_header_without_printing_key(
    monkeypatch, capsys
):
    from scripts import run_pipeline

    key = "phase7-watcher-canary"
    monkeypatch.setenv("PIPELINE_TEXT", "Deploy AWS web app")
    monkeypatch.setenv("API_KEY", key)
    observed = {}

    class Client:
        def __init__(self, **kwargs):
            observed.update(kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    async def watch(text, **kwargs):
        assert text == "Deploy AWS web app"
        assert isinstance(kwargs["client"], Client)

    monkeypatch.setattr(run_pipeline.httpx, "AsyncClient", Client)
    monkeypatch.setattr(run_pipeline, "watch_pipeline", watch)
    await run_pipeline.main()
    assert observed["headers"] == {"X-API-Key": key}
    assert key not in capsys.readouterr().out
