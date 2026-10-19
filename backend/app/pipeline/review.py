"""Locked review acceptance and guarded, runner-owned remediation retries."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.agents.security.agent import ReviewRetryScanError
from app.api.schemas import RetryResponse, ReviewRequest, ReviewResponse
from app.core.safety import PublicDataSafety
from app.db.repositories.packages import PackageRepository
from app.db.repositories.results import ResultsRepository
from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.domain.models import IaCPackage
from app.domain.paths import validate_relative_path
from app.domain.plan import DeploymentPlan
from app.domain.review import TERMINAL_RUNS, package_presentation, retry_targets
from app.domain.run_config import RunConfig
from app.domain.states import readiness_after_validation
from app.pipeline.stages import StageContext
from app.validation.workspace import ValidationWorkspace

if TYPE_CHECKING:
    from app.pipeline.runner import PipelineRunner

logger = logging.getLogger(__name__)


class ReviewError(ValueError):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


class ReviewService:
    def __init__(self, runner: "PipelineRunner") -> None:
        self.runner = runner
        self.writer = runner.writer
        self.safety = PublicDataSafety(runner.factory.settings)

    async def review(
        self,
        run_id: UUID,
        variant: Variant,
        body: ReviewRequest,
        *,
        auth_mode: str = "shared_key",
        user: Any = None,
    ) -> ReviewResponse:
        if (
            body.action in {"approve", "reject"}
            and user is None
            and not (body.reviewer_name or "").strip()
        ):
            raise ReviewError(400, "invalid_request", "Reviewer name is required.")
        reserved = False
        started = False
        accepted = False
        try:
            async with self.runner.session_factory() as session:
                async with session.begin():
                    repository = PackageRepository(session)
                    row = await repository.get_for_update(run_id, variant)
                    if row is None or PackageStatus(row.status) == PackageStatus.FAILED:
                        raise ReviewError(404, "not_found", "Package not found.")
                    snapshot = await ResultsRepository(session).snapshot(run_id)
                    if snapshot is None:
                        raise ReviewError(404, "not_found", "Pipeline run not found.")
                    run = snapshot.run
                    if RunStatus(run.status) not in TERMINAL_RUNS:
                        raise ReviewError(
                            409,
                            "run_in_progress",
                            "Wait until the automated pipeline finishes.",
                        )
                    if PackageStatus(row.status) != PackageStatus.PENDING_REVIEW:
                        raise ReviewError(
                            409, "not_pending_review", "Package is not pending review."
                        )
                    for path in body.target_files:
                        try:
                            validate_relative_path(path)
                        except ValueError:
                            raise ReviewError(
                                400, "invalid_request", "Invalid target file."
                            ) from None
                        if path not in row.files:
                            raise ReviewError(
                                400, "invalid_request", "Target file does not exist."
                            )
                    feedback = (
                        self.safety.text(body.feedback) if body.feedback else None
                    )
                    reasons = package_presentation(
                        RunStatus(run.status),
                        PackageStatus(row.status),
                        row.files,
                        row.security_report,
                        row.validation_report,
                        row.error,
                    )["review_reasons"]
                    if body.action == "retry":
                        if not retry_targets(
                            row.files,
                            row.security_report,
                            row.validation_report,
                            body.target_files,
                        ):
                            code = (
                                "feedback_needs_target"
                                if feedback
                                else "nothing_to_retry"
                            )
                            raise ReviewError(
                                422, code, "Choose an existing package file to retry."
                            )
                        if not self.runner.reserve():
                            raise ReviewError(
                                429,
                                "too_many_runs",
                                "Too many pipeline runs are active.",
                            )
                        reserved = True
                    decision = (
                        self.safety.value(
                            {
                                "action": body.action,
                                "reviewer_name": user.username
                                if user
                                else body.reviewer_name,
                                "user_id": str(user.id) if user else None,
                                "reason": body.reason,
                                "decided_at": datetime.now(UTC).isoformat(),
                                "identity_basis": "authenticated account"
                                if user
                                else "self-declared (shared-key authentication)"
                                if user or auth_mode != "local"
                                else "self-declared (no authentication — local mode)",
                            }
                        )
                        if body.action in {"approve", "reject"}
                        else None
                    )
                    row.review_decision = decision
                    previous = await self.writer.review_action(
                        session, run_id, variant, body.action, feedback
                    )
                    target = {
                        "approve": PackageStatus.ENGINEER_APPROVED,
                        "reject": PackageStatus.REJECTED,
                        "retry": PackageStatus.REMEDIATING,
                    }[body.action]
            accepted = True
            await self.writer.review_event(
                run_id,
                variant,
                target,
                previous,
                action=body.action,
                reasons=reasons,
                decision=decision,
            )
            if body.action == "retry":
                self.runner.start_review_retry(run_id, variant, body.target_files)
                started = True
                return RetryResponse(
                    run_id=run_id,
                    variant=variant,
                    status=target,
                    stream_url=f"/api/pipeline/{run_id}/stream",
                )
            return ReviewResponse(run_id=run_id, variant=variant, status=target)
        except BaseException:
            if accepted and reserved and not started:
                try:
                    await asyncio.shield(
                        self.writer.abort_review_retry(
                            run_id,
                            variant,
                            reason="review retry aborted: launch failed",
                        )
                    )
                except Exception:
                    logger.exception(
                        "could not settle failed retry launch for %s", run_id
                    )
            raise
        finally:
            if reserved and not started:
                self.runner.release()

    async def run_retry(
        self, run_id: UUID, variant: Variant, target_files: list[str]
    ) -> None:
        workspace = ValidationWorkspace()
        try:
            with workspace.activate():
                await self._run_retry_inside(run_id, variant, target_files)
        finally:
            workspace.close()

    async def _run_retry_inside(
        self, run_id: UUID, variant: Variant, target_files: list[str]
    ) -> None:
        try:
            async with self.runner.session_factory() as session:
                snapshot = await ResultsRepository(session).snapshot(run_id)
            if snapshot is None or snapshot.plan is None:
                raise ReviewRetryScanError("deployment plan unavailable")
            row = next(item for item in snapshot.packages if item.variant == variant)
            config = RunConfig(
                policy_profile=snapshot.run.policy_profile or "strict",
                provider=LLMProvider(snapshot.run.llm_provider),
                model=snapshot.run.model,
                max_iterations=snapshot.run.max_iterations,
            )
            ctx = StageContext(
                run_id,
                self.writer,
                DeploymentPlan.model_validate(snapshot.plan),
                max_iterations=snapshot.run.max_iterations,
            )
            security = self.runner.factory.create_security_agent(config)
            package = IaCPackage(
                variant=variant,
                files=dict(row.files),
                security_report=row.security_report,
                validation_report=row.validation_report,
            )
            scan = await security.remediate_from_review(
                ctx,
                variant,
                package,
                row.review_feedback,
                (row.validation_report or {}).get("failed_checks_for_remediation", []),
                target_files=target_files,
                start_committed=True,
            )
            async with self.runner.session_factory() as session:
                remediated = await PackageRepository(session).get(run_id, variant)
                if remediated is None:
                    raise ReviewRetryScanError("package unavailable")
                package = IaCPackage(
                    variant=variant,
                    files=dict(remediated.files),
                    security_report=remediated.security_report,
                    validation_report=remediated.validation_report,
                )
            outcome = await self.runner.validation_stage.run(ctx, variant, package)
            if outcome == PackageStatus.VALIDATION_ERROR:
                raise ReviewRetryScanError("validation could not complete")
            target = readiness_after_validation(scan, outcome)
            await self.writer.package_transition(
                run_id, variant, target, message=f"review retry package {target.value}"
            )
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(
                    asyncio.shield(
                        self.writer.abort_review_retry(
                            run_id,
                            variant,
                            reason="review retry interrupted by server shutdown",
                        )
                    ),
                    timeout=5,
                )
            except Exception:
                logger.exception(
                    "could not settle cancelled review retry for %s", run_id
                )
            raise
        except Exception as error:
            reason = (
                f"review retry aborted: {error}"
                if isinstance(error, ReviewRetryScanError)
                else "review retry aborted: internal failure"
            )
            if not isinstance(error, ReviewRetryScanError):
                logger.exception(
                    "review retry failed for %s variant %s", run_id, variant
                )
            await self.writer.abort_review_retry(run_id, variant, reason=reason)
