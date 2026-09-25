"""Accessors for application-owned resources."""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine

from app.events.log import EventLog


def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.engine  # type: ignore[no-any-return]


def get_event_log(request: Request) -> EventLog:
    return request.app.state.event_log  # type: ignore[no-any-return]
