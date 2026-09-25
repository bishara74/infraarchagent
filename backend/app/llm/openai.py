"""OpenAI Chat Completions implementation of the LLM provider contract."""

from typing import Any

import httpx2
import openai

from app.llm.base import LLMAdapter, LLMResponse, RetryPolicy, extract_json_object
from app.llm.errors import LLMPermanentError, LLMTransientError, status_error


class OpenAIAdapter(LLMAdapter):
    provider = "openai"

    def __init__(
        self,
        model: str,
        policy: RetryPolicy,
        api_key: str,
        *,
        http_client: httpx2.AsyncClient | None = None,
    ) -> None:
        super().__init__(model, policy)
        self.client = openai.AsyncOpenAI(
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
            raise status_error(error.status_code) from None
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
