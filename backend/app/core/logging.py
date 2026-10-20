"""Root-handler logging setup with secret redaction."""

import hashlib
import json
import logging
import os
import re
import traceback
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import ROOT, ConfigurationError, Settings

DYNAMIC_SECRETS: dict[bytes, tuple[bytes, bytes]] = {}


_MEMORY_CIPHER = AESGCM(os.urandom(32))


def register_secret(value: str) -> None:
    if value:
        digest = hashlib.sha256(value.encode()).digest()
        if digest not in DYNAMIC_SECRETS:
            nonce = os.urandom(12)
            DYNAMIC_SECRETS[digest] = (
                nonce,
                _MEMORY_CIPHER.encrypt(nonce, value.encode(), digest),
            )


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
    def __init__(self, api_key: str | None = None, *additional_keys: str) -> None:
        super().__init__()
        self.api_key = api_key
        self.keys = tuple(key for key in (api_key, *additional_keys) if key)

    def redact(self, value: str) -> str:
        for key in sorted(self.keys, key=len, reverse=True):
            value = value.replace(key, REDACTED)
        # Retain only process-encrypted material between calls, not plaintext keys.
        for digest, (nonce, ciphertext) in tuple(DYNAMIC_SECRETS.items()):
            transient = _MEMORY_CIPHER.decrypt(nonce, ciphertext, digest).decode()
            value = value.replace(transient, REDACTED)
        for pattern in KEY_PATTERNS:
            value = pattern.sub(REDACTED, value)
        value = BEARER.sub(f"Bearer {REDACTED}", value)
        return DB_PASSWORD.sub(rf"\1{REDACTED}\2", value)

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.split(".")[0] in {
            "openai",
            "anthropic",
            "httpx",
            "httpx2",
            "httpcore",
            "httpcore2",
        }:
            return False
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
    for name in ("openai", "anthropic", "httpx2", "httpcore2"):
        logging.getLogger(name).disabled = True
        logging.getLogger(name).addFilter(lambda record: False)
    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, LLMFileHandler):
            root.removeHandler(handler)
            handler.close()
    root.setLevel(settings.log_level.upper())
    if not root.handlers:
        new_handler = logging.StreamHandler()
        new_handler.setFormatter(
            logging.Formatter("%(levelname)s %(name)s %(message)s")
        )
        root.addHandler(new_handler)
    key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else None
    api_key = settings.api_key.get_secret_value() if settings.api_key else ""
    if settings.log_file is not None:
        path = settings.log_file
        if not path.is_absolute():
            path = ROOT / path
        try:
            fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
            stream = os.fdopen(fd, "a", encoding="utf-8")
        except OSError:
            raise ConfigurationError("Cannot open configured LOG_FILE.") from None
        root.addHandler(LLMFileHandler(stream, RedactingFilter(key, api_key)))
    for handler in root.handlers:
        for old_filter in list(handler.filters):
            if isinstance(old_filter, RedactingFilter):
                handler.removeFilter(old_filter)
        handler.addFilter(RedactingFilter(key, api_key))


class LLMFileHandler(logging.StreamHandler[Any]):
    """Only typed call diagnostics; never format the arbitrary log message."""

    def __init__(self, stream: Any, redactor: RedactingFilter) -> None:
        super().__init__(stream)
        self.redactor = redactor

    def emit(self, record: logging.LogRecord) -> None:
        from app.core.telemetry import safe_records

        if record.name != "app.llm.base":
            return
        raw = getattr(record, "llm_diagnostic", None)
        if not isinstance(raw, dict) or raw.get("kind") != "llm":
            return
        rows = safe_records([raw])
        try:
            self.stream.write(self.redactor.redact(json.dumps(rows[0])) + "\n")
            self.flush()
        except (OSError, ValueError):
            # Optional diagnostics must not change completion/acceptance behavior;
            # logging.handleError would print the arbitrary original message.
            return

    def close(self) -> None:
        try:
            self.stream.close()
        finally:
            super().close()
