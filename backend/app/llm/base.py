"""Provider-independent JSON completion and timing policy."""

import asyncio
import json
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from app.core.config import ReasoningEffort, ResponseFormat, Settings
from app.llm.errors import (
    LLMDeadlineExceeded,
    LLMPermanentError,
    LLMResponseFormatError,
    LLMRetryExhausted,
    LLMTransientError,
    ResponseStats,
)

logger = logging.getLogger(__name__)
FENCE = re.compile(r"```(?:json)?[ \t]*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class RetryPolicy:
    attempt_timeout: float
    max_attempts: int
    deadline: float
    backoff_base: float
    max_output_tokens: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "RetryPolicy":
        return cls(
            attempt_timeout=settings.llm_attempt_timeout_seconds,
            max_attempts=settings.llm_max_attempts,
            deadline=settings.llm_deadline_seconds,
            backoff_base=settings.llm_backoff_base_seconds,
            max_output_tokens=settings.llm_max_output_tokens,
        )


@dataclass(frozen=True)
class LLMResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    stop_reason: str | None = None
    served_by: str | None = None
    reasoning_tokens: int | None = None

    def stats(self) -> ResponseStats:
        return ResponseStats(
            self.input_tokens,
            self.output_tokens,
            self.stop_reason,
            len(self.text),
        )


@dataclass(frozen=True)
class LLMResult:
    data: dict[str, Any]
    response: LLMResponse
    attempts: int
    elapsed_seconds: float


def extract_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if not candidate:
        raise LLMResponseFormatError("empty")
    if candidate.count("```") >= 4:
        raise LLMResponseFormatError("multiple_blocks")
    fenced = FENCE.fullmatch(candidate)
    if fenced:
        candidate = fenced.group(1).strip()
    elif candidate.startswith("```"):
        raise LLMResponseFormatError(
            "truncated" if candidate.count("```") == 1 else "prose_after"
        )
    elif "```" in candidate:
        raise LLMResponseFormatError("prose_before")
    if not candidate:
        raise LLMResponseFormatError("empty")
    if not candidate.startswith("{"):
        if "{" in candidate:
            raise LLMResponseFormatError("prose_before")
        try:
            json.loads(candidate)
        except (ValueError, TypeError):
            pass
        else:
            raise LLMResponseFormatError("not_object")
    try:
        parsed, end = json.JSONDecoder().raw_decode(candidate)
    except json.JSONDecodeError as error:
        incomplete = error.pos >= len(candidate) - 1 and (
            "Unterminated" in error.msg
            or "Expecting value" in error.msg
            or "Expecting ',' delimiter" in error.msg
            or "Expecting property name" in error.msg
        )
        raise LLMResponseFormatError(
            "truncated" if incomplete else f"syntax_error@{error.pos}"
        ) from None
    if not isinstance(parsed, dict):
        raise LLMResponseFormatError("not_object")
    if candidate[end:].strip():
        raise LLMResponseFormatError("prose_after")
    return parsed


class LLMAdapter(ABC):
    provider = "unknown"

    def __init__(
        self,
        model: str,
        policy: RetryPolicy,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        response_format: ResponseFormat | None = None,
    ) -> None:
        self.model = model
        self.policy = policy
        self.reasoning_effort = reasoning_effort
        self.response_format = response_format
        self._sleep = sleep
        self._clock = clock
        self._rng = rng or random.Random()

    @abstractmethod
    async def send_prompt(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_output_tokens: int,
        timeout: float,
    ) -> LLMResponse: ...

    @abstractmethod
    def parse_response(self, response: LLMResponse) -> dict[str, Any]: ...

    async def complete_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        deadline: float | None = None,
        attempt_timeout: float | None = None,
        max_output_tokens: int | None = None,
    ) -> LLMResult:
        if attempt_timeout is not None and (
            not isinstance(attempt_timeout, (int, float))
            or not 0 < attempt_timeout < float("inf")
        ):
            raise ValueError("attempt_timeout must be finite and positive")
        if max_output_tokens is not None and max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
        started = self._clock()
        ends_at = (
            started + min(self.policy.deadline, deadline)
            if deadline is not None
            else started + self.policy.deadline
        )
        last_stats: ResponseStats | None = None
        for attempt in range(1, self.policy.max_attempts + 1):
            remaining = ends_at - self._clock()
            if remaining <= 0:
                raise LLMDeadlineExceeded(attempt - 1, self._clock() - started)
            selected_timeout = (
                attempt_timeout
                if attempt_timeout is not None
                else self.policy.attempt_timeout
            )
            timeout = min(selected_timeout, remaining)
            attempt_started = self._clock()
            response: LLMResponse | None = None
            last_stats = None
            retry_after: float | None = None
            rate_limit_headers: tuple[str, ...] = ()
            category = "success"
            format_reason: str | None = None
            try:
                response = await asyncio.wait_for(
                    self.send_prompt(
                        prompt,
                        system=system,
                        max_output_tokens=(
                            max_output_tokens
                            if max_output_tokens is not None
                            else self.policy.max_output_tokens
                        ),
                        timeout=timeout,
                    ),
                    timeout=timeout,
                )
                last_stats = response.stats()
                if response.stop_reason == "max_tokens":
                    raise LLMResponseFormatError("truncated", last_stats)
                data = self.parse_response(response)
                if self._clock() >= ends_at:
                    raise LLMDeadlineExceeded(attempt, self._clock() - started)
                return LLMResult(data, response, attempt, self._clock() - started)
            except TimeoutError:
                category = "timeout"
            except asyncio.CancelledError:
                category = "cancelled"
                raise
            except LLMTransientError as error:
                category = error.category
                retry_after = error.retry_after
                rate_limit_headers = error.rate_limit_headers
            except LLMResponseFormatError as error:
                category = (
                    "truncated" if error.reason == "truncated" else "invalid_json"
                )
                format_reason = error.reason
                last_stats = error.stats or last_stats
            except LLMDeadlineExceeded:
                category = "deadline"
                raise
            except LLMPermanentError as error:
                category = error.category
                raise
            except Exception:
                category = "unexpected"
                raise LLMPermanentError("unexpected") from None
            finally:
                stats = response.stats() if response is not None else None
                fields = [
                    f"provider={self.provider}",
                    f"model={self.model}",
                    f"attempt={attempt}",
                    f"outcome={category}",
                    f"reasoning_effort={self.reasoning_effort or 'unset'}",
                    f"latency={self._clock() - attempt_started:.3f}",
                    f"input_tokens={stats.input_tokens if stats else None}",
                    f"output_tokens={stats.output_tokens if stats else None}",
                    f"prompt_chars={len(prompt)}",
                    f"system_chars={len(system) if system else 0}",
                    f"retry_after={retry_after if retry_after is not None else 'none'}",
                    "rate_limit_headers="
                    + (",".join(rate_limit_headers) if rate_limit_headers else "none"),
                ]
                if response is not None and response.served_by is not None:
                    host = quote(response.served_by, safe="@._/-")
                    fields.append(f"served_by={host}")
                if response is not None and response.reasoning_tokens is not None:
                    fields.append(f"reasoning_tokens={response.reasoning_tokens}")
                if format_reason is not None:
                    fields.append(f"format_reason={format_reason}")
                logger.info("%s", " ".join(fields))
            elapsed = self._clock() - started
            if self._clock() >= ends_at:
                raise LLMDeadlineExceeded(attempt, elapsed)
            if attempt >= self.policy.max_attempts:
                raise LLMRetryExhausted(attempt, elapsed, category, last_stats)
            backoff = self.policy.backoff_base * 2 ** (attempt - 1)
            remaining = ends_at - self._clock()
            if retry_after is not None and retry_after >= remaining:
                raise LLMDeadlineExceeded(attempt, self._clock() - started)
            delay = min(max(self._rng.uniform(0, backoff), retry_after or 0), remaining)
            if delay > 0:
                await self._sleep(delay)
        raise LLMRetryExhausted(
            self.policy.max_attempts, self._clock() - started, "unknown"
        )
