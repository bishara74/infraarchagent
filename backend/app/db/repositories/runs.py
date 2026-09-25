"""Run persistence; status changes always use domain transitions."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PipelineRun
from app.domain.enums import LLMProvider, RunStatus
from app.domain.states import assert_run_transition


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        input_text: str,
        llm_provider: LLMProvider,
        max_iterations: int,
        *,
        model: str | None = None,
        run_id: UUID | None = None,
    ) -> PipelineRun:
        if max_iterations < 1:
            raise ValueError("max_iterations must be positive")
        row = PipelineRun(
            run_id=run_id or uuid4(),
            input_text=input_text,
            status=RunStatus.CREATED,
            start_time=datetime.now(UTC),
            end_time=None,
            llm_provider=llm_provider,
            model=model,
            max_iterations=max_iterations,
            error_message=None,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get(self, run_id: UUID) -> PipelineRun | None:
        return await self.session.get(PipelineRun, run_id)

    async def set_status(self, run_id: UUID, target: RunStatus) -> PipelineRun:
        row = await self.session.scalar(
            select(PipelineRun)
            .where(PipelineRun.run_id == run_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row is None:
            raise LookupError("run not found")
        assert_run_transition(RunStatus(row.status), target)
        row.status = target
        if target in {RunStatus.SUCCESS, RunStatus.PARTIAL_SUCCESS, RunStatus.FAILED}:
            row.end_time = datetime.now(UTC)
        await self.session.flush()
        return row
