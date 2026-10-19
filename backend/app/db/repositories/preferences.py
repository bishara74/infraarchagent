"""Optimistic preference writes and shared-workspace recent history."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentEvent, PipelineRun, User, UserPreferences, UserRecentRun


class PreferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID) -> dict[str, Any]:
        row = await self.session.get(UserPreferences, user_id)
        return (
            {"revision": row.revision, "data": row.data}
            if row
            else {"revision": 0, "data": {}}
        )

    async def save(self, user_id: UUID, revision: int, data: dict[str, Any]) -> bool:
        # Lock an existing user even before their first preference row exists.
        await self.session.get(User, user_id, with_for_update=True)
        row = await self.session.get(UserPreferences, user_id)
        if revision != (row.revision if row else 0):
            return False
        if row:
            row.revision += 1
            row.data = data
            row.updated_at = datetime.now(UTC)
        else:
            self.session.add(
                UserPreferences(
                    user_id=user_id, revision=1, data=data, updated_at=datetime.now(UTC)
                )
            )
        return True

    async def visit(self, user_id: UUID, run_id: UUID, seq: int = 0) -> bool:
        await self.session.get(User, user_id, with_for_update=True)
        if await self.session.get(PipelineRun, run_id) is None:
            return False
        bound = (
            await self.session.scalar(
                select(func.max(AgentEvent.seq)).where(AgentEvent.run_id == run_id)
            )
            or 0
        )
        row = await self.session.get(UserRecentRun, (user_id, run_id))
        if row:
            row.opened_at = datetime.now(UTC)
            row.last_seq = max(row.last_seq, min(seq, bound))
        else:
            self.session.add(
                UserRecentRun(
                    user_id=user_id,
                    run_id=run_id,
                    opened_at=datetime.now(UTC),
                    last_seq=min(seq, bound),
                )
            )
        return True

    async def recent(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = await self.session.execute(
            select(PipelineRun, UserRecentRun)
            .join(UserRecentRun, PipelineRun.run_id == UserRecentRun.run_id)
            .where(UserRecentRun.user_id == user_id)
            .order_by(UserRecentRun.opened_at.desc())
            .limit(100)
        )
        return [
            {
                "id": str(run.run_id),
                "title": run.input_text[:120],
                "time": run.start_time.isoformat(),
                "status": run.status,
                "last_seq": recent.last_seq,
            }
            for run, recent in rows
        ]
