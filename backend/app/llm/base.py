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

from app.core.config import Settings
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
    fenced = FENCE.fullmatch(candidate)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        parsed = json.loads(candidate)
    except (ValueError, TypeError):
        raise LLMResponseFormatError() from None
    if not isinstance(parsed, dict):
        raise LLMResponseFormatError()
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
    ) -> None:
        self.model = model
        self.policy = policy
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
        self, prompt: str, *, system: str | None = None
    ) -> LLMResult:
        started = self._clock()
        ends_at = started + self.policy.deadline
        last_stats: ResponseStats | None = None
        for attempt in range(1, self.policy.max_attempts + 1):
            remaining = ends_at - self._clock()
            if remaining <= 0:
                raise LLMDeadlineExceeded(attempt - 1, self._clock() - started)
            timeout = min(self.policy.attempt_timeout, remaining)
            attempt_started = self._clock()
            response: LLMResponse | None = None
            last_stats = None
            retry_after: float | None = None
            category = "success"
            try:
                response = await asyncio.wait_for(
                    self.send_prompt(
                        prompt,
                        system=system,
                        max_output_tokens=self.policy.max_output_tokens,
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
            except LLMResponseFormatError as error:
                category = error.reason
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
                logger.info(
                    "provider=%s model=%s attempt=%d outcome=%s latency=%.3f "
                    "input_tokens=%s output_tokens=%s prompt_chars=%d system_chars=%d",
                    self.provider,
                    self.model,
                    attempt,
                    category,
                    self._clock() - attempt_started,
                    stats.input_tokens if stats else None,
                    stats.output_tokens if stats else None,
                    len(prompt),
                    len(system) if system else 0,
                )
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
