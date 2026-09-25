import json
from typing import Any

import httpx2
import pytest

from app.llm.anthropic import AnthropicAdapter
from app.llm.base import RetryPolicy
from app.llm.errors import LLMPermanentError, LLMTransientError
from app.llm.openai import OpenAIAdapter

POLICY = RetryPolicy(30, 3, 150, 0, 16000)


def success_body(provider: str, *, truncated: bool = False) -> dict[str, Any]:
    if provider == "anthropic":
        return {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": "test-model",
            "content": [{"type": "text", "text": '{"ok":true}'}],
            "stop_reason": "max_tokens" if truncated else "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 11, "output_tokens": 7},
        }
    return {
        "id": "chatcmpl_test",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "finish_reason": "length" if truncated else "stop",
                "message": {"role": "assistant", "content": '{"ok":true}'},
            }
        ],
        "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
    }


def error_body(provider: str, status: int) -> dict[str, Any]:
    if provider == "anthropic":
        return {"type": "error", "error": {"type": "api_error", "message": "hidden"}}
    return {"error": {"type": "api_error", "message": "hidden", "code": None}}


def adapter_for(
    provider: str, client: httpx2.AsyncClient
) -> AnthropicAdapter | OpenAIAdapter:
    if provider == "anthropic":
        return AnthropicAdapter(
            "test-model", POLICY, "canary-placeholder", http_client=client
        )
    return OpenAIAdapter("test-model", POLICY, "canary-placeholder", http_client=client)


@pytest.mark.req("NFR-03", "FR-I-04")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
async def test_provider_request_response_and_no_sdk_retries(provider: str) -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(200, json=success_body(provider))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        assert adapter.client.max_retries == 0
        result = await adapter.complete_json("hello", system="instructions")
    assert result.data == {"ok": True}
    assert result.attempts == 1
    assert result.response.input_tokens == 11
    assert result.response.output_tokens == 7
    assert len(requests) == 1
    payload = json.loads(requests[0].content)
    assert payload["model"] == "test-model"
    assert payload["messages"][-1] == {"role": "user", "content": "hello"}
    if provider == "anthropic":
        assert payload["max_tokens"] == 16000
        assert payload["system"] == "instructions"
        assert not {"temperature", "top_p", "top_k"} & payload.keys()
    else:
        assert payload["max_completion_tokens"] == 16000
        assert payload["messages"][0] == {"role": "system", "content": "instructions"}
        assert requests[0].url.path.endswith("/chat/completions")


@pytest.mark.req("NFR-03")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
@pytest.mark.parametrize(
    "status,expected",
    [
        (400, LLMPermanentError),
        (401, LLMPermanentError),
        (403, LLMPermanentError),
        (404, LLMPermanentError),
        (429, LLMTransientError),
        (500, LLMTransientError),
    ],
)
async def test_provider_status_mapping(
    provider: str, status: int, expected: type[Exception]
) -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(status, json=error_body(provider, status))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        with pytest.raises(expected):
            await adapter.send_prompt("x", max_output_tokens=10, timeout=1)
    assert calls == 1


@pytest.mark.req("NFR-03")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
async def test_provider_token_limit_is_retried(provider: str) -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(200, json=success_body(provider, truncated=calls == 1))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        result = await adapter.complete_json("x")
    assert result.attempts == 2
    assert calls == 2


@pytest.mark.req("NFR-03")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
async def test_truncation_error_preserves_only_safe_metrics(provider: str) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=success_body(provider, truncated=True))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        adapter.policy = RetryPolicy(30, 1, 150, 0, 16000)
        from app.llm.errors import LLMRetryExhausted

        with pytest.raises(LLMRetryExhausted) as captured:
            await adapter.complete_json("x")
    assert captured.value.last_category == "truncated"
    assert captured.value.stats is not None
    assert captured.value.stats.output_tokens == 7
