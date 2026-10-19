"""FR-P-04 / NFR-01: frozen selections and pre-9h wire compatibility."""

import json
from pathlib import Path

import httpx
import httpx2
import pytest
from pydantic import SecretStr

from app.agents.factory import AgentFactory
from app.core.config import get_settings
from app.core.model_selection import ModelSelectionService
from app.domain.agent_selection import ROLES
from app.domain.enums import LLMProvider, Variant
from app.domain.run_config import RunConfig
from app.llm.catalog import normalize
from app.llm.openai import OpenAIAdapter
from tests.integration.test_phase9g_auth import KEY, authenticated

BASELINE = json.loads(
    (Path(__file__).parents[1] / "fixtures/phase9h-baseline-wire.json").read_text()
)


@pytest.mark.req("NFR-01", "FR-P-04")
@pytest.mark.parametrize("case", BASELINE["cases"])
async def test_header_run_matches_baseline_wire_byte_for_byte(db_engines, case):
    app, _ = await authenticated(db_engines[0])
    settings = app.state.settings.model_copy(
        update={
            "llm_provider": LLMProvider.OPENAI,
            "llm_model": "openai/gpt-oss-120b:nitro",
            "llm_api_key": SecretStr("baseline-test-only"),
            "llm_base_url": "https://openrouter.ai/api/v1",
            "llm_reasoning_effort": case["effort"],
            "security_fix_model": "fixer-test-model",
            "security_fix_reasoning_effort": case["fix_effort"],
            "llm_structured_output": case["structured_output"],
        }
    )
    app.state.settings = settings
    factory = AgentFactory(settings, session_factory=app.state.session_factory)
    captured = []
    app.state.runner.start = lambda run, text, config: captured.append((run, config))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        response = await client.post(
            "/api/pipeline/run",
            json={"text": "Deploy an AWS web service with a database and monitoring."},
        )
        assert response.status_code == 202
        run, config = captured[0]
        results = (await client.get(f"/api/pipeline/{run}/results")).json()
        assert set(results["run"]["agent_models"]) == set(ROLES)
        assert config.resolved_agents["fixer"].model == "fixer-test-model"
    adapters = {"architect": factory.create_architect(config).llm_adapter}
    adapters.update(
        {
            "generator_" + v.value: factory.create_generator(v, config).llm_adapter
            for v in Variant
        }
    )
    adapters["fixer"] = factory.create_security_agent(config).fix_agent.adapter
    for role, adapter in adapters.items():
        actual = []

        def handler(request, actual=actual, adapter=adapter):
            body = json.loads(request.content)
            actual.append(
                {
                    k: body[k]
                    for k in ("model", "reasoning", "response_format", "provider")
                    if k in body
                }
            )
            return httpx2.Response(
                200,
                json={
                    "id": "baseline",
                    "object": "chat.completion",
                    "created": 1,
                    "model": adapter.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "{}"},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )

        await adapter.client.close()
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(handler)
        ) as transport:
            adapter.client = OpenAIAdapter(
                adapter.model,
                adapter.policy,
                "baseline-test-only",
                base_url=settings.llm_base_url,
                http_client=transport,
            ).client
            adapter._structured_request.set(role != "architect")
            await adapter.send_prompt("baseline", max_output_tokens=100, timeout=1)
        # Baseline serialization includes complete schemas and omitted fields.
        assert (
            json.dumps(actual[0], separators=(",", ":")).encode()
            == json.dumps(case["parameters"][role], separators=(",", ":")).encode()
        )


@pytest.mark.req("FR-P-04")
async def test_offline_catalog_capabilities_and_selections(db_engines):
    app, _ = await authenticated(db_engines[0])
    service = ModelSelectionService(app.state.session_factory, get_settings(), {})
    assert (await service.catalog())["models"][0]["id"] == "stub"
    config = await service.resolve(
        RunConfig(agent_models={"generators": {"model": "stub"}}), interactive=False
    )
    assert set(config.resolved_agents) == set(ROLES)
    for choice in ({"model": "unknown"}, {"model": "stub", "thinking_mode": "high"}):
        with pytest.raises(ValueError):
            await service.resolve(
                RunConfig(agent_models={"generators": choice}), interactive=False
            )
    unknown = normalize({"id": "unknown"}, "custom")
    assert unknown["structured_output"] is None and unknown["thinking_modes"] == []
    declared = normalize(
        {
            "id": "manual",
            "capabilities": {
                "structured_output": True,
                "reasoning": True,
                "thinking_modes": ["low"],
            },
        },
        "custom",
    )
    assert declared["source"] == "admin" and declared["thinking_modes"] == ["low"]


@pytest.mark.req("NFR-01", "FR-P-04")
async def test_saved_offline_catalog_defaults_rejection_and_revocation(
    db_engines, monkeypatch
):
    from tests.integration.test_phase9h_credentials import MASTER

    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", MASTER)
    app, _ = await authenticated(db_engines[0])
    app.state.provider_http = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: pytest.fail("Offline catalog must not use HTTP")
        )
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        saved = await client.post(
            "/api/providers",
            json={
                "provider": "custom",
                "base_url": "https://custom.invalid/v1",
                "api_key": "offline-key-canary",
            },
        )
        identity = saved.json()["id"]
        await client.post(f"/api/providers/{identity}/default")
        defaults = {
            "architect": {"model": "manual", "thinking_mode": "low"},
            "generators": {"model": "manual", "thinking_mode": "low"},
            "fixer": {"model": "manual", "thinking_mode": "low"},
        }
        body = {
            "defaults": defaults,
            "static_models": [
                {
                    "credential_id": identity,
                    "id": "manual",
                    "capabilities": {
                        "structured_output": True,
                        "reasoning": True,
                        "thinking_modes": ["low"],
                    },
                }
            ],
        }
        assert (await client.put("/api/models/defaults", json=body)).status_code == 200
        catalog = (await client.get("/api/models")).json()
        assert (
            catalog["status"] == "offline" and catalog["models"][0]["source"] == "admin"
        )
        service = ModelSelectionService(
            app.state.session_factory, app.state.settings, {}, app.state.provider_http
        )
        resolved = await service.resolve(RunConfig(), interactive=True)
        assert len(resolved.resolved_agents) == 5 and resolved.credential_id is not None
        with pytest.raises(ValueError):
            await service.resolve(
                RunConfig(
                    agent_models={"fixer": {"model": "manual", "thinking_mode": "high"}}
                ),
                interactive=True,
            )
        bad = {**body, "static_models": [{"id": "manual", "api_key": "must-not-store"}]}
        assert (await client.put("/api/models/defaults", json=bad)).status_code == 400
        await client.post(f"/api/providers/{identity}/revoke")
        assert (await client.get("/api/models")).status_code == 409
    await app.state.provider_http.aclose()
