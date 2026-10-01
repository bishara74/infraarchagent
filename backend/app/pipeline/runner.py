"""Bounded background-task ownership for a single application process."""

import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.factory import AgentFactory
from app.domain.run_config import RunConfig
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.stages import SecurityStage, ValidationStage
from app.pipeline.state import PipelineStateWriter

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(
        self,
        *,
        capacity: int,
        factory: AgentFactory,
        session_factory: async_sessionmaker[AsyncSession],
        writer: PipelineStateWriter,
        security_stage: SecurityStage | None,
        validation_stage: ValidationStage,
    ) -> None:
        self.capacity = capacity
        self.factory = factory
        self.session_factory = session_factory
        self.writer = writer
        self.security_stage = security_stage
        self.validation_stage = validation_stage
        self.tasks: dict[UUID, asyncio.Task[object]] = {}
        self._reserved = 0

    def reserve(self) -> bool:
        if self._reserved >= self.capacity:
            return False
        self._reserved += 1
        return True

    def release(self) -> None:
        if self._reserved:
            self._reserved -= 1

    def start(self, run_id: UUID, text: str, config: RunConfig) -> None:
        if run_id in self.tasks:
            raise ValueError("run already started")
        orchestrator = PipelineOrchestrator(
            run_id,
            text,
            config,
            factory=self.factory,
            session_factory=self.session_factory,
            writer=self.writer,
            security_stage=self.security_stage,
            validation_stage=self.validation_stage,
        )
        task = asyncio.create_task(orchestrator.run(), name=f"pipeline-{run_id}")
        self.tasks[run_id] = task

        def finished(done: asyncio.Task[object]) -> None:
            self.tasks.pop(run_id, None)
            self.release()
            if not done.cancelled():
                try:
                    done.result()
                except Exception:
                    logger.exception("pipeline task escaped guard for run %s", run_id)

        task.add_done_callback(finished)

    async def shutdown(self) -> None:
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), timeout=10
                )
            except TimeoutError:
                logger.error(
                    "pipeline shutdown timed out; startup recovery will settle runs"
                )
