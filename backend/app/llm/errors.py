"""Safe errors and response metrics for the LLM boundary."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite

RATE_LIMIT_HEADER_NAMES = (
    "retry-after",
    "x-ratelimit-reset-tokens",
    "x-ratelimit-reset-requests",
)
_NUMBER = r"(?:\d+(?:\.\d*)?|\.\d+)"
_MILLISECONDS = re.compile(rf"({_NUMBER})ms", re.IGNORECASE)
_DURATION = re.compile(
    rf"(?:(?P<minutes>{_NUMBER})m)?(?:(?P<seconds>{_NUMBER})s)?", re.IGNORECASE
)


@dataclass(frozen=True)
class ResponseStats:
    input_tokens: int | None = None
    output_tokens: int | None = None
    stop_reason: str | None = None
    response_characters: int = 0


class LLMError(Exception):
    """Base class whose messages never contain provider response details."""


class LLMTransientError(LLMError):
    def __init__(
        self,
        category: str = "transient",
        *,
        retry_after: float | None = None,
        rate_limit_headers: tuple[str, ...] = (),
    ) -> None:
        self.category = category
        self.retry_after = retry_after
        self.rate_limit_headers = rate_limit_headers
        super().__init__(f"LLM {category} failure")


class LLMPermanentError(LLMError):
    def __init__(self, category: str = "permanent") -> None:
        self.category = category
        super().__init__(f"LLM {category} failure")


class LLMConfigurationError(LLMError):
    """A requested real provider lacks required configuration."""


class LLMResponseFormatError(LLMError):
    def __init__(
        self, reason: str = "invalid_json", stats: ResponseStats | None = None
    ) -> None:
        self.reason = reason
        self.stats = stats
        super().__init__(f"LLM response {reason}")


class LLMDeadlineExceeded(LLMError):
    def __init__(self, attempts: int, elapsed_seconds: float) -> None:
        self.attempts = attempts
        self.elapsed_seconds = elapsed_seconds
        super().__init__("LLM call deadline exceeded")


class LLMRetryExhausted(LLMError):
    def __init__(
        self,
        attempts: int,
        elapsed_seconds: float,
        last_category: str,
        stats: ResponseStats | None = None,
    ) -> None:
        self.attempts = attempts
        self.elapsed_seconds = elapsed_seconds
        self.last_category = last_category
        self.stats = stats
        super().__init__("LLM retry attempts exhausted")


def parse_retry_after(value: str | None) -> float | None:
    """Parse finite nonnegative numeric seconds or provider duration strings."""
    if value is None:
        return None
    candidate = value.strip()
    try:
        seconds = float(candidate)
    except ValueError:
        milliseconds = _MILLISECONDS.fullmatch(candidate)
        if milliseconds:
            seconds = float(milliseconds.group(1)) / 1000
        else:
            duration = _DURATION.fullmatch(candidate)
            if not duration or not (
                duration.group("minutes") or duration.group("seconds")
            ):
                return None
            seconds = float(duration.group("minutes") or 0) * 60 + float(
                duration.group("seconds") or 0
            )
    return seconds if isfinite(seconds) and seconds >= 0 else None


def rate_limit_wait(headers: Mapping[str, str]) -> tuple[float | None, tuple[str, ...]]:
    """Prefer Retry-After, then the largest valid provider reset duration."""
    names = tuple(
        name for name in RATE_LIMIT_HEADER_NAMES if headers.get(name) is not None
    )
    primary = parse_retry_after(headers.get("retry-after"))
    if primary is not None:
        return primary, names
    resets = [
        parsed
        for name in RATE_LIMIT_HEADER_NAMES[1:]
        if (parsed := parse_retry_after(headers.get(name))) is not None
    ]
    return (max(resets) if resets else None), names


def status_error(
    status_code: int,
    *,
    retry_after: float | None = None,
    rate_limit_headers: tuple[str, ...] = (),
) -> LLMError:
    if status_code == 429 or status_code >= 500:
        if status_code == 429:
            return LLMTransientError(
                "rate_limit",
                retry_after=retry_after,
                rate_limit_headers=rate_limit_headers,
            )
        return LLMTransientError("server")
    return LLMPermanentError("request")
