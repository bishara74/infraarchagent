"""Safe errors and response metrics for the LLM boundary."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResponseStats:
    input_tokens: int | None = None
    output_tokens: int | None = None
    stop_reason: str | None = None
    response_characters: int = 0


class LLMError(Exception):
    """Base class whose messages never contain provider response details."""


class LLMTransientError(LLMError):
    def __init__(self, category: str = "transient") -> None:
        self.category = category
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


def status_error(status_code: int) -> LLMError:
    if status_code == 429 or status_code >= 500:
        return LLMTransientError("rate_limit" if status_code == 429 else "server")
    return LLMPermanentError("request")
