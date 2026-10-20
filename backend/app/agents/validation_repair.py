"""Bounded validation feedback using the engineer-Retry remediation path."""

import asyncio
import time
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
from app.validation.gate import patch_syntax_failure
from app.validation.measurement import publish_measurement
from app.validation.workspace import current_workspace


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
        if report is None:
            started = time.monotonic()
            try:
                async with asyncio.timeout(max(0.001, budget.remaining())):
                    report = await validate_files(self.engine, ctx.plan, files)
            except TimeoutError:
                report = ValidationReport.build(
                    [], terraform_required=True, abort_reason="deadline"
                )
            await publish_measurement(
                ctx,
                variant,
                "initial_validation",
                time.monotonic() - started,
                phase=phase,
            )
        workspace = current_workspace()
        if (
            workspace is not None
            and phase == "before_security"
            and not workspace.observed
        ):
            workspace.observe(list(report.checks), "generated", files)
        history = list(metadata.rounds)
        if report.abort_reason == "deadline":
            history.append(
                RepairRound(
                    phase=phase,
                    index=1,
                    before_failed=report.summary.failed,
                    outcome="stopped",
                    reason="deadline",
                )
            )
            await publish_measurement(
                ctx,
                variant,
                "validation_repair_round",
                0.0,
                phase=phase,
                iteration=1,
                outcome="stopped",
                reason="deadline",
                attempted=False,
            )
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
                error_classes=sorted(
                    {c.message for c in report.checks if c.status == "failed"}
                ),
            )
            if budget.remaining() < 1:
                history.append(record)
                await publish_measurement(
                    ctx,
                    variant,
                    "validation_repair_round",
                    0.0,
                    phase=phase,
                    iteration=index,
                    outcome="stopped",
                    reason="deadline",
                    attempted=False,
                )
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
            started = time.monotonic()
            record = record.model_copy(update={"attempted": True})
            try:
                async with asyncio.timeout(budget.remaining()):
                    candidate, proposals, _ = await self.security._fix_pass(
                        ctx,
                        variant,
                        files,
                        targets,
                        budget,
                        feedback=None,
                        validation_failures=failures,
                    )
                    record = record.model_copy(
                        update={
                            "fixer_attempts": [
                                a
                                for p in proposals
                                for a in p.get("attempt_details", [])
                            ],
                            "schema_context_chars": sum(
                                int(p.get("schema_context_chars", 0)) for p in proposals
                            ),
                        }
                    )
                    touched = {
                        p
                        for p in files.keys() | candidate.keys()
                        if files.get(p) != candidate.get(p)
                    }
                    if (
                        not proposals
                        or any(not p["accepted"] for p in proposals)
                        or await patch_syntax_failure(files, candidate, touched)
                    ):
                        record = record.model_copy(
                            update={"outcome": "rejected", "reason": "invalid_patch"}
                        )
                    else:
                        candidate = self.security.safety.value(candidate)
                        checked = await validate_files(self.engine, ctx.plan, candidate)
                        reason = (
                            "verification_unavailable"
                            if checked.summary.result == "error"
                            else "no_improvement"
                            if checked.summary.failed >= before
                            else "improved"
                        )
                        if reason == "improved":
                            baseline = await scan_files(
                                self.security.scanner, files, variant
                            )
                            scanned = await scan_files(
                                self.security.scanner, candidate, variant
                            )
                            if fingerprints(scanned) - fingerprints(baseline):
                                reason = "new_blocking_findings"
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
                            if workspace is not None:
                                workspace.observe(
                                    list(checked.checks), "repair", candidate
                                )
            except TimeoutError:
                pass
            except ToolFailure:
                record = record.model_copy(
                    update={"reason": "verification_unavailable", "outcome": "rejected"}
                )
            record = record.model_copy(
                update={"duration_seconds": time.monotonic() - started}
            )
            await publish_measurement(
                ctx,
                variant,
                "validation_repair_round",
                record.duration_seconds,
                phase=phase,
                iteration=index,
                outcome=record.outcome,
                reason=record.reason,
                attempted=record.attempted,
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
        metadata = metadata.model_copy(
            update={
                "rounds": history,
                "measurements": list(workspace.measurements)
                if workspace
                else metadata.measurements,
            }
        )
        report = report.model_copy(update={"remediation": metadata})
        return package.model_copy(update={"files": files}), report, metadata
