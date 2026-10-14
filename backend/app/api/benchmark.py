"""Strictly authenticated, numeric-only generator configuration evidence."""

from fastapi import APIRouter, Depends, Request

from app.api.deps import require_benchmark_api_key
from app.core.generator_settings import GeneratorSettings

router = APIRouter(
    prefix="/api/benchmark", dependencies=[Depends(require_benchmark_api_key)]
)


@router.get("/settings", response_model=GeneratorSettings)
async def generator_settings(request: Request) -> GeneratorSettings:
    return GeneratorSettings.from_settings(request.app.state.settings)
