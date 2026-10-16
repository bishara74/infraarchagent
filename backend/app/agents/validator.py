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
from app.validation.measurement import publish_measurement
from app.validation.workspace import current_workspace


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
        if prepared_report is None:
            validation_started = time.monotonic()
            report = await validate_files(self.engine, ctx.plan, package.files)
            await publish_measurement(
                ctx, variant, "final_validation", time.monotonic() - validation_started
            )
        else:
            report = prepared_report
        workspace = current_workspace()
        if workspace is not None:
            annotated_checks = workspace.annotate(report.checks)
            report = report.model_copy(
                update={
                    "checks": annotated_checks,
                    "failed_checks_for_remediation": tuple(
                        c
                        for c in annotated_checks
                        if c.status == "failed" and c.file_path is not None
                    ),
                }
            )
        if report.remediation is None and package.validation_report:
            from app.domain.validation import RemediationReport

            metadata = package.validation_report.get("remediation")
            if metadata is not None:
                report = report.model_copy(
                    update={"remediation": RemediationReport.model_validate(metadata)}
                )
        if workspace is not None and report.remediation is not None:
            metadata = report.remediation.model_copy(
                update={
                    "measurements": list(workspace.measurements),
                    "final_origins": [
                        {
                            "check_id": c.check_id,
                            "file_path": c.file_path,
                            "line_start": c.line_start,
                            "message": c.message,
                            "origin": c.origin,
                        }
                        for c in report.checks
                        if c.status == "failed"
                    ],
                }
            )
            report = report.model_copy(update={"remediation": metadata})
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
            metrics={"prepared_report": prepared_report is not None},
        )
        return outcome
