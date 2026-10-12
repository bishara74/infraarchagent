"""Pipeline demo opt-in leaves every existing stub consumer unchanged."""

import json

import pytest

from app.agents.factory import AgentFactory
from app.agents.security.fix import FixAgent
from app.core.config import Settings
from app.domain.enums import LLMProvider, Variant
from app.domain.plan import DeploymentPlan
from app.llm.base import RetryPolicy
from app.llm.factory import build_adapter
from app.llm.stub import StubAdapter
from app.pipeline.demo_stub import (
    DEMO_PLAN,
    REVIEW_FIX,
    PipelineDemoFixStub,
    PipelineDemoStub,
    demo_file,
)
from app.validation.documents import PackageDocuments
from app.validation.references import reference_checks


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
@pytest.mark.parametrize("scenario", ["clean", "review"])
async def test_spike_and_evaluation_stub_paths_keep_existing_responses(
    scenario,
) -> None:
    configured = settings().model_copy(update={"pipeline_demo_scenario": scenario})
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


@pytest.mark.req("FR-V-01", "FR-UI-07")
@pytest.mark.parametrize("scenario", ["clean", "review"])
@pytest.mark.parametrize("variant", list(Variant))
async def test_demo_failure_is_built_in_and_security_only(scenario, variant):
    configured = settings().model_copy(update={"pipeline_demo_scenario": scenario})
    generator = AgentFactory(configured, pipeline_demo_stub=True).create_generator(
        variant
    )
    package = await generator.generate(DeploymentPlan.model_validate(DEMO_PLAN))
    failures = [
        check
        for check in reference_checks(PackageDocuments.parse(package.files))
        if check.status == "failed"
    ]
    if scenario == "review" and variant == Variant.SECURITY:
        assert len(failures) == 1
        assert failures[0].check_id == "terraform.local_ref"
        assert (
            failures[0].file_path == "terraform/main.tf" and failures[0].line_start == 4
        )
    else:
        assert failures == []


@pytest.mark.req("FR-S-08", "FR-S-09", "FR-UI-07")
@pytest.mark.parametrize(
    "scenario,with_failure,repaired",
    [("review", True, True), ("clean", True, False), ("review", False, False)],
)
async def test_demo_fixer_uses_validation_target_not_feedback(
    scenario, with_failure, repaired
):
    files = {"terraform/main.tf": demo_file(Variant.SECURITY, "review")}
    checks = reference_checks(PackageDocuments.parse(files))
    proposal = await FixAgent(
        PipelineDemoFixStub(RetryPolicy.from_settings(settings()), scenario=scenario)
    ).propose(
        path="terraform/main.tf",
        files=files,
        findings=[],
        plan=DeploymentPlan.model_validate(DEMO_PLAN),
        directive="security",
        remaining=30,
        feedback="Requested file: other.tf",
        validation_failures=[check.model_dump() for check in checks]
        if with_failure
        else [],
    )
    assert proposal.accepted and proposal.new_files == {}
    assert (REVIEW_FIX in (proposal.content or "")) == repaired
    if repaired:
        assert all(
            check.status == "passed"
            for check in reference_checks(
                PackageDocuments.parse({proposal.path: proposal.content})
            )
        )


@pytest.mark.req("NFR-01", "FR-I-04")
def test_review_scenario_does_not_wrap_real_runs_or_their_stub_fixers(monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.agents import factory as module

    monkeypatch.setattr(
        module, "build_adapter", lambda settings, **kwargs: StubAdapter("fixture")
    )
    configured = settings().model_copy(
        update={
            "llm_provider": LLMProvider.OPENAI,
            "llm_model": "real-model",
            "security_fix_provider": LLMProvider.STUB,
            "pipeline_demo_scenario": "review",
        }
    )
    factory = AgentFactory(
        configured, pipeline_demo_stub=True, session_factory=async_sessionmaker()
    )
    assert type(factory.create_architect().llm_adapter) is StubAdapter
    assert type(factory.create_generator(Variant.SECURITY).llm_adapter) is StubAdapter
    from app.domain.run_config import RunConfig

    assert (
        type(factory.create_security_agent(RunConfig()).fix_agent.adapter)
        is StubAdapter
    )
