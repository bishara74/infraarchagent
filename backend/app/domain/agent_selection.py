"""Frozen per-agent configuration; no credential material."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import LLMProvider

ROLES = (
    "architect",
    "generator_cost",
    "generator_performance",
    "generator_security",
    "fixer",
)
Thinking = Literal["off", "low", "medium", "high"]


class AgentChoice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    model: str = Field(min_length=1, max_length=128)
    thinking_mode: Thinking | None = None


class AgentSelection(AgentChoice):
    provider: LLMProvider
    configured_thinking: Thinking | None = None
    request_style: Literal["legacy", "openrouter", "openai", "anthropic"] = "legacy"
    reasoning_capable: bool = False
    thinking_types: dict[str, object] = {}
