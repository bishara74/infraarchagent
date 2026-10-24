"""Frozen per-agent configuration; no credential material."""

from typing import Any, Literal

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
    provider_order: tuple[str, ...] = ()


def reported_selections(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    """Unprobed legacy metadata is unknown; frozen runtime choices stay intact."""
    if raw is None:
        return None
    result = {}
    for role, value in raw.items():
        selection = dict(value)
        if selection.get("request_style") == "legacy":
            selection.update(
                reasoning_capable=None, reasoning_capability_source="unprobed"
            )
        elif selection.get("request_style") in {"openai", "openrouter", "anthropic"}:
            selection["reasoning_capability_source"] = "catalog"
        result[role] = selection
    return result
