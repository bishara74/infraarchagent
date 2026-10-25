"""Named-account lesson endpoints. Shared-key/local access is never governance."""

from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import require_api_key
from app.core.lessons import LessonError, LessonService
from app.domain.lessons import LessonInput, LessonStatus

router = APIRouter(prefix="/api/lessons", dependencies=[Depends(require_api_key)])


class Proposal(LessonInput):
    decision_id: UUID = Field(strict=False)
    previous_id: Annotated[UUID, Field(strict=False)] | None = None


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    confirmation_token: str | None = Field(default=None, max_length=128)


class Control(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    enabled: bool


async def require_account(request: Request, response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    if request.state.auth_mode != "account" or request.state.user is None:
        raise LessonError(
            403,
            "named_account_required",
            "Sign in with a named account to curate lessons.",
        )


async def require_lesson_admin(
    request: Request, _: Annotated[None, Depends(require_account)]
) -> None:
    if request.state.user.role != "admin":
        raise LessonError(
            403, "forbidden", "A named administrator account is required."
        )


def service(request: Request) -> LessonService:
    return LessonService(
        request.app.state.session_factory,
        request.app.state.settings,
        request.app.state.event_log,
    )


async def lesson_error_handler(request: Request, error: LessonError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status,
        content={"error": error.code, "message": error.message, **error.details},
        headers={"Cache-Control": "no-store"},
    )


@router.post("/check", dependencies=[Depends(require_account)])
async def check(request: Request, body: LessonInput) -> dict[str, Any]:
    result = service(request).check(body)
    return {
        "normalized_text": body.text if result["passed"] else None,
        "filter_result": result,
    }


@router.post("", dependencies=[Depends(require_account)], status_code=201)
async def propose(request: Request, body: Proposal) -> dict[str, Any]:
    lesson = LessonInput.model_validate(
        body.model_dump(exclude={"decision_id", "previous_id"})
    )
    return await service(request).propose(
        request.state.user, body.decision_id, lesson, body.previous_id
    )


@router.get("", dependencies=[Depends(require_lesson_admin)])
async def listing(
    request: Request,
    status: LessonStatus | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    lesson_id: UUID | None = None,
) -> dict[str, Any]:
    return await service(request).listing(status, page, lesson_id)


@router.get("/control", dependencies=[Depends(require_lesson_admin)])
async def control(request: Request) -> dict[str, Any]:
    return await service(request).controls()


@router.put("/control", dependencies=[Depends(require_lesson_admin)])
async def set_control(request: Request, body: Control) -> dict[str, Any]:
    runtime = request.app.state.lesson_runtime
    async with runtime.gate:
        if not body.enabled:
            runtime.disable()
        result = await service(request).set_enabled(request.state.user, body.enabled)
        runtime.synchronize(result)
        return result


@router.get("/history", dependencies=[Depends(require_lesson_admin)])
async def history(
    request: Request, page: Annotated[int, Query(ge=1)] = 1
) -> dict[str, Any]:
    return await service(request).history(page)


@router.get("/{identity}", dependencies=[Depends(require_lesson_admin)])
async def detail(request: Request, identity: UUID) -> dict[str, Any]:
    return await service(request).detail(identity)


@router.post("/{identity}/confirmation", dependencies=[Depends(require_lesson_admin)])
async def confirmation(request: Request, identity: UUID) -> dict[str, Any]:
    return await service(request).confirmation(
        request.state.user, request.state.session_hash, identity
    )


@router.post("/{identity}/{action}", dependencies=[Depends(require_lesson_admin)])
async def transition(
    request: Request,
    identity: UUID,
    action: Literal["approve", "reject", "retire"],
    body: Action,
) -> dict[str, Any]:
    return await service(request).transition(
        request.state.user,
        request.state.session_hash,
        identity,
        action,
        body.confirmation_token,
    )
