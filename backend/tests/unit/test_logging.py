import io
import logging

import pytest

from app.core.logging import RedactingFilter


@pytest.mark.req("NFR-01")
def test_redacts_message_args_and_exception_text() -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(RedactingFilter("configured-private-value"))
    logger = logging.getLogger("test_redaction")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        try:
            raise ValueError("configured-private-value in exception")
        except ValueError:
            logger.exception(
                "args: %s %s %s %s",
                "configured-private-value",
                "sk-ant-abc12345xyz",
                "sk-1234567890abcdef",
                "Bearer token-123",
            )
        logger.info("database %s", "postgresql://user:db-secret@localhost/db")
    finally:
        logger.removeHandler(handler)
    output = stream.getvalue()
    for secret in (
        "configured-private-value",
        "sk-ant-abc12345xyz",
        "sk-1234567890abcdef",
        "token-123",
        "db-secret",
    ):
        assert secret not in output
    assert output.count("[REDACTED]") >= 6
    assert "ValueError" in output
