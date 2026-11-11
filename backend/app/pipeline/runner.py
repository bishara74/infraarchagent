# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Bounded background-task ownership for a single application process."""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.factory import AgentFactory
from app.core.safety import PublicDataSafety
from app.db.models import User
from app.db.repositories.runs import RunRepository
from app.domain.enums import RunStatus, Variant
from app.domain.run_config import RunConfig
from app.domain.states import TERMINAL_RUNS
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.stages import SecurityStage, ValidationStage
from app.pipeline.state import PipelineStateWriter

logger = logging.getLogger(__name__)


class RunCancellationError(ValueError):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


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
        self._pipelines: dict[UUID, PipelineOrchestrator] = {}
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
        self._own(run_id, orchestrator.run(), name=f"pipeline-{run_id}")
        self._pipelines[run_id] = orchestrator

    async def cancel(
        self, run_id: UUID, *, user: User | None, reviewer_name: str | None
    ) -> None:
        async with self.writer.event_log.serialize_run(run_id):
            async with self.session_factory() as session:
                run = await RunRepository(session).get(run_id)
            if run is None:
                raise RunCancellationError(404, "not_found", "Pipeline run not found.")
            if (user is None and run.user_id is not None) or (
                user is not None and user.role != "admin" and user.id != run.user_id
            ):
                raise RunCancellationError(
                    403, "forbidden", "You cannot cancel this run."
                )
            task = self.tasks.get(run_id)
            pipeline = self._pipelines.get(run_id)
            if (
                RunStatus(run.status) in TERMINAL_RUNS
                or pipeline is None
                or task is None
                or task.done()
            ):
                raise RunCancellationError(
                    409, "not_cancellable", "This pipeline run cannot be cancelled."
                )
            identity = (
                user.username if user is not None else (reviewer_name or "").strip()
            )
            if not identity:
                raise RunCancellationError(
                    400, "invalid_request", "Reviewer name is required."
                )
            if pipeline.cancelled_by is None:
                pipeline.cancelled_by = PublicDataSafety(self.factory.settings).text(
                    identity
                )
                # An unstarted task enters the same cancellation handler on its
                # first step. Task.cancel() before entry would bypass that handler.
                if pipeline.entered:
                    task.cancel()

    def start_review_retry(
        self, run_id: UUID, variant: Variant, target_files: list[str]
    ) -> None:
        from app.pipeline.review import ReviewService

        self._own(
            uuid4(),
            ReviewService(self).run_retry(run_id, variant, target_files),
            name=f"review-{run_id}-{variant}",
        )

    def _own(
        self, task_id: UUID, coroutine: Coroutine[Any, Any, object], *, name: str
    ) -> None:
        task = asyncio.create_task(coroutine, name=name)
        self.tasks[task_id] = task

        def finished(done: asyncio.Task[object]) -> None:
            self.tasks.pop(task_id, None)
            self._pipelines.pop(task_id, None)
            self.release()
            if not done.cancelled():
                try:
                    done.result()
                except Exception:
                    logger.exception("pipeline task escaped guard for task %s", task_id)

        task.add_done_callback(finished)

    async def shutdown(self) -> None:
        tasks = list(self.tasks.values())
        for task_id, task in self.tasks.items():
            pipeline = self._pipelines.get(task_id)
            if pipeline is None or pipeline.cancelled_by is None:
                task.cancel()
        if tasks:
            _, pending = await asyncio.wait(tasks, timeout=10)
            if pending:
                logger.error(
                    "pipeline shutdown timed out; startup recovery will settle runs"
                )
