"""Authenticated settings evidence against real PostgreSQL, never dotenv."""

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import get_settings
from app.core.generator_settings import GeneratorSettings
from app.main import create_app


@pytest.mark.req("NFR-01", "PR-01", "PR-05")
@pytest.mark.parametrize(
    "configured,supplied,expected",
    [
        (False, None, 401),
        (False, "canary-placeholder", 401),
        (True, None, 401),
        (True, "wrong", 401),
        (True, "canary-placeholder", 200),
    ],
)
async def test_settings_require_configured_matching_key(
    db_engines, configured, supplied, expected
):
    settings = get_settings().model_copy(
        update={
            "api_key": SecretStr("canary-placeholder") if configured else None,
            "llm_api_key": SecretStr("canary-placeholder"),
            "generator_max_output_tokens": 12000,
            "generator_attempt_timeout_seconds": 150.0,
            "llm_deadline_seconds": 270.0,
            "generator_deadline_seconds": 270.0,
            "llm_structured_output": "off",
        }
    )
    app = create_app(settings, db_engines[0])
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/benchmark/settings",
            headers={"X-API-Key": supplied} if supplied else {},
        )
        health = await client.get("/api/health")
    assert response.status_code == expected
    assert "generator_settings" not in health.json()
    assert "max_output_tokens" not in health.text
    if expected == 200:
        assert response.json() == GeneratorSettings.from_settings(settings).model_dump()
        assert response.json()["max_output_tokens"] == 12000
    else:
        assert response.json() == {
            "error": "unauthorized",
            "message": "API authentication required.",
        }
        assert "max_output_tokens" not in response.text
    assert "canary-placeholder" not in response.text + health.text
