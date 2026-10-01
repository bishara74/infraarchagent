"""Accessors for application-owned resources."""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine

from app.events.broker import InMemoryBroker
from app.events.log import EventLog
from app.pipeline.runner import PipelineRunner
from app.pipeline.state import PipelineStateWriter


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
