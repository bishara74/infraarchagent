"""Offline generator wire, parsing and deadline regressions (Phase 9c)."""

import json
import logging

import httpx2
import pytest

from app.agents.generators.base import GeneratorLLMFailure
from app.agents.generators.cost import CostGeneratorAgent
from app.agents.generators.schema import (
    generator_wire_schema,
    validate_generator_output,
)
from app.domain.plan import DeploymentPlan
from app.llm.base import RetryPolicy
from app.llm.openai import OpenAIAdapter


def plan():
    return DeploymentPlan.model_validate(
        {
            "cloud_provider": "aws",
            "services": [{"name": "web", "aws_service": "ECS", "purpose": "Serve"}],
            "dependencies": [],
            "network": {
                "public_services": ["web"],
                "private_services": [],
                "ingress": [],
                "notes": "VPC",
            },
            "storage": [],
            "file_types": ["terraform"],
            "ambiguities": [],
        }
    )


def response(text, finish_reason="stop"):
    return httpx2.Response(
        200,
        json={
            "id": "mock",
            "object": "chat.completion",
            "created": 1,
            "model": "mock",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": finish_reason,
                    "message": {"role": "assistant", "content": text},
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        },
    )


def output(wire=False, content="terraform {}"):
    files = (
        [{"path": "terraform/main.tf", "content": content}]
        if wire
        else {"terraform/main.tf": content}
    )
    return {"files": files, "notes": ""}


def generator(client, mode="json_object", attempts=1, **kwargs):
    adapter = OpenAIAdapter(
        "mock-model",
        RetryPolicy(60, attempts, 150, 0, 16000),
        "canary-placeholder",
        http_client=client,
        base_url="https://openrouter.ai/api/v1",
        reasoning_effort="off",
        response_format="json_object",
    )
    return CostGeneratorAgent(
        adapter,
        deadline_seconds=kwargs.pop("deadline_seconds", 150),
        attempt_timeout=kwargs.pop("attempt_timeout", 90),
        max_output_tokens=8000,
        max_package_attempts=2,
        structured_output=mode,
        **kwargs,
    )


@pytest.mark.req("FR-G-02", "PR-01", "PR-05")
@pytest.mark.parametrize("mode", ["json_schema", "json_object", "off"])
async def test_generator_request_modes_and_budget(mode):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return response(json.dumps(output(wire=mode == "json_schema")))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        package = await generator(client, mode).generate(plan())
    body = requests[0]
    assert body["max_completion_tokens"] == 8000
    assert body["reasoning"] == {"enabled": False}
    assert "temperature" not in body
    assert package.files == {"terraform/main.tf": "terraform {}"}
    if mode == "json_schema":
        assert body["response_format"] == {
            "type": "json_schema",
            "json_schema": {
                "name": "generator_package",
                "strict": True,
                "schema": generator_wire_schema(),
            },
        }
        assert body["provider"] == {"require_parameters": True}
    elif mode == "json_object":
        assert body["response_format"] == {"type": "json_object"}
        assert "provider" not in body
    else:
        assert "response_format" not in body
        assert "provider" not in body


@pytest.mark.req("FR-G-02", "NFR-01")
@pytest.mark.parametrize(
    "source,accepted,reason",
    [
        (json.dumps(output(content="terraform {}\n# ```one``` ```two```")), True, None),
        ("Prose before " + json.dumps(output()) + " prose after", True, "salvaged"),
        ("```json\n" + json.dumps(output()) + "\n```", True, "salvaged"),
        (json.dumps(output()) + json.dumps(output()), False, "multiple_blocks"),
        (
            "```json\n"
            + json.dumps(output())
            + "\n```\n```json\n"
            + json.dumps(output())
            + "\n```",
            False,
            "multiple_blocks",
        ),
        ('Prose {"files":{"terraform/main.tf":7}} after', False, "schema_invalid"),
    ],
)
async def test_generator_parser_boundaries_and_schema(source, accepted, reason, caplog):
    caplog.set_level(logging.INFO, logger="app.llm.base")
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(lambda request: response(source))
    ) as client:
        agent = generator(client)
        if accepted:
            package = await agent.generate(plan())
            assert "terraform/main.tf" in package.files
        else:
            with pytest.raises(GeneratorLLMFailure):
                await agent.generate(plan())
    if reason is None:
        assert "format_reason=" not in caplog.text
    else:
        assert "format_reason=" + reason in caplog.text
    assert source not in caplog.text


@pytest.mark.req("PR-05", "FR-G-02")
async def test_length_is_truncated_even_if_object_is_valid(caplog):
    caplog.set_level(logging.INFO, logger="app.llm.base")
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(
            lambda request: response(json.dumps(output()), "length")
        )
    ) as client:
        with pytest.raises(GeneratorLLMFailure):
            await generator(client).generate(plan())
    assert "category=invalid_response" in caplog.text
    assert "format_reason=truncated" in caplog.text


@pytest.mark.req("FR-G-02")
def test_wire_round_trip_schema_and_duplicate_rejection():
    assert validate_generator_output(output(wire=True), wire_files=True) == output()
    schema = generator_wire_schema()
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["files", "notes"]
    assert schema["properties"]["files"]["items"]["additionalProperties"] is False
    assert "default" not in schema["properties"]["notes"]
    duplicate = output(wire=True)
    duplicate["files"] *= 2
    with pytest.raises(ValueError):
        validate_generator_output(duplicate, wire_files=True)


@pytest.mark.req("FR-G-02", "NFR-01")
@pytest.mark.parametrize("status", [400, 404])
async def test_structured_refusal_has_safe_fallback_advice(status):
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(
            lambda request: httpx2.Response(
                status, json={"error": {"message": "private provider body"}}
            )
        )
    ) as client:
        with pytest.raises(GeneratorLLMFailure) as caught:
            await generator(client, "json_schema").generate(plan())
    assert "LLM_STRUCTURED_OUTPUT=json_object" in str(caught.value)
    assert "private provider body" not in str(caught.value)
