"""Subscribe-before-replay closes the publication/replay race."""

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.requests import Request
from starlette.responses import StreamingResponse

from app.api.pipeline import stream_run
from app.core.config import get_settings
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import AgentName, LLMProvider, RunStatus
from app.events.kinds import run_status_payload
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
