"""Per-run LLM and remediation choices, without transport concerns."""

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import LLMProvider

if TYPE_CHECKING:
    from app.core.config import Settings


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
        return ResolvedRunConfig(
            provider=self.provider
            if self.provider is not None
            else settings.llm_provider,
            model=self.model if self.model is not None else settings.llm_model,
            max_iterations=(
                self.max_iterations
                if self.max_iterations is not None
                else settings.max_remediation_iterations
            ),
        )
