"""Real PostgreSQL fixtures: owner migrates and cleans; app runs the code."""

import subprocess
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import make_app_engine, make_owner_engine, make_session_factory

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def migrated_test_database() -> None:
    subprocess.run(
        [str(BACKEND / ".venv/bin/alembic"), "-x", "database=test", "upgrade", "head"],
        cwd=BACKEND,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
async def db_engines(
    migrated_test_database: None,
) -> AsyncIterator[tuple[AsyncEngine, AsyncEngine]]:
    settings = get_settings()
    app_engine = make_app_engine(settings, test=True)
    owner_engine = make_owner_engine(settings, test=True)
    try:
        async with owner_engine.begin() as connection:
            await connection.execute(
                text(
                    "TRUNCATE agent_events, generated_packages, "
                    "pipeline_runs RESTART IDENTITY"
                )
            )
        yield app_engine, owner_engine
    finally:
        await app_engine.dispose()
        await owner_engine.dispose()


@pytest.fixture
async def db_session(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> AsyncIterator[AsyncSession]:
    app_engine, _ = db_engines
    async with make_session_factory(app_engine)() as session:
        yield session


@pytest.fixture
def canary_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[Settings]:
    monkeypatch.setenv("LLM_API_KEY", "sk-ant-api03-CANARY-7f3c9e2a1b4d5e6f")
    get_settings.cache_clear()
    try:
        yield get_settings()
    finally:
        get_settings.cache_clear()
