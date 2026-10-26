"""Connectivity and read-only migration compatibility; never migrate here."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.deps import get_engine
from app.core.config import Settings, get_settings
from app.core.schema_gate import SchemaGate

router = APIRouter()


@router.get("/api/health")
async def health(
    request: Request,
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    gate: SchemaGate = request.app.state.schema_gate
    status = await gate.refresh(engine)
    ready = status.compatible and not gate.restart_required
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ok" if ready else "degraded",
            "database": "unavailable" if status.state == "unavailable" else "ok",
            "schema": {
                "current_revision": status.current,
                "expected_revision": status.expected,
                "compatible": status.compatible,
                "state": status.state,
                "restart_required": gate.restart_required,
            },
            **({} if ready else gate.error(status)),
            "llm_configured": settings.llm_api_key is not None,
            "runner_capacity": request.app.state.runner.capacity,
            "scanners": request.app.state.scanners,
            "validators": request.app.state.validators,
            "provider_mirror_present": request.app.state.provider_mirror_present,
        },
    )
