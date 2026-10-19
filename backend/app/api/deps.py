"""Accessors for application-owned resources."""

from typing import Annotated

from fastapi import Header, Request
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.auth import COOKIE_NAME, key_matches, origin_allowed, token_hash
from app.core.errors import ForbiddenError, UnauthorizedError
from app.events.broker import InMemoryBroker
from app.events.log import EventLog
from app.pipeline.runner import PipelineRunner
from app.pipeline.state import PipelineStateWriter


async def require_api_key(
    request: Request, supplied: Annotated[str | None, Header(alias="X-API-Key")] = None
) -> None:
    settings = request.app.state.settings
    request.state.session_hash = None
    if settings.api_key is None:
        request.state.auth_mode = "local"
    elif key_matches(settings, supplied):
        request.state.auth_mode = "shared_key"
    else:
        token = request.cookies.get(COOKIE_NAME)
        digest = token_hash(token) if token else None
        if digest is None or await request.app.state.auth.activity(digest) is None:
            raise UnauthorizedError()
        request.state.session_hash = digest
        request.state.auth_mode = "shared_key"
    if request.method not in {"GET", "HEAD", "OPTIONS"} and not origin_allowed(
        request, required=request.state.session_hash is not None
    ):
        raise ForbiddenError()


async def require_benchmark_api_key(
    request: Request, supplied: Annotated[str | None, Header(alias="X-API-Key")] = None
) -> None:
    if request.app.state.settings.api_key is None:
        raise UnauthorizedError()
    await require_api_key(request, supplied)


def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.engine  # type: ignore[no-any-return]


def get_event_log(request: Request) -> EventLog:
    return request.app.state.event_log  # type: ignore[no-any-return]


def get_broker(request: Request) -> InMemoryBroker:
    return request.app.state.broker  # type: ignore[no-any-return]


def get_runner(request: Request) -> PipelineRunner:
    return request.app.state.runner  # type: ignore[no-any-return]


def get_state_writer(request: Request) -> PipelineStateWriter:
    return request.app.state.writer  # type: ignore[no-any-return]
