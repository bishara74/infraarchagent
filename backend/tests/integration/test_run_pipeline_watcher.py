"""CLI watcher uses only the public API with an injectable HTTP transport."""

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import get_settings
from app.domain.enums import LLMProvider
from app.main import create_app
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
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            status, packages = await watch_pipeline(
                "Deploy an AWS web service", client=client, api_url="http://test"
            )
    assert status == "failed"
    assert packages == {
        "cost": "scan_error",
        "performance": "scan_error",
        "security": "scan_error",
    }
    output = capsys.readouterr().out
    assert "Run " in output
    assert "Final: failed" in output
