"""FR-S-01–07/09 scan, fix, rescan, and durable per-session reporting."""

import asyncio
import time
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
from app.agents.remediation import apply_proposals, scan_files
from app.agents.security.feedback import attempt_feedback
from app.agents.security.fix import FixAgent, FixProposal, editable_paths
from app.agents.security.verification import (
    TerraformVerifier,
    failure_count,
    terraform_files,
)
from app.core.config import Settings
from app.core.logging import RedactingFilter
from app.core.safety import PublicDataSafety
from app.db.repositories.packages import PackageRepository
from app.domain.enums import AgentName, AgentState, PackageStatus, Severity, Variant
from app.domain.models import IaCPackage, Violation
from app.domain.review import retry_targets, security_final
from app.domain.states import remediation_budget_decision
from app.domain.validation import ValidationCheck
from app.events.kinds import stage_notice_payload
from app.llm.errors import SAFE_MESSAGES
from app.pipeline.stages import StageContext
from app.scanners.runner import ToolFailure
from app.scanners.scan import Scanner, ScanResult
from app.security.acceptance import CandidateGuard
from app.security.catalogue import autofix
from app.security.diff import package_diff
from app.security.focus import RANK, focused_findings
from app.security.partial import RetainedCandidate, accept_groups, retained_metrics
from app.security.policy import SECURITY_POLICY_VERSION
from app.security.templates import build_template
from app.security.templates import requests as template_requests
from app.validation.idioms import repair_idioms
from app.validation.measurement import initialization_metrics, publish_measurement
from app.validation.workspace import ValidationWorkspace, current_workspace

DIRECTIVES = {
    Variant.COST: CostGeneratorAgent.optimisation_directive,
    Variant.PERFORMANCE: PerformanceGeneratorAgent.optimisation_directive,
    Variant.SECURITY: SecurityGeneratorAgent.optimisation_directive,
}
MAX_REPORT_DIFF = 20_000


class ReviewRetryScanError(RuntimeError):
    """Safe review-specific failure after persisting the retry session."""


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
        "terraform_findings_may_be_incomplete": scan.syntax_limited,
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
        terraform_verifier: TerraformVerifier | None = None,
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
        self.redactor = RedactingFilter(
            key, settings.api_key.get_secret_value() if settings.api_key else ""
        )
        self.safety = PublicDataSafety(settings)
        self.terraform_verifier = terraform_verifier or TerraformVerifier()

    def _redact_report(self, value: Any) -> Any:
        return self.safety.value(value)

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
        review_target_order: bool = False,
        previous_attempt: str = "",
        iteration_index: int = 0,
    ) -> tuple[dict[str, str], list[dict[str, Any]], str]:
        snapshot = dict(files)
        selected = {
            path: focused_findings(
                entries,
                self.settings.security_fix_max_resources,
                self.settings.security_fix_max_findings,
                iteration_index,
            )
            for path, entries in targets.items()
            if path in files
        }
        current = dict(files)
        results: list[dict[str, Any]] = []
        all_proposals: list[FixProposal] = []

        async def one(path: str, source: dict[str, str]) -> FixProposal:
            async with self.semaphore:
                remaining = budget.remaining()
                if remaining < 1:
                    return FixProposal(
                        path,
                        False,
                        "time_budget",
                        None,
                        {},
                        (),
                        schema_context_reason="not_attempted",
                    )
                linked = [f for f in validation_failures if f.get("file_path") == path]
                return await self.fix_agent.propose(
                    path=path,
                    files=source,
                    findings=selected[path],
                    plan=ctx.plan,
                    directive=DIRECTIVES[variant],
                    remaining=remaining,
                    feedback=feedback,
                    validation_failures=linked,
                    previous_attempt=previous_attempt,
                )

        paths = (
            list(selected)
            if review_target_order
            else sorted(
                selected,
                key=lambda p: (
                    min((RANK[f.severity.value] for f in selected[p]), default=4),
                    p,
                ),
            )
        )
        # Calls sharing editable context run sequentially with refreshed content.
        # Independent files still share the existing bounded semaphore.
        waves: list[list[str]] = []
        for path in paths:
            scope = editable_paths(files, path)
            for wave in waves:
                if all(not scope.intersection(editable_paths(files, p)) for p in wave):
                    wave.append(path)
                    break
            else:
                waves.append([path])
        for wave in waves:
            source = dict(current)
            proposals = await asyncio.gather(*(one(path, source) for path in wave))
            all_proposals.extend(proposals)
            current, records = apply_proposals(
                source, proposals, selected, ctx.plan, self.redactor
            )
            for record in records:
                sent = selected[record["file"]]
                attempted = record.get("schema_context_reason") != "not_attempted"
                sent_count = len(sent) if attempted else 0
                record.update(
                    call_attempted=attempted,
                    findings_sent=sent_count,
                    resources_sent=len({f.resource for f in sent}) if attempted else 0,
                    findings_deferred=len(targets[record["file"]]) - sent_count,
                )
            results.extend(records)
        for reason in sorted(
            {
                proposal.reason
                for proposal in all_proposals
                if isinstance(proposal.reason, str)
                and proposal.reason in SAFE_MESSAGES.values()
            }
        ):
            assert reason is not None
            await self._notice(ctx, variant, reason)
        return (
            current,
            sorted(results, key=lambda r: r["file"]),
            package_diff(snapshot, current),
        )

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

    async def confirm_final(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        """Readiness verification only: no extra fix passes or counter reset."""
        started = time.monotonic()
        try:
            scan = await scan_files(self.scanner, package.files, variant)
        finally:
            await publish_measurement(
                ctx, variant, "final_security_scan", time.monotonic() - started
            )
        blocking = [item for item in scan.violations if item.blocking]
        async with self.session_factory() as session:
            async with session.begin():
                repository = PackageRepository(session)
                row = await repository.get_for_update(ctx.run_id, variant)
                if row is None:
                    raise LookupError("package not found")
                final = dict(security_final(row.security_report))
                final.update(
                    outcome="exhausted" if blocking else "clean",
                    reason="final verification" if blocking else None,
                    remaining_blocking=[_finding(item) for item in blocking],
                )
                report = dict(row.security_report or {})
                report["final"] = self._redact_report(final)
                report["final_verification"] = self._redact_report(_scan_report(scan))
                row.security_report = report
        return PackageStatus.SCAN_EXHAUSTED if blocking else PackageStatus.SCAN_CLEAN

    async def remediate_from_review(
        self,
        ctx: StageContext,
        variant: Variant,
        package: IaCPackage,
        feedback: str | None,
        validation_failures: Sequence[dict[str, Any]],
        *,
        target_files: Sequence[str] = (),
        start_committed: bool = False,
    ) -> PackageStatus:
        async with self.session_factory() as session:
            row = await PackageRepository(session).get(ctx.run_id, variant)
            if row is None:
                raise LookupError("package not found")
            prior_report = row.security_report or {}
        prior_final = security_final(prior_report)
        findings: list[Violation] = []
        for raw in prior_final.get("remaining_blocking", []):
            try:
                findings.append(Violation.model_validate(raw))
            except ValueError:
                continue
        if not start_committed:
            async with self.session_factory() as session:
                async with session.begin():
                    previous = await ctx.writer.review_action(
                        session, ctx.run_id, variant, "retry", feedback
                    )
            await ctx.writer.review_event(
                ctx.run_id,
                variant,
                PackageStatus.REMEDIATING,
                previous,
                action="retry",
                reasons=[],
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
            target_files=target_files,
        )

    async def _loop(
        self,
        ctx: StageContext,
        variant: Variant,
        package: IaCPackage,
        **kwargs: Any,
    ) -> PackageStatus:
        if current_workspace() is not None:
            return await self._loop_inside(ctx, variant, package, **kwargs)
        workspace = ValidationWorkspace()
        try:
            with workspace.activate():
                return await self._loop_inside(ctx, variant, package, **kwargs)
        finally:
            workspace.close()

    async def _fix_iteration(
        self,
        ctx: StageContext,
        variant: Variant,
        files: dict[str, str],
        targets: Mapping[str, Sequence[Violation]],
        budget: AgentBudget,
        baseline_scan: ScanResult,
        verification: dict[str, Any],
        *,
        feedback: str | None,
        validation_failures: Sequence[dict[str, Any]],
        review_target_order: bool = False,
        previous_attempt: str = "",
        checkpoint: RetainedCandidate | None = None,
        iteration_index: int = 0,
    ) -> tuple[dict[str, str], list[dict[str, Any]], str, ScanResult]:
        iteration_original = dict(files)
        checkpoint = checkpoint or RetainedCandidate(dict(files), baseline_scan)
        if budget.remaining() < 0.001:
            raise TimeoutError
        verification.update(
            fix_started=False,
            candidate_created=False,
            reasons=[],
            terraform_verification_seconds=0.0,
            security_verification_seconds=0.0,
        )

        async def checked(source: dict[str, str]) -> list[ValidationCheck]:
            started = time.monotonic()
            try:
                return await self.terraform_verifier.checks(source)
            finally:
                verification["terraform_verification_seconds"] += (
                    time.monotonic() - started
                )

        before = await checked(files)
        verification["before_failed"] = failure_count(before)
        if budget.expired():
            raise TimeoutError
        automatic, records = autofix(files, list(baseline_scan.violations))
        verification["catalogue"] = records
        if automatic != files:
            verification.update(fix_started=True, candidate_created=True)
            guard = CandidateGuard(
                self.terraform_verifier, self.scanner, variant, budget, verification
            )
            result = await guard.evaluate(files, automatic, before, baseline_scan)
            for record in records:
                if record["status"] == "proposed":
                    record.update(
                        status="rejected" if result.reason else "retained",
                        reason=result.reason or "secure_default",
                    )
            if not result.reason:
                files, before, baseline_scan = automatic, result.checks, result.scan
                checkpoint.files, checkpoint.scan = dict(files), baseline_scan
                targets = {
                    path: [
                        v
                        for v in baseline_scan.violations
                        if v.blocking and v.file_path == path
                    ]
                    for path in sorted(
                        {v.file_path for v in baseline_scan.violations if v.blocking}
                    )
                }
                if not targets:
                    verification.update(
                        outcome="accepted",
                        deadline_only=False,
                        after_failed=failure_count(before),
                    )
                    return (
                        files,
                        [],
                        package_diff(iteration_original, files),
                        baseline_scan,
                    )
        verification["templates"] = []
        for module, kind in template_requests(files, list(baseline_scan.violations)):
            automatic, record = build_template(
                files, list(baseline_scan.violations), module, kind
            )
            verification["templates"].append(record)
            if automatic == files:
                continue
            verification.update(fix_started=True, candidate_created=True)
            guard = CandidateGuard(
                self.terraform_verifier, self.scanner, variant, budget, verification
            )
            result = await guard.evaluate(files, automatic, before, baseline_scan)
            record.update(
                status="rejected" if result.reason else "retained",
                reason=result.reason or "supporting_resources",
                introduced_findings=result.introduced,
            )
            if not result.reason:
                files, before, baseline_scan = automatic, result.checks, result.scan
                checkpoint.files, checkpoint.scan = dict(files), baseline_scan
                targets = {
                    path: [
                        v
                        for v in baseline_scan.violations
                        if v.blocking and v.file_path == path
                    ]
                    for path in sorted(
                        {v.file_path for v in baseline_scan.violations if v.blocking}
                    )
                }
        if files != iteration_original and not targets:
            verification.update(
                outcome="accepted",
                deadline_only=False,
                after_failed=failure_count(before),
            )
            return files, [], package_diff(iteration_original, files), baseline_scan
        verification["fix_started"] = True
        verification["candidate_created"] = False
        candidate, fixes, _ = await self._fix_pass(
            ctx,
            variant,
            files,
            targets,
            budget,
            feedback=feedback,
            validation_failures=validation_failures,
            review_target_order=review_target_order,
            previous_attempt=previous_attempt,
            iteration_index=iteration_index,
        )
        checkpoint.fixes = fixes
        retained_metrics(fixes, files, files)
        started = time.monotonic()
        candidate, records = repair_idioms(candidate)
        verification.update(
            candidate_created=candidate != files,
            deterministic_repairs=records,
            deterministic_seconds=time.monotonic() - started,
        )
        guard = CandidateGuard(
            self.terraform_verifier, self.scanner, variant, budget, verification
        )
        guard.check_cache[ValidationWorkspace.fingerprint(terraform_files(files))] = (
            before
        )
        result = await guard.evaluate(
            files, candidate, before, baseline_scan, force_scan=review_target_order
        )
        verification["after_failed"] = failure_count(result.checks)
        verification["error_classes"] = sorted(
            {c.message for c in result.checks if c.status == "failed"}
        )
        verification["partial_groups"] = []
        if result.reason:
            verification["reasons"].append(result.reason)
            verification["introduced_findings"] = result.introduced
            verification["rolled_back_files"] = sorted(
                p
                for p in files.keys() | candidate.keys()
                if files.get(p) != candidate.get(p)
            )
            candidate, after, scanned = await accept_groups(
                guard,
                files,
                candidate,
                before,
                baseline_scan,
                self.settings.security_partial_max_groups,
                verification["partial_groups"],
                checkpoint,
            )
        else:
            after, scanned = result.checks, result.scan
            checkpoint.files, checkpoint.scan = dict(candidate), scanned
        verification["retained_failed"] = failure_count(after)
        verification["outcome"] = (
            "rolled_back"
            if verification["reasons"]
            else "accepted"
            if candidate != iteration_original
            else "no_change"
        )
        verification["deadline_only"] = False
        verification["verification_seconds"] = (
            verification["terraform_verification_seconds"]
            + verification["security_verification_seconds"]
        )
        retained_metrics(fixes, files, candidate)
        workspace = current_workspace()
        if workspace:
            workspace.observe(after, "security_fix", candidate, partial=True)
            async with workspace.check(candidate):
                pass
        return candidate, fixes, package_diff(iteration_original, candidate), scanned

    async def _publish_iteration(
        self,
        ctx: StageContext,
        variant: Variant,
        record: dict[str, Any],
        iteration: int,
        metrics_start: int,
    ) -> None:
        workspace = current_workspace()
        for change in record.get("catalogue", []):
            await self._notice(
                ctx,
                variant,
                "deterministic security control evaluated",
                rule_ids=change["rule_ids"],
                resource=change["resource"],
                control=change["control"],
                outcome=change["status"],
                reason=change.get("reason"),
            )
        for template in record.get("templates", []):
            await self._notice(
                ctx,
                variant,
                "supporting security template evaluated",
                template=template["template"],
                outcome=template["status"],
                reason=template.get("reason"),
                introduced_findings=template.get("introduced_findings", []),
            )
        record["verification_seconds"] = record.get(
            "terraform_verification_seconds", 0.0
        ) + record.get("security_verification_seconds", 0.0)
        record.update(
            initialization_metrics(
                workspace.terraform_metrics[metrics_start:] if workspace else []
            )
        )
        if "deterministic_seconds" in record:
            await publish_measurement(
                ctx,
                variant,
                "deterministic_repairs",
                record["deterministic_seconds"],
                phase="security",
                iteration=iteration,
                count=len(record.get("deterministic_repairs", [])),
            )
        selected = {
            key: record[key]
            for key in (
                "before_failed",
                "after_failed",
                "init_runs",
                "init_reused",
                "reinitializations",
                "init_seconds",
                "validate_seconds",
                "deadline_only",
                "candidate_created",
                "fix_started",
                "outcome",
                "reasons",
                "terraform_verification_seconds",
                "security_verification_seconds",
            )
            if key in record
        }
        await publish_measurement(
            ctx,
            variant,
            "security_iteration_verification",
            record.get("verification_seconds", 0.0),
            phase="security",
            iteration=iteration,
            **selected,
        )

    async def _loop_inside(
        self,
        ctx: StageContext,
        variant: Variant,
        package: IaCPackage,
        *,
        kind: str,
        feedback: str | None = None,
        validation_failures: Sequence[dict[str, Any]] = (),
        initial_findings: Sequence[Violation] = (),
        target_files: Sequence[str] = (),
    ) -> PackageStatus:
        files = dict(package.files)
        session_start_files = dict(files)
        started_at = datetime.now(UTC).isoformat()
        budget = AgentBudget(self.settings.security_deadline_seconds, clock=ctx.clock)
        iterations: list[dict[str, Any]] = []
        previous_attempt = ""
        iteration_count = 0
        first_counts: dict[str, int] | None = None
        last_blocking: list[Violation] = list(initial_findings)
        outcome = "error"
        reason: str | None = None
        status = PackageStatus.SCAN_ERROR
        pending_scan: ScanResult | None = None
        pending_error: ToolFailure | None = None

        if kind == "review_retry":
            paths = retry_targets(
                files,
                {
                    "final": {
                        "remaining_blocking": [
                            _finding(item) for item in initial_findings
                        ]
                    }
                },
                {"failed_checks_for_remediation": list(validation_failures)},
                target_files,
            )
            targets: dict[str, list[Violation]] = {
                path: [
                    item
                    for item in initial_findings
                    if item.blocking and item.file_path == path
                ]
                for path in paths
            }
            if targets and budget.remaining() >= 1:
                verification: dict[str, Any] = {}
                iteration_source = dict(files)
                checkpoint = RetainedCandidate(
                    dict(files),
                    ScanResult(
                        list(initial_findings),
                        {"checkov": "ok", "trivy": "ok", "terraform": "ok"},
                    ),
                )
                iteration_budget = AgentBudget(
                    max(0.001, min(60.0, budget.remaining())), clock=ctx.clock
                )
                workspace = current_workspace()
                metrics_start = len(workspace.terraform_metrics) if workspace else 0
                try:
                    async with asyncio.timeout(iteration_budget.remaining()):
                        files, fixes, diff, pending_scan = await self._fix_iteration(
                            ctx,
                            variant,
                            files,
                            targets,
                            iteration_budget,
                            ScanResult(
                                list(initial_findings),
                                {"checkov": "ok", "trivy": "ok", "terraform": "ok"},
                            ),
                            verification,
                            feedback=feedback,
                            validation_failures=validation_failures,
                            review_target_order=True,
                            checkpoint=checkpoint,
                        )
                except ToolFailure as error:
                    files = dict(checkpoint.files)
                    pending_error = error
                    verification.setdefault("reasons", []).append(
                        "verification_unavailable"
                    )
                    verification.update(outcome="rolled_back", deadline_only=False)
                    fixes, diff = (
                        checkpoint.fixes,
                        package_diff(iteration_source, files),
                    )
                    if workspace:
                        async with workspace.check(files):
                            pass
                except TimeoutError:
                    files = dict(checkpoint.files)
                    verification["deadline_only"] = bool(
                        verification.get("candidate_created")
                        and not verification.get("reasons")
                    )
                    verification.setdefault("reasons", []).append("iteration_deadline")
                    verification["outcome"] = (
                        "rolled_back"
                        if verification.get("candidate_created")
                        else "stopped"
                    )
                    verification["verification_seconds"] = verification.get(
                        "terraform_verification_seconds", 0.0
                    ) + verification.get("security_verification_seconds", 0.0)
                    fixes, diff = (
                        checkpoint.fixes,
                        package_diff(iteration_source, files),
                    )
                    pending_scan = checkpoint.scan
                    if workspace:
                        async with workspace.check(files):
                            pass
                iteration_count = int(bool(verification.get("fix_started")))
                previous_attempt = attempt_feedback(verification, fixes, self.redactor)
                await self._publish_iteration(
                    ctx, variant, verification, iteration_count, metrics_start
                )
                capped, omitted = _capped_diff(diff)
                iterations.append(
                    {
                        "index": 0,
                        "scan": {"blocking": [_finding(v) for v in initial_findings]},
                        "fixes": fixes,
                        "diff": capped,
                        "diff_omitted_chars": omitted,
                        "verification": verification,
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
            iteration_budget = AgentBudget(
                max(0.001, min(60.0, budget.remaining())), clock=ctx.clock
            )
            try:
                async with asyncio.timeout(iteration_budget.remaining()):
                    if pending_error is not None:
                        raise pending_error
                    if pending_scan is None and budget.remaining() < 1:
                        raise TimeoutError
                    scan = pending_scan or await scan_files(
                        self.scanner, files, variant, iteration=iteration_count
                    )
                    pending_scan = None
            except (ToolFailure, TimeoutError) as error:
                reason = (
                    "security iteration deadline"
                    if isinstance(error, TimeoutError)
                    else f"{error.tool} is not installed"
                    if error.category == "not_installed"
                    else f"{error.tool} scan {error.category}"
                )
                status = PackageStatus.SCAN_ERROR
                if kind != "review_retry":
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
                    for tool in ("checkov", "trivy", "terraform")
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
            if not decision.apply_fix:
                reason = "iteration limit"
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
            targets = defaultdict(list)
            for item in blocking:
                targets[item.file_path].append(item)
            iteration_source = dict(files)
            checkpoint = RetainedCandidate(dict(files), scan)
            try:
                entry["verification"] = {}
                workspace = current_workspace()
                metrics_start = len(workspace.terraform_metrics) if workspace else 0
                async with asyncio.timeout(iteration_budget.remaining()):
                    files, fixes, diff, pending_scan = await self._fix_iteration(
                        ctx,
                        variant,
                        files,
                        targets,
                        iteration_budget,
                        scan,
                        entry["verification"],
                        feedback=feedback,
                        validation_failures=validation_failures,
                        previous_attempt=previous_attempt,
                        checkpoint=checkpoint,
                        iteration_index=iteration_count,
                    )
            except ToolFailure as error:
                files = dict(checkpoint.files)
                entry["fixes"] = checkpoint.fixes
                entry["diff"], entry["diff_omitted_chars"] = _capped_diff(
                    package_diff(iteration_source, files)
                )
                last_blocking = [v for v in checkpoint.scan.violations if v.blocking]
                reason = f"{error.tool} scan {error.category}"
                outcome, status = "error", PackageStatus.SCAN_ERROR
                verification = entry["verification"]
                verification.setdefault("reasons", []).append(
                    "verification_unavailable"
                )
                verification.update(outcome="rolled_back", deadline_only=False)
                if verification.get("fix_started"):
                    iteration_count = decision.next_iteration_count
                if workspace:
                    async with workspace.check(files):
                        pass
                await self._publish_iteration(
                    ctx, variant, verification, iteration_count, metrics_start
                )
                if kind != "review_retry":
                    await ctx.writer.package_transition(
                        ctx.run_id,
                        variant,
                        PackageStatus.SCANNING,
                        message="security verification failed",
                    )
                    await ctx.writer.package_transition(
                        ctx.run_id, variant, status, message=reason, error=reason
                    )
                break
            except TimeoutError:
                files = dict(checkpoint.files)
                entry["fixes"] = checkpoint.fixes
                entry["diff"], entry["diff_omitted_chars"] = _capped_diff(
                    package_diff(iteration_source, files)
                )
                last_blocking = [v for v in checkpoint.scan.violations if v.blocking]
                entry["stop_reason"] = "iteration_deadline"
                verification = entry.get("verification", {})
                reasons = verification.setdefault("reasons", [])
                verification["deadline_only"] = bool(
                    verification.get("candidate_created") and not reasons
                )
                reasons.append("iteration_deadline")
                verification["verification_seconds"] = verification.get(
                    "terraform_verification_seconds", 0.0
                ) + verification.get("security_verification_seconds", 0.0)
                workspace = current_workspace()
                if workspace:
                    async with workspace.check(files):
                        pass
                verification["outcome"] = (
                    "rolled_back"
                    if verification.get("candidate_created")
                    else "stopped"
                )
                if verification.get("fix_started"):
                    iteration_count = decision.next_iteration_count
                await self._publish_iteration(
                    ctx, variant, verification, iteration_count, metrics_start
                )
                previous_attempt = attempt_feedback(verification, [], self.redactor)
                if budget.remaining() >= 1 and iteration_count < ctx.max_iterations:
                    pending_scan = checkpoint.scan
                    await ctx.writer.package_transition(
                        ctx.run_id,
                        variant,
                        PackageStatus.SCANNING,
                        message="security iteration rolled back; retrying",
                    )
                    continue
                reason = (
                    "iteration limit"
                    if iteration_count >= ctx.max_iterations
                    else "time budget"
                )
                outcome, status = "exhausted", PackageStatus.SCAN_EXHAUSTED
                await ctx.writer.package_transition(
                    ctx.run_id, variant, status, message=reason
                )
                break
            previous_attempt = attempt_feedback(
                entry["verification"], fixes, self.redactor
            )
            entry["fixes"] = fixes
            await self._publish_iteration(
                ctx,
                variant,
                entry["verification"],
                decision.next_iteration_count,
                metrics_start,
            )
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
        trivy_count = first_counts["trivy"] if first_counts is not None else None
        terraform_count = (
            first_counts["terraform"] if first_counts is not None else None
        )
        session_report = {
            "kind": kind,
            "started_at": started_at,
            "feedback_present": bool(feedback),
            "fixing_provider": self.fixing_provider,
            "fixing_model": self.fixing_model,
            "fixing_reasoning_effort": self.fixing_reasoning_effort,
            "fix_attempt_timeout_seconds": getattr(
                self.fix_agent,
                "attempt_timeout",
                self.settings.fix_attempt_timeout_seconds,
            ),
            "iteration_timeout_seconds": 60.0,
            "security_stage_timeout_seconds": self.settings.security_deadline_seconds,
            "fix_max_resources": self.settings.security_fix_max_resources,
            "fix_max_findings": self.settings.security_fix_max_findings,
            "partial_max_groups": self.settings.security_partial_max_groups,
            "fix_passes": iteration_count,
            "iterations": iterations,
            "final": {
                "outcome": outcome,
                "reason": reason,
                "remaining_blocking": [_finding(item) for item in last_blocking],
                "first_scan_checkov_high_or_critical": checkov_count,
                "first_scan_trivy_high_or_critical": trivy_count,
                "first_scan_terraform_high_or_critical": terraform_count,
                "first_scan_combined_high_or_critical": (
                    sum(first_counts.values()) if first_counts is not None else None
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
                    original_files=self.safety.value(session_start_files),
                    files=self.safety.value(files),
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
        if kind == "review_retry" and status == PackageStatus.SCAN_ERROR:
            raise ReviewRetryScanError(reason or "security scan could not complete")
        return status
