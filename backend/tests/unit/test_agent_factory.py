import json

import pytest

from app.agents.factory import AgentFactory
from app.core.config import Settings
from app.domain.enums import LLMProvider
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
