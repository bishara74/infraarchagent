"""OpenAI Chat Completions implementation of the LLM provider contract."""

from typing import Any, Literal

import httpx2
import openai

from app.core.config import ReasoningEffort, ResponseFormat
from app.llm.base import LLMAdapter, LLMResponse, RetryPolicy, extract_json_object
from app.llm.errors import (
    LLMPermanentError,
    LLMTransientError,
    cached_tokens,
    rate_limit_wait,
    status_error,
)


class OpenAIAdapter(LLMAdapter):
    provider = "openai"

    def __init__(
        self,
        model: str,
        policy: RetryPolicy,
        api_key: str,
        *,
        http_client: httpx2.AsyncClient | None = None,
        base_url: str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        response_format: ResponseFormat | None = None,
        prompt_cache: Literal["off", "system"] = "off",
    ) -> None:
        super().__init__(
            model,
            policy,
            reasoning_effort=reasoning_effort,
            response_format=response_format,
        )
        self.prompt_cache = prompt_cache
        options: dict[str, Any] = {
            "api_key": api_key,
            "max_retries": 0,
            "http_client": http_client,
        }
        if base_url is not None:
            options["base_url"] = base_url
        self.client = openai.AsyncOpenAI(**options)

    async def send_prompt(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_output_tokens: int,
        timeout: float,
    ) -> LLMResponse:
        messages: list[dict[str, Any]] = []
        if system is not None:
            content: Any = system
            if self.prompt_cache == "system" and (
                self.model.startswith("anthropic/") or self.model.startswith("claude-")
            ):
                content = [
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            messages.append({"role": "system", "content": content})
        messages.append({"role": "user", "content": prompt})
        params: dict[str, Any] = {
            "model": self.model,
            "max_completion_tokens": max_output_tokens,
            "messages": messages,
            "timeout": timeout,
        }
        if self.reasoning_effort == "off":
            params["extra_body"] = {"reasoning": {"enabled": False}}
        elif self.reasoning_effort is not None:
            params["extra_body"] = {"reasoning": {"effort": self.reasoning_effort}}
        if self.response_format == "json_object":
            params["response_format"] = {"type": "json_object"}
        try:
            completion = await self.client.chat.completions.create(**params)
        except openai.APITimeoutError:
            raise LLMTransientError("timeout") from None
        except openai.APIConnectionError:
            raise LLMTransientError("connection") from None
        except openai.APIStatusError as error:
            retry_after, header_names = (
                rate_limit_wait(error.response.headers)
                if error.status_code == 429
                else (None, ())
            )
            raise status_error(
                error.status_code,
                retry_after=retry_after,
                rate_limit_headers=header_names,
            ) from None
        except (openai.APIError, httpx2.TransportError):
            raise LLMPermanentError("provider") from None
        provider = getattr(completion, "provider", None)
        served_by = provider if isinstance(provider, str) and provider else None
        details = (
            completion.usage.completion_tokens_details
            if completion.usage is not None
            else None
        )
        reported_reasoning = details.reasoning_tokens if details is not None else None
        reasoning_tokens = (
            reported_reasoning
            if isinstance(reported_reasoning, int) and reported_reasoning >= 0
            else None
        )
        prompt_details = getattr(completion.usage, "prompt_tokens_details", None)
        cached = cached_tokens(getattr(prompt_details, "cached_tokens", None))
        if not completion.choices:
            return LLMResponse(
                "",
                served_by=served_by,
                reasoning_tokens=reasoning_tokens,
                cached_input_tokens=cached,
            )
        choice = completion.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            input_tokens=completion.usage.prompt_tokens if completion.usage else None,
            output_tokens=(
                completion.usage.completion_tokens if completion.usage else None
            ),
            stop_reason=(
                "max_tokens"
                if choice.finish_reason == "length"
                else choice.finish_reason
            ),
            served_by=served_by,
            reasoning_tokens=reasoning_tokens,
            cached_input_tokens=cached,
        )

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
