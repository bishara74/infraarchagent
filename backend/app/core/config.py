"""Environment-backed settings. Secret values must not be logged or returned."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.domain.enums import LLMProvider

ROOT = Path(__file__).resolve().parents[3]
ReasoningEffort = Literal["off", "low", "medium", "high"]
ResponseFormat = Literal["json_object"]
StructuredOutput = Literal["json_schema", "json_object", "off"]


class ConfigurationError(ValueError):
    """A required setting is missing for a requested operation."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    log_file: Path | None = None

    @field_validator("log_file", mode="before")
    @classmethod
    def optional_log_file(cls, value: object) -> object:
        return None if value == "" else value

    database_url: SecretStr
    migration_database_url: SecretStr
    test_database_url: SecretStr
    test_migration_database_url: SecretStr
    llm_provider: LLMProvider = LLMProvider.STUB
    pipeline_demo_scenario: Literal["clean", "review"] = "clean"
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    api_key: SecretStr | None = None
    auth_idle_seconds: int = Field(default=1800, gt=0)
    auth_absolute_seconds: int = Field(default=43200, gt=0)
    auth_cookie_secure: bool = False
    auth_login_attempts_per_minute: int = Field(default=5, ge=1)
    llm_base_url: str | None = None
    llm_reasoning_effort: ReasoningEffort | None = None
    llm_response_format: ResponseFormat | None = None
    llm_structured_output: StructuredOutput = "json_schema"
    llm_prompt_cache: Literal["off", "system"] = "off"
    security_fix_provider: LLMProvider | None = None
    security_fix_model: str | None = None
    security_fix_reasoning_effort: ReasoningEffort | None = None
    broker_queue_size: int = Field(default=1000, ge=1)
    max_concurrent_runs: int = Field(default=5, ge=1)
    sse_keepalive_seconds: float = Field(default=15.0, gt=0)
    llm_attempt_timeout_seconds: float = Field(default=30.0, gt=0)
    llm_max_attempts: int = Field(default=3, ge=1)
    llm_deadline_seconds: float = Field(default=150.0, gt=0)
    agent_deadline_seconds: float = Field(default=150.0, gt=0)
    architect_max_plan_attempts: int = Field(default=3, ge=1)
    generator_deadline_seconds: float = Field(default=150.0, gt=0)
    generator_attempt_timeout_seconds: float = Field(default=120.0, gt=0)
    generator_max_output_tokens: int = Field(default=8000, ge=1)
    generator_max_package_attempts: int = Field(default=3, ge=1)
    llm_backoff_base_seconds: float = Field(default=1.0, ge=0)
    llm_max_output_tokens: int = Field(default=16000, ge=1)
    max_remediation_iterations: int = Field(default=4, ge=1)
    security_deadline_seconds: float = Field(default=240.0, gt=0)
    scanner_timeout_seconds: float = Field(default=120.0, gt=0)
    validator_tool_timeout_seconds: float = Field(default=60.0, gt=0)
    validator_max_parallel_tools: int = Field(default=3, ge=1, le=3)
    validation_repair_max_rounds: int = Field(default=2, ge=0)
    validation_deadline_seconds: float = Field(default=120.0, gt=0)
    post_security_repair_deadline_seconds: float = Field(default=60.0, gt=0)
    schema_context_max_chars: int = Field(default=16000, gt=0)
    fix_attempt_timeout_seconds: float = Field(default=90.0, gt=0)
    fix_max_output_tokens: int = Field(default=16000, ge=1)
    security_max_parallel_fixes: int = Field(default=4, ge=1)
    security_partial_max_groups: int = Field(default=6, ge=1, le=64)
    security_fix_max_resources: int = Field(default=2, ge=1, le=16)
    security_fix_max_findings: int = Field(default=12, ge=1, le=128)
    package_retention_days: int = Field(default=30, ge=1)
    log_level: str = "INFO"

    @field_validator("llm_model", mode="before")
    @classmethod
    def empty_model_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("security_fix_provider", "security_fix_model", mode="before")
    @classmethod
    def empty_fix_selection_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("llm_api_key", "api_key", mode="before")
    @classmethod
    def empty_key_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def empty_base_url_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator(
        "llm_reasoning_effort", "security_fix_reasoning_effort", mode="before"
    )
    @classmethod
    def empty_reasoning_effort_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("llm_response_format", mode="before")
    @classmethod
    def empty_response_format_is_none(cls, value: object) -> object:
        return None if value == "" else value

    def require_llm_key(self) -> str:
        if self.llm_api_key is None or not self.llm_api_key.get_secret_value():
            raise ConfigurationError("LLM_API_KEY is required for a real LLM adapter")
        return self.llm_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()


def require_llm_key(settings: Settings | None = None) -> str:
    return (settings or get_settings()).require_llm_key()
