import json

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.agents.factory import AgentFactory
from app.core.config import Settings
from app.domain.enums import LLMProvider, Variant
from app.domain.run_config import RunConfig
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
def test_overrides_reach_adapter() -> None:
    agent = AgentFactory(settings(llm_model="default")).create_architect(
        RunConfig(provider=LLMProvider.STUB, model="override", max_iterations=5)
    )
    assert agent.llm_adapter.model == "override"


@pytest.mark.req("FR-I-04")
def test_missing_real_provider_configuration_surfaces() -> None:
    with pytest.raises(LLMConfigurationError, match="LLM_MODEL"):
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
        assert agent.llm_adapter.model == "override"
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
            security_fix_provider="stub",
            security_fix_model="fixer-model",
            security_fix_reasoning_effort="off",
            llm_reasoning_effort="low",
        ),
        session_factory=async_sessionmaker(),
    ).create_security_agent(RunConfig(provider=LLMProvider.OPENAI, model="run-model"))
    override_adapter = overridden.fix_agent.adapter
    assert isinstance(override_adapter, StubAdapter)
    assert override_adapter.model == "fixer-model"
    assert override_adapter.reasoning_effort == "off"
    assert overridden.fixing_provider == "stub"
    assert overridden.fixing_model == "fixer-model"

    fallback = AgentFactory(
        settings(llm_reasoning_effort="low"),
        session_factory=async_sessionmaker(),
    ).create_security_agent(RunConfig(provider=LLMProvider.STUB, model="run-model"))
    fallback_adapter = fallback.fix_agent.adapter
    assert fallback_adapter.model == "run-model"
    assert fallback_adapter.reasoning_effort == "low"
    assert fallback.fixing_model == "run-model"
