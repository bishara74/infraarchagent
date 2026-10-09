"""One-statement current run/package/plan snapshot."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentEvent, GeneratedPackage, PipelineRun
from app.events.kinds import EventKind


@dataclass(frozen=True)
class ResultsSnapshot:
    run: PipelineRun
    packages: list[GeneratedPackage]
    plan: dict[str, Any] | None


class ResultsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def snapshot(self, run_id: UUID) -> ResultsSnapshot | None:
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
                select(PipelineRun, GeneratedPackage, plan)
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
            rows[0][0], [row[1] for row in rows if row[1] is not None], rows[0][2]
        )
