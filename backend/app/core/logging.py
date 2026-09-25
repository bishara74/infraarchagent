"""Root-handler logging setup with secret redaction."""

import logging
import re
import traceback

from app.core.config import Settings

REDACTED = "[REDACTED]"
KEY_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
)
BEARER = re.compile(r"\bBearer\s+\S+", re.IGNORECASE)
DB_PASSWORD = re.compile(
    r"(postgres(?:ql)?(?:\+asyncpg)?://[^:\s/@]+:)[^@\s/]+(@)",
    re.IGNORECASE,
)


class RedactingFilter(logging.Filter):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__()
        self.api_key = api_key

    def redact(self, value: str) -> str:
        if self.api_key:
            value = value.replace(self.api_key, REDACTED)
        for pattern in KEY_PATTERNS:
            value = pattern.sub(REDACTED, value)
        value = BEARER.sub(f"Bearer {REDACTED}", value)
        return DB_PASSWORD.sub(rf"\1{REDACTED}\2", value)

    def filter(self, record: logging.LogRecord) -> bool:
        rendered = record.getMessage()
        if record.exc_info:
            rendered += "\n" + "".join(traceback.format_exception(*record.exc_info))
        if record.stack_info:
            rendered += "\n" + record.stack_info
        record.msg = self.redact(rendered)
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


def configure_logging(settings: Settings) -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    if not root.handlers:
        new_handler = logging.StreamHandler()
        new_handler.setFormatter(
            logging.Formatter("%(levelname)s %(name)s %(message)s")
        )
        root.addHandler(new_handler)
    key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else None
    for handler in root.handlers:
        for old_filter in list(handler.filters):
            if isinstance(old_filter, RedactingFilter):
                handler.removeFilter(old_filter)
        handler.addFilter(RedactingFilter(key))
