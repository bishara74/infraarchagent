"""One-statement current run/package/plan snapshot."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentEvent, GeneratedPackage, PipelineRun
from app.domain.enums import PackageStatus, Variant
from app.events.kinds import EventKind


@dataclass(frozen=True)
class ResultsSnapshot:
    run: PipelineRun
    packages: list[GeneratedPackage]
    plan: dict[str, Any] | None
    telemetry: list[dict[str, Any]] = field(default_factory=list)


class ResultsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def archive_snapshot(self, run_id: UUID) -> ResultsSnapshot | None:
        # Establish a repeatable snapshot before package and label-event reads.
        await self.session.connection(
            execution_options={"isolation_level": "REPEATABLE READ"}
        )
        return await self.snapshot(run_id)

    async def review_retry_before(
        self, run_id: UUID, variant: Variant, label_seq: int
    ) -> bool:
        return (
            await self.session.scalar(
                select(AgentEvent.seq)
                .where(
                    AgentEvent.run_id == run_id,
                    AgentEvent.seq < label_seq,
                    AgentEvent.payload["kind"].astext == EventKind.PACKAGE_STATUS,
                    AgentEvent.payload["variant"].astext == variant.value,
                    AgentEvent.payload["review_action"].astext == "retry",
                )
                .limit(1)
            )
        ) is not None

    async def label_event(
        self, run_id: UUID, variant: Variant, status: PackageStatus
    ) -> AgentEvent | None:
        return await self.session.scalar(
            select(AgentEvent)
            .where(
                AgentEvent.run_id == run_id,
                AgentEvent.payload["kind"].astext == EventKind.PACKAGE_STATUS,
                AgentEvent.payload["variant"].astext == variant.value,
                AgentEvent.new_state.in_(
                    [
                        status.value,
                        "production_ready"
                        if status
                        in {
                            PackageStatus.CHECKS_PASSED,
                            PackageStatus.ENGINEER_APPROVED,
                        }
                        else "not_production_ready"
                        if status == PackageStatus.REJECTED
                        else status.value,
                    ]
                ),
            )
            .order_by(AgentEvent.seq.desc())
            .limit(1)
        )

    async def snapshot(self, run_id: UUID) -> ResultsSnapshot | None:
        telemetry = (
            select(
                func.jsonb_agg(
                    aggregate_order_by(AgentEvent.payload["telemetry"], AgentEvent.seq)
                )
            )
            .where(
                AgentEvent.run_id == PipelineRun.run_id,
                AgentEvent.payload["notice"].astext == "runtime telemetry",
            )
            .correlate(PipelineRun)
            .scalar_subquery()
        )
        plan = (
            select(AgentEvent.payload["plan"])
            .where(
                AgentEvent.run_id == PipelineRun.run_id,
                AgentEvent.payload["kind"].astext == EventKind.PLAN_CREATED,
            )
            .order_by(AgentEvent.seq.desc())
            .limit(1)
            .correlate(PipelineRun)
            .scalar_subquery()
        )
        rows = (
            await self.session.execute(
                select(PipelineRun, GeneratedPackage, plan, telemetry)
                .outerjoin(
                    GeneratedPackage, GeneratedPackage.run_id == PipelineRun.run_id
                )
                .where(PipelineRun.run_id == run_id)
                .order_by(GeneratedPackage.variant)
            )
        ).all()
        if not rows:
            return None
        return ResultsSnapshot(
            rows[0][0],
            [row[1] for row in rows if row[1] is not None],
            rows[0][2],
            [record for batch in rows[0][3] or [] for record in batch],
        )
