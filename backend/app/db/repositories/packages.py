"""Package persistence and the package-only retention sweep."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GeneratedPackage
from app.domain.enums import PackageStatus, Variant
from app.domain.paths import validate_file_map
from app.domain.states import assert_package_transition, review_retry_abort_path
from app.domain.validation import ValidationReport
from app.security.diff import package_diff


class PackageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_update(
        self, run_id: UUID, variant: Variant
    ) -> GeneratedPackage | None:
        return await self.session.scalar(
            select(GeneratedPackage)
            .where(
                GeneratedPackage.run_id == run_id, GeneratedPackage.variant == variant
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    async def list_review_retries(self) -> list[tuple[UUID, Variant]]:
        rows = (
            await self.session.execute(
                select(GeneratedPackage.run_id, GeneratedPackage.variant).where(
                    GeneratedPackage.review_retry_started_at.is_not(None)
                )
            )
        ).all()
        return [(run_id, Variant(variant)) for run_id, variant in rows]

    async def review_action(
        self, run_id: UUID, variant: Variant, action: str, feedback: str | None
    ) -> PackageStatus:
        target = {
            "approve": PackageStatus.ENGINEER_APPROVED,
            "reject": PackageStatus.REJECTED,
            "retry": PackageStatus.REMEDIATING,
        }[action]
        row, previous = await self.transition_status(run_id, variant, target)
        row.error = None
        if action in {"retry", "reject"}:
            row.review_feedback = feedback
        if action == "retry":
            row.iteration_count = 0
            row.review_retry_started_at = datetime.now(UTC)
        await self.session.flush()
        return previous

    async def abort_review_retry(
        self, run_id: UUID, variant: Variant, reason: str
    ) -> list[tuple[PackageStatus, PackageStatus]]:
        row = await self.get_for_update(run_id, variant)
        if row is None:
            raise LookupError("package not found")
        previous = PackageStatus(row.status)
        path = review_retry_abort_path(
            previous, retry_started=row.review_retry_started_at is not None
        )
        changes = []
        for target in path:
            # The path itself supplies the narrowly scoped review-only rules.
            changes.append((previous, target))
            row.status = target
            previous = target
        row.error = reason
        row.review_retry_started_at = None
        await self.session.flush()
        return changes or [(previous, previous)]

    async def create(self, run_id: UUID, variant: Variant) -> GeneratedPackage:
        row = GeneratedPackage(
            package_id=uuid4(),
            run_id=run_id,
            variant=variant,
            files={},
            original_files=None,
            security_report=None,
            validation_report=None,
            remediation_diff=None,
            iteration_count=0,
            status=PackageStatus.GENERATING,
            review_feedback=None,
            error=None,
            created_at=datetime.now(UTC),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get(self, run_id: UUID, variant: Variant) -> GeneratedPackage | None:
        return await self.session.scalar(
            select(GeneratedPackage).where(
                GeneratedPackage.run_id == run_id, GeneratedPackage.variant == variant
            )
        )

    async def list_for_run(self, run_id: UUID) -> list[GeneratedPackage]:
        result = await self.session.scalars(
            select(GeneratedPackage)
            .where(GeneratedPackage.run_id == run_id)
            .order_by(GeneratedPackage.variant)
        )
        return list(result)

    async def set_status(
        self,
        run_id: UUID,
        variant: Variant,
        target: PackageStatus,
        *,
        error: str | None = None,
    ) -> GeneratedPackage:
        row, _ = await self.transition_status(run_id, variant, target, error=error)
        return row

    async def transition_status(
        self,
        run_id: UUID,
        variant: Variant,
        target: PackageStatus,
        *,
        error: str | None = None,
    ) -> tuple[GeneratedPackage, PackageStatus]:
        row = await self.session.scalar(
            select(GeneratedPackage)
            .where(
                GeneratedPackage.run_id == run_id, GeneratedPackage.variant == variant
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row is None:
            raise LookupError("package not found")
        previous = PackageStatus(row.status)
        assert_package_transition(previous, target)
        row.status = target
        if target in {
            PackageStatus.PENDING_REVIEW,
            PackageStatus.CHECKS_PASSED,
            PackageStatus.REJECTED,
        }:
            row.review_retry_started_at = None
        if error is not None:
            row.error = error
        await self.session.flush()
        return row, previous

    async def save_files(
        self, run_id: UUID, variant: Variant, files: dict[str, str]
    ) -> GeneratedPackage:
        safe_files = validate_file_map(files)
        row = await self.session.scalar(
            select(GeneratedPackage)
            .where(
                GeneratedPackage.run_id == run_id, GeneratedPackage.variant == variant
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row is None:
            raise LookupError("package not found")
        row.files = safe_files
        await self.session.flush()
        return row

    async def save_automatic_repairs(
        self,
        run_id: UUID,
        variant: Variant,
        *,
        original_files: dict[str, str],
        files: dict[str, str],
    ) -> None:
        row = await self.get_for_update(run_id, variant)
        if row is None:
            raise LookupError("package not found")
        if row.original_files is None:
            row.original_files = validate_file_map(original_files)
        row.files = validate_file_map(files)
        row.remediation_diff = package_diff(row.original_files, row.files)
        await self.session.flush()

    async def reset_iteration_count(self, run_id: UUID, variant: Variant) -> None:
        row = await self.get(run_id, variant)
        if row is None:
            raise LookupError("package not found")
        row.iteration_count = 0
        await self.session.flush()

    async def save_security_results(
        self,
        run_id: UUID,
        variant: Variant,
        *,
        original_files: dict[str, str],
        files: dict[str, str],
        session_report: dict[str, Any],
        iteration_count: int,
        policy_version: str,
        prompt_version: str,
        tools: dict[str, str | None],
    ) -> GeneratedPackage:
        safe_original = validate_file_map(original_files)
        safe_files = validate_file_map(files)
        row = await self.session.scalar(
            select(GeneratedPackage)
            .where(
                GeneratedPackage.run_id == run_id,
                GeneratedPackage.variant == variant,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row is None:
            raise LookupError("package not found")
        if row.original_files is None:
            row.original_files = safe_original
        old_report = row.security_report or {}
        sessions = list(old_report.get("sessions", []))
        sessions.append(session_report)
        omitted = int(old_report.get("omitted_session_count", 0))
        if len(sessions) > 10:
            omitted += len(sessions) - 10
            sessions = sessions[-10:]
        row.files = safe_files
        row.remediation_diff = package_diff(row.original_files, safe_files)
        row.iteration_count = iteration_count
        row.security_report = {
            "policy_version": policy_version,
            "prompt_version": prompt_version,
            "tools": tools,
            "fixing_provider": session_report.get("fixing_provider"),
            "fixing_model": session_report.get("fixing_model"),
            "fixing_reasoning_effort": session_report.get("fixing_reasoning_effort"),
            "sessions": sessions,
            "final": session_report["final"],
            "omitted_session_count": omitted,
        }
        await self.session.flush()
        return row

    async def save_validation_results(
        self, run_id: UUID, variant: Variant, report: ValidationReport
    ) -> GeneratedPackage:
        validated = ValidationReport.model_validate_json(report.model_dump_json())
        row = await self.session.scalar(
            select(GeneratedPackage)
            .where(
                GeneratedPackage.run_id == run_id, GeneratedPackage.variant == variant
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row is None:
            raise LookupError("package not found")
        if PackageStatus(row.status) != PackageStatus.VALIDATING:
            raise ValueError("validation report requires a validating package")
        row.validation_report = validated.model_dump(mode="json")
        await self.session.flush()
        return row

    async def delete_expired(
        self, now: datetime, retention_days: int, dry_run: bool
    ) -> int:
        if now.tzinfo is None or retention_days < 1:
            raise ValueError("retention requires aware time and positive days")
        cutoff = now.astimezone(UTC) - timedelta(days=retention_days)
        expired = GeneratedPackage.created_at < cutoff
        if dry_run:
            count = await self.session.scalar(
                select(func.count()).select_from(GeneratedPackage).where(expired)
            )
            return int(count or 0)
        result = await self.session.scalars(
            delete(GeneratedPackage)
            .where(expired)
            .returning(GeneratedPackage.package_id)
        )
        return len(list(result))
