"""Per-run LLM and remediation choices, without transport concerns."""

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import LLMProvider

if TYPE_CHECKING:
    from app.core.config import Settings


class RunConfigError(ValueError):
    """A provider override lacks its own model; message contains no input."""

    message = "model is required when overriding the provider"

    def __init__(self) -> None:
        super().__init__(self.message)


class ResolvedRunConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: LLMProvider
    model: str | None
    max_iterations: int = Field(ge=1)


class RunConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: LLMProvider | None = None
    model: str | None = None
    max_iterations: int | None = Field(default=None, ge=1)

    def resolve(self, settings: "Settings") -> ResolvedRunConfig:
        provider = self.provider if self.provider is not None else settings.llm_provider
        model: str | None
        if self.model is not None:
            model = self.model
        elif provider == settings.llm_provider:
            model = settings.llm_model
        elif provider == LLMProvider.STUB:
            model = "stub"
        else:
            raise RunConfigError()
        if model is None and provider == LLMProvider.STUB:
            model = "stub"
        return ResolvedRunConfig(
            provider=provider,
            model=model,
            max_iterations=(
                self.max_iterations
                if self.max_iterations is not None
                else settings.max_remediation_iterations
            ),
        )
