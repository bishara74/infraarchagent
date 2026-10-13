"""Anthropic Messages implementation of the LLM provider contract."""

from typing import Any

import anthropic
import httpx2

from app.core.config import ReasoningEffort
from app.llm.base import LLMAdapter, LLMResponse, RetryPolicy, extract_json_object
from app.llm.errors import (
    LLMError,
    LLMPermanentError,
    LLMResponseFormatError,
    LLMTransientError,
    cached_response_tokens,
    check_error_envelope,
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
        failure: LLMError
        http_status: int | None = None
        try:
            raw = await self.client.messages.with_raw_response.create(**params)
            http_status = raw.http_response.status_code
            body = await raw.json()
            check_error_envelope(body, http_status)
            cached = cached_response_tokens(body, "usage", "cache_read_input_tokens")
            message = await raw.parse()
        except anthropic.APITimeoutError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(None, type(error).__name__)
            raise failure from None
        except anthropic.APIConnectionError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(None, type(error).__name__)
            raise failure from None
        except anthropic.APIStatusError as error:
            retry_after, header_names = (
                rate_limit_wait(error.response.headers)
                if error.status_code == 429
                else (None, ())
            )
            raise status_error(
                error.status_code,
                body=error.body,
                exception_class=type(error).__name__,
                retry_after=retry_after,
                rate_limit_headers=header_names,
            ) from None
        except LLMError:
            raise
        except httpx2.TransportError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(http_status, type(error).__name__)
            raise failure from None
        except (ValueError, TypeError, anthropic.APIResponseValidationError) as error:
            failure = LLMResponseFormatError("invalid_json")
            failure.diagnostics(http_status, type(error).__name__)
            raise failure from None
        except anthropic.APIError as error:
            failure = LLMPermanentError("provider_error")
            failure.diagnostics(http_status, type(error).__name__)
            raise failure from None
        if not isinstance(message.content, list):
            failure = LLMResponseFormatError("empty")
            failure.diagnostics(http_status, None)
            raise failure from None
        return LLMResponse(
            text="".join(
                block.text for block in message.content if block.type == "text"
            ),
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            stop_reason=message.stop_reason,
            cached_input_tokens=cached,
            http_status=http_status,
        )

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
