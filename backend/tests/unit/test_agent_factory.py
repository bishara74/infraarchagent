import json

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.agents.factory import AgentFactory
from app.core.config import Settings
from app.domain.enums import LLMProvider, Variant
from app.domain.run_config import RunConfig, RunConfigError
from app.llm.errors import LLMConfigurationError
from app.llm.stub import StubAdapter


def settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "postgresql+asyncpg://app:secret@localhost/db",
        "migration_database_url": "postgresql+asyncpg://owner:secret@localhost/db",
        "test_database_url": "postgresql+asyncpg://app:secret@localhost/test",
        "test_migration_database_url": "postgresql+asyncpg://owner:secret@localhost/test",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.mark.req("FR-I-04", "FR-A-01")
async def test_factory_builds_stub_agent_and_script_can_be_loaded_afterward() -> None:
    agent = AgentFactory(settings()).create_architect()
    assert isinstance(agent.llm_adapter, StubAdapter)
    fixture = {
        "cloud_provider": "aws",
        "services": [{"name": "web", "aws_service": "ECS", "purpose": "Serve"}],
        "dependencies": [],
        "network": {
            "public_services": ["web"],
            "private_services": [],
            "ingress": [],
            "notes": "VPC",
        },
        "storage": [],
        "file_types": ["terraform"],
        "ambiguities": [],
    }
    agent.llm_adapter.load_script([json.dumps(fixture)])
    agent.parse_input("build a web app")
    assert (await agent.generate_plan()).services[0].name == "web"


@pytest.mark.req("FR-I-04")
def test_stub_model_override_is_normalized() -> None:
    agent = AgentFactory(settings(llm_model="default")).create_architect(
        RunConfig(provider=LLMProvider.STUB, model="override", max_iterations=5)
    )
    assert agent.llm_adapter.model == "stub"


@pytest.mark.req("FR-I-04", "FR-G-01")
@pytest.mark.parametrize("provider", [LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
def test_real_model_override_reaches_architect_and_generators(monkeypatch, provider):
    from app.agents import factory as module

    calls = []

    def recorded_adapter(settings, **kwargs):
        calls.append(kwargs)
        return StubAdapter(kwargs["model"])

    monkeypatch.setattr(module, "build_adapter", recorded_adapter)
    factory = AgentFactory(settings())
    config = RunConfig(provider=provider, model="override")
    architect = factory.create_architect(config)
    generators = factory.create_generators(config)
    assert calls == [{"provider": provider, "model": "override"}] * 4
    assert architect.llm_adapter.model == "override"
    assert all(agent.llm_adapter.model == "override" for agent in generators)


@pytest.mark.req("FR-I-04")
def test_missing_real_provider_configuration_surfaces() -> None:
    with pytest.raises(RunConfigError, match="model is required when overriding"):
        AgentFactory(settings()).create_architect(
            RunConfig(provider=LLMProvider.OPENAI)
        )
    with pytest.raises(LLMConfigurationError, match="LLM_API_KEY"):
        AgentFactory(settings()).create_architect(
            RunConfig(provider=LLMProvider.OPENAI, model="real-model")
        )


@pytest.mark.req("FR-G-01", "FR-I-04")
def test_generator_factory_order_settings_and_run_overrides() -> None:
    configured = settings(
        llm_model="default",
        generator_deadline_seconds=90,
        generator_attempt_timeout_seconds=75,
        generator_max_output_tokens=12345,
        generator_max_package_attempts=4,
    )
    agents = AgentFactory(configured).create_generators(
        RunConfig(provider=LLMProvider.STUB, model="override")
    )
    assert [agent.variant for agent in agents] == list(Variant)
    assert len({id(agent.llm_adapter) for agent in agents}) == 3
    for agent in agents:
        assert agent.llm_adapter.model == "stub"
        assert agent.deadline_seconds == 90
        assert agent.attempt_timeout == 75
        assert agent.max_output_tokens == 12345
        assert agent.max_package_attempts == 4
    security_agent = AgentFactory(configured).create_generator(Variant.SECURITY)
    assert security_agent.variant is Variant.SECURITY


@pytest.mark.req("FR-S-02")
def test_security_fix_model_override_and_run_fallback_reach_adapter() -> None:
    overridden = AgentFactory(
        settings(
            llm_provider="openai",
            security_fix_provider="stub",
            security_fix_model="fixer-model",
            security_fix_reasoning_effort="off",
            llm_reasoning_effort="low",
        ),
        session_factory=async_sessionmaker(),
    ).create_security_agent(RunConfig(provider=LLMProvider.OPENAI, model="run-model"))
    override_adapter = overridden.fix_agent.adapter
    assert isinstance(override_adapter, StubAdapter)
    assert override_adapter.model == "stub"
    assert override_adapter.reasoning_effort == "off"
    assert overridden.fixing_provider == "stub"
    assert overridden.fixing_model == "stub"

    fallback = AgentFactory(
        settings(llm_reasoning_effort="low"),
        session_factory=async_sessionmaker(),
    ).create_security_agent(RunConfig(provider=LLMProvider.STUB, model="run-model"))
    fallback_adapter = fallback.fix_agent.adapter
    assert fallback_adapter.model == "stub"
    assert fallback_adapter.reasoning_effort == "low"
    assert fallback.fixing_model == "stub"


@pytest.mark.req("FR-I-04", "FR-S-02", "NFR-01")
@pytest.mark.parametrize("configured_provider", ["openai", "stub"])
@pytest.mark.parametrize("run_model", [None, "fixture-model"])
def test_stub_fixer_ignores_deployment_overrides_and_builds_no_network_adapter(
    monkeypatch, configured_provider, run_model
):
    from app.agents import factory as module

    original = module.build_adapter
    built = []

    def stub_only(settings, **kwargs):
        assert kwargs["provider"] == LLMProvider.STUB
        assert kwargs["model"] == "stub"
        assert kwargs["reasoning_effort"] is None
        adapter = original(settings, **kwargs)
        built.append(adapter)
        return adapter

    monkeypatch.setattr(module, "build_adapter", stub_only)
    agent = AgentFactory(
        settings(
            llm_provider=configured_provider,
            llm_model="deployment-model",
            security_fix_provider="anthropic",
            security_fix_model="paid-fixer-model",
            security_fix_reasoning_effort="high",
            llm_reasoning_effort="low",
        ),
        session_factory=async_sessionmaker(),
    ).create_security_agent(RunConfig(provider=LLMProvider.STUB, model=run_model))
    assert len(built) == 1 and isinstance(built[0], StubAdapter)
    assert agent.fixing_provider == "stub" and agent.fixing_model == "stub"
    assert agent.fixing_reasoning_effort == "low"


@pytest.mark.req("FR-I-04", "FR-S-02")
@pytest.mark.parametrize("run_provider", ["openai", "anthropic"])
def test_real_fixer_overrides_are_scoped_to_configured_provider(
    monkeypatch, run_provider
):
    from app.agents import factory as module

    calls = []

    def recorded_adapter(settings, **kwargs):
        calls.append(kwargs)
        adapter = StubAdapter(
            kwargs["model"], reasoning_effort=kwargs["reasoning_effort"]
        )
        adapter.provider = kwargs["provider"].value
        return adapter

    monkeypatch.setattr(module, "build_adapter", recorded_adapter)
    agent = AgentFactory(
        settings(
            llm_provider="openai",
            llm_model="deployment-model",
            security_fix_provider="anthropic",
            security_fix_model="hybrid-fixer",
            security_fix_reasoning_effort="high",
        ),
        session_factory=async_sessionmaker(),
    ).create_security_agent(RunConfig(provider=run_provider, model="run-model"))
    expected_model = "hybrid-fixer" if run_provider == "openai" else "run-model"
    expected_effort = "high" if run_provider == "openai" else None
    assert calls == [
        {
            "provider": LLMProvider.ANTHROPIC,
            "model": expected_model,
            "reasoning_effort": expected_effort,
        }
    ]
    assert agent.fixing_provider == "anthropic"
    assert agent.fixing_model == expected_model
    assert agent.fixing_reasoning_effort == expected_effort


@pytest.mark.req("FR-V-05", "NFR-01")
def test_validator_factory_needs_sessions_but_no_llm(monkeypatch):
    from app.agents import factory as module
    from app.agents.validator import ValidatorAgent

    def forbidden(*args, **kwargs):
        raise AssertionError("validator must not build an LLM adapter")

    monkeypatch.setattr(module, "build_adapter", forbidden)
    configured = settings(
        llm_provider=LLMProvider.OPENAI,
        validator_tool_timeout_seconds=7,
        validator_max_parallel_tools=2,
        validation_deadline_seconds=42,
    )
    with pytest.raises(RuntimeError, match="session"):
        AgentFactory(configured).create_validator_agent()
    agent = AgentFactory(
        configured, session_factory=async_sessionmaker()
    ).create_validator_agent()
    assert isinstance(agent, ValidatorAgent)
    assert agent.engine.max_parallel_tools == 2 and agent.engine.deadline_seconds == 42
    assert agent.engine.runner.runner.timeout_seconds == 7
