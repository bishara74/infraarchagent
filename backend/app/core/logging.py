"""Root-handler logging setup with secret redaction."""

import hashlib
import logging
import os
import re
import traceback

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings

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
    root.setLevel(settings.log_level.upper())
    if not root.handlers:
        new_handler = logging.StreamHandler()
        new_handler.setFormatter(
            logging.Formatter("%(levelname)s %(name)s %(message)s")
        )
        root.addHandler(new_handler)
    key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else None
    api_key = settings.api_key.get_secret_value() if settings.api_key else ""
    for handler in root.handlers:
        for old_filter in list(handler.filters):
            if isinstance(old_filter, RedactingFilter):
                handler.removeFilter(old_filter)
        handler.addFilter(RedactingFilter(key, api_key))
