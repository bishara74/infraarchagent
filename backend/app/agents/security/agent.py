"""FR-S-01–07/09 scan, fix, rescan, and durable per-session reporting."""

import asyncio
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.budget import AgentBudget
from app.agents.generators.cost import CostGeneratorAgent
from app.agents.generators.performance import PerformanceGeneratorAgent
from app.agents.generators.security import SecurityGeneratorAgent
from app.agents.prompts.security_fix import SECURITY_FIX_PROMPT_VERSION
from app.agents.security.fix import FixAgent, FixProposal
from app.core.config import Settings
from app.core.logging import RedactingFilter
from app.db.repositories.packages import PackageRepository
from app.domain.enums import AgentName, AgentState, PackageStatus, Severity, Variant
from app.domain.models import IaCPackage, Violation
from app.domain.package_layout import package_structure_errors
from app.domain.states import remediation_budget_decision
from app.events.kinds import stage_notice_payload
from app.pipeline.stages import StageContext
from app.scanners.runner import ToolFailure
from app.scanners.scan import Scanner, ScanResult
from app.security.diff import package_diff
from app.security.policy import SECURITY_POLICY_VERSION

DIRECTIVES = {
    Variant.COST: CostGeneratorAgent.optimisation_directive,
    Variant.PERFORMANCE: PerformanceGeneratorAgent.optimisation_directive,
    Variant.SECURITY: SecurityGeneratorAgent.optimisation_directive,
}
MAX_REPORT_DIFF = 20_000


def _finding(item: Violation) -> dict[str, Any]:
    return item.model_dump(mode="json")


def _scan_report(scan: ScanResult) -> dict[str, Any]:
    blocking = [item for item in scan.violations if item.blocking]
    advisory = [item for item in scan.violations if not item.blocking]
    return {
        "blocking": [_finding(item) for item in blocking],
        "advisory_count": len(advisory),
        "advisory_sample": [_finding(item) for item in advisory[:20]],
        "advisory_omitted_count": max(0, len(advisory) - 20),
        "counts_by_severity": dict(
            Counter(item.severity.value for item in scan.violations)
        ),
        "tool_status": scan.tool_status,
        "syntax_limited": scan.syntax_limited,
        "tfsec_other_findings_unavailable": scan.syntax_limited,
    }


def _capped_diff(diff: str) -> tuple[str, int]:
    return diff[:MAX_REPORT_DIFF], max(0, len(diff) - MAX_REPORT_DIFF)


class SecurityAgent:
    def __init__(
        self,
        scanner: Scanner,
        fix_agent: FixAgent,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
        *,
        versions: Mapping[str, str | None] | None = None,
        semaphore: asyncio.Semaphore | None = None,
        fixing_provider: str | None = None,
        fixing_model: str | None = None,
        fixing_reasoning_effort: str | None = None,
    ) -> None:
        self.scanner = scanner
        self.fix_agent = fix_agent
        self.session_factory = session_factory
        self.settings = settings
        self.versions = dict(versions or {})
        self.fixing_provider = fixing_provider
        self.fixing_model = fixing_model
        self.fixing_reasoning_effort = fixing_reasoning_effort
        self.semaphore = semaphore or asyncio.Semaphore(
            settings.security_max_parallel_fixes
        )
        key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else None
        self.redactor = RedactingFilter(key)

    def _redact_report(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.redactor.redact(value)
        if isinstance(value, list):
            return [self._redact_report(item) for item in value]
        if isinstance(value, dict):
            return {key: self._redact_report(item) for key, item in value.items()}
        return value

    async def _notice(
        self,
        ctx: StageContext,
        variant: Variant,
        message: str,
        *,
        status: PackageStatus = PackageStatus.REMEDIATING,
        **metrics: Any,
    ) -> None:
        await ctx.writer.event_log.append(
            ctx.run_id,
            AgentName.SECURITY,
            status,
            message=message,
            payload=stage_notice_payload(variant, message, metrics),
        )

    async def _fix_pass(
        self,
        ctx: StageContext,
        variant: Variant,
        files: dict[str, str],
        targets: Mapping[str, Sequence[Violation]],
        budget: AgentBudget,
        *,
        feedback: str | None,
        validation_failures: Sequence[dict[str, Any]],
    ) -> tuple[dict[str, str], list[dict[str, Any]], str]:
        snapshot = dict(files)

        async def one(path: str) -> FixProposal:
            async with self.semaphore:
                remaining = budget.remaining()
                if remaining < 1:
                    return FixProposal(path, False, "time_budget", None, {}, ())
                linked = [
                    failure
                    for failure in validation_failures
                    if failure.get("file_path") == path
                ]
                return await self.fix_agent.propose(
                    path=path,
                    files=snapshot,
                    findings=targets[path],
                    plan=ctx.plan,
                    directive=DIRECTIVES[variant],
                    remaining=remaining,
                    feedback=feedback,
                    validation_failures=linked,
                )

        proposals = await asyncio.gather(*(one(path) for path in sorted(targets)))
        results: list[dict[str, Any]] = []
        current = dict(snapshot)
        for proposal in proposals:
            accepted = proposal.accepted
            reason = proposal.reason
            if accepted:
                candidate = dict(current)
                assert proposal.content is not None
                candidate[proposal.path] = proposal.content
                if any(path in candidate for path in proposal.new_files):
                    accepted, reason = False, "new_file_conflict"
                else:
                    candidate.update(proposal.new_files)
                    if package_structure_errors(candidate, ctx.plan.file_types):
                        accepted, reason = False, "invalid_merged_structure"
                    else:
                        current = candidate
            results.append(
                {
                    "file": proposal.path,
                    "rule_ids": sorted(
                        {item.rule_id for item in targets[proposal.path]}
                    ),
                    "accepted": accepted,
                    "reason": reason,
                    "summaries": [
                        self.redactor.redact(text) for text in proposal.summaries
                    ],
                    "new_files": sorted(proposal.new_files) if accepted else [],
                    "input_tokens": proposal.input_tokens,
                    "output_tokens": proposal.output_tokens,
                }
            )
        return current, results, package_diff(snapshot, current)

    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.SECURITY,
            AgentState.RUNNING,
            message="security scan started",
            variant=variant,
        )
        await ctx.writer.package_transition(
            ctx.run_id, variant, PackageStatus.SCANNING, message="security scan started"
        )
        return await self._loop(ctx, variant, package, kind="automated")

    async def remediate_from_review(
        self,
        ctx: StageContext,
        variant: Variant,
        package: IaCPackage,
        feedback: str | None,
        validation_failures: Sequence[dict[str, Any]],
    ) -> PackageStatus:
        async with self.session_factory() as session:
            row = await PackageRepository(session).get(ctx.run_id, variant)
            if row is None:
                raise LookupError("package not found")
            prior_report = row.security_report or {}
        sessions = prior_report.get("sessions") or []
        prior_final = sessions[-1].get("final", {}) if sessions else {}
        findings: list[Violation] = []
        for raw in prior_final.get("remaining_blocking", []):
            try:
                findings.append(Violation.model_validate(raw))
            except ValueError:
                continue
        await ctx.writer.package_transition(
            ctx.run_id,
            variant,
            PackageStatus.REMEDIATING,
            message="review remediation retry started",
        )
        async with self.session_factory() as session:
            async with session.begin():
                await PackageRepository(session).reset_iteration_count(
                    ctx.run_id, variant
                )
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.SECURITY,
            AgentState.RUNNING,
            message="review remediation retry started",
            variant=variant,
        )
        return await self._loop(
            ctx,
            variant,
            package,
            kind="review_retry",
            feedback=feedback,
            validation_failures=validation_failures,
            initial_findings=findings,
        )

    async def _loop(
        self,
        ctx: StageContext,
        variant: Variant,
        package: IaCPackage,
        *,
        kind: str,
        feedback: str | None = None,
        validation_failures: Sequence[dict[str, Any]] = (),
        initial_findings: Sequence[Violation] = (),
    ) -> PackageStatus:
        files = dict(package.files)
        session_start_files = dict(files)
        started_at = datetime.now(UTC).isoformat()
        budget = AgentBudget(self.settings.security_deadline_seconds, clock=ctx.clock)
        iterations: list[dict[str, Any]] = []
        seen: set[frozenset[tuple[str, str, str]]] = set()
        iteration_count = 0
        first_counts: dict[str, int] | None = None
        last_blocking: list[Violation] = []
        outcome = "error"
        reason: str | None = None
        status = PackageStatus.SCAN_ERROR

        if kind == "review_retry":
            targets: dict[str, list[Violation]] = defaultdict(list)
            for item in initial_findings:
                if item.blocking and item.file_path in files:
                    targets[item.file_path].append(item)
            for failure in validation_failures:
                path = failure.get("file_path")
                if isinstance(path, str) and path in files:
                    targets.setdefault(path, [])
            if targets and budget.remaining() >= 1:
                files, fixes, diff = await self._fix_pass(
                    ctx,
                    variant,
                    files,
                    targets,
                    budget,
                    feedback=feedback,
                    validation_failures=validation_failures,
                )
                iteration_count = 1
                capped, omitted = _capped_diff(diff)
                iterations.append(
                    {
                        "index": 0,
                        "scan": {"blocking": [_finding(v) for v in initial_findings]},
                        "fixes": fixes,
                        "diff": capped,
                        "diff_omitted_chars": omitted,
                    }
                )
                await self._notice(
                    ctx,
                    variant,
                    "review fix pass completed",
                    iteration=0,
                    blocking_by_severity=dict(
                        Counter(v.severity.value for v in initial_findings)
                    ),
                    advisory_count=0,
                    fixes_accepted=sum(bool(f["accepted"]) for f in fixes),
                    fixes_rejected=sum(not f["accepted"] for f in fixes),
                )
            elif feedback is not None and not targets:
                message = "no file could be targeted; feedback was not applied"
                iterations.append(
                    {"index": 0, "notice": message, "fixes": [], "diff": ""}
                )
                await self._notice(ctx, variant, message)
            await ctx.writer.package_transition(
                ctx.run_id,
                variant,
                PackageStatus.SCANNING,
                message="review retry scanning",
            )

        while True:
            try:
                scan = await self.scanner.scan(files, variant)
            except ToolFailure as error:
                reason = (
                    f"{error.tool} is not installed"
                    if error.category == "not_installed"
                    else f"{error.tool} scan {error.category}"
                )
                status = PackageStatus.SCAN_ERROR
                await ctx.writer.package_transition(
                    ctx.run_id, variant, status, message=reason, error=reason
                )
                break
            if first_counts is None:
                first_counts = {
                    tool: sum(
                        item.tool == tool
                        and item.severity in {Severity.HIGH, Severity.CRITICAL}
                        for item in scan.violations
                    )
                    for tool in ("checkov", "tfsec")
                }
            blocking = [item for item in scan.violations if item.blocking]
            last_blocking = blocking
            entry: dict[str, Any] = {
                "index": iteration_count,
                "scan": _scan_report(scan),
                "fixes": [],
                "diff": "",
                "diff_omitted_chars": 0,
            }
            iterations.append(entry)
            if not blocking:
                outcome, status = "clean", PackageStatus.SCAN_CLEAN
                await self._notice(
                    ctx,
                    variant,
                    "security scan complete",
                    status=PackageStatus.SCANNING,
                    iteration=iteration_count,
                    blocking_by_severity={},
                    advisory_count=entry["scan"]["advisory_count"],
                    fixes_accepted=0,
                    fixes_rejected=0,
                )
                await ctx.writer.package_transition(
                    ctx.run_id, variant, status, message="no blocking security findings"
                )
                break
            await ctx.writer.package_transition(
                ctx.run_id,
                variant,
                PackageStatus.REMEDIATING,
                message="blocking security findings found",
            )
            decision = remediation_budget_decision(iteration_count, ctx.max_iterations)
            fingerprints = frozenset(item.fingerprint() for item in blocking)
            if not decision.apply_fix:
                reason = "iteration limit"
            elif fingerprints in seen:
                reason = "no progress"
            elif budget.remaining() < 1:
                reason = "time budget"
            if reason is not None:
                outcome, status = "exhausted", PackageStatus.SCAN_EXHAUSTED
                await self._notice(
                    ctx,
                    variant,
                    "security remediation exhausted",
                    iteration=iteration_count,
                    blocking_by_severity=dict(
                        Counter(v.severity.value for v in blocking)
                    ),
                    advisory_count=entry["scan"]["advisory_count"],
                    fixes_accepted=0,
                    fixes_rejected=0,
                )
                await ctx.writer.package_transition(
                    ctx.run_id, variant, status, message=reason
                )
                break
            seen.add(fingerprints)
            targets = defaultdict(list)
            for item in blocking:
                targets[item.file_path].append(item)
            files, fixes, diff = await self._fix_pass(
                ctx,
                variant,
                files,
                targets,
                budget,
                feedback=feedback,
                validation_failures=validation_failures,
            )
            entry["fixes"] = fixes
            entry["diff"], entry["diff_omitted_chars"] = _capped_diff(diff)
            iteration_count = decision.next_iteration_count
            await self._notice(
                ctx,
                variant,
                "security fix pass completed",
                iteration=iteration_count,
                blocking_by_severity=dict(Counter(v.severity.value for v in blocking)),
                advisory_count=entry["scan"]["advisory_count"],
                fixes_accepted=sum(bool(f["accepted"]) for f in fixes),
                fixes_rejected=sum(not f["accepted"] for f in fixes),
            )
            await ctx.writer.package_transition(
                ctx.run_id,
                variant,
                PackageStatus.SCANNING,
                message="security rescan started",
            )

        checkov_count = first_counts["checkov"] if first_counts is not None else None
        tfsec_count = first_counts["tfsec"] if first_counts is not None else None
        session_report = {
            "kind": kind,
            "started_at": started_at,
            "feedback_present": bool(feedback),
            "fixing_provider": self.fixing_provider,
            "fixing_model": self.fixing_model,
            "fixing_reasoning_effort": self.fixing_reasoning_effort,
            "fix_passes": iteration_count,
            "iterations": iterations,
            "final": {
                "outcome": outcome,
                "reason": reason,
                "remaining_blocking": [_finding(item) for item in last_blocking],
                "first_scan_checkov_high_or_critical": checkov_count,
                "first_scan_tfsec_high_or_critical": tfsec_count,
                "first_scan_combined_high_or_critical": (
                    checkov_count + tfsec_count
                    if checkov_count is not None and tfsec_count is not None
                    else None
                ),
            },
        }
        session_report["diff"], session_report["diff_omitted_chars"] = _capped_diff(
            package_diff(session_start_files, files)
        )
        async with self.session_factory() as session:
            async with session.begin():
                await PackageRepository(session).save_security_results(
                    ctx.run_id,
                    variant,
                    original_files=session_start_files,
                    files=files,
                    session_report=self._redact_report(session_report),
                    iteration_count=iteration_count,
                    policy_version=SECURITY_POLICY_VERSION,
                    prompt_version=SECURITY_FIX_PROMPT_VERSION,
                    tools=self.versions,
                )
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.SECURITY,
            AgentState.FAILED
            if status == PackageStatus.SCAN_ERROR
            else AgentState.COMPLETED,
            previous=AgentState.RUNNING,
            message=reason or f"security {outcome}",
            variant=variant,
        )
        return status
