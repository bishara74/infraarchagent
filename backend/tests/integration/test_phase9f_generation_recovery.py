"""FR-G-02/FR-S-03: syntax recovery precedes the first scanner baseline."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.agents.generators.security import SecurityGeneratorAgent
from app.agents.security.fix import FixProposal
from app.agents.validator import ValidatorAgent
from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus, Variant
from app.domain.plan import DeploymentPlan
from app.domain.run_config import RunConfig
from app.llm.stub import StubAdapter
from app.pipeline.orchestrator import PipelineOrchestrator
from app.scanners.scan import ScanResult
from app.validation.engine import ValidationEngine
from app.validation.workspace import ValidationWorkspace
from tests.integration.test_security_agent import agent, finding, setup
from tests.unit.test_generators import reply
from tests.unit.test_phase9e_gate import Runner


@pytest.mark.req("FR-G-02", "FR-S-03", "FR-V-03", "NFR-01")
@pytest.mark.parametrize(
    "recovery_path", ["syntax_round_1", "regeneration", "normalization"]
)
async def test_generation_syntax_recovery_keeps_newly_revealed_findings_blocking(
    db_engines,
    recovery_path,
):
    engine, _ = db_engines
    ctx, _ = await setup(engine, max_iterations=1)
    ctx = replace(
        ctx,
        plan=DeploymentPlan.model_validate(
            {
                **ctx.plan.model_dump(),
                "file_types": ["terraform"],
            }
        ),
    )
    original = {"terraform/main.tf": 'output "x" { value = [var.name var.other] }'}
    valid = {"terraform/main.tf": 'output "x" { value = [var.name, var.other] }'}
    if recovery_path == "normalization":
        original = {
            "terraform/main.tf": 'output "x" { value = var.name description = "keep" }'
        }

    class Fixer:
        async def propose(self, **kwargs):
            if kwargs.get("syntax_only"):
                if recovery_path == "regeneration":
                    return FixProposal(
                        kwargs["path"], False, "invalid_syntax", None, {}, ()
                    )
                return FixProposal(
                    kwargs["path"], True, None, valid["terraform/main.tf"], {}, ()
                )
            return FixProposal(kwargs["path"], False, "invalid_patch", None, {}, ())

    class Scanner:
        calls = 0

        async def scan(self, files, variant, **kwargs):
            self.calls += 1
            return ScanResult([finding("NEWLY_VISIBLE")], {"checkov": "ok"})

    scanner = Scanner()
    security = agent(engine, scanner, Fixer())
    settings = get_settings()
    sessions = make_session_factory(engine)
    generator = SecurityGeneratorAgent(
        StubAdapter(script=[reply(original), reply(valid)]),
        deadline_seconds=150,
        attempt_timeout=140,
        max_output_tokens=16000,
        max_package_attempts=2,
    )
    pipeline = PipelineOrchestrator(
        ctx.run_id,
        "test generation",
        RunConfig(),
        factory=SimpleNamespace(settings=settings),
        session_factory=sessions,
        writer=ctx.writer,
        security_stage=security,
        validation_stage=ValidatorAgent(
            ValidationEngine(Runner(), versions={}), sessions
        ),
    )
    workspace = ValidationWorkspace()
    try:
        with workspace.activate():
            package = await generator.generate(ctx.plan)
            recovered = await pipeline._prepare_generation(
                generator, ctx.plan, package, ctx.clock()
            )
            assert (
                recovered.validation_report["remediation"]["generation_syntax"]["path"]
                == recovery_path
            )
            assert 'variable "name"' in recovered.files["terraform/variables.tf"]
            assert scanner.calls == 0
            async with sessions() as session:
                async with session.begin():
                    await PackageRepository(session).save_files(
                        ctx.run_id, Variant.SECURITY, recovered.files
                    )
            result = await security.run(ctx, Variant.SECURITY, recovered)
        assert result == PackageStatus.SCAN_EXHAUSTED
        async with sessions() as session:
            row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert (
            row.security_report["final"]["remaining_blocking"][0]["rule_id"]
            == "NEWLY_VISIBLE"
        )
        assert row.security_report["final"]["remaining_blocking"][0]["blocking"]
    finally:
        workspace.close()


@pytest.mark.req("FR-V-03", "FR-V-04", "FR-P-04")
async def test_duplicate_repair_retains_originals_report_and_event(db_engines):
    from sqlalchemy import select

    from app.db.models import AgentEvent
    from tests.unit.test_phase9m_duplicates import ALB, LOGS

    engine, _ = db_engines
    ctx, _ = await setup(engine)
    ctx = replace(
        ctx,
        plan=DeploymentPlan.model_validate(
            {**ctx.plan.model_dump(), "file_types": ["terraform"]}
        ),
    )
    sessions = make_session_factory(engine)
    original = {"terraform/main.tf": ALB + LOGS}
    generator = SecurityGeneratorAgent(
        StubAdapter(script=[reply(original)]),
        deadline_seconds=150,
        attempt_timeout=140,
        max_output_tokens=16000,
        max_package_attempts=2,
    )
    pipeline = PipelineOrchestrator(
        ctx.run_id,
        "duplicate repair",
        RunConfig(),
        factory=SimpleNamespace(settings=get_settings()),
        session_factory=sessions,
        writer=ctx.writer,
        security_stage=None,
        validation_stage=ValidatorAgent(
            ValidationEngine(Runner(), versions={}), sessions
        ),
    )
    workspace = ValidationWorkspace()
    try:
        with workspace.activate():
            package = await generator.generate(ctx.plan)
            # Exercise deterministic repair/event publication without model recovery.
            generator.deadline_seconds = 0
            fixed = await pipeline._prepare_generation(
                generator, ctx.plan, package, ctx.clock()
            )
            metadata = fixed.validation_report["remediation"]
            assert metadata["deterministic_repairs"][0]["kind"] == "duplicate_block"
            assert metadata["deterministic_repairs"][0]["origin"] == "generated"
            async with sessions() as session, session.begin():
                await PackageRepository(session).save_automatic_repairs(
                    ctx.run_id,
                    Variant.SECURITY,
                    original_files=workspace.original_files,
                    files=fixed.files,
                )
        async with sessions() as session:
            row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
            events = (
                await session.scalars(
                    select(AgentEvent).where(AgentEvent.run_id == ctx.run_id)
                )
            ).all()
        assert row.original_files == original
        assert row.files["terraform/main.tf"].count('resource "aws_lb"') == 1
        assert any(
            event.payload.get("measurement", {}).get("stage") == "deterministic_repairs"
            for event in events
        )
    finally:
        workspace.close()
