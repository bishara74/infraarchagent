"""Fail closed before API dependencies/recovery when migration versions disagree."""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.db.schema import SchemaStatus, schema_status

logger = logging.getLogger(__name__)


class SchemaGate:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self.status: SchemaStatus | None = None
        self.lock = asyncio.Lock()
        self.logged = False
        self.restart_required = False
        self.started_incompatible = False

    async def refresh(self, engine: AsyncEngine | None = None) -> SchemaStatus:
        async with self.lock:
            status = await schema_status(engine if engine is not None else self.engine)
            if engine is None or engine is self.engine:
                self.status = status
                self.restart_required = self.started_incompatible and status.compatible
            if not status.compatible and not self.logged:
                logger.error("%s", status.message)
                self.logged = True
            return status

    async def startup(self) -> bool:
        status = await self.refresh()
        self.started_incompatible = not status.compatible
        return status.compatible

    async def current(self) -> SchemaStatus:
        return self.status if self.status is not None else await self.refresh()

    def error(self, status: SchemaStatus) -> dict[str, str]:
        return {
            "error": "database_unavailable"
            if status.state == "unavailable"
            else "database_schema_mismatch",
            "message": (
                "Database migration is complete. "
                "Restart the server to complete startup recovery."
            )
            if self.restart_required
            else status.message,
            "current_revision": status.current,
            "expected_revision": status.expected,
        }


class DatabaseSchemaMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if (
            scope["type"] == "http"
            and (path == "/api" or path.startswith("/api/"))
            and path not in {"/api/health", "/api/health/"}
        ):
            gate: SchemaGate = scope["app"].state.schema_gate
            status = await gate.current()
            if not status.compatible or gate.restart_required:
                await JSONResponse(gate.error(status), status_code=503)(
                    scope, receive, send
                )
                return
        await self.app(scope, receive, send)
