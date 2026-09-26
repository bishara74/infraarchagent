"""OpenAI Chat Completions implementation of the LLM provider contract."""

from typing import Any

import httpx2
import openai

from app.llm.base import LLMAdapter, LLMResponse, RetryPolicy, extract_json_object
from app.llm.errors import (
    LLMPermanentError,
    LLMTransientError,
    parse_retry_after,
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
            retry_after = (
                parse_retry_after(error.response.headers.get("retry-after"))
                if error.status_code == 429
                else None
            )
            raise status_error(error.status_code, retry_after=retry_after) from None
        except (openai.APIError, httpx2.TransportError):
            raise LLMPermanentError("provider") from None
        if not completion.choices:
            return LLMResponse("")
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
        )

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
