"""FR-V-04/05 and FR-S-09: durable reports, events and review retries."""

import json

import pytest
from sqlalchemy import select

from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixProposal
from app.agents.validator import ValidatorAgent
from app.core.config import get_settings
from app.db.models import AgentEvent
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import AgentName, LLMProvider, PackageStatus, Variant
from app.domain.models import IaCPackage
from app.domain.states import readiness_after_validation
from app.domain.validation import ValidationReport
from app.events.log import EventLog
from app.events.publisher import NullPublisher
from app.pipeline.stages import StageContext
from app.pipeline.state import PipelineStateWriter
from app.validation.engine import ValidationEngine
from tests.integration.test_security_agent import ScriptedScanner
from tests.unit.test_generators import plan
from tests.unit.test_validation_engine import Clean, mirror


async def setup(
    engine,
    files,
    scan_outcome=PackageStatus.SCAN_CLEAN,
    *,
    publisher=None,
    scanned=True,
):
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            run = await RunRepository(session).create(
                ("Validate infrastructure"), LLMProvider.STUB, 3
            )
            repository = PackageRepository(session)
            await repository.create(run.run_id, Variant.SECURITY)
            await repository.save_files(run.run_id, Variant.SECURITY, files)
            await repository.transition_status(
                run.run_id, Variant.SECURITY, PackageStatus.GENERATED
            )
            if scanned:
                await repository.transition_status(
                    run.run_id, Variant.SECURITY, PackageStatus.SCANNING
                )
                if scan_outcome == PackageStatus.SCAN_EXHAUSTED:
                    await repository.transition_status(
                        run.run_id, Variant.SECURITY, PackageStatus.REMEDIATING
                    )
                await repository.transition_status(
                    run.run_id, Variant.SECURITY, scan_outcome
                )
    writer = PipelineStateWriter(
        sessions, EventLog(sessions, publisher or NullPublisher())
    )
    return StageContext(
        run.run_id,
        writer,
        plan(
            *(
                [("dockerfile")]
                if any(path.startswith("docker/") for path in files)
                else []
            )
        ),
    ), IaCPackage(variant=Variant.SECURITY, files=files)


@pytest.mark.req("FR-V-04", "FR-V-05", "NFR-01")
@pytest.mark.parametrize(
    ("case,scan,target"),
    [
        (("valid"), PackageStatus.SCAN_CLEAN, PackageStatus.PRODUCTION_READY),
        (("invalid"), PackageStatus.SCAN_CLEAN, PackageStatus.PENDING_REVIEW),
        (("valid"), PackageStatus.SCAN_EXHAUSTED, PackageStatus.PENDING_REVIEW),
        (("error"), PackageStatus.SCAN_CLEAN, PackageStatus.PENDING_REVIEW),
    ],
)
async def test_persist_report_before_outcome_and_option_c(
    db_engines, tmp_path, case, scan, target
):
    engine, _ = db_engines
    sessions = make_session_factory(engine)

    class Observe:
        def __init__(self):
            self.observed = False

        async def publish(self, event):
            if event.payload.get("kind") == ("package_status") and event.new_state in {
                ("valid"),
                ("invalid"),
                ("validation_error"),
            }:
                async with sessions() as session:
                    row = await PackageRepository(session).get(
                        event.run_id, Variant.SECURITY
                    )
                    assert row.validation_report is not None
                    assert (
                        ValidationReport.model_validate(
                            row.validation_report
                        ).summary.result
                        == case
                    )
                    self.observed = True

    observer = Observe()
    files = {"terraform/main.tf": "terraform {}\n# canary-key"}
    if case == "invalid":
        files["docker/Dockerfile"] = "RUN echo hello"
    ctx, package = await setup(engine, files, scan, publisher=observer)
    validation = ValidationEngine(
        Clean(),
        mirror=tmp_path / ("missing") if case == ("error") else mirror(tmp_path),
        versions={},
    )
    outcome = await ValidatorAgent(validation, sessions).run(
        ctx, Variant.SECURITY, package
    )
    assert readiness_after_validation(scan, outcome) == target
    await ctx.writer.package_transition(
        ctx.run_id, Variant.SECURITY, target, message=("readiness")
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        events = list(
            await session.scalars(select(AgentEvent).order_by(AgentEvent.seq))
        )
    assert observer.observed and row.status == target
    report = ValidationReport.model_validate(row.validation_report)
    assert report.summary.result == case
    assert "canary-key" not in json.dumps(row.validation_report)
    assert "canary-key" not in json.dumps([e.payload for e in events])
    assert [
        e.new_state for e in events if e.payload.get("kind") == ("package_status")
    ] == [("validating"), outcome, target]
    assert (
        len(
            [
                e
                for e in events
                if e.agent_name == AgentName.VALIDATOR
                and e.payload.get("kind") == ("stage_notice")
            ]
        )
        == 1
    )


@pytest.mark.req("FR-V-04")
async def test_repository_refuses_report_in_wrong_state(db_engines):
    engine, _ = db_engines
    ctx, _ = await setup(engine, {"terraform/main.tf": "terraform {}"})
    async with make_session_factory(engine)() as session:
        async with session.begin():
            with pytest.raises(ValueError, match="validating"):
                await PackageRepository(session).save_validation_results(
                    ctx.run_id,
                    Variant.SECURITY,
                    ValidationReport.build([], terraform_required=False),
                )


@pytest.mark.req("FR-S-09", "FR-V-04", "FR-V-05")
async def test_validation_only_retry_delivers_persisted_failures_then_revalidates(
    db_engines, tmp_path
):
    engine, _ = db_engines
    sessions = make_session_factory(engine)
    original = {
        "terraform/main.tf": "terraform {}",
        "docker/Dockerfile": "RUN echo hello",
    }
    ctx, package = await setup(engine, original, scanned=False)
    scanner = ScriptedScanner([[], []])

    class Fix:
        def __init__(self):
            self.calls = []

        async def propose(self, **kwargs):
            self.calls.append(kwargs)
            return FixProposal(kwargs["path"], True, None, "FROM alpine:3.20\n", {}, ())

    fixer = Fix()
    security = SecurityAgent(scanner, fixer, sessions, get_settings())
    assert (
        await security.run(ctx, Variant.SECURITY, package) == PackageStatus.SCAN_CLEAN
    )
    validator = ValidatorAgent(
        ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={}), sessions
    )
    assert await validator.run(ctx, Variant.SECURITY, package) == PackageStatus.INVALID
    await ctx.writer.package_transition(
        ctx.run_id, Variant.SECURITY, PackageStatus.PENDING_REVIEW, message=("review")
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        failures = row.validation_report["failed_checks_for_remediation"]
        persisted = package.model_copy(update={"files": dict(row.files)})
    assert failures and all(f["file_path"] == "docker/Dockerfile" for f in failures)
    assert (
        await security.remediate_from_review(
            ctx, Variant.SECURITY, persisted, ("Add the base image"), failures
        )
        == PackageStatus.SCAN_CLEAN
    )
    assert len(fixer.calls) == 1
    assert fixer.calls[0]["feedback"] == "Add the base image"
    assert fixer.calls[0]["validation_failures"] == failures
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        remediated = package.model_copy(update={"files": dict(row.files)})
        assert row.original_files == original
        assert len(row.security_report["sessions"]) == 2
    assert scanner.calls == 2
    assert await validator.run(ctx, Variant.SECURITY, remediated) == PackageStatus.VALID


@pytest.mark.req("FR-V-04", "FR-V-05")
@pytest.mark.parametrize("abort", ["deadline", "internal_error"])
async def test_stage_aborts_persist_error_reports(db_engines, tmp_path, abort):
    import asyncio

    engine, _ = db_engines
    ctx, package = await setup(engine, {"terraform/main.tf": "terraform {}"})

    class Abort(Clean):
        async def run_command(self, *args, **kwargs):
            if abort == "internal_error":
                raise RuntimeError("canary-key")
            await asyncio.Event().wait()

    sessions = make_session_factory(engine)
    validator = ValidatorAgent(
        ValidationEngine(
            Abort(), mirror=mirror(tmp_path), versions={}, deadline_seconds=0.1
        ),
        sessions,
    )
    assert (
        await validator.run(ctx, Variant.SECURITY, package)
        == PackageStatus.VALIDATION_ERROR
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        report = ValidationReport.model_validate(row.validation_report)
    assert report.abort_reason == abort and report.summary.result == "error"
    assert "canary-key" not in report.model_dump_json()


@pytest.mark.req("FR-S-09", "FR-V-05")
async def test_security_evaluator_validates_persisted_remediated_files(
    db_engines, tmp_path, monkeypatch
):
    from scripts import eval_security

    engine, _ = db_engines
    modified = {"terraform/main.tf": "terraform {}\n# persisted remediation"}
    observed = []

    class Factory:
        def __init__(self, settings, **kwargs):
            self.sessions = kwargs["session_factory"]

        def create_security_agent(self, config):
            sessions = self.sessions

            class Security:
                async def run(self, ctx, variant, package):
                    await ctx.writer.package_transition(
                        ctx.run_id, variant, PackageStatus.SCANNING, message="scan"
                    )
                    async with sessions() as session:
                        async with session.begin():
                            await PackageRepository(session).save_security_results(
                                ctx.run_id,
                                variant,
                                original_files=package.files,
                                files=modified,
                                session_report={"final": {"reason": "clean"}},
                                iteration_count=0,
                                policy_version="test",
                                prompt_version="test",
                                tools={},
                            )
                    await ctx.writer.package_transition(
                        ctx.run_id, variant, PackageStatus.SCAN_CLEAN, message="clean"
                    )
                    return PackageStatus.SCAN_CLEAN

            return Security()

        def create_validator_agent(self):
            class Inspect(ValidatorAgent):
                async def run(self, ctx, variant, package):
                    observed.append(package.files)
                    return await super().run(ctx, variant, package)

            return Inspect(
                ValidationEngine(Clean(), mirror=provider_mirror, versions={}),
                self.sessions,
            )

    provider_mirror = mirror(tmp_path)
    monkeypatch.setattr(eval_security, "AgentFactory", Factory)
    folder = tmp_path / "model/three_tier/security"
    package = IaCPackage(
        variant=Variant.SECURITY, files={"terraform/main.tf": "terraform {}"}
    )
    await eval_security._remediate(get_settings(), None, folder, package, 3)
    assert observed == [modified]
