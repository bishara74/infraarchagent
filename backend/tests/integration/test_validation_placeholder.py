"""FR-S-07: Phase 5 records validation unavailability before review."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.models import AgentEvent
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider, PackageStatus, Variant
from app.domain.models import IaCPackage
from app.domain.plan import DeploymentPlan
from app.events.log import EventLog
from app.events.publisher import NullPublisher
from app.pipeline.demo_stub import DEMO_PLAN
from app.pipeline.stages import StageContext, UnavailableValidationStage
from app.pipeline.state import PipelineStateWriter


@pytest.mark.req("FR-S-07")
@pytest.mark.parametrize(
    "scan_outcome", [PackageStatus.SCAN_CLEAN, PackageStatus.SCAN_EXHAUSTED]
)
async def test_placeholder_records_legal_transitions_and_notice(
    db_engines: tuple[AsyncEngine, AsyncEngine], scan_outcome: PackageStatus
) -> None:
    engine, _ = db_engines
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            run = await RunRepository(session).create(
                "test validation", LLMProvider.STUB, 3
            )
            repository = PackageRepository(session)
            await repository.create(run.run_id, Variant.SECURITY)
            await repository.save_files(
                run.run_id, Variant.SECURITY, {"terraform/main.tf": "terraform {}\n"}
            )
            await repository.transition_status(
                run.run_id, Variant.SECURITY, PackageStatus.GENERATED
            )
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
    writer = PipelineStateWriter(sessions, EventLog(sessions, NullPublisher()))
    ctx = StageContext(run.run_id, writer, DeploymentPlan.model_validate(DEMO_PLAN))
    result = await UnavailableValidationStage().run(
        ctx,
        Variant.SECURITY,
        IaCPackage(
            variant=Variant.SECURITY, files={"terraform/main.tf": "terraform {}\n"}
        ),
    )
    assert result == PackageStatus.VALIDATION_ERROR
    async with sessions() as session:
        row = await PackageRepository(session).get(run.run_id, Variant.SECURITY)
        events = list(
            await session.scalars(select(AgentEvent).order_by(AgentEvent.seq))
        )
    assert row is not None and row.status == PackageStatus.VALIDATION_ERROR
    assert any(
        event.payload.get("notice") == "validation is not available in this build"
        for event in events
    )
    assert [
        event.new_state
        for event in events
        if event.payload.get("kind") == "package_status"
    ] == [PackageStatus.VALIDATING, PackageStatus.VALIDATION_ERROR]
