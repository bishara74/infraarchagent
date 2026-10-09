"""Persist deterministic validation before publishing its package outcome."""

import time

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.safety import PublicDataSafety
from app.db.repositories.packages import PackageRepository
from app.domain.enums import AgentName, AgentState, PackageStatus, Variant
from app.domain.models import IaCPackage
from app.domain.validation import ValidationReport, package_validation_status
from app.events.kinds import stage_notice_payload
from app.pipeline.stages import StageContext
from app.validation.engine import ValidationEngine


class ValidatorAgent:
    def __init__(
        self,
        engine: ValidationEngine,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        settings: Settings | None = None,
    ) -> None:
        self.engine = engine
        self.session_factory = session_factory
        self.safety = PublicDataSafety(settings) if settings else None

    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        started = time.monotonic()
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.VALIDATOR,
            AgentState.RUNNING,
            message="validation started",
            variant=variant,
        )
        await ctx.writer.package_transition(
            ctx.run_id, variant, PackageStatus.VALIDATING, message="validation started"
        )
        report = await self.engine.validate(ctx.plan, package.files)
        if self.safety is not None:
            report = ValidationReport.model_validate(
                self.safety.value(report.model_dump(mode="json"))
            )
        async with self.session_factory() as session:
            async with session.begin():
                await PackageRepository(session).save_validation_results(
                    ctx.run_id, variant, report
                )
        outcome = package_validation_status(report.summary.result)
        await ctx.writer.event_log.append(
            ctx.run_id,
            AgentName.VALIDATOR,
            PackageStatus.VALIDATING,
            message="validation summary",
            payload=stage_notice_payload(
                variant,
                "validation summary",
                {
                    **report.summary.model_dump(),
                    "duration_seconds": round(time.monotonic() - started, 3),
                },
            ),
        )
        await ctx.writer.package_transition(
            ctx.run_id,
            variant,
            outcome,
            message=f"validation {report.summary.result}",
            error="validation could not complete"
            if outcome == PackageStatus.VALIDATION_ERROR
            else None,
        )
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.VALIDATOR,
            AgentState.FAILED
            if outcome == PackageStatus.VALIDATION_ERROR
            else AgentState.COMPLETED,
            previous=AgentState.RUNNING,
            message=f"validation {report.summary.result}",
            variant=variant,
        )
        return outcome
