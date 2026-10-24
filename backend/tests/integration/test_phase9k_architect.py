"""FR-A-01, FR-P-04, NFR-01: benchmark Architect isolation at the HTTP wire."""

import json
from unittest.mock import AsyncMock

import httpx
import httpx2
import pytest
from pydantic import SecretStr

from app.agents.factory import AgentFactory
from app.db.repositories.providers import ProviderRepository
from app.domain.agent_selection import ROLES
from app.domain.enums import LLMProvider, Variant
from tests.integration.test_phase9g_auth import KEY, authenticated
from tests.phase9k_fixtures import fake_snapshot

pytestmark = pytest.mark.req("FR-A-01", "FR-P-04", "NFR-01")
MODEL = "test-only/architect-2099"


@pytest.mark.parametrize("thinking", [None, "medium"])
async def test_header_architect_override_preserves_sibling_http_bytes(
    db_engines, monkeypatch, thinking, tmp_path
):
    app, _ = await authenticated(db_engines[0])
    snapshot_path = tmp_path / "catalogue.json"
    fake_snapshot(snapshot_path)
    settings = app.state.settings.model_copy(
        update={
            "openrouter_catalogue_snapshot": snapshot_path,
            "llm_provider": LLMProvider.OPENAI,
            "llm_model": "test-only/baseline:nitro",
            "llm_api_key": SecretStr("synthetic-environment-canary"),
            "llm_base_url": "https://openrouter.ai/api/v1",
            "llm_reasoning_effort": "low",
            "security_fix_model": "test-only/fixer",
            "security_fix_reasoning_effort": "high",
            "llm_response_format": "json_object",
        }
    )
    app.state.settings = settings
    captured = []
    app.state.runner.start = lambda run, text, config: captured.append((run, config))
    # Shared-key resolution must never load browser settings or saved credentials.
    forbidden = AsyncMock(side_effect=AssertionError("Browser repository accessed"))
    monkeypatch.setattr(ProviderRepository, "settings", forbidden)
    monkeypatch.setattr(ProviderRepository, "material", forbidden)

    def metadata(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": MODEL,
                            "supported_parameters": ["reasoning", "response_format"],
                        }
                    ]
                },
            )
        return httpx.Response(200, json={"data": {"usage": 0}})

    app.state.provider_http = httpx.AsyncClient(transport=httpx.MockTransport(metadata))
    wires = []
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        for config in (
            {},
            {
                "agent_models": {
                    "architect": {"model": MODEL, "thinking_mode": thinking}
                }
            },
        ):
            response = await client.post(
                "/api/pipeline/run",
                json={
                    "text": "Deploy an AWS web service with a private database.",
                    "config": config,
                },
            )
            assert response.status_code == 202, response.text
            run, resolved = captured[-1]
            assert resolved.credential_id is None
            assert (
                len(
                    (await client.get(f"/api/pipeline/{run}/results")).json()["run"][
                        "agent_models"
                    ]
                )
                == 5
            )
            factory = AgentFactory(settings, session_factory=app.state.session_factory)
            adapters = {
                "architect": factory.create_architect(resolved).llm_adapter,
                **{
                    "generator_" + v.value: factory.create_generator(
                        v, resolved
                    ).llm_adapter
                    for v in Variant
                },
                "fixer": factory.create_security_agent(resolved).fix_agent.adapter,
            }
            requests = {}
            for role, adapter in adapters.items():

                def completion(request, role=role, requests=requests):
                    requests[role] = (
                        str(request.url),
                        request.method,
                        request.headers["authorization"],
                        request.content,
                    )
                    return httpx2.Response(
                        200,
                        json={
                            "id": "fake",
                            "object": "chat.completion",
                            "created": 1,
                            "model": "fake",
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
                adapter.client = __import__("openai").AsyncOpenAI(
                    api_key="synthetic-environment-canary",
                    base_url=settings.llm_base_url,
                    http_client=httpx2.AsyncClient(
                        transport=httpx2.MockTransport(completion)
                    ),
                )
                adapter._structured_request.set(role != "architect")
                await adapter.send_prompt(
                    "fixed prompt",
                    system="fixed system",
                    max_output_tokens=100,
                    timeout=1,
                )
                await adapter.client.close()
            wires.append(requests)
    await app.state.provider_http.aclose()
    forbidden.assert_not_awaited()
    for role in ROLES[1:]:
        assert wires[0][role] == wires[1][role]
    architect = json.loads(wires[1]["architect"][3])
    assert architect["model"] == MODEL
    assert architect["response_format"] == {"type": "json_object"}
    assert architect.get("reasoning") == ({"effort": thinking} if thinking else None)
    assert wires[0]["architect"] != wires[1]["architect"]
