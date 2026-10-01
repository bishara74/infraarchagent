"""Architect, parallel generators, then per-package stages and settlement."""

import asyncio
import logging
import time
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.architect import ArchitectError
from app.agents.factory import AgentFactory
from app.agents.generators.base import GeneratorAgent, GeneratorError
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import AgentName, AgentState, PackageStatus, RunStatus, Variant
from app.domain.models import IaCPackage
from app.domain.run_config import RunConfig
from app.domain.states import classify_run, readiness_after_validation
from app.events.kinds import (
    package_generated_payload,
    package_status_payload,
    plan_created_payload,
)
from app.pipeline.stages import SecurityStage, StageContext, ValidationStage
from app.pipeline.state import PipelineStateWriter

logger = logging.getLogger(__name__)
GENERATOR_NAMES = {
    Variant.COST: AgentName.GENERATOR_COST,
    Variant.PERFORMANCE: AgentName.GENERATOR_PERFORMANCE,
    Variant.SECURITY: AgentName.GENERATOR_SECURITY,
}


class PipelineOrchestrator:
    def __init__(
        self,
        run_id: UUID,
        text: str,
        run_config: RunConfig,
        *,
        factory: AgentFactory,
        session_factory: async_sessionmaker[AsyncSession],
        writer: PipelineStateWriter,
        security_stage: SecurityStage,
        validation_stage: ValidationStage,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.run_id = run_id
        self.text = text
        self.run_config = run_config
        self.factory = factory
        self.session_factory = session_factory
        self.writer = writer
        self.security_stage = security_stage
        self.validation_stage = validation_stage
        self.clock = clock

    async def _generate(
        self, generator: GeneratorAgent, plan: object
    ) -> tuple[Variant, IaCPackage | None]:
        variant = generator.variant
        name = GENERATOR_NAMES[variant]
        await self.writer.agent_state(
            self.run_id,
            name,
            AgentState.RUNNING,
            message="generator started",
            variant=variant,
        )
        try:
            package = await generator.generate(plan)  # type: ignore[arg-type]
            async with self.session_factory() as session:
                async with session.begin():
                    await PackageRepository(session).save_files(
                        self.run_id, variant, package.files
                    )
        except GeneratorError as error:
            await self._generation_failed(variant, str(error))
            return variant, None
        except Exception:
            logger.exception("generator %s failed for run %s", variant, self.run_id)
            await self._generation_failed(variant, "package generation failed")
            return variant, None
        await self.writer.package_transition(
            self.run_id, variant, PackageStatus.GENERATED, message="package generated"
        )
        info = generator.last_run
        metrics = (
            {
                "attempts": info.package_attempts,
                "llm_attempts": info.total_llm_attempts,
                "elapsed_seconds": info.elapsed_seconds,
                "input_tokens": info.input_tokens,
                "output_tokens": info.output_tokens,
                "prompt_version": info.prompt_version,
            }
            if info
            else {}
        )
        await self.writer.event_log.append(
            self.run_id,
            name,
            PackageStatus.GENERATED,
            message="package files stored",
            payload=package_generated_payload(
                variant, package.files, metrics, info.notes if info else None
            ),
        )
        await self.writer.agent_state(
            self.run_id,
            name,
            AgentState.COMPLETED,
            previous=AgentState.RUNNING,
            message="generator completed",
            variant=variant,
        )
        return variant, package

    async def _generation_failed(self, variant: Variant, message: str) -> None:
        await self.writer.package_transition(
            self.run_id, variant, PackageStatus.FAILED, message=message, error=message
        )
        await self.writer.agent_state(
            self.run_id,
            GENERATOR_NAMES[variant],
            AgentState.FAILED,
            previous=AgentState.RUNNING,
            message=message,
            variant=variant,
        )

    async def _package_status(self, variant: Variant) -> PackageStatus:
        async with self.session_factory() as session:
            row = await PackageRepository(session).get(self.run_id, variant)
            if row is None:
                raise LookupError("package not found")
            return PackageStatus(row.status)

    async def _stage_error(
        self, variant: Variant, *, validation: bool
    ) -> PackageStatus:
        current = await self._package_status(variant)
        if validation:
            if current in {PackageStatus.SCAN_CLEAN, PackageStatus.SCAN_EXHAUSTED}:
                await self.writer.package_transition(
                    self.run_id,
                    variant,
                    PackageStatus.VALIDATING,
                    message="validation started",
                )
            await self.writer.package_transition(
                self.run_id,
                variant,
                PackageStatus.VALIDATION_ERROR,
                message="validation failed unexpectedly",
                error="validation failed",
            )
            return PackageStatus.VALIDATION_ERROR
        if current == PackageStatus.GENERATED:
            await self.writer.package_transition(
                self.run_id,
                variant,
                PackageStatus.SCANNING,
                message="security stage started",
            )
        await self.writer.package_transition(
            self.run_id,
            variant,
            PackageStatus.SCAN_ERROR,
            message="security stage failed unexpectedly",
            error="security stage failed",
        )
        return PackageStatus.SCAN_ERROR

    async def _post_generation(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        try:
            scan = await self.security_stage.run(ctx, variant, package)
        except Exception:
            logger.exception(
                "security stage failed for run %s variant %s", self.run_id, variant
            )
            scan = await self._stage_error(variant, validation=False)
        if scan == PackageStatus.SCAN_ERROR:
            return scan
        try:
            validation = await self.validation_stage.run(ctx, variant, package)
        except Exception:
            logger.exception(
                "validation stage failed for run %s variant %s", self.run_id, variant
            )
            validation = await self._stage_error(variant, validation=True)
        target = readiness_after_validation(scan, validation)
        await self.writer.package_transition(
            self.run_id, variant, target, message=f"package {target.value}"
        )
        return target

    async def _run_core(self) -> RunStatus:
        await self.writer.run_transition(
            self.run_id, RunStatus.RUNNING, message="pipeline started"
        )
        architect = self.factory.create_architect(self.run_config)
        await self.writer.agent_state(
            self.run_id,
            AgentName.ARCHITECT,
            AgentState.RUNNING,
            message="architect started",
        )
        try:
            architect.parse_input(self.text)
            plan = await architect.generate_plan()
        except ArchitectError as error:
            await self.writer.agent_state(
                self.run_id,
                AgentName.ARCHITECT,
                AgentState.FAILED,
                previous=AgentState.RUNNING,
                message=str(error),
            )
            await self.writer.run_transition(
                self.run_id,
                RunStatus.FAILED,
                message=str(error),
                error_message=str(error),
            )
            return RunStatus.FAILED
        await self.writer.agent_state(
            self.run_id,
            AgentName.ARCHITECT,
            AgentState.COMPLETED,
            previous=AgentState.RUNNING,
            message="architect completed",
        )
        await self.writer.event_log.append(
            self.run_id,
            AgentName.ARCHITECT,
            AgentState.COMPLETED,
            message="deployment plan created",
            payload=plan_created_payload(plan),
        )
        async with self.session_factory() as session:
            async with session.begin():
                repository = PackageRepository(session)
                for variant in Variant:
                    await repository.create(self.run_id, variant)
        for variant in Variant:
            await self.writer.event_log.append(
                self.run_id,
                AgentName.ORCHESTRATOR,
                PackageStatus.GENERATING,
                message="package generation queued",
                payload=package_status_payload(variant),
            )
        generators = self.factory.create_generators(self.run_config)
        results = await asyncio.gather(
            *(self._generate(generator, plan) for generator in generators),
            return_exceptions=True,
        )
        packages: dict[Variant, IaCPackage] = {}
        for result in results:
            if isinstance(result, BaseException):
                raise result
            variant, package = result
            if package is not None:
                packages[variant] = package
        if not packages:
            await self.writer.run_transition(
                self.run_id,
                RunStatus.FAILED,
                message="no package could be generated",
                error_message="no package could be generated",
            )
            return RunStatus.FAILED
        ctx = StageContext(self.run_id, self.writer, plan, self.clock)
        await asyncio.gather(
            *(
                self._post_generation(ctx, variant, package)
                for variant, package in packages.items()
            )
        )
        async with self.session_factory() as session:
            rows = await PackageRepository(session).list_for_run(self.run_id)
        statuses = {Variant(row.variant): PackageStatus(row.status) for row in rows}
        target = classify_run(True, statuses)
        await self.writer.run_transition(
            self.run_id, target, message=f"pipeline {target.value}"
        )
        return target

    async def _fail_unexpected(self, message: str) -> None:
        async with self.session_factory() as session:
            row = await RunRepository(session).get(self.run_id)
        if row is not None and RunStatus(row.status) in {
            RunStatus.CREATED,
            RunStatus.RUNNING,
        }:
            await self.writer.run_transition(
                self.run_id,
                RunStatus.FAILED,
                message=message,
                error_message=message,
            )

    async def run(self) -> RunStatus:
        try:
            return await self._run_core()
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(
                    asyncio.shield(
                        self._fail_unexpected("interrupted by server shutdown")
                    ),
                    timeout=5,
                )
            except Exception:
                logger.exception("could not settle cancelled run %s", self.run_id)
            raise
        except Exception:
            logger.exception("pipeline failed unexpectedly for run %s", self.run_id)
            try:
                await self._fail_unexpected("internal error; see server logs")
            except Exception:
                logger.exception("could not settle failed run %s", self.run_id)
            return RunStatus.FAILED
