import pytest

from app.domain.input_rules import (
    InputContentError,
    InputLengthError,
    NoInfrastructureIntentError,
    validate_request_text,
)


@pytest.mark.req("FR-I-01")
@pytest.mark.parametrize(
    "text,valid",
    [
        ("host a123", False),
        ("host a1234", True),
        ("host " + "x" * 1995, True),
        ("host " + "x" * 1996, False),
    ],
)
def test_length_boundaries(text: str, valid: bool) -> None:
    if valid:
        assert validate_request_text(text) == text
    else:
        with pytest.raises(InputLengthError):
            validate_request_text(text)


@pytest.mark.req("FR-I-01")
def test_strip_unicode_and_validation_order() -> None:
    assert validate_request_text("  host árvíz  ") == "host árvíz"
    assert validate_request_text("host áéíóú") == "host áéíóú"
    for text in ("   ", "a web app", "hello", "    host a123   "):
        with pytest.raises(InputLengthError):
            validate_request_text(text)
    with pytest.raises(InputContentError):
        validate_request_text("hello\x00")
    with pytest.raises(InputContentError):
        validate_request_text("host my app\x7f")
    assert validate_request_text("host my\nblog") == "host my\nblog"


@pytest.mark.req("FR-I-02")
@pytest.mark.parametrize(
    "text",
    [
        "build a web app",
        "host my blog",
        "I need a database for my shop",
        "deploy a microservice to kubernetes",
        "Postgres behind an API",
        "Postgres behind APIs",
    ],
)
def test_accepts_infrastructure_examples(text: str) -> None:
    assert validate_request_text(text) == text


@pytest.mark.req("FR-I-02")
@pytest.mark.parametrize(
    "text",
    [
        "hello, how is it going?",
        "what's the weather today",
        "tell me a joke about cats",
        "how are you doing",
        "thanks a lot",
        "the apiary is open today",
    ],
)
def test_rejects_clear_non_infrastructure_examples(text: str) -> None:
    with pytest.raises(NoInfrastructureIntentError) as captured:
        validate_request_text(text)
    assert captured.value.message
    assert captured.value.code


@pytest.mark.req("FR-I-01", "FR-I-02")
def test_all_errors_have_safe_messages() -> None:
    for text, error_type in [
        ("hello", InputLengthError),
        ("host my app\x01", InputContentError),
        ("tell me a joke", NoInfrastructureIntentError),
    ]:
        with pytest.raises(error_type) as captured:
            validate_request_text(text)
        assert captured.value.message and captured.value.code
