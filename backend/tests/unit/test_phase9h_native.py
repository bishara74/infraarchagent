"""NFR-01 native/compatible request mappings, offline metadata, benchmark records."""

import json

import httpx2
import pytest

from app.domain.agent_selection import ROLES
from app.llm.anthropic import AnthropicAdapter
from app.llm.base import RetryPolicy
from app.llm.catalog import normalize
from app.llm.openai import OpenAIAdapter
from scripts.benchmark import Harness


@pytest.mark.req("NFR-01")
async def test_explicit_native_thinking_and_schema_wire():
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx2.Response(
            200,
            json={
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": "native-test",
                "content": [{"type": "text", "text": "{}"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
        adapter = AnthropicAdapter(
            "native-test",
            RetryPolicy(1, 1, 10, 0, 8000),
            "synthetic-native-key",
            http_client=client,
            reasoning_effort="low",
        )
        adapter.request_style = "anthropic"
        adapter.reasoning_capable = True
        adapter.thinking_types = {"adaptive": {"supported": True}}
        adapter.structured_output = "json_schema"
        adapter.output_schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        adapter._structured_request.set(True)
        await adapter.send_prompt("test", max_output_tokens=8000, timeout=1)
    assert requests[0]["thinking"] == {"type": "adaptive"}
    assert requests[0]["output_config"]["effort"] == "low"
    assert requests[0]["output_config"]["format"]["schema"] == adapter.output_schema


@pytest.mark.req("NFR-01")
async def test_explicit_openai_off_uses_native_effort_parameter():
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx2.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 1,
                "model": "openai-test",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "{}"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
        adapter = OpenAIAdapter(
            "openai-test",
            RetryPolicy(1, 1, 10, 0, 8000),
            "synthetic-openai-key",
            http_client=client,
            reasoning_effort="off",
        )
        adapter.request_style = "openai"
        adapter.reasoning_capable = True
        await adapter.send_prompt("test", max_output_tokens=100, timeout=1)
    assert requests[0]["reasoning_effort"] == "none" and "reasoning" not in requests[0]


@pytest.mark.req("FR-P-04")
def test_benchmark_environment_records_all_five_selections(tmp_path):
    path = tmp_path / "environment.json"
    path.write_text("{}")
    harness = Harness(None, output=tmp_path)
    selections = {
        role: {"model": "configured-model", "thinking_mode": "low"} for role in ROLES
    }
    harness.finish(
        {"run_id": "fixture"},
        {
            "run": {
                "provider": "stub",
                "status": "success",
                "model": "stub",
                "agent_models": selections,
            },
            "packages": [],
            "missing_variants": [],
        },
        [],
        1,
    )
    assert (
        json.loads(path.read_text())["resolved_agent_selections"]["fixture"]
        == selections
    )
    native = normalize(
        {
            "id": "native",
            "capabilities": {
                "structured_outputs": {"supported": True},
                "thinking": {
                    "supported": True,
                    "types": {"adaptive": {"supported": True}},
                },
                "effort": {"low": {"supported": True}, "high": {"supported": False}},
            },
        },
        "anthropic",
    )
    assert native["thinking_modes"] == ["off", "low"]


@pytest.mark.req("NFR-01")
def test_dynamic_secret_redaction_retains_no_plaintext_registry():
    from app.core.logging import DYNAMIC_SECRETS, RedactingFilter, register_secret

    secret = "synthetic secret with spaces and arbitrary format"
    register_secret(secret)
    assert secret not in repr(DYNAMIC_SECRETS)
    assert (
        RedactingFilter().redact("prefix " + secret + " suffix")
        == "prefix [REDACTED] suffix"
    )


@pytest.mark.req("NFR-01")
async def test_managed_native_credential_uses_single_v1_path(monkeypatch):
    import anthropic
    from pydantic import SecretStr

    from app.core.credentials import CredentialMaterial

    adapter = AnthropicAdapter(
        "native-test", RetryPolicy(1, 1, 10, 0, 8000), "placeholder-not-used"
    )
    original = anthropic.AsyncAnthropic
    seen = []

    def respond(request):
        seen.append(request.url.path)
        assert request.headers["x-api-key"] == "synthetic-native-key"
        return httpx2.Response(
            200,
            json={
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": "native-test",
                "content": [{"type": "text", "text": "{}"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    def mocked(*args, **kwargs):
        kwargs["http_client"] = httpx2.AsyncClient(
            transport=httpx2.MockTransport(respond)
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(anthropic, "AsyncAnthropic", mocked)

    async def credential():
        return CredentialMaterial(
            "anthropic",
            "messages",
            "https://api.anthropic.com/v1",
            SecretStr("synthetic-native-key"),
        )

    adapter.credential_resolver = credential
    await adapter.send_prompt("test", max_output_tokens=100, timeout=1)
    await adapter.client.close()
    assert seen == ["/v1/messages"]
