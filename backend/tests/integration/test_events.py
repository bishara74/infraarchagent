import asyncio
import random
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import Settings
from app.core.logging import configure_logging
from app.db.models import AgentEvent
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import AgentName, AgentState, LLMProvider
from app.events.log import EventLog
from app.events.publisher import EventRecord, NullPublisher, RecordingPublisher


async def _new_run(session: AsyncSession) -> UUID:
    row = await RunRepository(session).create("AWS web app", LLMProvider.STUB, 3)
    await session.commit()
    return row.run_id


@pytest.mark.req("FR-P-04")
async def test_append_and_replay(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app, _ = db_engines
    run_id = await _new_run(db_session)
    publisher = RecordingPublisher()
    log = EventLog(make_session_factory(app), publisher)
    first = await log.append(run_id, AgentName.ORCHESTRATOR, AgentState.RUNNING)
    second = await log.append(
        run_id,
        AgentName.ARCHITECT,
        AgentState.COMPLETED,
        AgentState.RUNNING,
        payload={"stage": "plan"},
    )
    assert [event.event_id for event in publisher.events] == [
        first.event_id,
        second.event_id,
    ]
    assert [event.event_id for event in await log.list_after(run_id, None)] == [
        first.event_id,
        second.event_id,
    ]
    assert [event.event_id for event in await log.list_after(run_id, first.seq)] == [
        second.event_id
    ]
    assert first.seq < second.seq
    assert first.timestamp.tzinfo is not None
    assert first.timestamp.utcoffset().total_seconds() == 0


async def test_single_instance_publishes_in_sequence_order(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app, _ = db_engines
    run_id = await _new_run(db_session)
    publisher = RecordingPublisher()
    log = EventLog(make_session_factory(app), publisher)
    await asyncio.gather(
        *(
            log.append(run_id, AgentName.ORCHESTRATOR, AgentState.RUNNING)
            for _ in range(20)
        )
    )
    sequences = [event.seq for event in publisher.events]
    assert sequences == sorted(sequences)
    assert len(sequences) == 20


class _HoldingLog(EventLog):
    def __init__(self, app: AsyncEngine) -> None:
        super().__init__(make_session_factory(app), NullPublisher())
        self.inserted = asyncio.Event()
        self.release = asyncio.Event()

    async def _after_insert(self, record: EventRecord) -> None:
        self.inserted.set()
        await self.release.wait()


class _ProbeLog(EventLog):
    def __init__(self, app: AsyncEngine) -> None:
        super().__init__(make_session_factory(app), NullPublisher())
        self.attempted = asyncio.Event()

    async def _acquire_advisory_lock(self, session: AsyncSession, run_id: UUID) -> None:
        self.attempted.set()
        await super()._acquire_advisory_lock(session, run_id)


@pytest.mark.req("FR-P-04")
async def test_advisory_lock_serializes_insert_before_commit(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app, _ = db_engines
    run_id = await _new_run(db_session)
    first_log = _HoldingLog(app)
    second_log = _ProbeLog(app)
    first_task = asyncio.create_task(
        first_log.append(run_id, AgentName.ORCHESTRATOR, AgentState.RUNNING)
    )
    await first_log.inserted.wait()
    second_task = asyncio.create_task(
        second_log.append(run_id, AgentName.ARCHITECT, AgentState.RUNNING)
    )
    try:
        await second_log.attempted.wait()
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(asyncio.shield(second_task), timeout=0.3)
    finally:
        first_log.release.set()
    first = await first_task
    second = await second_task
    assert second.seq > first.seq


@pytest.mark.req("FR-P-04")
async def test_two_instances_commit_prefix_property(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app, _ = db_engines
    run_r = await _new_run(db_session)
    run_s = await _new_run(db_session)
    log_a = EventLog(make_session_factory(app), NullPublisher())
    log_b = EventLog(make_session_factory(app), NullPublisher())
    log_s = EventLog(make_session_factory(app), NullPublisher())
    await log_a.append(run_r, AgentName.ORCHESTRATOR, AgentState.RUNNING)
    await log_s.append(run_s, AgentName.ORCHESTRATOR, AgentState.RUNNING)
    snapshots: list[list[UUID]] = []
    reader_started = asyncio.Event()
    finished = asyncio.Event()

    async def read_snapshots() -> None:
        reader_started.set()
        while not finished.is_set():
            events = await log_a.list_after(run_r, None)
            assert all(a.seq < b.seq for a, b in zip(events, events[1:], strict=False))
            snapshots.append([event.event_id for event in events])
            await asyncio.sleep(0)

    reader = asyncio.create_task(read_snapshots())
    await reader_started.wait()
    rng = random.Random(17)
    choices = [log_a, log_b] * 100
    rng.shuffle(choices)
    assert log_a in choices and log_b in choices
    tasks = [
        asyncio.create_task(log.append(run_r, AgentName.SECURITY, AgentState.RUNNING))
        for log in choices[:199]
    ]
    tasks += [
        asyncio.create_task(
            log_s.append(run_s, AgentName.VALIDATOR, AgentState.RUNNING)
        )
        for _ in range(30)
    ]
    try:
        await asyncio.gather(*tasks)
    finally:
        finished.set()
        await reader
    final = await log_a.list_after(run_r, None)
    final_ids = [event.event_id for event in final]
    assert len(final_ids) == 200
    assert snapshots
    assert all(snapshot == final_ids[: len(snapshot)] for snapshot in snapshots)
    assert any(b.seq > a.seq + 1 for a, b in zip(final, final[1:], strict=False))


class _VisiblePublisher:
    def __init__(self, app: AsyncEngine) -> None:
        self.app = app

    async def publish(self, event: EventRecord) -> None:
        async with self.app.connect() as connection:
            count = await connection.scalar(
                select(func.count())
                .select_from(AgentEvent)
                .where(AgentEvent.event_id == event.event_id)
            )
        assert count == 1


async def test_publish_happens_after_commit(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app, _ = db_engines
    run_id = await _new_run(db_session)
    log = EventLog(make_session_factory(app), _VisiblePublisher(app))
    event = await log.append(run_id, AgentName.ORCHESTRATOR, AgentState.RUNNING)
    assert event.seq >= 1


class _FailingPublisher:
    def __init__(self, secret: str) -> None:
        self.secret = secret

    async def publish(self, event: EventRecord) -> None:
        raise RuntimeError(self.secret)


@pytest.mark.req("NFR-01")
async def test_publish_failure_is_durable_and_redacted(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    db_session: AsyncSession,
    canary_key: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app, _ = db_engines
    run_id = await _new_run(db_session)
    key = canary_key.require_llm_key()
    configure_logging(canary_key)
    log = EventLog(make_session_factory(app), _FailingPublisher(key))
    event = await log.append(run_id, AgentName.ORCHESTRATOR, AgentState.RUNNING)
    assert [item.event_id for item in await log.list_after(run_id, None)] == [
        event.event_id
    ]
    assert key not in caplog.text
    assert "event publish failed" in caplog.text


async def test_event_input_validation(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app, _ = db_engines
    run_id = await _new_run(db_session)
    log = EventLog(make_session_factory(app), NullPublisher())
    for state, payload in (
        ("nonsense", {}),
        ("running", {"bad": object()}),
        ("running", {"too_large": "x" * 65536}),
    ):
        with pytest.raises(ValueError):
            await log.append(run_id, AgentName.ORCHESTRATOR, state, payload=payload)
    assert await log.list_after(run_id, None) == []
