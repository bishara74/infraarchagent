"""FR-UI-01 / FR-P-04 / NFR-01: retry and unprobed environment defaults."""

import httpx
import pytest
from pydantic import SecretStr

from app.core.model_selection import ModelSelectionError, ModelSelectionService
from app.domain.enums import LLMProvider
from app.domain.run_config import RunConfig
from tests.integration.test_phase9g_auth import KEY, authenticated
from tests.integration.test_phase9h_credentials import MASTER


@pytest.mark.req("FR-UI-01", "NFR-01")
def test_lifecycle_projection_uses_only_provider_declarations():
    from app.llm.catalog import normalize

    declared = normalize(
        {
            "id": "declared",
            "supported_parameters": ["structured_outputs"],
            "deprecated": True,
            "expiration_date": "2026-01-01",
        },
        "openrouter",
    )
    assert declared["deprecated"] is True
    assert declared["expiration_date"] == "2026-01-01"
    unknown = normalize({"id": "unknown"}, "openrouter")
    assert unknown["structured_output"] is None
    assert unknown["deprecated"] is None and unknown["expiration_date"] is None


@pytest.mark.req("FR-UI-01", "NFR-01")
async def test_failed_catalogues_retry_and_refresh_bypasses_success_cache(db_engines):
    app, _ = await authenticated(db_engines[0])
    app.state.settings = app.state.settings.model_copy(
        update={
            "llm_provider": LLMProvider.OPENAI,
            "llm_model": "configured-model",
            "llm_api_key": SecretStr("synthetic-round2-provider"),
            "llm_base_url": "https://custom.invalid/v1",
        }
    )
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if len(calls) == 1:
            raise httpx.ConnectError("provider-secret-must-not-escape")
        return httpx.Response(200, json={"data": [{"id": "available"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as provider:
        app.state.provider_http = provider
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1",
            headers={"X-API-Key": KEY},
        ) as client:
            failed = await client.get("/api/models")
            assert failed.json()["error_code"] == "network_error"
            assert "provider-secret" not in failed.text
            assert (await client.get("/api/models")).json()["status"] == "ok"
            assert len(calls) == 2
            await client.get("/api/models")
            assert len(calls) == 2
            await client.get("/api/models?refresh=true")
            assert len(calls) == 3
            client.headers.clear()
            assert (await client.get("/api/models?refresh=true")).status_code == 401


@pytest.mark.req("FR-UI-01", "FR-P-04", "NFR-01")
async def test_unknown_environment_fallback_retains_legacy_selection(
    db_engines, monkeypatch
):
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", MASTER)
    app, _ = await authenticated(db_engines[0])
    app.state.settings = app.state.settings.model_copy(
        update={
            "llm_provider": LLMProvider.OPENAI,
            "llm_model": "openai/gpt-oss-120b:nitro",
            "llm_reasoning_effort": "low",
        }
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        identity = (
            await client.post(
                "/api/providers",
                json={"provider": "openrouter", "api_key": "synthetic-round2-key"},
            )
        ).json()["id"]
        await client.post(f"/api/providers/{identity}/default")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"data": [{"id": "openai/gpt-oss-120b:nitro"}]}
            )
        )
    ) as provider:
        service = ModelSelectionService(
            app.state.session_factory, app.state.settings, {}, provider
        )
        legacy = await service.resolve(RunConfig(), interactive=False)
        interactive = await service.resolve(RunConfig(), interactive=True)
        assert interactive.resolved_agents == legacy.resolved_agents
        assert str(interactive.credential_id) == identity
        with pytest.raises(ModelSelectionError):
            await service.resolve(
                RunConfig(
                    agent_models={"fixer": {"model": "openai/gpt-oss-120b:nitro"}}
                ),
                interactive=True,
            )
