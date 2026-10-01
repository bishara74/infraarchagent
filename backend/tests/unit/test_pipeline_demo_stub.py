"""Pipeline demo opt-in leaves every existing stub consumer unchanged."""

import json

import pytest

from app.agents.factory import AgentFactory
from app.core.config import Settings
from app.domain.enums import LLMProvider, Variant
from app.llm.factory import build_adapter
from app.llm.stub import StubAdapter
from app.pipeline.demo_stub import PipelineDemoStub


def settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://app:placeholder@localhost/db",
        migration_database_url="postgresql+asyncpg://owner:placeholder@localhost/db",
        test_database_url="postgresql+asyncpg://app:placeholder@localhost/test",
        test_migration_database_url="postgresql+asyncpg://owner:placeholder@localhost/test",
        llm_provider=LLMProvider.STUB,
        _env_file=None,
    )


@pytest.mark.req("NFR-03", "FR-P-01")
async def test_spike_and_evaluation_stub_paths_keep_existing_responses() -> None:
    configured = settings()
    spike = build_adapter(configured, provider=LLMProvider.STUB)
    assert type(spike) is StubAdapter
    assert (await spike.complete_json("phase 1 spike")).data == {
        "files": {"stub.txt": "ok"}
    }

    evaluator = AgentFactory(configured)
    architect = evaluator.create_architect()
    generator = evaluator.create_generator(Variant.COST)
    assert type(architect.llm_adapter) is StubAdapter
    assert type(generator.llm_adapter) is StubAdapter
    for adapter in (architect.llm_adapter, generator.llm_adapter):
        assert isinstance(adapter, StubAdapter)
        adapter.load_script([json.dumps({"known": "scripted output"})])
        assert (await adapter.complete_json("evaluation")).data == {
            "known": "scripted output"
        }

    demo = AgentFactory(configured, pipeline_demo_stub=True)
    assert isinstance(demo.create_architect().llm_adapter, PipelineDemoStub)
    assert isinstance(demo.create_generator(Variant.COST).llm_adapter, PipelineDemoStub)
