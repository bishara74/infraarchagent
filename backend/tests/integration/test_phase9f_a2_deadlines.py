"""PR-05/NFR-01: real PostgreSQL locks and mandatory finalization deadlines."""

import asyncio
import time
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import text

from app.core.deadlines import active_deadline, bounded_phase, iteration_window
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import AgentName, PackageStatus, Variant
from tests.integration.test_security_agent import (
    ScriptedFix,
    ScriptedScanner,
    agent,
    finding,
    setup,
)

pytestmark = pytest.mark.req("PR-05", "NFR-01", "FR-S-03", "FR-S-04")


async def test_event_advisory_lock_wait_is_clipped_and_not_inserted(db_engines):
    engine, _ = db_engines
    ctx, _ = await setup(engine)
    events = ctx.writer.event_log
    before = await events.list_after(ctx.run_id, None)
    async with make_session_factory(engine)() as holder:
        async with holder.begin():
            await holder.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:run_id, 0))"),
                {"run_id": str(ctx.run_id)},
            )
            with pytest.raises(TimeoutError):
                async with iteration_window(
                    time.monotonic() + 0.05, time.monotonic, {}
                ):
                    await events.append(
                        ctx.run_id,
                        AgentName.SECURITY,
                        PackageStatus.REMEDIATING,
                        message="must time out before insertion",
                    )
    assert await events.list_after(ctx.run_id, None) == before


@pytest.mark.parametrize(
    "blocked_phase", ["notice", "closing_transition", "restoration"]
)
async def test_complete_iteration_bounds_finalization_and_settles_legally(
    db_engines, monkeypatch, blocked_phase
):
    engine, _ = db_engines
    ctx, package = await setup(engine)
    security = agent(engine, ScriptedScanner([[finding("RULE")]]), ScriptedFix())

    # Expire only after the phase under test is reached. Setup work must not
    # race a short timer under concurrent verification CPU contention.
    @asynccontextmanager
    async def short_window(end, clock, record):
        async with iteration_window(time.monotonic() + 60, time.monotonic, record):
            yield

    monkeypatch.setattr("app.agents.security.agent.iteration_window", short_window)
    entered = asyncio.Event()

    async def blocked():
        entered.set()
        window = active_deadline.get()
        window.end = window.clock()
        async with bounded_phase("blocked_finalization"):
            await asyncio.Event().wait()

    async def fix(*args, **kwargs):
        kwargs["checkpoint"].fixes = []
        if blocked_phase == "restoration":
            # The restoration phase runs inside the complete iteration window.
            window = active_deadline.get()
            window.end = window.clock()
            raise TimeoutError
        return args[2], [], "", args[5]

    monkeypatch.setattr(security, "_fix_iteration", fix)
    notice = security._notice
    transition = ctx.writer.package_transition

    async def slow_notice(*args, **kwargs):
        if blocked_phase == "notice" and args[2] == "security fix pass completed":
            await blocked()
        return await notice(*args, **kwargs)

    async def slow_transition(*args, **kwargs):
        if (
            blocked_phase == "closing_transition"
            and kwargs.get("message") == "security rescan started"
        ):
            await blocked()
        return await transition(*args, **kwargs)

    monkeypatch.setattr(security, "_notice", slow_notice)
    monkeypatch.setattr(ctx.writer, "package_transition", slow_transition)
    assert (
        await security.run(ctx, Variant.SECURITY, package) == PackageStatus.SCAN_ERROR
    )
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    verification = row.security_report["sessions"][0]["iterations"][0]["verification"]
    assert verification["absolute_deadline"]
    assert "complete_iteration" in verification["deadline_timings"]
    assert "_iteration_deadline" not in verification
    assert row.files == package.files
    if blocked_phase != "restoration":
        assert entered.is_set()


async def test_committed_clean_transition_with_interrupted_publication_fails_closed(
    db_engines, monkeypatch
):
    engine, _ = db_engines
    ctx, package = await setup(engine)
    security = agent(engine, ScriptedScanner([[]]), ScriptedFix())

    @asynccontextmanager
    async def short_window(end, clock, record):
        async with iteration_window(time.monotonic() + 60, time.monotonic, record):
            yield

    monkeypatch.setattr("app.agents.security.agent.iteration_window", short_window)
    publish = ctx.writer.event_log.publisher.publish
    entered = asyncio.Event()

    async def slow_publish(record):
        if record.new_state == "scan_clean":
            entered.set()
            window = active_deadline.get()
            window.end = window.clock()
            async with bounded_phase("blocked_publication"):
                await asyncio.Event().wait()
        await publish(record)

    monkeypatch.setattr(ctx.writer.event_log.publisher, "publish", slow_publish)
    assert (
        await security.run(ctx, Variant.SECURITY, package) == PackageStatus.SCAN_ERROR
    )
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    assert entered.is_set() and row.status == "scan_error"
    records = await ctx.writer.event_log.list_after(ctx.run_id, None)
    assert any(r.new_state == "scan_clean" for r in records)
    assert any(r.new_state == "scan_error" for r in records)
