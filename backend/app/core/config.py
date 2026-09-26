"""Environment-backed settings. Secret values must not be logged or returned."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.domain.enums import LLMProvider

ROOT = Path(__file__).resolve().parents[3]


class ConfigurationError(ValueError):
    """A required setting is missing for a requested operation."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    database_url: SecretStr
    migration_database_url: SecretStr
    test_database_url: SecretStr
    test_migration_database_url: SecretStr
    llm_provider: LLMProvider = LLMProvider.STUB
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    llm_attempt_timeout_seconds: float = Field(default=30.0, gt=0)
    llm_max_attempts: int = Field(default=3, ge=1)
    llm_deadline_seconds: float = Field(default=150.0, gt=0)
    llm_backoff_base_seconds: float = Field(default=1.0, ge=0)
    llm_max_output_tokens: int = Field(default=16000, ge=1)
    max_remediation_iterations: int = Field(default=3, ge=1)
    package_retention_days: int = Field(default=30, ge=1)
    log_level: str = "INFO"

    @field_validator("llm_model", mode="before")
    @classmethod
    def empty_model_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("llm_api_key", mode="before")
    @classmethod
    def empty_key_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def empty_base_url_is_none(cls, value: object) -> object:
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
