"""Offline wire-shape regressions for Phase 9 provider diagnostics."""

import logging

import httpx2
import pytest

from app.agents.architect import ArchitectLLMFailure
from app.agents.generators.base import GeneratorLLMFailure
from app.domain.enums import Variant
from app.llm.errors import LLMPermanentError, LLMRetryExhausted, failure_message
from tests.unit.test_llm_providers import adapter_for


@pytest.mark.req("NFR-01", "FR-A-04", "NFR-03")
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
@pytest.mark.parametrize(
    "status,message,category,attempts",
    [
        (401, "secret-canary", "auth_failed", 1),
        (402, "secret-canary", "usage_limit", 1),
        (403, "Key limit exceeded secret-canary", "usage_limit", 1),
        (403, "Permission denied secret-canary", "request_rejected", 1),
        (400, "secret-canary", "request_rejected", 1),
        (422, "secret-canary", "request_rejected", 1),
        (404, "secret-canary", "model_unavailable", 1),
        (429, "secret-canary", "rate_limited", 3),
        (503, "secret-canary", "provider_error", 3),
    ],
)
async def test_wire_failures_are_safe(
    provider, status, message, category, attempts, caplog
):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx2.Response(status, json={"error": {"message": message}})

    caplog.set_level(logging.INFO, logger="app.llm.base")
    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        with pytest.raises((LLMPermanentError, LLMRetryExhausted)) as caught:
            await adapter_for(provider, client).complete_json("test")
    assert len(calls) == attempts
    assert "secret-canary" not in str(caught.value) + caplog.text
    assert f"category={category}" in caplog.text
    assert f"http_status={status}" in caplog.text
    assert "exception_class=none" not in caplog.text
    assert str(ArchitectLLMFailure(category)) == failure_message(category)
    assert str(GeneratorLLMFailure(Variant.COST, category)) == failure_message(category)


@pytest.mark.req("NFR-01", "NFR-03")
@pytest.mark.parametrize(
    "body,category",
    [
        ({"error": {"code": 403, "message": "Key limit exceeded"}}, "usage_limit"),
        ({"error": {"code": 429, "message": "secret-canary"}}, "rate_limited"),
        ({"error": "secret-canary"}, "invalid_response"),
        ({"unexpected": "secret-canary"}, "invalid_response"),
    ],
)
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
async def test_success_http_error_envelopes(provider, body, category, caplog):
    caplog.set_level(logging.INFO, logger="app.llm.base")
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json=body))
    ) as client:
        with pytest.raises((LLMPermanentError, LLMRetryExhausted)):
            await adapter_for(provider, client).complete_json("test")
    assert f"category={category}" in caplog.text
    assert "http_status=200" in caplog.text
    assert "secret-canary" not in caplog.text


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
async def test_transport_original_class(provider, caplog):
    def handler(request):
        raise httpx2.ConnectError("secret-canary", request=request)

    caplog.set_level(logging.INFO, logger="app.llm.base")
    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        with pytest.raises(LLMRetryExhausted):
            await adapter_for(provider, client).complete_json("test")
    assert "category=unreachable" in caplog.text
    assert "http_status=none" in caplog.text
    assert "exception_class=APIConnectionError" in caplog.text
    assert "secret-canary" not in caplog.text
