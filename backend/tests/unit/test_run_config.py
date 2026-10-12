import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.domain.enums import LLMProvider
from app.domain.run_config import RunConfig, RunConfigError


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
    assert default.model == "stub"
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


@pytest.mark.req("FR-I-04")
@pytest.mark.parametrize(
    "config,expected_provider,expected_model",
    [
        ({}, LLMProvider.OPENAI, "deployment-model"),
        ({"provider": "openai"}, LLMProvider.OPENAI, "deployment-model"),
        ({"provider": "stub"}, LLMProvider.STUB, "stub"),
        ({"provider": "stub", "model": "fixture"}, LLMProvider.STUB, "stub"),
        (
            {"provider": "anthropic", "model": "alternate"},
            LLMProvider.ANTHROPIC,
            "alternate",
        ),
        ({"model": "alternate"}, LLMProvider.OPENAI, "alternate"),
    ],
)
def test_model_resolution_is_scoped_to_provider(
    config, expected_provider, expected_model
):
    configured = settings().model_copy(
        update={"llm_provider": LLMProvider.OPENAI, "llm_model": "deployment-model"}
    )
    resolved = RunConfig.model_validate(config).resolve(configured)
    assert (resolved.provider, resolved.model) == (expected_provider, expected_model)


@pytest.mark.req("FR-I-04")
@pytest.mark.parametrize("provider", [LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
def test_different_real_provider_requires_explicit_model(provider):
    with pytest.raises(
        RunConfigError, match="^model is required when overriding the provider$"
    ):
        RunConfig(provider=provider).resolve(settings())


@pytest.mark.req("FR-I-04")
def test_unconfigured_stub_model_is_resolved_in_domain():
    assert (
        RunConfig().resolve(settings().model_copy(update={"llm_model": None})).model
        == "stub"
    )


@pytest.mark.req("FR-I-04", "NFR-01")
@pytest.mark.parametrize("configured_provider", list(LLMProvider))
@pytest.mark.parametrize("model", [None, "deployment-model", "fixture-model"])
def test_stub_model_always_resolves_to_stub(configured_provider, model):
    configured = settings().model_copy(
        update={"llm_provider": configured_provider, "llm_model": "paid-model"}
    )
    resolved = RunConfig(provider=LLMProvider.STUB, model=model).resolve(configured)
    assert resolved.model == "stub"
