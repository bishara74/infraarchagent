"""Mocked provider bodies stay out of persisted/live/public failure surfaces."""

import asyncio
from uuid import UUID

import httpx
import httpx2
import pytest
from sqlalchemy import text

from app.agents.architect import ArchitectAgent
from app.core.config import get_settings
from app.llm.base import RetryPolicy
from app.llm.errors import failure_message
from app.llm.openai import OpenAIAdapter
from app.main import create_app


@pytest.mark.req("NFR-01", "FR-A-04")
@pytest.mark.parametrize(
    "status,message,category",
    [
        (401, "authentication failed", "auth_failed"),
        (403, "Key limit exceeded", "usage_limit"),
        (403, "Permission denied", "request_rejected"),
    ],
)
async def test_provider_canary_through_run_events_results_and_database(
    db_engines, canary_key, caplog, monkeypatch, status, message, category
):
    key = canary_key.require_llm_key()
    forbidden = (key, "provider.invalid", "key-ref-fixture", "12.34")
    body = {
        "error": {
            "message": message
            + " "
            + key
            + " https://provider.invalid key-ref-fixture 12.34"
        }
    }
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(
            lambda request: httpx2.Response(status, json=body)
        )
    ) as sdk_client:
        settings = canary_key.model_copy(update={"api_key": None})
        app = create_app(settings, db_engines[0])
        app.dependency_overrides[get_settings] = lambda: settings
        adapter = OpenAIAdapter(
            "fixture", RetryPolicy(1, 1, 5, 0, 100), key, http_client=sdk_client
        )
        monkeypatch.setattr(
            app.state.runner.factory,
            "create_architect",
            lambda config: ArchitectAgent(adapter, deadline_seconds=10),
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            accepted = await client.post(
                "/api/pipeline/run",
                json={
                    "text": "Create an AWS web service.",
                    "config": {"provider": "stub"},
                },
            )
            run_id = UUID(accepted.json()["run_id"])
            await asyncio.gather(*list(app.state.runner.tasks.values()))
            results = await client.get(f"/api/pipeline/{run_id}/results")
            stream = await client.get(f"/api/pipeline/{run_id}/stream")
    assert results.json()["run"]["error_message"] == failure_message(category)
    assert failure_message(category) in stream.text
    for surface in (results.text, stream.text, caplog.text):
        assert all(value not in surface for value in forbidden)
    async with db_engines[0].connect() as connection:
        for table in ("pipeline_runs", "generated_packages", "agent_events"):
            rows = await connection.scalars(text(f"SELECT t::text FROM {table} t"))
            assert all(all(value not in row for value in forbidden) for row in rows)
