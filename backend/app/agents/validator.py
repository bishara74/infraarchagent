"""Persist deterministic validation before publishing its package outcome."""

import time

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.remediation import validate_files
from app.core.config import Settings
from app.core.safety import PublicDataSafety
from app.db.repositories.packages import PackageRepository
from app.domain.enums import AgentName, AgentState, PackageStatus, Variant
from app.domain.models import IaCPackage
from app.domain.validation import (
    ValidationCheck,
    ValidationReport,
    check_order,
    package_validation_status,
)
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
        self,
        ctx: StageContext,
        variant: Variant,
        package: IaCPackage,
        *,
        prepared_report: ValidationReport | None = None,
        already_validating: bool = False,
    ) -> PackageStatus:
        started = time.monotonic()
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.VALIDATOR,
            AgentState.RUNNING,
            message="validation started",
            variant=variant,
        )
        if not already_validating:
            await ctx.writer.package_transition(
                ctx.run_id,
                variant,
                PackageStatus.VALIDATING,
                message="validation started",
            )
        report = prepared_report or await validate_files(
            self.engine, ctx.plan, package.files
        )
        if report.remediation is None and package.validation_report:
            from app.domain.validation import RemediationReport

            metadata = package.validation_report.get("remediation")
            if metadata is not None:
                report = report.model_copy(
                    update={"remediation": RemediationReport.model_validate(metadata)}
                )
        if self.safety is not None:
            safe = self.safety.value(report.model_dump(mode="json"))
            checks = sorted(
                (ValidationCheck.model_validate(item) for item in safe["checks"]),
                key=check_order,
            )
            safe["checks"] = tuple(checks)
            safe["failed_checks_for_remediation"] = tuple(
                check
                for check in checks
                if check.status == "failed" and check.file_path is not None
            )
            report = ValidationReport.model_validate(safe)
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
