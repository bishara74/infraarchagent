"""OpenAI Chat Completions implementation of the LLM provider contract."""

from typing import Any, Literal
from urllib.parse import urlparse

import httpx2
import openai

from app.core.config import ReasoningEffort, ResponseFormat
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


class OpenAIAdapter(LLMAdapter):
    provider = "openai"
    supports_structured_output = True

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
        structured_output = (
            self.structured_output if self._generator_request.get() else None
        )
        if structured_output == "json_schema":
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "generator_package",
                    "strict": True,
                    "schema": self.output_schema,
                },
            }
            if urlparse(str(self.client.base_url)).hostname == "openrouter.ai":
                params.setdefault("extra_body", {})["provider"] = {
                    "require_parameters": True
                }
        elif structured_output == "json_object" or (
            structured_output is None and self.response_format == "json_object"
        ):
            params["response_format"] = {"type": "json_object"}
        failure: LLMError | None = None
        http_status: int | None = None
        try:
            raw = await self.client.chat.completions.with_raw_response.create(**params)
            http_status = raw.http_response.status_code
            body = raw.http_response.json()
            check_error_envelope(body, http_status)
            check_success_body(body, self.provider, http_status)
            cached = cached_response_tokens(
                body,
                "usage",
                "prompt_tokens_details",
                "cached_tokens",
            )
            completion = raw.parse()
        except openai.APITimeoutError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(None, type(error).__name__)
        except openai.APIConnectionError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(None, type(error).__name__)
        except openai.APIStatusError as error:
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
        except (ValueError, TypeError, openai.APIResponseValidationError) as error:
            failure = LLMResponseFormatError("invalid_json")
            failure.diagnostics(http_status, type(error).__name__)
        except openai.APIError as error:
            failure = LLMPermanentError("provider_error")
            failure.diagnostics(http_status, type(error).__name__)
        if failure is not None:
            failure.__context__ = None
            raise failure from None
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
                "",
                served_by=served_by,
                reasoning_tokens=reasoning_tokens,
                cached_input_tokens=cached,
                http_status=http_status,
            )
        choice = completion.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            input_tokens=cached_response_tokens(body, "usage", "prompt_tokens"),
            output_tokens=(cached_response_tokens(body, "usage", "completion_tokens")),
            stop_reason=(
                "max_tokens"
                if choice.finish_reason == "length"
                else choice.finish_reason
            ),
            served_by=served_by,
            reasoning_tokens=reasoning_tokens,
            cached_input_tokens=cached,
            http_status=http_status,
        )

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
