"""Package persistence and the package-only retention sweep."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GeneratedPackage
from app.domain.enums import PackageStatus, Variant
from app.domain.paths import validate_file_map
from app.domain.states import assert_package_transition
from app.security.diff import package_diff


class PackageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
            "sessions": sessions,
            "omitted_session_count": omitted,
        }
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
