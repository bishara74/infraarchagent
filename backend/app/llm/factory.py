"""Configuration-based provider selection."""

from app.core.config import ConfigurationError, ReasoningEffort, Settings
from app.domain.enums import LLMProvider
from app.domain.run_config import RunConfig, RunConfigError
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
    reasoning_effort: ReasoningEffort | None = None,
) -> LLMAdapter:
    try:
        selected = LLMProvider(provider or settings.llm_provider)
    except ValueError:
        raise LLMConfigurationError("Unknown LLM_PROVIDER") from None
    try:
        resolved = RunConfig(provider=selected, model=model).resolve(settings)
    except RunConfigError as error:
        raise LLMConfigurationError(str(error)) from None
    chosen_policy = policy or RetryPolicy.from_settings(settings)
    chosen_effort = reasoning_effort or settings.llm_reasoning_effort
    if selected is LLMProvider.STUB:
        assert resolved.model is not None
        return StubAdapter(
            resolved.model,
            chosen_policy,
            reasoning_effort=chosen_effort,
            response_format=settings.llm_response_format,
        )
    chosen_model = resolved.model
    if not chosen_model:
        raise LLMConfigurationError("LLM_MODEL is required for a real LLM adapter")
    try:
        key = settings.require_llm_key()
    except ConfigurationError:
        raise LLMConfigurationError(
            "LLM_API_KEY is required for a real LLM adapter"
        ) from None
    if selected is LLMProvider.ANTHROPIC:
        return AnthropicAdapter(
            chosen_model,
            chosen_policy,
            key,
            reasoning_effort=chosen_effort,
        )
    if settings.llm_response_format is None:
        return OpenAIAdapter(
            chosen_model,
            chosen_policy,
            key,
            base_url=settings.llm_base_url,
            prompt_cache=settings.llm_prompt_cache,
            reasoning_effort=chosen_effort,
        )
    return OpenAIAdapter(
        chosen_model,
        chosen_policy,
        key,
        base_url=settings.llm_base_url,
        prompt_cache=settings.llm_prompt_cache,
        reasoning_effort=chosen_effort,
        response_format=settings.llm_response_format,
    )
