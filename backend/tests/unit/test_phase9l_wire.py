"""NFR-01 / FR-A-05: complete baseline request bytes and zero disabled hooks."""

import json
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx2
import pytest
from pydantic import SecretStr

from app.agents.factory import AgentFactory
from app.agents.prompts.architect import ARCHITECT_SYSTEM_PROMPT
from app.agents.prompts.architect import build_user_prompt as architect_prompt
from app.agents.prompts.generator import build_system_prompt
from app.agents.prompts.generator import build_user_prompt as generator_prompt
from app.core.config import get_settings
from app.core.lesson_runtime import LessonRuntime
from app.domain.enums import LLMProvider, Variant
from app.domain.lessons import content_hash, empty_snapshot
from app.domain.run_config import RunConfig
from app.llm.openai import OpenAIAdapter
from tests.unit.test_generators import plan

BASELINE = json.loads(
    (Path(__file__).parents[1] / "fixtures/phase9l-baseline-bodies.json").read_text()
)
pytestmark = pytest.mark.req("NFR-01", "FR-A-05", "FR-P-04")


@pytest.mark.parametrize(
    "mode", ["off", "benchmark_enabled", "unconfigured", "empty_role"]
)
@pytest.mark.parametrize("case", list(BASELINE["bodies"]))
async def test_complete_body_bytes_and_zero_hook_invocations(case, mode):
    structured, role = case.split(":")
    settings = get_settings().model_copy(
        update={
            "llm_provider": LLMProvider.OPENAI,
            "llm_model": "wire-model",
            "llm_api_key": SecretStr("phase9l-mock-only"),
            "llm_base_url": "https://openrouter.ai/api/v1",
            "llm_structured_output": structured,
            "llm_reasoning_effort": "low",
            "lessons_enabled": mode != "off",
        }
    )

    def forbidden(*args, **kwargs):
        pytest.fail("Disabled/benchmark/empty-role lessons must not query governance.")

    runtime = LessonRuntime(forbidden, None)
    factory = AgentFactory(settings, lesson_runtime=runtime)
    snapshot = empty_snapshot(
        "benchmark" if mode == "benchmark_enabled" else "server_disabled"
    )
    if mode == "empty_role":
        entries = [
            {
                "id": str(uuid4()),
                "lesson_id": str(uuid4()),
                "revision": 1,
                "scope_role": "architect" if role != "architect" else "generator_cost",
                "text": "Prefer concise operational documentation.",
                "self_approved": False,
            }
        ]
        snapshot = {
            "lessons_enabled": True,
            "entries": entries,
            "set_hash": content_hash(entries),
            "set_version": 1,
            "disable_generation": 0,
            "reason": "eligible",
        }
    config = (
        RunConfig(lessons=snapshot, lesson_run_id=uuid4())
        if mode != "unconfigured"
        else None
    )
    if role == "architect":
        agent = factory.create_architect(config)
        adapter = agent.llm_adapter
        prompt = architect_prompt("Deploy an AWS web service with a database.")
        system = ARCHITECT_SYSTEM_PROMPT
    else:
        agent = factory.create_generator(
            Variant(role.removeprefix("generator_")), config
        )
        adapter = agent.llm_adapter
        prompt = generator_prompt(plan())
        system = build_system_prompt(
            agent.optimisation_directive,
            max_output_tokens=agent.max_output_tokens,
            wire_files=agent.wire_files,
            plan=plan(),
        )
    assert adapter.lesson_hook is None and adapter.lesson_gate is None
    dispatch = AsyncMock(side_effect=AssertionError("Lesson dispatch must not run"))
    adapter._lesson_dispatch = dispatch
    captured = []

    def handler(request):
        captured.append(request.content)
        return httpx2.Response(
            200,
            json={
                "id": "wire",
                "object": "chat.completion",
                "created": 1,
                "model": "wire-model",
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
    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        replacement = OpenAIAdapter(
            "wire-model",
            adapter.policy,
            "phase9l-mock-only",
            base_url=settings.llm_base_url,
            http_client=client,
        )
        adapter.client = replacement.client
        await adapter.complete_json(
            prompt,
            system=system,
            max_output_tokens=8000,
            response_validator=(lambda value: value) if role != "architect" else None,
        )
        await replacement.client.close()
    assert captured == [BASELINE["bodies"][case].encode()]
    dispatch.assert_not_called()
