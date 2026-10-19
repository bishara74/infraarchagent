"""User-scoped, non-secret preference API."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.requests import ClientDisconnect

from app.api.auth import failure
from app.api.deps import require_api_key
from app.core.safety import PublicDataSafety
from app.db.repositories.preferences import PreferenceRepository
from app.domain.agent_selection import ROLES, AgentChoice
from app.domain.run_config import RunConfig

router = APIRouter(prefix="/api/me", dependencies=[Depends(require_api_key)])


class UIChoices(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_scroll: bool = True
    config_open: bool = False
    report_tab: Literal["security", "validation"] = "security"


class PreferenceData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt_draft: str = Field(default="", max_length=10000)
    role_defaults: dict[str, AgentChoice] = Field(default_factory=dict)
    draft_config: dict[str, object] = Field(default_factory=dict)
    ui: UIChoices = Field(default_factory=UIChoices)


class UpdatePreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0)
    data: PreferenceData


@router.get("/preferences")
async def preferences(request: Request) -> JSONResponse:
    if request.state.user is None:
        return failure(401, "unauthorized", "Log in with an account.")
    async with request.app.state.session_factory() as session:
        result = await PreferenceRepository(session).get(request.state.user.id)
    return JSONResponse(
        PublicDataSafety(request.app.state.settings).value(result),
        headers={"Cache-Control": "no-store"},
    )


@router.put("/preferences")
async def save_preferences(request: Request) -> JSONResponse:
    if request.state.user is None:
        return failure(401, "unauthorized", "Log in with an account.")
    try:
        body = UpdatePreferences.model_validate(await request.json())
        if set(body.data.role_defaults) - {*ROLES, "generators"} or {
            "credential_id",
            "resolved_agents",
        } & set(body.data.draft_config):
            raise ValueError
        RunConfig.model_validate(body.data.draft_config)
        data = PublicDataSafety(request.app.state.settings).value(
            body.data.model_dump(mode="json")
        )
        async with request.app.state.session_factory() as session, session.begin():
            saved = await PreferenceRepository(session).save(
                request.state.user.id, body.revision, data
            )
        if not saved:
            return failure(
                409,
                "preference_conflict",
                "Preferences changed elsewhere. Reload saved preferences; "
                "your unsaved draft is retained.",
            )
        return JSONResponse({"revision": body.revision + 1, "data": data})
    except (ValueError, ValidationError, ClientDisconnect):
        return failure(
            400,
            "invalid_request",
            "Check preference fields. Secrets are not preference fields.",
        )


@router.get("/recent-runs")
async def recent(request: Request) -> JSONResponse:
    if request.state.user is None:
        return failure(401, "unauthorized", "Log in with an account.")
    async with request.app.state.session_factory() as session:
        result = await PreferenceRepository(session).recent(request.state.user.id)
    return JSONResponse(PublicDataSafety(request.app.state.settings).value(result))


class CursorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seq: int = Field(default=0, ge=0, le=9223372036854775807)


@router.put("/recent-runs/{run_id}")
async def visit(run_id: UUID, request: Request) -> JSONResponse:
    if request.state.user is None:
        return failure(401, "unauthorized", "Log in with an account.")
    try:
        body = CursorInput.model_validate(await request.json())
    except (ValueError, ValidationError, ClientDisconnect):
        return failure(400, "invalid_request", "Invalid event cursor.")
    async with request.app.state.session_factory() as session, session.begin():
        found = await PreferenceRepository(session).visit(
            request.state.user.id, run_id, body.seq
        )
    return (
        JSONResponse({"saved": True})
        if found
        else failure(404, "not_found", "Pipeline run not found.")
    )
