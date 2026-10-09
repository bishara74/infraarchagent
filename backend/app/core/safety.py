"""Secret and execution-path protection for persisted/public package data."""

import re
from typing import Any

from app.core.config import ROOT, Settings
from app.core.logging import REDACTED, RedactingFilter


class PublicDataSafety:
    def __init__(self, settings: Settings) -> None:
        self.redactor = RedactingFilter(
            settings.llm_api_key.get_secret_value() if settings.llm_api_key else None,
            settings.api_key.get_secret_value() if settings.api_key else "",
        )

    def text(self, value: str) -> str:
        value = self.redactor.redact(value)
        value = value.replace(str(ROOT), REDACTED)
        return re.sub(
            r"/tmp/(?:infraarch[^\s\"'<>]*|pytest-of-[^\s\"'<>]*)", REDACTED, value
        )

    def value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, dict):
            return {self.text(key): self.value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.value(item) for item in value]
        return value
