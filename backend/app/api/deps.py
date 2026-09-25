"""Accessors for application-owned resources."""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine


def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.engine  # type: ignore[no-any-return]
