"""Anthropic Messages implementation of the LLM provider contract."""

from typing import Any

import anthropic
import httpx2

from app.core.config import ReasoningEffort
from app.llm.base import LLMAdapter, LLMResponse, RetryPolicy, extract_json_object
from app.llm.errors import (
    LLMPermanentError,
    LLMTransientError,
    rate_limit_wait,
    status_error,
)


class AnthropicAdapter(LLMAdapter):
    provider = "anthropic"

    def __init__(
        self,
        model: str,
        policy: RetryPolicy,
        api_key: str,
        *,
        http_client: httpx2.AsyncClient | None = None,
        reasoning_effort: ReasoningEffort | None = None,
    ) -> None:
        super().__init__(model, policy, reasoning_effort=reasoning_effort)
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key, max_retries=0, http_client=http_client
        )

    async def send_prompt(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_output_tokens: int,
        timeout: float,
    ) -> LLMResponse:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_output_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "timeout": timeout,
        }
        if system is not None:
            params["system"] = system
        try:
            message = await self.client.messages.create(**params)
        except anthropic.APITimeoutError:
            raise LLMTransientError("timeout") from None
        except anthropic.APIConnectionError:
            raise LLMTransientError("connection") from None
        except anthropic.APIStatusError as error:
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
        except (anthropic.APIError, httpx2.TransportError):
            raise LLMPermanentError("provider") from None
        return LLMResponse(
            text="".join(
                block.text for block in message.content if block.type == "text"
            ),
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            stop_reason=message.stop_reason,
        )

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
