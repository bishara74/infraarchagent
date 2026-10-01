"""HTTP submission and SSE progress endpoints; orchestration stays in services."""

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_broker, get_event_log, get_runner, get_state_writer
from app.core.config import Settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import AgentName, RunStatus
from app.domain.input_rules import InputRuleError, validate_request_text
from app.domain.run_config import RunConfig
from app.events.broker import InMemoryBroker
from app.events.kinds import EventKind, run_status_payload, to_sse
from app.events.log import EventLog
from app.llm.errors import LLMConfigurationError
from app.llm.factory import build_adapter
from app.pipeline.runner import PipelineRunner
from app.pipeline.state import PipelineStateWriter

router = APIRouter(prefix="/api/pipeline")
TERMINAL_RUNS = {RunStatus.SUCCESS, RunStatus.PARTIAL_SUCCESS, RunStatus.FAILED}
ACTIVE_PACKAGE_STATES = {"scanning", "remediating", "validating"}


def failure(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


@router.post("/run", status_code=202)
async def submit_run(
    request: Request,
    runner: Annotated[PipelineRunner, Depends(get_runner)],
    event_log: Annotated[EventLog, Depends(get_event_log)],
    writer: Annotated[PipelineStateWriter, Depends(get_state_writer)],
) -> JSONResponse:
    try:
        body = await request.json()
    except (ValueError, UnicodeDecodeError):
        return failure(400, "invalid_request", "Request body must be valid JSON.")
    if not isinstance(body, dict) or not isinstance(body.get("text"), str):
        return failure(400, "invalid_request", "A text string is required.")
    if set(body) - {"text", "config"}:
        return failure(400, "invalid_request", "Unknown request field.")
    try:
        text = validate_request_text(body["text"])
    except InputRuleError as error:
        status = 422 if error.code == "no_infrastructure_intent" else 400
        return failure(status, error.code, error.message)
    try:
        config = RunConfig.model_validate(body.get("config") or {})
        if body.get("config") is not None and not isinstance(body["config"], dict):
            raise ValueError("config must be an object")
        settings: Settings = request.app.state.settings
        resolved = config.resolve(settings)
        build_adapter(settings, provider=resolved.provider, model=resolved.model)
    except (ValidationError, ValueError, LLMConfigurationError) as error:
        message = (
            str(error)
            if isinstance(error, LLMConfigurationError)
            else "Invalid run configuration."
        )
        return failure(400, "invalid_request", message)
    if not runner.reserve():
        return failure(429, "too_many_runs", "Too many pipeline runs are active.")
    run_id: UUID | None = None
    try:
        session_factory: async_sessionmaker[AsyncSession] = (
            request.app.state.session_factory
        )
        async with session_factory() as session:
            async with session.begin():
                row = await RunRepository(session).create(
                    text,
                    resolved.provider,
                    resolved.max_iterations,
                    model=resolved.model
                    or ("stub" if resolved.provider.value == "stub" else None),
                )
                run_id = row.run_id
        await event_log.append(
            run_id,
            AgentName.ORCHESTRATOR,
            RunStatus.CREATED,
            message="pipeline accepted",
            payload=run_status_payload(),
        )
        runner.start(run_id, text, config)
    except Exception:
        runner.release()
        if run_id is not None:
            try:
                await writer.run_transition(
                    run_id,
                    RunStatus.FAILED,
                    message="pipeline launch failed",
                    error_message="pipeline launch failed",
                )
            except Exception:
                pass
        raise
    return JSONResponse(
        status_code=202,
        content={
            "run_id": str(run_id),
            "status": RunStatus.CREATED.value,
            "stream_url": f"/api/pipeline/{run_id}/stream",
        },
    )


async def _can_close(
    session_factory: async_sessionmaker[AsyncSession],
    run_id: UUID,
    terminal_event_seen: bool,
) -> bool:
    if not terminal_event_seen:
        return False
    async with session_factory() as session:
        row = await RunRepository(session).get(run_id)
        packages = await PackageRepository(session).list_for_run(run_id)
    return (
        row is not None
        and RunStatus(row.status) in TERMINAL_RUNS
        and not any(item.status in ACTIVE_PACKAGE_STATES for item in packages)
    )


@router.get("/{run_id}/stream")
async def stream_run(
    run_id: str,
    request: Request,
    event_log: Annotated[EventLog, Depends(get_event_log)],
    broker: Annotated[InMemoryBroker, Depends(get_broker)],
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> Response:
    try:
        parsed_id = UUID(run_id)
    except ValueError:
        return failure(400, "invalid_request", "Malformed run ID.")
    if last_event_id is None:
        cursor: int | None = None
    elif last_event_id.isascii() and last_event_id.isdecimal():
        cursor = int(last_event_id)
    else:
        return failure(400, "invalid_request", "Malformed Last-Event-ID.")
    session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.session_factory
    )
    async with session_factory() as session:
        if await RunRepository(session).get(parsed_id) is None:
            return failure(404, "not_found", "Pipeline run not found.")
    keepalive: float = request.app.state.settings.sse_keepalive_seconds

    async def events() -> AsyncIterator[str]:
        last_sent = cursor
        terminal_event_seen = False
        async with broker.subscribe(parsed_id) as subscription:
            for record in await event_log.list_after(parsed_id, cursor):
                if last_sent is not None and record.seq <= last_sent:
                    continue
                yield to_sse(record)
                last_sent = record.seq
                if (
                    record.payload.get("kind") == EventKind.RUN_STATUS
                    and record.new_state in TERMINAL_RUNS
                ):
                    terminal_event_seen = True
            if cursor is not None and not terminal_event_seen:
                terminal_event_seen = any(
                    record.seq <= cursor
                    and record.payload.get("kind") == EventKind.RUN_STATUS
                    and record.new_state in TERMINAL_RUNS
                    for record in await event_log.list_after(parsed_id, None)
                )
            if await _can_close(session_factory, parsed_id, terminal_event_seen):
                return
            while not subscription.overflowed:
                try:
                    queued = await asyncio.wait_for(
                        subscription.queue.get(), timeout=keepalive
                    )
                except TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if queued is None or subscription.overflowed:
                    return
                record = queued
                if last_sent is not None and record.seq <= last_sent:
                    continue
                yield to_sse(record)
                last_sent = record.seq
                if (
                    record.payload.get("kind") == EventKind.RUN_STATUS
                    and record.new_state in TERMINAL_RUNS
                ):
                    terminal_event_seen = True
                if await _can_close(session_factory, parsed_id, terminal_event_seen):
                    return

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
