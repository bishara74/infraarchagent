"""FR-P-04 / NFR-01: header-only, read-only preflight with strict public projection."""

from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text

from app.db.repositories.providers import ProviderRepository
from app.domain.enums import LLMProvider
from tests.integration.test_phase9g_auth import KEY, ORIGIN, authenticated
from tests.phase9k_fixtures import ARCHITECT, BASELINE, fake_snapshot

pytestmark = pytest.mark.req("FR-P-04", "NFR-01", "FR-A-01")


async def setup(db_engines, tmp_path):
    path = tmp_path / "snapshot.json"
    fake_snapshot(path)
    app, _ = await authenticated(
        db_engines[0],
        llm_provider=LLMProvider.OPENAI,
        llm_model=BASELINE + ":nitro",
        llm_api_key=SecretStr("synthetic-secret-llm-canary"),
        llm_base_url="https://openrouter.ai/api/v1",
        openrouter_catalogue_snapshot=path,
    )
    app.state.runner.start = lambda *args: pytest.fail("Preflight submitted a run")
    return app


async def counts(app):
    async with app.state.session_factory() as session:
        return [
            (await session.execute(text(f"SELECT count(*) FROM {table}"))).scalar()
            for table in (
                "pipeline_runs",
                "agent_events",
                "generated_packages",
                "llm_settings",
                "provider_credentials",
            )
        ]


async def test_preflight_is_read_only_and_exactly_allowlists_public_fields(
    db_engines, tmp_path, monkeypatch
):
    app = await setup(db_engines, tmp_path)
    forbidden = AsyncMock(side_effect=AssertionError("Credential repository accessed"))
    monkeypatch.setattr(ProviderRepository, "settings", forbidden)
    monkeypatch.setattr(ProviderRepository, "material", forbidden)
    before = await counts(app)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        response = await client.post(
            "/api/benchmark/preflight",
            json={
                "agent_models": {
                    "architect": {"model": ARCHITECT, "thinking_mode": "medium"}
                },
                "provider_preferences": {"fixer": "Test Fast"},
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert set(body) == {"selections", "snapshot"}
        assert set(body["snapshot"]) == {"source", "captured_at", "sha256"}
        assert len(body["selections"]) == 5
        assert all(
            set(s) == {"model", "thinking_mode", "provider_order"}
            for s in body["selections"].values()
        )
        assert body["selections"]["architect"]["model"] == ARCHITECT
        assert body["selections"]["architect"]["provider_order"] == []
        assert body["selections"]["fixer"]["provider_order"] == ["test-fast"]
        for secret in (
            KEY,
            "synthetic-secret-llm-canary",
            "credential_id",
            "api_key",
            "authorization",
            "secret",
            "token",
            "key_fragment",
        ):
            assert secret not in response.text
        for invalid in (
            {"credential_id": "secret-canary"},
            {"resolved_agents": {}},
            {"provider_preferences": {"fixer": "no-such-test-provider"}},
        ):
            error = await client.post("/api/benchmark/preflight", json=invalid)
            assert error.status_code == 400 and "secret-canary" not in error.text
    assert await counts(app) == before
    forbidden.assert_not_awaited()


async def test_preflight_rejects_cookie_only_missing_wrong_and_local_auth(
    db_engines, tmp_path
):
    app = await setup(db_engines, tmp_path)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
    ) as client:
        for headers in ({}, {"X-API-Key": "wrong"}):
            assert (
                await client.post("/api/benchmark/preflight", json={}, headers=headers)
            ).status_code == 401
        assert (
            await client.post("/api/auth/login", json={"api_key": KEY}, headers=ORIGIN)
        ).status_code == 200
        assert (
            await client.post("/api/benchmark/preflight", json={}, headers=ORIGIN)
        ).status_code == 401
        app.state.settings = app.state.settings.model_copy(update={"api_key": None})
        client.cookies.clear()
        assert (
            await client.post("/api/benchmark/preflight", json={})
        ).status_code == 401


async def test_preflight_missing_snapshot_is_fixed_guidance(db_engines, tmp_path):
    app = await setup(db_engines, tmp_path)
    app.state.settings.openrouter_catalogue_snapshot.unlink()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        response = await client.post("/api/benchmark/preflight", json={})
        assert response.status_code == 400
        assert "make catalogue-snapshot" in response.text
        assert str(tmp_path) not in response.text


async def test_preflight_refuses_native_transport_without_credential_probe(
    db_engines, tmp_path, monkeypatch
):
    app = await setup(db_engines, tmp_path)
    app.state.settings = app.state.settings.model_copy(
        update={
            "llm_provider": LLMProvider.ANTHROPIC,
            "llm_base_url": "https://native.invalid",
        }
    )
    from app.core import model_selection

    probe = AsyncMock(side_effect=AssertionError("Authenticated catalogue probe"))
    monkeypatch.setattr(model_selection, "probe", probe)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        response = await client.post(
            "/api/benchmark/preflight",
            json={"agent_models": {"architect": {"model": ARCHITECT}}},
        )
        assert response.status_code == 400
    probe.assert_not_awaited()
