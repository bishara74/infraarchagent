"""Deterministic generator barrier and run settlement with fake stages."""

import asyncio
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.requests import Request
from starlette.responses import StreamingResponse

from app.agents.architect import ArchitectInvalidPlan
from app.agents.generators.base import GeneratorError
from app.api.pipeline import stream_run
from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.domain.models import IaCPackage
from app.domain.plan import DeploymentPlan
from app.domain.run_config import RunConfig
from app.events.log import EventLog
from app.events.publisher import NullPublisher
from app.main import create_app
from app.pipeline.demo_stub import DEMO_PLAN
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.stages import StageContext
from app.pipeline.state import PipelineStateWriter


class FakeArchitect:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def parse_input(self, text: str) -> None:
        assert text

    async def generate_plan(self) -> DeploymentPlan:
        if self.fail:
            raise ArchitectInvalidPlan(["invalid plan"])
        return DeploymentPlan.model_validate(DEMO_PLAN)


class FakeGenerator:
    def __init__(
        self,
        variant: Variant,
        *,
        release: asyncio.Event | None = None,
        started: asyncio.Event | None = None,
        fail: bool = False,
    ) -> None:
        self.variant = variant
        self.release = release
        self.started = started
        self.fail = fail
        self.last_run = None

    async def generate(self, plan: DeploymentPlan) -> IaCPackage:
        assert plan.file_types
        if self.started is not None:
            self.started.set()
        if self.release is not None:
            await self.release.wait()
        if self.fail:
            raise GeneratorError(self.variant, "generator failed")
        return IaCPackage(
            variant=self.variant,
            files={"terraform/main.tf": f"# {self.variant.value}"},
        )


class FakeFactory:
    def __init__(
        self, generators: list[FakeGenerator], *, architect_fails: bool = False
    ) -> None:
        self.generators = generators
        self.architect_fails = architect_fails
        self.generators_created = False

    def create_architect(self, config: RunConfig) -> FakeArchitect:
        return FakeArchitect(self.architect_fails)

    def create_generators(self, config: RunConfig) -> list[FakeGenerator]:
        self.generators_created = True
        return self.generators


class FakeSecurity:
    def __init__(self, outcome: PackageStatus = PackageStatus.SCAN_CLEAN) -> None:
        self.outcome = outcome
        self.calls: list[Variant] = []

    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        self.calls.append(variant)
        await ctx.writer.package_transition(
            ctx.run_id, variant, PackageStatus.SCANNING, message="scan started"
        )
        if self.outcome == PackageStatus.SCAN_EXHAUSTED:
            await ctx.writer.package_transition(
                ctx.run_id,
                variant,
                PackageStatus.REMEDIATING,
                message="remediation started",
            )
        await ctx.writer.package_transition(
            ctx.run_id, variant, self.outcome, message="scan ended"
        )
        return self.outcome


class FakeValidation:
    def __init__(self, outcome: PackageStatus = PackageStatus.VALID) -> None:
        self.outcome = outcome

    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        await ctx.writer.package_transition(
            ctx.run_id,
            variant,
            PackageStatus.VALIDATING,
            message="validation started",
        )
        await ctx.writer.package_transition(
            ctx.run_id, variant, self.outcome, message="validation ended"
        )
        return self.outcome


class BrokenSecurity:
    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        raise RuntimeError("hidden provider failure")


@pytest.mark.req("FR-S-02", "FR-S-07")
async def test_validation_receives_remediated_files(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines

    class ChangedSecurity:
        async def run(
            self, ctx: StageContext, variant: Variant, package: IaCPackage
        ) -> PackageStatus:
            await ctx.writer.package_transition(
                ctx.run_id, variant, PackageStatus.SCANNING, message="scanning"
            )
            async with make_session_factory(engine)() as session:
                async with session.begin():
                    await PackageRepository(session).save_files(
                        ctx.run_id, variant, {"terraform/main.tf": "remediated\n"}
                    )
            await ctx.writer.package_transition(
                ctx.run_id, variant, PackageStatus.SCAN_CLEAN, message="clean"
            )
            return PackageStatus.SCAN_CLEAN

    class InspectValidation(FakeValidation):
        async def run(
            self, ctx: StageContext, variant: Variant, package: IaCPackage
        ) -> PackageStatus:
            assert package.files == {"terraform/main.tf": "remediated\n"}
            return await super().run(ctx, variant, package)

    orchestrator, _, _ = await make_orchestrator(
        engine, FakeFactory([FakeGenerator(v) for v in Variant])
    )
    orchestrator.security_stage = ChangedSecurity()
    orchestrator.validation_stage = InspectValidation()
    assert await orchestrator.run() == RunStatus.SUCCESS


async def make_orchestrator(
    engine: AsyncEngine,
    factory: FakeFactory,
    security: FakeSecurity | None = None,
) -> tuple[PipelineOrchestrator, UUID, PipelineStateWriter]:
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            run = await RunRepository(session).create(
                "Deploy AWS web service", LLMProvider.STUB, 3
            )
            run_id = run.run_id
    writer = PipelineStateWriter(sessions, EventLog(sessions, NullPublisher()))
    orchestrator = PipelineOrchestrator(
        run_id,
        "Deploy AWS web service",
        RunConfig(),
        factory=factory,  # type: ignore[arg-type]
        session_factory=sessions,
        writer=writer,
        security_stage=security or FakeSecurity(),
        validation_stage=FakeValidation(),
    )
    return orchestrator, run_id, writer


@pytest.mark.req("FR-P-01", "FR-P-02", "FR-G-01")
async def test_barrier_blocks_security_until_every_generator_resolves(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    started = [asyncio.Event() for _ in range(3)]
    release = [asyncio.Event() for _ in range(2)]
    factory = FakeFactory(
        [
            FakeGenerator(Variant.COST, started=started[0]),
            FakeGenerator(Variant.PERFORMANCE, started=started[1], release=release[0]),
            FakeGenerator(Variant.SECURITY, started=started[2], release=release[1]),
        ]
    )
    security = FakeSecurity()
    orchestrator, _, _ = await make_orchestrator(engine, factory, security)
    task = asyncio.create_task(orchestrator.run())
    try:
        await asyncio.gather(*(event.wait() for event in started))
        assert security.calls == []
        release[0].set()
        await asyncio.wait_for(
            _wait_for_package(engine, orchestrator.run_id, Variant.PERFORMANCE),
            timeout=5,
        )
        assert security.calls == []
        release[1].set()
        assert await task == RunStatus.SUCCESS
        assert set(security.calls) == set(Variant)
    finally:
        release[0].set()
        release[1].set()
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def _wait_for_package(
    engine: AsyncEngine, run_id: UUID, variant: Variant
) -> None:
    sessions = make_session_factory(engine)
    while True:
        async with sessions() as session:
            row = await PackageRepository(session).get(run_id, variant)
            if row is not None and row.status == PackageStatus.GENERATED:
                return
        await asyncio.sleep(0)


@pytest.mark.req("FR-P-03", "FR-G-06")
@pytest.mark.parametrize(
    "failed_variant,scan_outcome,expected",
    [
        (Variant.SECURITY, PackageStatus.SCAN_CLEAN, RunStatus.PARTIAL_SUCCESS),
        (None, PackageStatus.SCAN_EXHAUSTED, RunStatus.PARTIAL_SUCCESS),
    ],
)
async def test_partial_and_review_outcomes(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    failed_variant: Variant | None,
    scan_outcome: PackageStatus,
    expected: RunStatus,
) -> None:
    engine, _ = db_engines
    factory = FakeFactory(
        [FakeGenerator(variant, fail=variant == failed_variant) for variant in Variant]
    )
    orchestrator, run_id, _ = await make_orchestrator(
        engine, factory, FakeSecurity(scan_outcome)
    )
    assert await orchestrator.run() == expected
    async with make_session_factory(engine)() as session:
        rows = await PackageRepository(session).list_for_run(run_id)
    statuses = {Variant(row.variant): PackageStatus(row.status) for row in rows}
    if failed_variant:
        assert statuses[failed_variant] == PackageStatus.FAILED
        assert all(
            status == PackageStatus.PRODUCTION_READY
            for variant, status in statuses.items()
            if variant != failed_variant
        )
    else:
        assert set(statuses.values()) == {PackageStatus.PENDING_REVIEW}


@pytest.mark.req("FR-A-04", "FR-P-03")
async def test_architect_failure_never_constructs_generators(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    factory = FakeFactory([], architect_fails=True)
    orchestrator, run_id, _ = await make_orchestrator(engine, factory)
    assert await orchestrator.run() == RunStatus.FAILED
    assert not factory.generators_created
    async with make_session_factory(engine)() as session:
        row = await RunRepository(session).get(run_id)
        packages = await PackageRepository(session).list_for_run(run_id)
    assert row is not None and row.error_message
    assert packages == []


@pytest.mark.req("FR-P-03")
async def test_all_generators_fail_and_run_settles(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    factory = FakeFactory([FakeGenerator(variant, fail=True) for variant in Variant])
    orchestrator, run_id, _ = await make_orchestrator(engine, factory)
    assert await orchestrator.run() == RunStatus.FAILED
    async with make_session_factory(engine)() as session:
        row = await RunRepository(session).get(run_id)
    assert row is not None and row.status == RunStatus.FAILED


@pytest.mark.req("FR-P-03")
async def test_unexpected_stage_error_becomes_scan_error(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    factory = FakeFactory([FakeGenerator(variant) for variant in Variant])
    orchestrator, run_id, _ = await make_orchestrator(engine, factory)
    orchestrator.security_stage = BrokenSecurity()
    assert await orchestrator.run() == RunStatus.FAILED
    async with make_session_factory(engine)() as session:
        rows = await PackageRepository(session).list_for_run(run_id)
    assert len(rows) == 3
    assert all(row.status == PackageStatus.SCAN_ERROR for row in rows)


@pytest.mark.req("FR-P-03", "FR-P-04", "NFR-01")
async def test_unexpected_core_error_fails_run_without_exposing_exception(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    private_message = "private create_generators failure marker"
    public_message = "internal error; see server logs"

    class BrokenFactory(FakeFactory):
        def create_generators(self, config: RunConfig) -> list[FakeGenerator]:
            self.generators_created = True
            raise RuntimeError(private_message)

    factory = BrokenFactory([])
    orchestrator, run_id, writer = await make_orchestrator(engine, factory)
    assert await orchestrator.run() == RunStatus.FAILED
    assert factory.generators_created

    async with make_session_factory(engine)() as session:
        row = await RunRepository(session).get(run_id)
    assert row is not None
    assert row.status == RunStatus.FAILED
    assert row.error_message == public_message
    assert private_message not in str(
        {column.key: getattr(row, column.key) for column in row.__table__.columns}
    )

    events = await writer.event_log.list_after(run_id, None)
    assert any(
        event.new_state == RunStatus.FAILED and event.message == public_message
        for event in events
    )
    assert private_message not in str(events)

    app = create_app(get_settings(), engine)
    request = Request(
        {"type": "http", "method": "GET", "path": "/", "headers": [], "app": app}
    )
    response = await stream_run(
        str(run_id), request, app.state.event_log, app.state.broker, None
    )
    assert isinstance(response, StreamingResponse)
    stream = response.body_iterator
    try:
        frames = [await asyncio.wait_for(anext(stream), timeout=2) for _ in events]
        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(anext(stream), timeout=2)
    finally:
        await stream.aclose()
    assert public_message in "".join(frames)
    assert private_message not in "".join(frames)


@pytest.mark.req("FR-P-03")
async def test_cancelled_run_is_failed(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    started = asyncio.Event()
    release = asyncio.Event()
    factory = FakeFactory(
        [
            FakeGenerator(variant, started=started, release=release)
            for variant in Variant
        ]
    )
    orchestrator, run_id, _ = await make_orchestrator(engine, factory)
    task = asyncio.create_task(orchestrator.run())
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    async with make_session_factory(engine)() as session:
        row = await RunRepository(session).get(run_id)
    assert row is not None and row.status == RunStatus.FAILED
