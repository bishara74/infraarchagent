"""OpenAI Chat Completions implementation of the LLM provider contract."""

from typing import Any, Literal

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
        failure: LLMError
        http_status: int | None = None
        try:
            raw = await self.client.chat.completions.with_raw_response.create(**params)
            http_status = raw.http_response.status_code
            body = raw.http_response.json()
            check_error_envelope(body, http_status)
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
            raise failure from None
        except openai.APIConnectionError as error:
            failure = LLMTransientError("unreachable")
            failure.diagnostics(None, type(error).__name__)
            raise failure from None
        except openai.APIStatusError as error:
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
        except (ValueError, TypeError, openai.APIResponseValidationError) as error:
            failure = LLMResponseFormatError("invalid_json")
            failure.diagnostics(http_status, type(error).__name__)
            raise failure from None
        except openai.APIError as error:
            failure = LLMPermanentError("provider_error")
            failure.diagnostics(http_status, type(error).__name__)
            raise failure from None
        if not isinstance(completion.choices, list):
            failure = LLMResponseFormatError("empty")
            failure.diagnostics(http_status, None)
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
            http_status=http_status,
        )

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
