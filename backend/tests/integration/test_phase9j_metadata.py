"""FR-UI-01 / NFR-01: public configuration metadata and label parity."""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from app.core.config import get_settings
from app.core.model_selection import ModelSelectionService
from app.domain.run_config import RunConfig
from tests.integration.test_phase9g_auth import KEY, authenticated


@pytest.mark.req("FR-UI-01", "NFR-01")
async def test_public_model_metadata_is_configured_and_secret_free(db_engines):
    app, _ = await authenticated(db_engines[0], max_remediation_iterations=7)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        response = await client.get("/api/models")
        assert response.status_code == 200
        body = response.json()
        assert body["server_default_max_iterations"] == 7
        assert body["resolution_context"] == {
            "provider": "stub",
            "model": None,
            "thinking_mode": None,
            "fixer_provider": None,
            "fixer_model": None,
            "fixer_thinking_mode": None,
        }
        from app.domain.enums import LLMProvider

        app.state.settings = app.state.settings.model_copy(
            update={
                "llm_provider": LLMProvider.OPENAI,
                "llm_model": "configured-primary",
                "llm_reasoning_effort": "low",
                "security_fix_provider": LLMProvider.ANTHROPIC,
                "security_fix_model": "configured-fixer",
                "security_fix_reasoning_effort": "high",
            }
        )
        configured = await client.get("/api/models")
        assert configured.status_code == 200
        assert configured.json()["resolution_context"] == {
            "provider": "openai",
            "model": "configured-primary",
            "thinking_mode": "low",
            "fixer_provider": "anthropic",
            "fixer_model": "configured-fixer",
            "fixer_thinking_mode": "high",
        }
        assert KEY not in configured.text and "api_key" not in configured.text
        assert KEY not in response.text
        assert "api_key" not in response.text and "password" not in response.text
        client.headers.clear()
        assert (await client.get("/api/models")).status_code == 401


CASES = json.loads(
    (
        Path(__file__).resolve().parents[3]
        / "frontend/src/test/fixtures/model-defaults.json"
    ).read_text()
)


@pytest.mark.req("FR-P-04", "FR-UI-01")
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
async def test_ui_label_fixtures_match_actual_resolver(case):
    settings = get_settings().model_copy(update=case["settings"])
    service = ModelSelectionService(None, settings, {})
    models = {
        "openai/gpt-oss-120b",
        "google/gemini-3.8-flash:batch",
        "saved",
        "fixed",
        "specific",
        "group",
    }
    service.catalog = AsyncMock(
        return_value={
            "defaults": case["saved"],
            "provider": "openrouter",
            "credential_id": case["credential_id"],
            "models": [
                {
                    "id": model,
                    "structured_output": True,
                    "reasoning": True,
                    "thinking_modes": ["low", "high"],
                }
                for model in models
            ],
        }
    )
    result = await service.resolve(
        RunConfig.model_validate(case["config"]),
        interactive=True,
        personal=case["personal"],
    )
    for role, expected in case["expected"].items():
        actual = result.resolved_agents[role]
        assert {
            "model": actual.model,
            "thinking_mode": actual.thinking_mode,
        } == expected
