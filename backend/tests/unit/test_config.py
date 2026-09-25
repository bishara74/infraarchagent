import pytest
from pydantic import ValidationError

from app.core.config import ConfigurationError, Settings, require_llm_key


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "postgresql+asyncpg://app:secret@localhost/db",
        "migration_database_url": "postgresql+asyncpg://owner:secret@localhost/db",
        "test_database_url": "postgresql+asyncpg://app:secret@localhost/test",
        "test_migration_database_url": "postgresql+asyncpg://owner:secret@localhost/test",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_defaults_and_secret_representations() -> None:
    settings = _settings(llm_api_key="sk-ant-api03-CANARY-7f3c9e2a1b4d5e6f")
    assert settings.llm_provider == "stub"
    assert settings.max_remediation_iterations == 3
    assert settings.package_retention_days == 30
    assert "CANARY" not in repr(settings)
    assert "secret" not in repr(settings)


def test_llm_key_is_optional_until_required() -> None:
    settings = _settings(llm_api_key="")
    assert settings.llm_api_key is None
    with pytest.raises(ConfigurationError, match="LLM_API_KEY"):
        require_llm_key(settings)
    assert require_llm_key(_settings(llm_api_key="available")) == "available"


@pytest.mark.parametrize(
    "field", ["max_remediation_iterations", "package_retention_days"]
)
def test_positive_limits(field: str) -> None:
    with pytest.raises(ValidationError):
        _settings(**{field: 0})
