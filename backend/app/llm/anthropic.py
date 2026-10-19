"""Anthropic Messages implementation of the LLM provider contract."""

from typing import Any, cast

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
    check_success_body,
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
        if self.credential_resolver is not None:
            material = await self.credential_resolver()
            delegate = AnthropicAdapter(
                self.model,
                self.policy,
                material.secret.get_secret_value(),
                reasoning_effort=self.reasoning_effort,
            )
            delegate.client.base_url = material.base_url.rstrip("/") + "/"
            delegate.request_style, delegate.reasoning_capable = (
                self.request_style,
                self.reasoning_capable,
            )
            delegate.thinking_types = self.thinking_types
            delegate.structured_output, delegate.output_schema = (
                self.structured_output,
                self.output_schema,
            )
            delegate._structured_request.set(self._structured_request.get())
            try:
                return await delegate.send_prompt(
                    prompt,
                    system=system,
                    max_output_tokens=max_output_tokens,
                    timeout=timeout,
                )
            finally:
                await delegate.client.close()
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_output_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "timeout": timeout,
        }
        if self.request_style == "anthropic":
            if self.reasoning_capable and self.reasoning_effort is not None:
                if self.reasoning_effort == "off":
                    params["thinking"] = {"type": "disabled"}
                elif isinstance(self.thinking_types.get("adaptive"), dict) and cast(
                    dict[str, Any], self.thinking_types["adaptive"]
                ).get("supported"):
                    params["thinking"] = {"type": "adaptive"}
                    params["output_config"] = {"effort": self.reasoning_effort}
                else:
                    budget = {"low": 1024, "medium": 2048, "high": 4096}[
                        self.reasoning_effort
                    ]
                    if budget >= max_output_tokens:
                        raise LLMPermanentError("request_rejected")
                    params["thinking"] = {"type": "enabled", "budget_tokens": budget}
            if (
                self._structured_request.get()
                and self.structured_output == "json_schema"
            ):
                params.setdefault("output_config", {})["format"] = {
                    "type": "json_schema",
                    "schema": self.output_schema,
                }
        if system is not None:
            params["system"] = system
        failure: LLMError | None = None
        http_status: int | None = None
        try:
            raw = await self.client.messages.with_raw_response.create(**params)
            http_status = raw.http_response.status_code
            body = await raw.json()
            check_error_envelope(body, http_status)
            check_success_body(body, self.provider, http_status)
            cached = cached_response_tokens(body, "usage", "cache_read_input_tokens")
            message = await raw.parse()
        except anthropic.APITimeoutError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(None, type(error).__name__)
        except anthropic.APIConnectionError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(None, type(error).__name__)
        except anthropic.APIStatusError as error:
            retry_after, header_names = (
                rate_limit_wait(error.response.headers)
                if error.status_code == 429
                else (None, ())
            )
            failure = status_error(
                error.status_code,
                body=error.body,
                exception_class=type(error).__name__,
                retry_after=retry_after,
                rate_limit_headers=header_names,
            )
        except LLMError as error:
            failure = error
            if failure.http_status is None:
                failure.http_status = http_status
        except httpx2.TransportError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(http_status, type(error).__name__)
        except (ValueError, TypeError, anthropic.APIResponseValidationError) as error:
            failure = LLMResponseFormatError("invalid_json")
            failure.diagnostics(http_status, type(error).__name__)
        except anthropic.APIError as error:
            failure = LLMPermanentError("provider_error")
            failure.diagnostics(http_status, type(error).__name__)
        if failure is not None:
            failure.__context__ = None
            raise failure from None
        if not isinstance(message.content, list):
            failure = LLMResponseFormatError("empty")
            failure.diagnostics(http_status, None)
            raise failure from None
        return LLMResponse(
            text="".join(
                block.text for block in message.content if block.type == "text"
            ),
            input_tokens=cached_response_tokens(body, "usage", "input_tokens"),
            output_tokens=cached_response_tokens(body, "usage", "output_tokens"),
            stop_reason=message.stop_reason,
            cached_input_tokens=cached,
            http_status=http_status,
        )

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
