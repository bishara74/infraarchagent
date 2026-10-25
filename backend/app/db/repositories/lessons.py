"""Lesson persistence. A global transaction lock orders sets and governance."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AgentEvent,
    LessonAuditEvent,
    LessonControl,
    LessonRevision,
    LessonSet,
)
from app.domain.lessons import GOVERNANCE_LOCK, content_hash


def lesson_entry(row: LessonRevision) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "lesson_id": str(row.lesson_id),
        "revision": row.revision,
        "scope_role": row.scope_role,
        "applies_to": row.applies_to,
        "category": row.category,
        "text": row.text,
        "self_approved": row.self_approved,
        "filter_version": (row.approval_filter_result or row.filter_result)["version"],
    }


class LessonRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def control(self) -> LessonControl:
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": str(GOVERNANCE_LOCK)},
        )
        row = await self.session.get(LessonControl, 1, populate_existing=True)
        if row is None:
            # Also supports a fresh, isolated test database after owner cleanup.
            if await self.session.get(LessonSet, 0) is None:
                self.session.add(
                    LessonSet(
                        version=0,
                        sha256=content_hash([]),
                        entries=[],
                        created_at=datetime.now(UTC),
                    )
                )
                await self.session.flush()
            row = LessonControl(
                id=1, runtime_enabled=False, disable_generation=0, set_version=0
            )
            self.session.add(row)
            await self.session.flush()
        return row

    async def decision(self, identity: UUID) -> AgentEvent | None:
        row = await self.session.get(AgentEvent, identity)
        if (
            row is None
            or row.payload.get("kind") != "package_status"
            or row.payload.get("review_action") not in {"approve", "reject"}
        ):
            return None
        return row

    async def get(self, identity: UUID) -> LessonRevision | None:
        return await self.session.get(LessonRevision, identity, populate_existing=True)

    async def latest(self, lesson_id: UUID) -> int:
        return int(
            await self.session.scalar(
                select(func.max(LessonRevision.revision)).where(
                    LessonRevision.lesson_id == lesson_id
                )
            )
            or 0
        )

    async def active(self) -> list[LessonRevision]:
        return list(
            await self.session.scalars(
                select(LessonRevision)
                .where(LessonRevision.status == "approved")
                .order_by(LessonRevision.lesson_id, LessonRevision.revision)
            )
        )

    async def new_set(self, control: LessonControl) -> LessonSet:
        entries = [lesson_entry(row) for row in await self.active()]
        row = LessonSet(
            version=control.set_version + 1,
            sha256=content_hash(entries),
            entries=entries,
            created_at=datetime.now(UTC),
        )
        self.session.add(row)
        await self.session.flush()
        control.set_version = row.version
        return row

    async def listing(
        self, status: str | None, page: int, lesson_id: UUID | None = None
    ) -> tuple[list[LessonRevision], int]:
        conditions = []
        if status:
            conditions.append(LessonRevision.status == status)
        if lesson_id:
            conditions.append(LessonRevision.lesson_id == lesson_id)
        count = int(
            await self.session.scalar(
                select(func.count()).select_from(LessonRevision).where(*conditions)
            )
            or 0
        )
        rows = await self.session.scalars(
            select(LessonRevision)
            .where(*conditions)
            .order_by(LessonRevision.created_at.desc(), LessonRevision.id)
            .limit(25)
            .offset((page - 1) * 25)
        )
        return list(rows), count

    async def history(self, page: int) -> tuple[list[LessonAuditEvent], int]:
        count = int(
            await self.session.scalar(
                select(func.count()).select_from(LessonAuditEvent)
            )
            or 0
        )
        rows = await self.session.scalars(
            select(LessonAuditEvent)
            .order_by(LessonAuditEvent.seq.desc())
            .limit(25)
            .offset((page - 1) * 25)
        )
        return list(rows), count
