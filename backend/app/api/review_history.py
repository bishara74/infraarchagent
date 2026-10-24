"""Administrator review history; no package payloads or credential projections."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.api.deps import require_admin
from app.core.review_history import ReviewHistoryService
from app.core.safety import PublicDataSafety
from app.domain.review_categories import ReviewCategory

router = APIRouter(prefix="/api/reviews/history", dependencies=[Depends(require_admin)])


class HistoryFilters(BaseModel):
    category: ReviewCategory | Literal["not_recorded"] | None = None
    decision: Literal["approve", "reject"] | None = None
    date_from: date | None = None
    date_to: date | None = None


def service(request: Request) -> ReviewHistoryService:
    return ReviewHistoryService(
        request.app.state.session_factory, PublicDataSafety(request.app.state.settings)
    )


@router.get("")
async def history(
    request: Request, filters: Annotated[HistoryFilters, Depends()], page: int = 1
) -> Response:
    if page < 1 or (
        filters.date_from and filters.date_to and filters.date_from > filters.date_to
    ):
        return JSONResponse(
            {"error": "invalid_request", "message": "Check the page and date range."},
            status_code=400,
        )
    return JSONResponse(
        await service(request).read(
            filters.model_dump(mode="json", exclude_none=True), page
        ),
        headers={"Cache-Control": "no-store"},
    )


@router.get("/export")
async def export(
    request: Request,
    filters: Annotated[HistoryFilters, Depends()],
    format: Literal["csv", "json"] = "json",
) -> Response:
    if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
        return JSONResponse(
            {"error": "invalid_request", "message": "Check the date range."},
            status_code=400,
        )
    content = await service(request).export(
        filters.model_dump(mode="json", exclude_none=True), format
    )
    return Response(
        content,
        media_type="text/csv" if format == "csv" else "application/json",
        headers={
            "Content-Disposition": f'attachment; filename="review-history.{format}"',
            "Cache-Control": "no-store",
        },
    )
