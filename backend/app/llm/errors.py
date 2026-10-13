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


SAFE_MESSAGES = {
    "auth_failed": "The LLM provider refused the request: authentication failed.",
    "usage_limit": "The LLM provider refused the request: usage limit reached.",
    "model_unavailable": "The requested language model is unavailable.",
    "rate_limited": "The LLM provider rate limited the request.",
    "provider_error": "The LLM provider could not complete the request.",
    "unreachable": "The LLM provider could not be reached.",
    "invalid_response": "The LLM provider returned an unusable response.",
    "request_rejected": (
        "The LLM provider rejected the request (check model options and permissions)."
    ),
}
LEGACY_CATEGORIES = {
    "request": "request_rejected",
    "rate_limit": "rate_limited",
    "server": "provider_error",
    "connection": "unreachable",
    "timeout": "unreachable",
    "deadline": "unreachable",
    "invalid_json": "invalid_response",
    "truncated": "invalid_response",
    "unexpected": "provider_error",
    "permanent": "provider_error",
    "transient": "provider_error",
    "stub_script_exhausted": "provider_error",
}


def safe_category(category: str) -> str:
    return (
        category
        if category in SAFE_MESSAGES
        else LEGACY_CATEGORIES.get(category, "provider_error")
    )


def failure_message(category: str) -> str:
    return SAFE_MESSAGES[safe_category(category)]


@dataclass(frozen=True)
class ResponseStats:
    input_tokens: int | None = None
    output_tokens: int | None = None
    stop_reason: str | None = None
    response_characters: int = 0
    cached_input_tokens: int | None = None


class LLMError(Exception):
    """Base class whose messages never contain provider response details."""

    http_status: int | None = None
    original_exception_class: str | None = None

    def diagnostics(self, http_status: int | None, exception_class: str | None) -> None:
        self.http_status = http_status
        self.original_exception_class = exception_class


class LLMTransientError(LLMError):
    def __init__(
        self,
        category: str = "transient",
        *,
        retry_after: float | None = None,
        rate_limit_headers: tuple[str, ...] = (),
    ) -> None:
        self.category = (
            category if category in LEGACY_CATEGORIES else safe_category(category)
        )
        self.retry_after = retry_after
        self.rate_limit_headers = rate_limit_headers
        super().__init__(failure_message(self.category))


class LLMPermanentError(LLMError):
    def __init__(self, category: str = "permanent") -> None:
        self.category = (
            category if category in LEGACY_CATEGORIES else safe_category(category)
        )
        super().__init__(
            "LLM stub_script_exhausted"
            if category == "stub_script_exhausted"
            else failure_message(self.category)
        )


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
    body: object = None,
    http_status: int | None = None,
    exception_class: str | None = None,
    retry_after: float | None = None,
    rate_limit_headers: tuple[str, ...] = (),
) -> LLMError:
    envelope = body.get("error", body) if isinstance(body, dict) else {}
    envelope = envelope if isinstance(envelope, dict) else {}
    metadata = envelope.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    message = envelope.get("message")
    message = message[:4096].lower() if isinstance(message, str) else ""
    budget = metadata.get("limit_source") in (
        "openrouter_key_limit",
        "openrouter_guardrail_budget",
        "openrouter_workspace_budget",
        "openrouter_credits",
    ) or any(
        phrase in message
        for phrase in (
            "key limit exceeded",
            "credit limit exceeded",
            "budget limit exceeded",
            "insufficient credits",
            "spending limit exceeded",
        )
    )
    if status_code == 401:
        category = "auth_failed"
    elif status_code == 402 or status_code == 403 and budget:
        category = "usage_limit"
    elif status_code == 404:
        category = "model_unavailable"
    elif status_code == 429:
        category = "rate_limited"
    elif 500 <= status_code <= 599:
        category = "provider_error"
    else:
        category = "request_rejected"
    error: LLMError = (
        LLMTransientError(
            category, retry_after=retry_after, rate_limit_headers=rate_limit_headers
        )
        if category in {"rate_limited", "provider_error"}
        else LLMPermanentError(category)
    )
    error.diagnostics(
        http_status if http_status is not None else status_code, exception_class
    )
    return error


def check_error_envelope(body: object, http_status: int) -> None:
    if not isinstance(body, dict):
        raise LLMResponseFormatError("invalid_json")
    if "error" not in body:
        return
    error = body["error"]
    code = error.get("code") if isinstance(error, dict) else None
    if type(code) is int and 400 <= code <= 599:
        raise status_error(code, body=body, http_status=http_status) from None
    failure = LLMResponseFormatError("invalid_json")
    failure.diagnostics(http_status, None)
    raise failure from None


def cached_tokens(value: object) -> int | None:
    """Absent or malformed provider metrics are unknown, not zero."""
    return value if type(value) is int and value >= 0 else None


def cached_response_tokens(body: object, *path: str) -> int | None:
    """Inspect wire metrics before SDK integer coercion loses their types."""
    value = body
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return cached_tokens(value)


def check_success_body(body: object, provider: str, http_status: int) -> None:
    usable = isinstance(body, dict)
    if isinstance(body, dict) and provider == "openai":
        choices = body.get("choices")
        usable = isinstance(choices, list) and bool(choices)
        if isinstance(choices, list) and choices:
            choice = choices[0]
            message = choice.get("message") if isinstance(choice, dict) else None
            usable = isinstance(message, dict) and isinstance(
                message.get("content"), str
            )
    elif isinstance(body, dict):
        content = body.get("content")
        usable = isinstance(content, list) and bool(content)
        if isinstance(content, list) and content:
            usable = all(
                isinstance(block, dict)
                and (block.get("type") != "text" or isinstance(block.get("text"), str))
                for block in content
            )
    if not usable:
        failure = LLMResponseFormatError("empty")
        failure.diagnostics(http_status, None)
        raise failure from None
