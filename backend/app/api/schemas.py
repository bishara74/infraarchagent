"""Strict, documented Phase 7 API contracts."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.domain.plan import DeploymentPlan


class StrictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RunResult(StrictResponse):
    id: UUID
    status: RunStatus
    input_text: str
    start_time: datetime
    end_time: datetime | None
    provider: LLMProvider
    model: str | None
    max_iterations: int
    error_message: str | None


class PackageResult(StrictResponse):
    """A variant that produced files; generation failures are missing_variants."""

    variant: Variant
    status: PackageStatus
    iteration_count: int
    error: str | None
    files: dict[str, str]
    original_files: dict[str, str] | None
    security_report: dict[str, Any] | None
    validation_report: dict[str, Any] | None
    review_feedback: str | None
    readiness_label: Literal["production_ready", "not_production_ready"] | None
    downloadable: bool
    review_available: bool
    review_reasons: list[
        Literal[
            "unresolved_security_findings",
            "validation_failed",
            "validation_error",
            "retry_aborted",
        ]
    ]
    retry_targets: list[str]


class MissingVariant(StrictResponse):
    variant: Variant
    error: str


class ResultsResponse(StrictResponse):
    run: RunResult
    plan: DeploymentPlan | None
    packages: list[PackageResult]
    missing_variants: list[MissingVariant]
