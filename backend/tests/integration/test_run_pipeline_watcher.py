"""CLI watcher uses only the public API with an injectable HTTP transport."""

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import get_settings
from app.domain.enums import LLMProvider
from app.main import create_app
from app.scanners.runner import RecordedToolRunner, ToolResult
from app.scanners.scan import Scanner
from scripts.run_pipeline import watch_pipeline


@pytest.mark.req("FR-P-04")
async def test_watcher_prints_terminal_summary_offline(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    capsys: pytest.CaptureFixture[str],
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
                * 3,
                "trivy": [ToolResult('{"Results":[]}', "", 0, 0)] * 3,
                "terraform": [ToolResult('{"diagnostics":[]}', "", 0, 0)] * 3,
            }
        )
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            status, packages = await watch_pipeline(
                "Deploy an AWS web service", client=client, api_url="http://test"
            )
    assert status == "partial_success"
    assert packages == {
        "cost": "pending_review",
        "performance": "pending_review",
        "security": "pending_review",
    }
    output = capsys.readouterr().out
    assert "Run " in output
    assert "Final: partial_success" in output
