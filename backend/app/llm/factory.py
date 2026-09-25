"""Configuration-based provider selection."""

from app.core.config import ConfigurationError, Settings
from app.domain.enums import LLMProvider
from app.llm.anthropic import AnthropicAdapter
from app.llm.base import LLMAdapter, RetryPolicy
from app.llm.errors import LLMConfigurationError
from app.llm.openai import OpenAIAdapter
from app.llm.stub import StubAdapter


def build_adapter(
    settings: Settings,
    *,
    provider: LLMProvider | str | None = None,
    model: str | None = None,
    policy: RetryPolicy | None = None,
) -> LLMAdapter:
    try:
        selected = LLMProvider(provider or settings.llm_provider)
    except ValueError:
        raise LLMConfigurationError("Unknown LLM_PROVIDER") from None
    chosen_policy = policy or RetryPolicy.from_settings(settings)
    if selected is LLMProvider.STUB:
        return StubAdapter(model or settings.llm_model or "stub", chosen_policy)
    chosen_model = model or settings.llm_model
    if not chosen_model:
        raise LLMConfigurationError("LLM_MODEL is required for a real LLM adapter")
    try:
        key = settings.require_llm_key()
    except ConfigurationError:
        raise LLMConfigurationError(
            "LLM_API_KEY is required for a real LLM adapter"
        ) from None
    if selected is LLMProvider.ANTHROPIC:
        return AnthropicAdapter(chosen_model, chosen_policy, key)
    return OpenAIAdapter(chosen_model, chosen_policy, key)
