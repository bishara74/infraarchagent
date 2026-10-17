"""Explicit public allowlist for authenticated benchmark configuration evidence."""

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings, StructuredOutput


class GeneratorSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    max_output_tokens: int = Field(ge=1)
    structured_output: StructuredOutput
    attempt_timeout_seconds: float = Field(gt=0)
    completion_timeout_seconds: float = Field(gt=0)
    generator_budget_seconds: float = Field(gt=0)
    llm_max_attempts: int = Field(ge=1)
    max_package_attempts: int = Field(ge=1)
    fix_attempt_timeout_seconds: float | None = Field(default=None, gt=0)
    security_iteration_timeout_seconds: float | None = Field(default=None, gt=0)
    security_deadline_seconds: float | None = Field(default=None, gt=0)
    security_fix_max_resources: int | None = Field(default=None, ge=1)
    security_fix_max_findings: int | None = Field(default=None, ge=1)
    security_partial_max_groups: int | None = Field(default=None, ge=1)

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeneratorSettings":
        return cls(
            max_output_tokens=settings.generator_max_output_tokens,
            structured_output=settings.llm_structured_output,
            attempt_timeout_seconds=settings.generator_attempt_timeout_seconds,
            completion_timeout_seconds=settings.llm_deadline_seconds,
            generator_budget_seconds=settings.generator_deadline_seconds,
            llm_max_attempts=settings.llm_max_attempts,
            max_package_attempts=settings.generator_max_package_attempts,
            fix_attempt_timeout_seconds=settings.fix_attempt_timeout_seconds,
            security_iteration_timeout_seconds=60.0,
            security_deadline_seconds=settings.security_deadline_seconds,
            security_fix_max_resources=settings.security_fix_max_resources,
            security_fix_max_findings=settings.security_fix_max_findings,
            security_partial_max_groups=settings.security_partial_max_groups,
        )
