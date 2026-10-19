"""HTTP submission and SSE progress endpoints; orchestration stays in services."""

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

import anyio
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import (
    get_broker,
    get_event_log,
    get_runner,
    get_state_writer,
    require_api_key,
)
from app.api.models import service as model_service
from app.api.schemas import (
    ResultsResponse,
    RetryResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.core.config import Settings
from app.core.credentials import CredentialError
from app.core.model_selection import ModelSelectionError
from app.core.safety import PublicDataSafety
from app.db.repositories.packages import PackageRepository
from app.db.repositories.preferences import PreferenceRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import AgentName, RunStatus, Variant
from app.domain.input_rules import InputRuleError, validate_request_text
from app.domain.run_config import RunConfig, RunConfigError
from app.events.broker import InMemoryBroker
from app.events.kinds import EventKind, event_status, run_status_payload, to_sse
from app.events.log import EventLog
from app.events.publisher import EventRecord
from app.llm.errors import LLMConfigurationError
from app.llm.factory import build_adapter
from app.pipeline.results import ResultsService
from app.pipeline.review import ReviewError, ReviewService
from app.pipeline.runner import PipelineRunner
from app.pipeline.state import PipelineStateWriter

router = APIRouter(prefix="/api/pipeline", dependencies=[Depends(require_api_key)])
TERMINAL_RUNS = {RunStatus.SUCCESS, RunStatus.PARTIAL_SUCCESS, RunStatus.FAILED}
ACTIVE_PACKAGE_STATES = {"scanning", "remediating", "validating"}


def failure(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


@router.get("/{run_id}/results", response_model=ResultsResponse)
async def get_results(run_id: str, request: Request) -> ResultsResponse | JSONResponse:
    try:
        parsed = UUID(run_id)
    except ValueError:
        return failure(400, "invalid_request", "Malformed run ID.")
    result = await ResultsService(
        request.app.state.session_factory, request.app.state.settings
    ).results(parsed)
    return (
        result
        if result is not None
        else failure(404, "not_found", "Pipeline run not found.")
    )


@router.post(
    "/{run_id}/packages/{variant}/review",
    response_model=ReviewResponse | RetryResponse,
    responses={202: {"model": RetryResponse}},
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": ReviewRequest.model_json_schema()}
            },
        }
    },
)
async def review_package(run_id: str, variant: str, request: Request) -> Response:
    try:
        parsed = UUID(run_id)
        selected = Variant(variant)
        body = ReviewRequest.model_validate(await request.json())
    except (ValueError, UnicodeDecodeError):
        return failure(400, "invalid_request", "Invalid review request.")
    try:
        result = await ReviewService(request.app.state.runner).review(
            parsed,
            selected,
            body,
            auth_mode=request.state.auth_mode,
            user=request.state.user,
        )
    except ReviewError as error:
        return failure(error.status, error.code, error.message)
    return JSONResponse(
        status_code=202 if isinstance(result, RetryResponse) else 200,
        content=result.model_dump(mode="json"),
    )


@router.get(
    "/{run_id}/download/{variant}",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/zip": {"schema": {"type": "string", "format": "binary"}}
            }
        }
    },
)
async def download_package(run_id: str, variant: str, request: Request) -> Response:
    try:
        parsed, selected = UUID(run_id), Variant(variant)
    except ValueError:
        return failure(400, "invalid_request", "Invalid download request.")
    try:
        archive, filename = await ResultsService(
            request.app.state.session_factory, request.app.state.settings
        ).download(parsed, selected)
    except ReviewError as error:
        return failure(error.status, error.code, error.message)
    return Response(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
        text = PublicDataSafety(request.app.state.settings).text(
            validate_request_text(body["text"])
        )
    except InputRuleError as error:
        status = 422 if error.code == "no_infrastructure_intent" else 400
        return failure(status, error.code, error.message)
    try:
        if isinstance(body.get("config"), dict) and (
            {"resolved_agents", "credential_id"} & set(body["config"])
        ):
            raise ValueError("Private configuration fields")
        config = RunConfig.model_validate(body.get("config") or {})
        if body.get("config") is not None and not isinstance(body["config"], dict):
            raise ValueError("config must be an object")
        settings: Settings = request.app.state.settings
        personal = None
        if request.state.user:
            async with request.app.state.session_factory() as session:
                personal = (
                    await PreferenceRepository(session).get(request.state.user.id)
                )["data"].get("role_defaults")
        config = await model_service(request).resolve(
            config, interactive=request.state.auth_mode == "account", personal=personal
        )
        resolved = config.resolve(settings)
        if not config.credential_id:
            build_adapter(settings, provider=resolved.provider, model=resolved.model)
    except ModelSelectionError as error:
        return failure(400, "invalid_model", str(error))
    except CredentialError:
        return failure(
            409,
            "credential_unavailable",
            "Select an active provider and check the encryption key.",
        )
    except RunConfigError as error:
        return failure(400, "invalid_request", error.message)
    except (
        ValidationError,
        ValueError,
        LLMConfigurationError,
    ) as error:
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
                    policy_profile=resolved.policy_profile,
                    model=PublicDataSafety(settings).value(resolved.model),
                    user_id=request.state.user.id if request.state.user else None,
                    agent_models=PublicDataSafety(settings).value(
                        {
                            k: v.model_dump(mode="json")
                            for k, v in config.resolved_agents.items()
                        }
                    ),
                    credential_id=config.credential_id,
                )
                run_id = row.run_id
                if request.state.user:
                    await PreferenceRepository(session).visit(
                        request.state.user.id, run_id
                    )
        await event_log.append(
            run_id,
            AgentName.ORCHESTRATOR,
            RunStatus.CREATED,
            message="pipeline accepted",
            payload={
                **run_status_payload(),
                "policy_profile": resolved.policy_profile,
                "agent_models": {
                    k: v.model_dump(mode="json")
                    for k, v in config.resolved_agents.items()
                },
            },
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
    observed_packages: dict[str, str],
) -> bool:
    if not terminal_event_seen:
        return False
    # StreamingResponse disconnects use level-triggered cancellation. Finish
    # the owned read and return its connection before honoring that cancellation.
    with anyio.CancelScope(shield=True):
        async with session_factory() as session:
            row = await RunRepository(session).get(run_id)
            packages = await PackageRepository(session).list_for_run(run_id)
    return (
        row is not None
        and RunStatus(row.status) in TERMINAL_RUNS
        and not any(
            item.status in ACTIVE_PACKAGE_STATES
            or item.review_retry_started_at is not None
            for item in packages
        )
        and all(observed_packages.get(item.variant) == item.status for item in packages)
    )


async def _replay_records(
    event_log: EventLog, run_id: UUID, cursor: int | None
) -> list[EventRecord]:
    # Includes list_after's session cleanup, but never a yield or live wait.
    with anyio.CancelScope(shield=True):
        records = await event_log.list_after(run_id, cursor)
    return records


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
        current_packages = await PackageRepository(session).list_for_run(parsed_id)
    keepalive: float = request.app.state.settings.sse_keepalive_seconds
    safety = PublicDataSafety(request.app.state.settings)

    async def active_session() -> bool:
        if getattr(request.state, "auth_mode", None) == "local":
            return not await request.app.state.auth.has_users()
        digest = getattr(request.state, "session_hash", None)
        return (
            digest is None or await request.app.state.auth.activity(digest) is not None
        )

    async def events() -> AsyncIterator[str]:
        last_sent = cursor
        terminal_event_seen = False
        observed_packages: dict[str, str] = {}
        legacy_outcomes: dict[int, str] = {}

        def observe(record: EventRecord) -> None:
            nonlocal terminal_event_seen
            if (
                record.payload.get("kind") == EventKind.RUN_STATUS
                and record.new_state in TERMINAL_RUNS
            ):
                terminal_event_seen = True
            elif record.payload.get("kind") == EventKind.PACKAGE_STATUS:
                observed_packages[str(record.payload.get("variant"))] = event_status(
                    record, legacy_outcomes.get(record.seq)
                )

        async with broker.subscribe(parsed_id) as subscription:
            records = await _replay_records(event_log, parsed_id, None)
            latest = {
                r.payload.get("variant"): r
                for r in records
                if r.payload.get("kind") == EventKind.PACKAGE_STATUS
            }
            for item in current_packages:
                record = latest.get(item.variant)
                if (
                    record
                    and record.new_state in {"production_ready", "not_production_ready"}
                    and item.status
                    in {
                        "checks_passed",
                        "engineer_approved",
                        "rejected",
                        "pending_review",
                    }
                ):
                    legacy_outcomes[record.seq] = item.status
            if cursor is not None:
                for record in records:
                    if record.seq <= cursor:
                        observe(record)
            for record in records:
                if last_sent is not None and record.seq <= last_sent:
                    continue
                if not await active_session():
                    return
                yield safety.text(
                    to_sse(record, legacy_status=legacy_outcomes.get(record.seq))
                )
                last_sent = record.seq
                observe(record)
                if (
                    record.payload.get("kind") == EventKind.RUN_STATUS
                    and record.new_state in TERMINAL_RUNS
                ):
                    terminal_event_seen = True
            if await _can_close(
                session_factory, parsed_id, terminal_event_seen, observed_packages
            ):
                return
            while not subscription.overflowed:
                try:
                    queued = await asyncio.wait_for(
                        subscription.queue.get(), timeout=keepalive
                    )
                except TimeoutError:
                    if not await active_session():
                        return
                    yield ": keepalive\n\n"
                    continue
                if queued is None or subscription.overflowed:
                    return
                record = queued
                if last_sent is not None and record.seq <= last_sent:
                    continue
                if not await active_session():
                    return
                yield safety.text(
                    to_sse(record, legacy_status=legacy_outcomes.get(record.seq))
                )
                last_sent = record.seq
                if (
                    record.payload.get("kind") == EventKind.RUN_STATUS
                    and record.new_state in TERMINAL_RUNS
                ):
                    terminal_event_seen = True
                observe(record)
                if await _can_close(
                    session_factory, parsed_id, terminal_event_seen, observed_packages
                ):
                    return

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{run_id}/events")
async def history(
    run_id: UUID, request: Request, after: int = 0, through: int | None = None
) -> JSONResponse:
    if after < 0 or (through is not None and through < 0):
        return failure(400, "invalid_request", "Invalid event cursor.")
    async with request.app.state.session_factory() as session:
        if await RunRepository(session).get(run_id) is None:
            return failure(404, "not_found", "Pipeline run not found.")
        packages = await PackageRepository(session).list_for_run(run_id)
    records = await _replay_records(request.app.state.event_log, run_id, None)
    latest = {
        r.payload.get("variant"): r
        for r in records
        if r.payload.get("kind") == EventKind.PACKAGE_STATUS
    }
    outcomes = {
        latest[p.variant].seq: p.status for p in packages if p.variant in latest
    }
    page = [
        r for r in records if r.seq > after and (through is None or r.seq <= through)
    ]
    import json

    events = [
        json.loads(to_sse(r, legacy_status=outcomes.get(r.seq)).split("data: ", 1)[1])
        for r in page[:500]
    ]
    return JSONResponse(
        PublicDataSafety(request.app.state.settings).value(
            {"events": events, "has_more": len(page) > 500}
        ),
        headers={"Cache-Control": "no-store"},
    )
