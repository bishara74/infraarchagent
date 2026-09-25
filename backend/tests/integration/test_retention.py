import asyncio
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import AgentName, AgentState, LLMProvider, Variant
from app.events.log import EventLog
from app.events.publisher import NullPublisher


async def _cli(*arguments: str) -> str:
    backend = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["DATABASE_URL"] = get_settings().test_database_url.get_secret_value()
    process = await asyncio.create_subprocess_exec(
        str(backend / ".venv/bin/python"),
        "-m",
        "app.cli",
        "sweep-packages",
        *arguments,
        cwd=backend,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    assert process.returncode == 0, stderr.decode()
    return stdout.decode().strip()


async def test_sweep_only_deletes_expired_packages(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app, _ = db_engines
    now = datetime.now(UTC)
    run = await RunRepository(db_session).create("AWS web app", LLMProvider.STUB, 3)
    packages = PackageRepository(db_session)
    old = await packages.create(run.run_id, Variant.COST)
    await packages.create(run.run_id, Variant.PERFORMANCE)
    old.created_at = now - timedelta(days=31)
    run_id = run.run_id
    await db_session.commit()
    event = await EventLog(make_session_factory(app), NullPublisher()).append(
        run_id, AgentName.ORCHESTRATOR, AgentState.RUNNING
    )

    assert await packages.delete_expired(now, 30, dry_run=True) == 1
    assert len(await packages.list_for_run(run_id)) == 2
    assert await _cli("--days", "30", "--dry-run") == "1 package(s) would be deleted"
    assert len(await packages.list_for_run(run_id)) == 2
    assert await _cli("--days", "30") == "1 package(s) deleted"
    db_session.expire_all()
    remaining = await packages.list_for_run(run_id)
    assert len(remaining) == 1 and remaining[0].variant == Variant.PERFORMANCE
    assert await RunRepository(db_session).get(run_id) is not None
    rows = await EventLog(make_session_factory(app), NullPublisher()).list_after(
        run_id, None
    )
    assert [row.event_id for row in rows] == [event.event_id]
