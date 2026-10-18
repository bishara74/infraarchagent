"""Async database engines, sessions, and health probing."""

from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.core.deadlines import active_deadline


async def clip_database_waits(session: AsyncSession) -> None:
    window = active_deadline.get()
    if window is None:
        return
    window.check()
    milliseconds = str(max(1, int(window.remaining() * 1000)))
    await session.execute(
        text(
            "SELECT set_config('statement_timeout', :limit, true), "
            "set_config('lock_timeout', :limit, true)"
        ),
        {"limit": milliseconds},
    )


def make_app_engine(settings: Settings, *, test: bool = False) -> AsyncEngine:
    url = settings.test_database_url if test else settings.database_url
    return make_database_engine(url)


def make_database_engine(url: SecretStr) -> AsyncEngine:
    """Construct an engine without requiring unrelated application settings."""
    return create_async_engine(url.get_secret_value(), echo=False)


def make_owner_engine(settings: Settings, *, test: bool = False) -> AsyncEngine:
    url = (
        settings.test_migration_database_url
        if test
        else settings.migration_database_url
    )
    return create_async_engine(url.get_secret_value(), echo=False)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def database_is_available(engine: AsyncEngine) -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        return False
    return True
