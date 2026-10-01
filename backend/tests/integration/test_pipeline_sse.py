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
