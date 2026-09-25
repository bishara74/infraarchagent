from uuid import UUID

import httpx
import pytest
from fastapi import Request

from app.api.deps import get_engine, get_event_log
from app.core.config import Settings, get_settings
from app.main import create_app


class _Connection:
    async def execute(self, statement: object) -> None:
        return None


class _ConnectionContext:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    async def __aenter__(self) -> _Connection:
        if self.fail:
            raise OSError("database unavailable")
        return _Connection()

    async def __aexit__(self, *args: object) -> None:
        return None


class _Engine:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def connect(self) -> _ConnectionContext:
        return _ConnectionContext(fail=self.fail)


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "postgresql+asyncpg://app:secret@localhost/db",
        "migration_database_url": "postgresql+asyncpg://owner:secret@localhost/db",
        "test_database_url": "postgresql+asyncpg://app:secret@localhost/test",
        "test_migration_database_url": "postgresql+asyncpg://owner:secret@localhost/test",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_health_without_llm_key_and_unreachable_database() -> None:
    settings = _settings(llm_api_key="")
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_engine] = lambda: _Engine()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "database": "ok",
            "llm_configured": False,
        }
        app.dependency_overrides[get_engine] = lambda: _Engine(fail=True)
        response = await client.get("/api/health")
        assert response.status_code == 503
        assert response.json()["database"] == "unavailable"


@pytest.mark.asyncio
async def test_unexpected_error_is_client_safe() -> None:
    app = create_app(_settings())

    def fail(request: Request) -> None:
        raise RuntimeError("private exception detail")

    app.add_api_route("/fail", fail)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/fail")
    assert response.status_code == 500
    assert response.json()["error"] == "internal_error"
    UUID(response.json()["request_id"])
    assert "private exception detail" not in response.text


def test_create_app_exposes_one_shared_event_log() -> None:
    app = create_app(_settings())
    request = Request({"type": "http", "app": app, "path": "/", "method": "GET"})
    assert get_event_log(request) is app.state.event_log
    assert get_event_log(request) is get_event_log(request)
