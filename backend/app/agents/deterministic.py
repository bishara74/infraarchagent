"""D-56: documented validation repairs use the existing candidate guard."""

import asyncio
from typing import Any

from app.agents.budget import AgentBudget
from app.agents.remediation import ValidationService
from app.agents.security.agent import SecurityAgent
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationReport
from app.scanners.runner import ToolFailure
from app.security.acceptance import CandidateGuard
from app.validation.equivalents import repair_equivalents


async def checked_repairs(
    files: dict[str, str],
    plan: DeploymentPlan,
    variant: Variant,
    report: ValidationReport,
    engine: ValidationService,
    security: SecurityAgent,
    budget: AgentBudget,
) -> tuple[dict[str, str], ValidationReport, list[dict[str, Any]]]:
    candidate, records = repair_equivalents(files)
    if candidate == files or budget.remaining() < 1:
        return files, report, []
    reason = "verification_unavailable"
    checked = report
    try:
        async with asyncio.timeout(budget.remaining()):
            before = await security.terraform_verifier.checks(files)
            baseline = await security.scanner.scan(files, variant)
            guard = CandidateGuard(
                security.terraform_verifier,
                security.scanner,
                variant,
                budget,
                {
                    "terraform_verification_seconds": 0.0,
                    "security_verification_seconds": 0.0,
                },
            )
            result = await guard.evaluate(files, candidate, before, baseline)
            reason = result.reason or "improved"
            if reason == "improved":
                checked = await engine.validate(plan, candidate)
                if checked.summary.result == "error":
                    reason = "verification_unavailable"
                elif checked.summary.failed >= report.summary.failed:
                    reason = "no_improvement"
    except (TimeoutError, ToolFailure):
        reason = "verification_unavailable"
    retained = reason == "improved"
    for record in records:
        record.update(outcome="accepted" if retained else "rejected", reason=reason)
    return (candidate, checked, records) if retained else (files, report, records)
