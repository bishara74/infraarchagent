"""Provider-independent JSON completion and timing policy."""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from app.core.config import ReasoningEffort, ResponseFormat, Settings, StructuredOutput
from app.core.credentials import CredentialMaterial
from app.core.telemetry import observe, tags
from app.llm.errors import (
    LLMDeadlineExceeded,
    LLMPermanentError,
    LLMResponseFormatError,
    LLMRetryExhausted,
    LLMTransientError,
    ResponseStats,
    cached_tokens,
    safe_category,
)
from app.llm.json_output import Validator, validated_json
from app.llm.json_output import extract_json_object as extract_json_object

logger = logging.getLogger(__name__)


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
    http_status: int | None = None
    served_by: str | None = None
    reasoning_tokens: int | None = None
    cached_input_tokens: int | None = None

    def stats(self) -> ResponseStats:
        return ResponseStats(
            self.input_tokens,
            self.output_tokens,
            self.stop_reason,
            len(self.text),
            self.cached_input_tokens,
        )


@dataclass(frozen=True)
class LLMResult:
    data: dict[str, Any]
    response: LLMResponse
    attempts: int
    elapsed_seconds: float
    format_reason: str | None = None


@dataclass(frozen=True)
class LLMAttempt:
    attempt: int
    outcome: str
    category: str
    format_reason: str | None
    elapsed_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    response_characters: int | None
    package_attempt: int = 1
    deadline_exceeded: bool = False
    overrun_seconds: float = 0.0
    reasoning_tokens: int | None = None
    call_id: str | None = None
    run_id: str | None = None
    role: str | None = None
    variant: str | None = None
    phase: str | None = None
    call_kind: str | None = None
    iteration: int | None = None
    started_at: str | None = None
    finished_at: str | None = None
    requested_effort: str | None = None
    response_format: str | None = None
    request_style: str | None = None
    served_by: str | None = None
    provider: str | None = None
    model: str | None = None
    cached_input_tokens: int | None = None


class LLMAdapter(ABC):
    provider = "unknown"
    supports_structured_output = False

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
        self.credential_resolver: Callable[[], Awaitable[CredentialMaterial]] | None = (
            None
        )
        self.request_style = "legacy"
        self.reasoning_capable = False
        self.thinking_types: dict[str, object] = {}
        self.model = model
        self.policy = policy
        self.reasoning_effort = reasoning_effort
        self.response_format = response_format
        self.structured_output: StructuredOutput | None = None
        self.output_schema: dict[str, Any] | None = None
        self.output_schema_name = "generator_package"
        self._structured_request: ContextVar[bool] = ContextVar(
            "structured_request", default=False
        )
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
        attempt_observer: Callable[[LLMAttempt], None] | None = None,
        response_validator: Validator | None = None,
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
        retry_prompt = prompt
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
            started_at = datetime.now(UTC).isoformat()
            response: LLMResponse | None = None
            last_stats = None
            retry_after: float | None = None
            rate_limit_headers: tuple[str, ...] = ()
            category = "success"
            format_reason: str | None = None
            http_status: int | None = None
            exception_class: str | None = None
            attempt_prompt = retry_prompt
            context_token = self._structured_request.set(response_validator is not None)
            try:
                response = await asyncio.wait_for(
                    self.send_prompt(
                        attempt_prompt,
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
                if response_validator is not None:
                    data, format_reason = validated_json(
                        response.text, response_validator
                    )
                else:
                    data = self.parse_response(response)
                if self._clock() >= ends_at:
                    raise LLMDeadlineExceeded(attempt, self._clock() - started)
                return LLMResult(
                    data, response, attempt, self._clock() - started, format_reason
                )
            except TimeoutError as error:
                category = "timeout"
                exception_class = type(error).__name__
            except asyncio.CancelledError:
                category = "cancelled"
                raise
            except LLMTransientError as error:
                error.__context__ = None
                category = error.category
                http_status = error.http_status
                exception_class = error.original_exception_class
                retry_after = error.retry_after
                rate_limit_headers = error.rate_limit_headers
            except LLMResponseFormatError as error:
                error.__context__ = None
                category = (
                    "truncated" if error.reason == "truncated" else "invalid_json"
                )
                http_status = error.http_status or (
                    response.http_status if response else None
                )
                exception_class = error.original_exception_class
                format_reason = error.reason
                last_stats = error.stats or last_stats
                if response_validator is not None:
                    retry_prompt = (
                        prompt
                        + "\nCorrection: Previous response failed ("
                        + format_reason
                        + "). Answer again with exactly one JSON object, "
                        "no markdown fences or surrounding text. "
                        "Keep the response within the output budget."
                    )
            except LLMDeadlineExceeded:
                category = "deadline"
                raise
            except LLMPermanentError as error:
                error.__context__ = None
                category = error.category
                http_status = error.http_status
                exception_class = error.original_exception_class
                raise
            except Exception as error:
                category = "unexpected"
                exception_class = type(error).__name__
                raise LLMPermanentError("unexpected") from None
            finally:
                self._structured_request.reset(context_token)
                stats = response.stats() if response is not None else None
                log_category = (
                    category
                    if category in {"success", "cancelled"}
                    else safe_category(category)
                )
                fields = [
                    f"provider={self.provider}",
                    f"model={self.model}",
                    f"attempt={attempt}",
                    f"outcome={category}",
                    f"category={log_category}",
                    f"http_status={http_status if http_status is not None else 'none'}",
                    f"exception_class={exception_class or 'none'}",
                    f"reasoning_effort={self.reasoning_effort or 'unset'}",
                    f"latency={self._clock() - attempt_started:.3f}",
                    f"input_tokens={stats.input_tokens if stats else None}",
                    f"output_tokens={stats.output_tokens if stats else None}",
                    "cached_input_tokens="
                    + str(stats.cached_input_tokens if stats else None),
                    f"prompt_chars={len(attempt_prompt)}",
                    f"system_chars={len(system) if system else 0}",
                    f"retry_after={retry_after if retry_after is not None else 'none'}",
                    "rate_limit_headers="
                    + (",".join(rate_limit_headers) if rate_limit_headers else "none"),
                ]
                if (
                    category == "success"
                    and response is not None
                    and response.served_by is not None
                ):
                    host = quote(response.served_by, safe="@._/-")
                    fields.append(f"served_by={host}")
                if response is not None and response.reasoning_tokens is not None:
                    fields.append(f"reasoning_tokens={response.reasoning_tokens}")
                if format_reason is not None:
                    fields.append(f"format_reason={format_reason}")
                call_id = str(uuid4())
                context = tags.get() or {}
                requested_effort = (
                    self.reasoning_effort
                    if self.request_style == "legacy" or self.reasoning_capable
                    else None
                )
                requested_format = (
                    (self.structured_output if response_validator else None)
                    or self.response_format
                    or "off"
                )
                if self.provider == "anthropic":
                    requested_effort = (
                        self.reasoning_effort
                        if self.request_style == "anthropic" and self.reasoning_capable
                        else None
                    )
                    requested_format = (
                        "json_schema"
                        if self.request_style == "anthropic"
                        and response_validator
                        and self.structured_output == "json_schema"
                        else "off"
                    )
                detail = LLMAttempt(
                    attempt=attempt,
                    outcome=category,
                    category=log_category,
                    format_reason=format_reason,
                    elapsed_seconds=max(0.0, self._clock() - attempt_started),
                    input_tokens=cached_tokens(stats.input_tokens) if stats else None,
                    output_tokens=cached_tokens(stats.output_tokens) if stats else None,
                    response_characters=stats.response_characters if stats else None,
                    reasoning_tokens=cached_tokens(response.reasoning_tokens)
                    if response
                    else None,
                    call_id=call_id,
                    run_id=context.get("run_id"),
                    role=context.get("role"),
                    variant=context.get("variant"),
                    phase=context.get("phase"),
                    call_kind=context.get("call_kind"),
                    iteration=context.get("iteration"),
                    started_at=started_at,
                    finished_at=datetime.now(UTC).isoformat(),
                    requested_effort=requested_effort,
                    response_format=requested_format,
                    request_style=self.request_style,
                    served_by=response.served_by if response else None,
                    provider=self.provider,
                    model=self.model,
                    cached_input_tokens=cached_tokens(response.cached_input_tokens)
                    if response
                    else None,
                )
                diagnostic = observe(
                    {
                        **asdict(detail),
                        "id": call_id,
                        "kind": "llm",
                        "model": self.model,
                        "executed": True,
                        "completed": category == "success",
                    }
                )
                logger.info(
                    "%s", " ".join(fields), extra={"llm_diagnostic": diagnostic}
                )
                if attempt_observer is not None:
                    attempt_observer(detail)
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
