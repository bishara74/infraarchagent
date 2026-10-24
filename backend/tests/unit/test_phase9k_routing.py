"""NFR-01 / FR-P-04: anonymous metadata and honest provider fallback statistics."""

from types import SimpleNamespace

import httpx
import httpx2
import pytest

from app.llm.base import RetryPolicy
from app.llm.openai import OpenAIAdapter
from app.llm.public_catalogue import (
    CatalogueError,
    load_snapshot,
    provider_order,
    public_endpoints,
    public_get,
)
from scripts.phase9k_routing import preferences, routing_statistics, status_preflight
from tests.phase9k_fixtures import ARCHITECT, BASELINE, fake_snapshot

pytestmark = pytest.mark.req("NFR-01", "FR-P-04", "PR-01")


def test_role_preferences_and_snapshot_validation(tmp_path):
    assert preferences(SimpleNamespace(provider_preference="Test Fast")) == {
        role: "Test Fast"
        for role in (
            "generator_cost",
            "generator_performance",
            "generator_security",
            "fixer",
        )
    }
    with pytest.raises(CatalogueError, match="make catalogue-snapshot"):
        load_snapshot(tmp_path / "missing")
    snapshot = fake_snapshot(tmp_path / "snapshot.json")
    assert load_snapshot(tmp_path / "snapshot.json") == snapshot
    assert provider_order(snapshot, BASELINE + ":nitro", "Test Fast") == ("test-fast",)
    with pytest.raises(CatalogueError, match="does not serve"):
        provider_order(snapshot, ARCHITECT, "Nonexistent Test Provider")


async def test_public_http_never_reads_keys_settings_or_sends_auth(monkeypatch):
    import os

    import app.core.config

    monkeypatch.setattr(
        app.core.config, "get_settings", lambda: pytest.fail("Settings read")
    )
    original = os.environ.get
    monkeypatch.setattr(
        os.environ,
        "get",
        lambda key, *a: (
            pytest.fail("Key read")
            if "KEY" in key or "TOKEN" in key
            else original(key, *a)
        ),
    )
    calls = []

    def reply(request):
        calls.append(request)
        assert request.url.host == "openrouter.ai"
        assert not {"authorization", "x-api-key", "cookie"} & set(request.headers)
        return httpx.Response(
            200,
            json={
                "data": {
                    "endpoints": [
                        {"provider_name": "Test Fast", "tag": "test-fast", "status": 0}
                    ]
                }
            },
            headers={"set-cookie": "secret=synthetic-cookie"},
        )

    transport = httpx.MockTransport(reply)
    await public_get("/models", transport=transport)
    await public_endpoints(BASELINE, transport=transport)
    assert len(calls) == 2


@pytest.mark.parametrize("status", [401, 403, 302, 500])
async def test_no_authenticated_retry_or_redirect(status):
    calls = []

    def reply(request):
        calls.append(request)
        return httpx.Response(status, headers={"location": "https://evil.invalid"})

    with pytest.raises(CatalogueError, match="no authenticated retry"):
        await public_get("/models", transport=httpx.MockTransport(reply))
    assert len(calls) == 1


async def test_health_confirmation_force_and_healthy_dedup():
    selections = {
        role: {"model": BASELINE, "provider_order": ["test-fast"]}
        for role in ("generator_cost", "fixer")
    }
    transport = httpx.MockTransport(
        lambda r: httpx.Response(
            200, json={"data": {"endpoints": [{"tag": "test-fast", "status": 1}]}}
        )
    )
    with pytest.raises(ValueError, match="confirmation"):
        await status_preflight(selections, transport=transport, confirm=lambda: False)
    assert (
        len(
            await status_preflight(
                selections, transport=transport, confirm=lambda: True
            )
        )
        == 1
    )
    assert len(await status_preflight(selections, transport=transport, force=True)) == 1
    healthy = httpx.MockTransport(
        lambda r: httpx.Response(
            200, json={"data": {"endpoints": [{"tag": "test-fast", "status": 0}]}}
        )
    )
    assert (await status_preflight(selections, transport=healthy))[0]["status"] == "ok"


def test_fallback_counts_known_unknown_unpreferred_and_duplicate_calls():
    calls = [
        {"kind": "llm", "call_id": str(i), "role": role, "served_by": provider}
        for i, (role, provider) in enumerate(
            [
                ("fixer", "Test Fast"),
                ("fixer", "Test Backup"),
                ("fixer", None),
                ("architect", "Test Backup"),
            ]
        )
    ]
    counts = routing_statistics(
        calls + [calls[0]], {"fixer": {"provider_order": ["test-fast"]}}
    )
    assert (
        counts["preferred_calls"],
        counts["fallback_calls"],
        counts["unknown_calls"],
    ) == (1, 1, 1)
    assert counts["fallback_share"] == 0.5 and counts["any_fallback"]
    assert routing_statistics(calls, {})["fallback_share"] is None


async def test_routing_merges_strict_schema_and_server_fallback():
    import json

    bodies = []

    def reply(request):
        bodies.append(json.loads(request.content))
        return httpx2.Response(
            200,
            json={
                "id": "fake",
                "object": "chat.completion",
                "created": 1,
                "model": BASELINE,
                "provider": "Test Backup",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "{}"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    adapter = OpenAIAdapter(
        BASELINE,
        RetryPolicy(1, 1, 2, 0, 100),
        "synthetic-only",
        base_url="https://openrouter.ai/api/v1",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(reply)),
    )
    adapter.provider_order = ("test-fast",)
    adapter.structured_output = "json_schema"
    adapter.output_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    adapter._structured_request.set(True)
    result = await adapter.send_prompt("fake", max_output_tokens=100, timeout=1)
    await adapter.client.close()
    assert bodies[0]["provider"] == {
        "require_parameters": True,
        "order": ["test-fast"],
        "allow_fallbacks": True,
    }
    assert result.served_by == "Test Backup"
