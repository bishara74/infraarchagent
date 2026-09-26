import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.domain.enums import LLMProvider
from app.domain.run_config import RunConfig


def settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://app:secret@localhost/db",
        migration_database_url="postgresql+asyncpg://owner:secret@localhost/db",
        test_database_url="postgresql+asyncpg://app:secret@localhost/test",
        test_migration_database_url="postgresql+asyncpg://owner:secret@localhost/test",
        llm_provider=LLMProvider.STUB,
        llm_model="default-model",
        max_remediation_iterations=3,
        _env_file=None,
    )


@pytest.mark.req("FR-I-04")
def test_defaults_and_overrides() -> None:
    default = RunConfig().resolve(settings())
    assert default.provider is LLMProvider.STUB
    assert default.model == "default-model"
    assert default.max_iterations == 3
    override = RunConfig(
        provider=LLMProvider.OPENAI, model="alternate", max_iterations=5
    )
    resolved = override.resolve(settings())
    assert (resolved.provider, resolved.model, resolved.max_iterations) == (
        LLMProvider.OPENAI,
        "alternate",
        5,
    )
    with pytest.raises(ValidationError):
        resolved.max_iterations = 2


@pytest.mark.req("FR-I-04")
def test_invalid_limit_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RunConfig(max_iterations=0)
