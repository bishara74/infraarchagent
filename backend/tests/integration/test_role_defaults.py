"""FR-UI-01 / FR-P-04: independent role defaults from controls to request wire."""

import itertools
import json
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import httpx2
import openai
import pytest
from pydantic import SecretStr

from app.agents.factory import AgentFactory
from app.core.config import get_settings
from app.core.model_selection import ModelSelectionError, ModelSelectionService
from app.domain.agent_selection import ROLES
from app.domain.enums import LLMProvider, Variant
from app.domain.run_config import RunConfig
from tests.integration.test_phase9g_auth import ORIGIN, authenticated
from tests.integration.test_phase9h_accounts import PASSWORD
from tests.integration.test_phase9h_credentials import MASTER

MATRIX = json.loads(
    (
        Path(__file__).parents[3] / "frontend/src/test/fixtures/model-tiers.json"
    ).read_text()
)
ENVIRONMENT = "openai/gpt-oss-120b:nitro"
ARCHITECT = "anthropic/claude-opus-4.5"


def settings_for_roles(**updates):
    return get_settings().model_copy(
        update={
            "llm_provider": LLMProvider.OPENAI,
            "llm_model": ENVIRONMENT,
            "llm_reasoning_effort": "low",
            "llm_api_key": SecretStr("role-defaults-synthetic-key"),
            "llm_base_url": "https://openrouter.ai/api/v1",
            "security_fix_provider": None,
            "security_fix_model": None,
            "security_fix_reasoning_effort": None,
            **updates,
        }
    )


def catalog_for(defaults=None, credential=True):
    names = {"environment", "openai/gpt-oss-120b", ARCHITECT, "separate-fixer"}
    for case in MATRIX:
        for tier in case["layers"].values():
            names.update(choice["model"] for choice in tier.values())
    return {
        "provider": "openrouter",
        "credential_id": "00000000-0000-0000-0000-000000000001" if credential else None,
        "defaults": defaults or {},
        "models": [
            {
                "id": name,
                "structured_output": True,
                "reasoning": True,
                "thinking_modes": ["off", "low", "high"],
            }
            for name in names
        ],
    }


@pytest.mark.req("FR-UI-01", "FR-P-04")
@pytest.mark.parametrize("case", MATRIX, ids=lambda case: case["name"])
@pytest.mark.parametrize("role", ROLES[1:4])
async def test_all_generator_tier_and_specificity_combinations(case, role):
    service = ModelSelectionService(
        None, settings_for_roles(llm_model="environment"), {}
    )
    service.catalog = AsyncMock(return_value=catalog_for(case["layers"]["admin"]))
    result = await service.resolve(
        RunConfig(agent_models=case["layers"]["run"]),
        interactive=True,
        personal=case["layers"]["personal"],
    )
    selection = result.resolved_agents[role]
    assert {"model": selection.model, "thinking_mode": selection.thinking_mode} == case[
        "expected"
    ][role]


@pytest.mark.req("FR-P-04", "FR-UI-01")
@pytest.mark.parametrize(
    "credential,fixer",
    tuple(itertools.product((False, True), (None, "separate-fixer"))),
)
@pytest.mark.parametrize("tier", ("run", "personal", "admin"))
async def test_architect_choice_is_isolated_at_every_tier(credential, fixer, tier):
    service = ModelSelectionService(
        None, settings_for_roles(security_fix_model=fixer), {}
    )
    service.catalog = AsyncMock(return_value=catalog_for(credential=credential))
    baseline = await service.resolve(RunConfig(), interactive=True)
    choices = {"architect": {"model": ARCHITECT, "thinking_mode": None}}
    if tier == "admin":
        service.catalog.return_value["defaults"] = choices
    actual = await service.resolve(
        RunConfig(agent_models=choices if tier == "run" else {}),
        interactive=True,
        personal=choices if tier == "personal" else None,
    )
    assert actual.resolved_agents["architect"].model == ARCHITECT
    assert actual.resolved_agents["architect"].thinking_mode is None
    for role in ROLES[1:]:
        assert actual.resolved_agents[role] == baseline.resolved_agents[role]


@pytest.mark.req("FR-P-04", "FR-UI-01")
async def test_unconfigured_role_cannot_borrow_architect_but_all_explicit_roles_work():
    service = ModelSelectionService(None, settings_for_roles(llm_model=None), {})
    service.catalog = AsyncMock(return_value=catalog_for())
    with pytest.raises(ModelSelectionError, match="Choose a model for Cost Generator"):
        await service.resolve(
            RunConfig(agent_models={"architect": {"model": ARCHITECT}}),
            interactive=True,
        )
    result = await service.resolve(
        RunConfig(agent_models={role: {"model": ARCHITECT} for role in ROLES}),
        interactive=True,
    )
    assert all(value.model == ARCHITECT for value in result.resolved_agents.values())


@pytest.mark.req("FR-P-04", "FR-UI-01", "NFR-01")
@pytest.mark.parametrize("fixer", (None, "separate-fixer"))
async def test_account_submission_persistence_and_architect_only_wire_isolation(
    db_engines, monkeypatch, fixer
):
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", MASTER)
    app, _ = await authenticated(db_engines[0])
    settings = settings_for_roles(security_fix_model=fixer)
    app.state.settings = app.state.auth.settings = settings
    captured = []
    app.state.runner.start = lambda run, text, config: captured.append((run, config))
    factory = AgentFactory(settings, session_factory=app.state.session_factory)
    bodies = []

    def completion(request):
        body = json.loads(request.content)
        bodies.append(
            (
                str(request.url),
                request.method,
                request.headers["authorization"],
                request.content,
            )
        )
        return httpx2.Response(
            200,
            json={
                "id": "mock",
                "object": "chat.completion",
                "created": 1,
                "model": body["model"],
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "{}"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    original = openai.AsyncOpenAI

    def mocked_openai(*args, **kwargs):
        kwargs["http_client"] = httpx2.AsyncClient(
            transport=httpx2.MockTransport(completion)
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(openai, "AsyncOpenAI", mocked_openai)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=("127.0.0.1", 1)),
        base_url="http://127.0.0.1",
    ) as client:
        setup = await client.post(
            "/api/auth/setup",
            json={"username": "RoleTester", "password": PASSWORD},
            headers=ORIGIN,
        )
        assert setup.status_code == 200
        created = await client.post(
            "/api/providers",
            headers=ORIGIN,
            json={
                "provider": "openrouter",
                "api_key": "role-defaults-saved-synthetic-key",
            },
        )
        identity = created.json()["id"]
        assert (
            await client.post(f"/api/providers/{identity}/default", headers=ORIGIN)
        ).status_code == 200
        declarations = [
            {
                "id": model,
                "credential_id": identity,
                "capabilities": {
                    "structured_output": True,
                    "reasoning": True,
                    "thinking_modes": ["low", "high"],
                },
            }
            for model in ("openai/gpt-oss-120b", ARCHITECT, "separate-fixer")
        ]
        assert (
            await client.put(
                "/api/models/defaults",
                headers=ORIGIN,
                json={"defaults": {}, "static_models": declarations},
            )
        ).status_code == 200
        wires = []
        for overrides in ({}, {"architect": {"model": ARCHITECT}}):
            response = await client.post(
                "/api/pipeline/run",
                headers=ORIGIN,
                json={
                    "text": "Deploy an AWS web service with a database and monitoring.",
                    "config": {"agent_models": overrides},
                },
            )
            assert response.status_code == 202, response.text
            run, config = captured[-1]
            assert set(config.agent_models) == set(overrides)
            assert set(config.resolved_agents) == set(ROLES)
            reported = (await client.get(f"/api/pipeline/{run}/results")).json()["run"][
                "agent_models"
            ]
            for role, selection in config.resolved_agents.items():
                assert reported[role]["model"] == selection.model
                assert (
                    reported[role]["configured_thinking"]
                    == selection.configured_thinking
                )
            adapters = {
                "architect": factory.create_architect(config).llm_adapter,
                **{
                    "generator_" + variant.value: factory.create_generator(
                        variant, config
                    ).llm_adapter
                    for variant in Variant
                },
                "fixer": factory.create_security_agent(config).fix_agent.adapter,
            }
            requests = {}
            for role, adapter in adapters.items():
                adapter._structured_request.set(role != "architect")
                await adapter.send_prompt(
                    "fixed synthetic prompt",
                    system="fixed synthetic system",
                    max_output_tokens=100,
                    timeout=1,
                )
                requests[role] = bodies[-1]
                await adapter.client.close()
            wires.append(requests)
        for role in ROLES[1:]:
            assert wires[0][role] == wires[1][role]
            body = json.loads(wires[1][role][-1])
            assert (
                body["model"] == (fixer or ENVIRONMENT)
                if role == "fixer"
                else body["model"] == ENVIRONMENT
            )
            assert body["reasoning"] == {"effort": "low"}
            assert body["response_format"]["type"] == "json_schema"
        assert json.loads(wires[0]["architect"][-1])["model"] == ENVIRONMENT
        assert json.loads(wires[1]["architect"][-1])["model"] == ARCHITECT
        assert wires[0]["architect"][:3] == wires[1]["architect"][:3]
        assert captured[1][1].model == ARCHITECT
