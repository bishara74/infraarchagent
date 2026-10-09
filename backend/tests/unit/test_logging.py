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


@pytest.mark.req("NFR-01")
def test_both_keys_redacted_without_replacing_operator_traceback():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(RedactingFilter("prefix-key", "prefix-key-long"))
    logger = logging.getLogger("phase7_operator_trace")
    logger.addHandler(handler)
    logger.propagate = False
    try:
        try:
            raise RuntimeError("prefix-key-long prefix-key /home/operator/app.py")
        except RuntimeError:
            logger.exception("operator traceback")
    finally:
        logger.removeHandler(handler)
    output = stream.getvalue()
    assert "prefix-key" not in output and "-long" not in output
    assert "Traceback (most recent call last)" in output
    assert "RuntimeError" in output and "/home/operator/app.py" in output
