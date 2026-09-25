"""Database health endpoint; LLM credentials are optional in Phase 0."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.deps import get_engine
from app.core.config import Settings, get_settings
from app.db.session import database_is_available

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/health")
async def health(
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    configured = settings.llm_api_key is not None
    if not await database_is_available(engine):
        logger.warning("database health check failed")
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "database": "unavailable",
                "llm_configured": configured,
            },
        )
    return JSONResponse(
        content={"status": "ok", "database": "ok", "llm_configured": configured}
    )
