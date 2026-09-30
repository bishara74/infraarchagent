import json
import logging
import random
from typing import Any

import httpx2
import pytest

from app.core.config import ReasoningEffort
from app.llm.anthropic import AnthropicAdapter
from app.llm.base import RetryPolicy
from app.llm.errors import LLMDeadlineExceeded, LLMPermanentError, LLMTransientError
from app.llm.openai import OpenAIAdapter

POLICY = RetryPolicy(30, 3, 150, 0, 16000)


class FakeClock:
    def __init__(self) -> None:
        self.time = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.time

    async def sleep(self, duration: float) -> None:
        self.sleeps.append(duration)
        self.time += duration


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


@pytest.mark.req("PR-05", "NFR-01")
@pytest.mark.parametrize("diagnostics", [True, False])
async def test_openrouter_serving_diagnostics_are_optional(
    diagnostics: bool, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="app.llm.base")
    body = success_body("openai")
    if diagnostics:
        body["provider"] = "Fireworks AI"
        body["usage"]["completion_tokens_details"] = {"reasoning_tokens": 4}

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=body)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = OpenAIAdapter(
            "test-model", POLICY, "canary-placeholder", http_client=client
        )
        result = await adapter.complete_json("x")
    line = next(
        record.getMessage()
        for record in caplog.records
        if record.name == "app.llm.base"
    )
    if diagnostics:
        assert result.response.served_by == "Fireworks AI"
        assert result.response.reasoning_tokens == 4
        assert "served_by=Fireworks%20AI" in line
        assert "reasoning_tokens=4" in line
    else:
        assert result.response.served_by is None
        assert result.response.reasoning_tokens is None
        assert "served_by=" not in line
        assert "reasoning_tokens=" not in line


@pytest.mark.req("PR-05")
@pytest.mark.parametrize(
    ("effort", "reasoning"),
    [
        (None, None),
        ("off", {"enabled": False}),
        ("low", {"effort": "low"}),
        ("medium", {"effort": "medium"}),
        ("high", {"effort": "high"}),
    ],
)
async def test_openai_compatible_reasoning_request_body_and_log(
    effort: ReasoningEffort | None,
    reasoning: dict[str, str | bool] | None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.llm.base")
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(200, json=success_body("openai"))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = OpenAIAdapter(
            "test-model",
            POLICY,
            "canary-placeholder",
            http_client=client,
            reasoning_effort=effort,
        )
        assert (await adapter.complete_json("x")).data == {"ok": True}
    payload = json.loads(requests[0].content)
    assert "reasoning_effort" not in payload
    if reasoning is None:
        assert "reasoning" not in payload
    else:
        assert payload["reasoning"] == reasoning
    line = next(
        record.getMessage()
        for record in caplog.records
        if record.name == "app.llm.base"
    )
    assert f"reasoning_effort={effort or 'unset'}" in line.split(" ")


@pytest.mark.req("PR-05")
async def test_anthropic_ignores_reasoning_effort_in_request(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.llm.base")
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(200, json=success_body("anthropic"))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = AnthropicAdapter(
            "test-model",
            POLICY,
            "canary-placeholder",
            http_client=client,
            reasoning_effort="high",
        )
        assert (await adapter.complete_json("x")).data == {"ok": True}
    payload = json.loads(requests[0].content)
    assert "reasoning" not in payload
    assert "thinking" not in payload
    assert "output_config" not in payload
    assert any(
        "reasoning_effort=high" in record.getMessage().split(" ")
        for record in caplog.records
        if record.name == "app.llm.base"
    )


@pytest.mark.req("PR-05")
async def test_openrouter_missing_usage_does_not_break_response() -> None:
    body = success_body("openai")
    del body["usage"]

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=body)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = OpenAIAdapter(
            "test-model", POLICY, "canary-placeholder", http_client=client
        )
        result = await adapter.complete_json("x")
    assert result.response.input_tokens is None
    assert result.response.output_tokens is None
    assert result.response.served_by is None
    assert result.response.reasoning_tokens is None


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
@pytest.mark.parametrize("error_type", [httpx2.ConnectError, httpx2.ReadTimeout])
async def test_provider_transport_failures_are_transient(
    provider: str, error_type: type[httpx2.TransportError]
) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise error_type("offline", request=request)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        with pytest.raises(LLMTransientError):
            await adapter.send_prompt("x", max_output_tokens=10, timeout=1)


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


@pytest.mark.req("FR-A-04", "PR-05")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
async def test_rate_limit_retry_after_waits_before_success(provider: str) -> None:
    calls = 0
    clock = FakeClock()

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx2.Response(
                429,
                headers={"retry-after": "20"},
                json=error_body(provider, 429),
            )
        return httpx2.Response(200, json=success_body(provider))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        adapter.policy = RetryPolicy(30, 2, 60, 1, 16000)
        adapter._clock = clock.now
        adapter._sleep = clock.sleep
        adapter._rng = random.Random(0)
        result = await adapter.complete_json("x")
    assert result.attempts == calls == 2
    assert clock.sleeps == [20]


@pytest.mark.req("FR-A-04", "PR-05")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
async def test_rate_limit_retry_after_beyond_deadline_stops_without_sleep(
    provider: str,
) -> None:
    calls = 0
    clock = FakeClock()

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(
            429, headers={"retry-after": "20"}, json=error_body(provider, 429)
        )

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        adapter.policy = RetryPolicy(30, 2, 10, 1, 16000)
        adapter._clock = clock.now
        adapter._sleep = clock.sleep
        with pytest.raises(LLMDeadlineExceeded) as captured:
            await adapter.complete_json("x")
    assert captured.value.attempts == calls == 1
    assert clock.sleeps == []


@pytest.mark.req("FR-A-04", "PR-05")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
@pytest.mark.parametrize("retry_after", [None, "not-seconds"])
async def test_missing_or_invalid_retry_after_uses_jittered_backoff(
    provider: str, retry_after: str | None
) -> None:
    calls = 0
    clock = FakeClock()

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            headers = {"retry-after": retry_after} if retry_after is not None else {}
            return httpx2.Response(429, headers=headers, json=error_body(provider, 429))
        return httpx2.Response(200, json=success_body(provider))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        adapter.policy = RetryPolicy(30, 2, 60, 1, 16000)
        adapter._clock = clock.now
        adapter._sleep = clock.sleep
        adapter._rng = random.Random(0)
        assert (await adapter.complete_json("x")).attempts == 2
    assert calls == 2
    assert clock.sleeps == [random.Random(0).uniform(0, 1)]


@pytest.mark.req("FR-A-04", "PR-05", "NFR-01")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
async def test_reset_hint_fallback_waits_and_logs_only_header_names(
    provider: str, caplog: pytest.LogCaptureFixture
) -> None:
    calls = 0
    clock = FakeClock()
    caplog.set_level(logging.INFO, logger="app.llm.base")

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx2.Response(
                429,
                headers={
                    "retry-after": "invalid-secret-value",
                    "x-ratelimit-reset-tokens": "7.66s",
                    "x-ratelimit-reset-requests": "1m2.5s",
                },
                json=error_body(provider, 429),
            )
        return httpx2.Response(200, json=success_body(provider))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        adapter.policy = RetryPolicy(30, 2, 100, 0, 16000)
        adapter._clock = clock.now
        adapter._sleep = clock.sleep
        assert (await adapter.complete_json("x")).attempts == 2
    assert clock.sleeps == [62.5]
    first_line = next(
        record.getMessage()
        for record in caplog.records
        if record.name == "app.llm.base" and "attempt=1" in record.getMessage()
    )
    assert "retry_after=62.5" in first_line
    assert (
        "rate_limit_headers=retry-after,x-ratelimit-reset-tokens,"
        "x-ratelimit-reset-requests"
    ) in first_line
    assert "invalid-secret-value" not in caplog.text
    assert "7.66s" not in caplog.text
    assert "1m2.5s" not in caplog.text


@pytest.mark.req("FR-A-04", "PR-05")
@pytest.mark.parametrize("provider", ["anthropic", "openai"])
async def test_reset_hint_obeys_deadline(provider: str) -> None:
    clock = FakeClock()

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            429,
            headers={"x-ratelimit-reset-tokens": "20s"},
            json=error_body(provider, 429),
        )

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = adapter_for(provider, client)
        adapter.policy = RetryPolicy(30, 2, 10, 0, 16000)
        adapter._clock = clock.now
        adapter._sleep = clock.sleep
        with pytest.raises(LLMDeadlineExceeded):
            await adapter.complete_json("x")
    assert clock.sleeps == []
