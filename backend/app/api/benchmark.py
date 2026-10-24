"""Strictly authenticated, numeric-only generator configuration evidence."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError

from app.api.auth import failure
from app.api.deps import require_benchmark_api_key
from app.api.models import service
from app.core.generator_settings import GeneratorSettings
from app.core.model_selection import ModelSelectionError
from app.core.safety import PublicDataSafety
from app.domain.agent_selection import AgentChoice, Thinking
from app.domain.run_config import RunConfig
from app.llm.public_catalogue import CatalogueError, load_snapshot, provenance

router = APIRouter(
    prefix="/api/benchmark", dependencies=[Depends(require_benchmark_api_key)]
)


@router.get("/settings", response_model=GeneratorSettings)
async def generator_settings(request: Request) -> GeneratorSettings:
    return GeneratorSettings.from_settings(request.app.state.settings)


class PreflightRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_models: dict[str, AgentChoice] = {}
    provider_preferences: dict[str, str] = {}


class PublicSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str
    thinking_mode: Thinking | None
    provider_order: list[str]


class SnapshotProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    captured_at: str
    sha256: str


class PreflightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selections: dict[str, PublicSelection]
    snapshot: SnapshotProvenance


@router.post("/preflight", response_model=PreflightResponse)
async def preflight(request: Request) -> PreflightResponse | JSONResponse:
    """Resolve only: no submission, writes, provider calls or credential lookup."""
    try:
        body = PreflightRequest.model_validate(await request.json())
        snapshot = load_snapshot(
            request.app.state.settings.openrouter_catalogue_snapshot
        )
        config = await service(request).resolve(
            RunConfig(**body.model_dump()), interactive=False
        )
        safety = PublicDataSafety(request.app.state.settings)
        return PreflightResponse(
            selections={
                role: PublicSelection(
                    model=safety.text(s.model),
                    thinking_mode=s.thinking_mode,
                    provider_order=[safety.text(p) for p in s.provider_order],
                )
                for role, s in config.resolved_agents.items()
            },
            snapshot=SnapshotProvenance(**provenance(snapshot)),
        )
    except (ValidationError, ValueError, CatalogueError, ModelSelectionError):
        return failure(
            400,
            "invalid_benchmark_config",
            "Invalid benchmark configuration or snapshot; run make catalogue-snapshot.",
        )
