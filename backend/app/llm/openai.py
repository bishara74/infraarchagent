"""OpenAI Chat Completions implementation of the LLM provider contract."""

from typing import Any

import httpx2
import openai

from app.llm.base import LLMAdapter, LLMResponse, RetryPolicy, extract_json_object
from app.llm.errors import (
    LLMPermanentError,
    LLMTransientError,
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
    ) -> None:
        super().__init__(model, policy)
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
        messages: list[dict[str, str]] = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        params: dict[str, Any] = {
            "model": self.model,
            "max_completion_tokens": max_output_tokens,
            "messages": messages,
            "timeout": timeout,
        }
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
        if not completion.choices:
            return LLMResponse(
                "", served_by=served_by, reasoning_tokens=reasoning_tokens
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
        )

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
