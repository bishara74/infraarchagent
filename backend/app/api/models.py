"""Safe model catalogs and explicit administrator defaults."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.requests import ClientDisconnect

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
async def models(request: Request, refresh: bool = False) -> JSONResponse:
    try:
        catalog = await service(request).catalog(refresh=refresh)
        from app.domain.run_config import RunConfig

        legacy = await service(request).resolve(RunConfig(), interactive=False)
        settings = request.app.state.settings
        catalog["server_default_max_iterations"] = settings.max_remediation_iterations
        # Only non-secret selection inputs, needed to mirror existing role fallbacks.
        catalog["resolution_context"] = {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "thinking_mode": settings.llm_reasoning_effort,
            "fixer_provider": settings.security_fix_provider,
            "fixer_model": settings.security_fix_model,
            "fixer_thinking_mode": settings.security_fix_reasoning_effort,
        }
        catalog["output_token_limits"] = {
            "architect": settings.llm_max_output_tokens,
            "generators": settings.generator_max_output_tokens,
            "fixer": settings.fix_max_output_tokens,
        }
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


class Capabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")
    structured_output: bool | None = None
    reasoning: bool | None = None
    thinking_modes: list[str] = Field(default_factory=list, max_length=4)


class ModelDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(default="", max_length=200)
    credential_id: str | None = None
    context_length: int | None = Field(default=None, gt=0)
    pricing: dict[str, str | float] = Field(default_factory=dict)
    capabilities: Capabilities = Field(default_factory=Capabilities)


class ModelDefaults(BaseModel):
    model_config = ConfigDict(extra="forbid")
    defaults: dict[str, AgentChoice] = Field(default_factory=dict)
    static_models: list[ModelDeclaration] = Field(default_factory=list, max_length=1000)


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
            row.static_models = safety.value(
                [item.model_dump(mode="json") for item in body.static_models]
            )
        request.app.state.catalog_cache.clear()
        return JSONResponse({"saved": True})
    except (ValueError, ValidationError, ClientDisconnect):
        return failure(
            400, "invalid_request", "Check model defaults and capability declarations."
        )


@router.get("/defaults", dependencies=[Depends(require_admin)])
async def get_defaults(request: Request) -> dict[str, object]:
    async with request.app.state.session_factory() as session, session.begin():
        row = await ProviderRepository(session).settings()
        return {"defaults": row.agent_defaults, "static_models": row.static_models}
