"""Strict, documented Phase 7 API contracts."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.domain.plan import DeploymentPlan


class StrictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RunResult(StrictResponse):
    agent_models: dict[str, Any] | None = None
    policy_profile: Literal["strict", "contextual-v1"] = "strict"
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
    profile_assessments: dict[str, Any] = Field(default_factory=dict)
    review_decision: dict[str, Any] | None = None
    review_feedback: str | None
    readiness_label: (
        Literal["checks_passed", "engineer_approved", "rejected", "pending_review"]
        | None
    )
    downloadable: bool
    review_available: bool
    retry_in_progress: bool
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


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action: Literal["approve", "retry", "reject"]
    reviewer_name: str | None = Field(default=None, max_length=120)
    reason: str | None = Field(default=None, max_length=2000)
    feedback: str | None = None
    target_files: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("feedback", mode="before")
    @classmethod
    def trimmed_feedback(cls, value: object) -> str | None:
        if not isinstance(value, str):
            raise ValueError("feedback must be text")
        trimmed = value.strip()
        if len(trimmed) > 2000:
            raise ValueError("feedback exceeds limit")
        return trimmed or None

    @model_validator(mode="after")
    def targets_only_for_retry(self) -> "ReviewRequest":
        if self.action in {"approve", "reject"}:
            if not self.reason or not self.reason.strip():
                raise ValueError("reviewer name and reason are required")
            self.reviewer_name = (
                self.reviewer_name.strip() if self.reviewer_name else None
            )
            self.reason = self.reason.strip()
        if "target_files" in self.model_fields_set and self.action != "retry":
            raise ValueError("targets require retry")
        return self


class ReviewResponse(StrictResponse):
    run_id: UUID
    variant: Variant
    status: PackageStatus


class RetryResponse(ReviewResponse):
    stream_url: str
