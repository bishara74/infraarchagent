"""Subscribe-before-replay and package-aware stream closure."""

import asyncio
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.requests import Request
from starlette.responses import StreamingResponse

from app.api.pipeline import stream_run
from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import AgentName, LLMProvider, PackageStatus, RunStatus, Variant
from app.events.kinds import package_status_payload, run_status_payload
from app.main import create_app


def request_for(app: object) -> Request:
    return Request(
        {"type": "http", "method": "GET", "path": "/", "headers": [], "app": app}
    )


@pytest.mark.req("FR-P-04", "PR-02")
@pytest.mark.req("UC-02")
async def test_replay_and_live_overlap_has_no_duplicate_or_gap(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, _ = db_engines
    app = create_app(get_settings(), engine)
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            row = await RunRepository(session).create(
                "Deploy AWS web service", LLMProvider.STUB, 3
            )
            run_id: UUID = row.run_id
    log = app.state.event_log
    first = await log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        RunStatus.CREATED,
        payload=run_status_payload(),
    )
    original_list_after = log.list_after
    injected = False

    async def racing_list_after(run: UUID, cursor: int | None):
        nonlocal injected
        if cursor is None and not injected:
            injected = True
            await log.append(
                run_id,
                AgentName.ORCHESTRATOR,
                RunStatus.RUNNING,
                RunStatus.CREATED,
                payload=run_status_payload(),
            )
        return await original_list_after(run, cursor)

    monkeypatch.setattr(log, "list_after", racing_list_after)
    response = await stream_run(
        str(run_id), request_for(app), log, app.state.broker, None
    )
    assert isinstance(response, StreamingResponse)
    stream = response.body_iterator
    first_frame = await anext(stream)
    second_frame = await anext(stream)
    assert f"id: {first.seq}\n" in first_frame
    assert "event: run_status" in second_frame
    resumed_live = await stream_run(
        str(run_id), request_for(app), log, app.state.broker, str(first.seq)
    )
    assert isinstance(resumed_live, StreamingResponse)
    resumed_stream = resumed_live.body_iterator
    assert await anext(resumed_stream) == second_frame
    await app.state.writer.run_transition(
        run_id,
        RunStatus.FAILED,
        message="stopped",
    )
    terminal_frame = await anext(stream)
    assert await anext(resumed_stream) == terminal_frame
    assert 'status": "failed' in terminal_frame
    with pytest.raises(StopAsyncIteration):
        await anext(stream)
    with pytest.raises(StopAsyncIteration):
        await anext(resumed_stream)
    frames = [first_frame, second_frame, terminal_frame]
    ids = [int(frame.split("\n", 1)[0][4:]) for frame in frames]
    assert ids == [item.seq for item in await original_list_after(run_id, None)]

    resumed = await stream_run(
        str(run_id), request_for(app), log, app.state.broker, str(first.seq)
    )
    assert isinstance(resumed, StreamingResponse)
    remaining = [item async for item in resumed.body_iterator]
    assert len(remaining) == 2
    assert "failed" in remaining[-1]


@pytest.mark.req("FR-P-04")
async def test_idle_stream_sends_keepalive(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    app = create_app(
        get_settings().model_copy(update={"sse_keepalive_seconds": 0.01}), engine
    )
    async with make_session_factory(engine)() as session:
        async with session.begin():
            row = await RunRepository(session).create(
                "Deploy AWS web service", LLMProvider.STUB, 3
            )
            run_id = row.run_id
    await app.state.event_log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        RunStatus.CREATED,
        payload=run_status_payload(),
    )
    response = await stream_run(
        str(run_id), request_for(app), app.state.event_log, app.state.broker, None
    )
    assert isinstance(response, StreamingResponse)
    stream = response.body_iterator
    assert "id: " in await anext(stream)
    assert await anext(stream) == ": keepalive\n\n"
    await stream.aclose()


@pytest.mark.req("FR-P-04", "FR-S-09")
async def test_terminal_run_stream_stays_open_during_package_retry(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    app = create_app(
        get_settings().model_copy(update={"sse_keepalive_seconds": 0.01}), engine
    )
    sessions = make_session_factory(engine)
    log = app.state.event_log
    variant = Variant.COST
    async with sessions() as session:
        async with session.begin():
            row = await RunRepository(session).create(
                "Deploy AWS web service", LLMProvider.STUB, 3
            )
            run_id = row.run_id
            await PackageRepository(session).create(run_id, variant)
    await log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        RunStatus.CREATED,
        payload=run_status_payload(),
    )
    await log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        PackageStatus.GENERATING,
        payload=package_status_payload(variant),
    )

    async def package_transition(
        previous: PackageStatus, target: PackageStatus
    ) -> None:
        async with sessions() as session:
            async with session.begin():
                await PackageRepository(session).set_status(run_id, variant, target)
        await log.append(
            run_id,
            AgentName.ORCHESTRATOR,
            target,
            previous,
            payload=package_status_payload(variant),
        )

    for previous, target in zip(
        (
            PackageStatus.GENERATING,
            PackageStatus.GENERATED,
            PackageStatus.SCANNING,
            PackageStatus.REMEDIATING,
            PackageStatus.SCAN_EXHAUSTED,
            PackageStatus.VALIDATING,
            PackageStatus.VALID,
        ),
        (
            PackageStatus.GENERATED,
            PackageStatus.SCANNING,
            PackageStatus.REMEDIATING,
            PackageStatus.SCAN_EXHAUSTED,
            PackageStatus.VALIDATING,
            PackageStatus.VALID,
            PackageStatus.PENDING_REVIEW,
        ),
        strict=True,
    ):
        await package_transition(previous, target)
    for previous, target in (
        (RunStatus.CREATED, RunStatus.RUNNING),
        (RunStatus.RUNNING, RunStatus.PARTIAL_SUCCESS),
    ):
        async with sessions() as session:
            async with session.begin():
                await RunRepository(session).set_status(run_id, target)
        await log.append(
            run_id,
            AgentName.ORCHESTRATOR,
            target,
            previous,
            payload=run_status_payload(),
        )
    await package_transition(PackageStatus.PENDING_REVIEW, PackageStatus.REMEDIATING)

    replay = await log.list_after(run_id, None)
    response = await stream_run(
        str(run_id), request_for(app), log, app.state.broker, None
    )
    assert isinstance(response, StreamingResponse)
    stream = response.body_iterator

    async def read_frame() -> str:
        return await asyncio.wait_for(anext(stream), timeout=2)

    try:
        frames = [await read_frame() for _ in replay]
        assert [int(frame.split("\n", 1)[0][4:]) for frame in frames] == [
            record.seq for record in replay
        ]
        assert '"status": "remediating"' in frames[-1]
        assert await read_frame() == ": keepalive\n\n"

        await package_transition(PackageStatus.REMEDIATING, PackageStatus.SCANNING)
        scanning = await read_frame()
        assert "event: package_status" in scanning
        assert '"status": "scanning"' in scanning
        assert await read_frame() == ": keepalive\n\n"

        await package_transition(PackageStatus.SCANNING, PackageStatus.SCAN_CLEAN)
        clean = await read_frame()
        assert "event: package_status" in clean
        assert '"status": "scan_clean"' in clean
        with pytest.raises(StopAsyncIteration):
            await read_frame()
    finally:
        await stream.aclose()


@pytest.mark.req("FR-P-04", "FR-S-09")
async def test_http_retry_stream_includes_validation_and_final_state(
    db_engines, monkeypatch
):
    from tests.integration.test_pipeline_review import (
        client_for,
        install_retry,
        pending_app,
        review_url,
        state,
    )
    from tests.integration.test_security_agent import ScriptedScanner

    app, run_id = await pending_app(db_engines[0])
    gate = asyncio.Event()
    scanning = asyncio.Event()

    class Scanner(ScriptedScanner):
        async def scan(self, *args, **kwargs):
            scanning.set()
            await gate.wait()
            return await super().scan(*args, **kwargs)

    install_retry(app, monkeypatch, scanner=Scanner([[]]))
    async with client_for(app) as client:
        assert (
            await client.post(review_url(run_id), json={"action": "retry"})
        ).status_code == 202
    await asyncio.wait_for(scanning.wait(), 2)
    response = await stream_run(
        str(run_id), request_for(app), app.state.event_log, app.state.broker, None
    )
    stream = response.body_iterator
    frames = []
    try:
        # Drain replay while scanning is explicitly held, then release the retry.
        replay = await app.state.event_log.list_after(run_id, None)
        for _ in replay:
            frames.append(await asyncio.wait_for(anext(stream), 2))
        gate.set()
        while True:
            try:
                frames.append(await asyncio.wait_for(anext(stream), 2))
            except StopAsyncIteration:
                break
    finally:
        gate.set()
        await stream.aclose()
        await asyncio.gather(*app.state.runner.tasks.values())
    data = "".join(frames)
    assert '"status": "scan_clean"' in data
    assert '"status": "validating"' in data and '"status": "checks_passed"' in data
    assert "review fix pass completed" in data
    assert (await state(app, run_id))[1].status == "checks_passed"


@pytest.mark.req("FR-P-04", "FR-S-09")
async def test_final_state_commit_does_not_close_before_its_frame(db_engines):
    from app.api.pipeline import _can_close
    from tests.integration.test_pipeline_review import pending_app

    app, run_id = await pending_app(db_engines[0])
    observed = {"cost": "pending_review"}
    async with app.state.session_factory() as session:
        async with session.begin():
            previous = await app.state.writer.review_action(
                session, run_id, Variant.COST, "approve", None
            )
    assert not await _can_close(app.state.session_factory, run_id, True, observed)
    await app.state.writer.review_event(
        run_id,
        Variant.COST,
        PackageStatus.ENGINEER_APPROVED,
        previous,
        action="approve",
        reasons=["validation_failed"],
    )
    observed["cost"] = "engineer_approved"
    assert await _can_close(app.state.session_factory, run_id, True, observed)


@pytest.mark.req("FR-P-04", "PR-02")
@pytest.mark.parametrize("read_point", ["replay", "resume", "close"])
async def test_cancelled_stream_finishes_database_read_and_cleanup(
    db_engines, monkeypatch, tmp_path, read_point
):
    """Disconnect at an explicit checkpoint while a real pooled read is owned."""
    import anyio
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.agents.validator import ValidatorAgent
    from app.validation.engine import ValidationEngine
    from tests.integration.test_pipeline_api import _empty_scanner
    from tests.integration.test_pipeline_review import client_for
    from tests.unit.test_validation_engine import Clean, mirror

    engine, _ = db_engines
    app = create_app(
        get_settings().model_copy(update={"pipeline_demo_scenario": "clean"}), engine
    )
    sessions = app.state.session_factory
    async with sessions() as session, session.begin():
        row = await RunRepository(session).create(
            "Deploy AWS web service", LLMProvider.STUB, 3
        )
        run_id = row.run_id
    event = await app.state.event_log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        RunStatus.CREATED,
        payload=run_status_payload(),
    )
    if read_point == "close":
        await app.state.writer.run_transition(
            run_id, RunStatus.FAILED, message="stopped"
        )
    response = await stream_run(
        str(run_id),
        request_for(app),
        app.state.event_log,
        app.state.broker,
        str(event.seq) if read_point == "resume" else None,
    )
    assert isinstance(response, StreamingResponse)
    stream = response.body_iterator
    if read_point == "close":
        await anext(stream)
        await anext(stream)

    entered, release, finished = anyio.Event(), anyio.Event(), anyio.Event()
    original_execute = AsyncSession.execute
    armed = True
    completed = False
    cancelled = False
    holder = []

    async def blocked_execute(session, *args, **kwargs):
        nonlocal armed, completed, cancelled
        result = await original_execute(session, *args, **kwargs)
        if armed:
            armed = False
            entered.set()
            try:
                await release.wait()
                completed = True
            except anyio.get_cancelled_exc_class():
                cancelled = True
                raise
        return result

    async def consume():
        try:
            with anyio.CancelScope() as scope:
                holder.append(scope)
                try:
                    async for _ in stream:
                        await anyio.lowlevel.checkpoint()
                finally:
                    await stream.aclose()
        finally:
            finished.set()

    # Scope matches StreamingResponse's level-triggered AnyIO disconnect.
    with monkeypatch.context() as patch:
        patch.setattr(AsyncSession, "execute", blocked_execute)
        async with anyio.create_task_group() as group:
            group.start_soon(consume)
            with anyio.fail_after(2):
                await entered.wait()
            holder[0].cancel()
            release.set()
            with anyio.fail_after(1):
                await finished.wait()
    assert completed and not cancelled, "disconnect interrupted an owned database read"
    assert run_id not in app.state.broker._subscribers
    assert engine.sync_engine.pool.checkedout() == 0

    # Same engine/pool, real orchestrator/agents/persistence, offline tool adapters.
    app.state.runner.factory.scanner = _empty_scanner()
    app.state.runner.validation_stage = ValidatorAgent(
        ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={}), sessions
    )
    async with app.router.lifespan_context(app), client_for(app) as client:
        accepted = await client.post(
            "/api/pipeline/run",
            json={"text": "Deploy an AWS web service", "config": {"provider": "stub"}},
        )
        assert accepted.status_code == 202
        await asyncio.gather(*app.state.runner.tasks.values())
        result = await client.get(f"/api/pipeline/{accepted.json()['run_id']}/results")
        assert result.status_code == 200
        body = result.json()
        assert body["run"]["status"] == "success"
        assert len(body["packages"]) == 3
        assert all(item["status"] == "checks_passed" for item in body["packages"])


@pytest.mark.req("FR-P-04", "PR-02")
@pytest.mark.parametrize("after_keepalive", [False, True])
async def test_cancelled_stream_does_not_shield_live_or_keepalive_wait(
    db_engines, monkeypatch, after_keepalive
):
    import anyio

    engine, _ = db_engines
    app = create_app(
        get_settings().model_copy(update={"sse_keepalive_seconds": 60}), engine
    )
    async with app.state.session_factory() as session, session.begin():
        row = await RunRepository(session).create(
            "Deploy AWS web service", LLMProvider.STUB, 3
        )
        run_id = row.run_id
    response = await stream_run(
        str(run_id), request_for(app), app.state.event_log, app.state.broker, None
    )
    assert isinstance(response, StreamingResponse)
    stream = response.body_iterator
    if after_keepalive:

        async def expire_first_wait(awaitable, *, timeout):
            assert timeout == 60
            awaitable.close()
            raise TimeoutError

        with monkeypatch.context() as patch:
            patch.setattr(asyncio, "wait_for", expire_first_wait)
            assert await anext(stream) == ": keepalive\n\n"
    waiting, finished = anyio.Event(), anyio.Event()
    original_get = asyncio.Queue.get
    holder = []

    async def observe_wait(queue):
        waiting.set()
        return await original_get(queue)

    async def consume():
        try:
            with anyio.CancelScope() as scope:
                holder.append(scope)
                try:
                    await anext(stream)
                finally:
                    await stream.aclose()
        finally:
            finished.set()

    monkeypatch.setattr(asyncio.Queue, "get", observe_wait)
    async with anyio.create_task_group() as group:
        group.start_soon(consume)
        with anyio.fail_after(2):
            await waiting.wait()
        holder[0].cancel()
        # A deadlock watchdog, not a PR latency measurement.
        with anyio.fail_after(0.5):
            await finished.wait()
    assert run_id not in app.state.broker._subscribers
