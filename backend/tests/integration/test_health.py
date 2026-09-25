import httpx
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.api.deps import get_engine
from app.core.config import get_settings
from app.main import create_app


async def test_health_real_database_and_unreachable_override(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app_engine, _ = db_engines
    settings = get_settings().model_copy(update={"llm_api_key": None})
    app = create_app(settings, app_engine)
    app.dependency_overrides[get_settings] = lambda: settings
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

        configured = settings.model_copy(update={"llm_api_key": SecretStr("test-only")})
        app.dependency_overrides[get_settings] = lambda: configured
        assert (await client.get("/api/health")).json()["llm_configured"] is True

        unreachable = create_async_engine(
            "postgresql+asyncpg://infraarch_app:unused@127.0.0.1:1/infraarch_test"
        )
        try:
            app.dependency_overrides[get_engine] = lambda: unreachable
            response = await client.get("/api/health")
            assert response.status_code == 503
            assert response.json() == {
                "status": "degraded",
                "database": "unavailable",
                "llm_configured": True,
            }
        finally:
            await unreachable.dispose()
