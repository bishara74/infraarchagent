"""Safe model catalogs and explicit administrator defaults."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.api.auth import failure
from app.api.deps import require_admin, require_api_key
from app.core.credentials import CredentialError
from app.core.model_selection import ModelSelectionService
from app.core.safety import PublicDataSafety
from app.db.repositories.providers import ProviderRepository
from app.domain.agent_selection import ROLES, AgentChoice

router = APIRouter(prefix="/api/models", dependencies=[Depends(require_api_key)])


def service(request: Request) -> ModelSelectionService:
    return ModelSelectionService(
        request.app.state.session_factory,
        request.app.state.settings,
        request.app.state.catalog_cache,
        getattr(request.app.state, "provider_http", None),
    )


@router.get("")
async def models(request: Request) -> JSONResponse:
    try:
        catalog = await service(request).catalog()
        from app.domain.run_config import RunConfig

        legacy = await service(request).resolve(RunConfig(), interactive=False)
        catalog["environment_defaults"] = {
            k: v.model_dump(mode="json") for k, v in legacy.resolved_agents.items()
        }
        return JSONResponse(PublicDataSafety(request.app.state.settings).value(catalog))
    except CredentialError:
        return failure(
            409,
            "credential_unavailable",
            "Select an active provider and check the encryption key.",
        )


class ModelDefaults(BaseModel):
    model_config = ConfigDict(extra="forbid")
    defaults: dict[str, AgentChoice] = Field(default_factory=dict)
    static_models: list[dict[str, Any]] = Field(default_factory=list, max_length=1000)


@router.put("/defaults", dependencies=[Depends(require_admin)])
async def defaults(request: Request) -> JSONResponse:
    try:
        body = ModelDefaults.model_validate(await request.json())
        if set(body.defaults) - {*ROLES, "generators"}:
            raise ValueError
        safety = PublicDataSafety(request.app.state.settings)
        async with request.app.state.session_factory() as session, session.begin():
            row = await ProviderRepository(session).settings(lock=True)
            row.agent_defaults = safety.value(
                {k: v.model_dump() for k, v in body.defaults.items()}
            )
            row.static_models = safety.value(body.static_models)
        request.app.state.catalog_cache.clear()
        return JSONResponse({"saved": True})
    except (ValueError, ValidationError):
        return failure(
            400, "invalid_request", "Check model defaults and capability declarations."
        )
