"""Bounded validation feedback using the engineer-Retry remediation path."""

import asyncio
from typing import Literal

from app.agents.budget import AgentBudget
from app.agents.remediation import ValidationService, scan_files, validate_files
from app.agents.security.agent import SecurityAgent
from app.domain.enums import AgentName, PackageStatus, Variant
from app.domain.models import IaCPackage, Violation
from app.domain.validation import RemediationReport, RepairRound, ValidationReport
from app.events.kinds import stage_notice_payload
from app.pipeline.stages import StageContext
from app.scanners.runner import ToolFailure
from app.scanners.scan import ScanResult


def fingerprints(scan: ScanResult) -> set[tuple[str, str, str]]:
    return {item.fingerprint() for item in scan.violations if item.blocking}


class ValidationRepair:
    def __init__(self, security: SecurityAgent, engine: ValidationService) -> None:
        self.security = security
        self.engine = engine

    async def run(
        self,
        ctx: StageContext,
        variant: Variant,
        package: IaCPackage,
        *,
        rounds: int,
        budget: AgentBudget,
        phase: Literal["generation", "before_security", "after_security"],
        metadata: RemediationReport,
        report: ValidationReport | None = None,
    ) -> tuple[IaCPackage, ValidationReport, RemediationReport]:
        files = dict(package.files)
        report = report or await validate_files(self.engine, ctx.plan, files)
        history = list(metadata.rounds)
        for index in range(1, rounds + 1):
            if report.summary.result != "invalid":
                break
            before = report.summary.failed
            record = RepairRound(
                phase=phase,
                index=index,
                before_failed=before,
                outcome="stopped",
                reason="deadline",
            )
            if budget.remaining() < 1:
                history.append(record)
                break
            failures = [
                {
                    key: getattr(check, key)
                    for key in (
                        "check_id",
                        "message",
                        "file_path",
                        "line_start",
                        "line_end",
                    )
                }
                for check in report.failed_checks_for_remediation
            ]
            targets: dict[str, list[Violation]] = {
                str(check["file_path"]): []
                for check in failures
                if check["file_path"] in files
            }
            if not targets:
                history.append(record.model_copy(update={"reason": "no_targets"}))
                break
            try:
                async with asyncio.timeout(budget.remaining()):
                    baseline = await scan_files(self.security.scanner, files, variant)
                    candidate, proposals, _ = await self.security._fix_pass(
                        ctx,
                        variant,
                        files,
                        targets,
                        budget,
                        feedback=None,
                        validation_failures=failures,
                    )
                    if not proposals or any(not p["accepted"] for p in proposals):
                        record = record.model_copy(
                            update={"outcome": "rejected", "reason": "invalid_patch"}
                        )
                    else:
                        candidate = self.security.safety.value(candidate)
                        checked = await validate_files(self.engine, ctx.plan, candidate)
                        scanned = await scan_files(
                            self.security.scanner, candidate, variant
                        )
                        reason = (
                            "verification_unavailable"
                            if checked.summary.result == "error"
                            else "no_improvement"
                            if checked.summary.failed >= before
                            else "new_blocking_findings"
                            if fingerprints(scanned) - fingerprints(baseline)
                            else "improved"
                        )
                        accepted = reason == "improved"
                        record = record.model_copy(
                            update={
                                "after_failed": checked.summary.failed,
                                "outcome": "accepted" if accepted else "rejected",
                                "reason": reason,
                            }
                        )
                        if accepted:
                            files, report = candidate, checked
            except TimeoutError:
                pass
            except ToolFailure:
                record = record.model_copy(
                    update={"reason": "verification_unavailable", "outcome": "rejected"}
                )
            history.append(record)
            await ctx.writer.event_log.append(
                ctx.run_id,
                AgentName.VALIDATOR,
                PackageStatus.GENERATING
                if phase == "generation"
                else PackageStatus.VALIDATING,
                message="validation repair round",
                payload=stage_notice_payload(
                    variant, "validation repair round", record.model_dump()
                ),
            )
            if record.outcome != "accepted":
                break
        else:
            if report.summary.result == "invalid":
                history.append(
                    RepairRound(
                        phase=phase,
                        index=rounds + 1,
                        before_failed=report.summary.failed,
                        outcome="stopped",
                        reason="round_limit",
                    )
                )
        metadata = metadata.model_copy(update={"rounds": history})
        report = report.model_copy(update={"remediation": metadata})
        return package.model_copy(update={"files": files}), report, metadata
