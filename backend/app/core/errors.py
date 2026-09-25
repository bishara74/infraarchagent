"""Client-safe unexpected error handling."""

import logging
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid4())
    logger.error("request %s failed", request_id, exc_info=exc)
    return JSONResponse(
        status_code=500, content={"error": "internal_error", "request_id": request_id}
    )
