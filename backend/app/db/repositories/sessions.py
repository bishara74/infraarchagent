"""Atomic session expiry checks and renewal, without raw credentials."""

from datetime import datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuthSession


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, digest: str, now: datetime, absolute: datetime) -> None:
        self.session.add(
            AuthSession(
                token_hash=digest,
                created_at=now,
                last_activity_at=now,
                absolute_expires_at=absolute,
                revoked_at=None,
            )
        )
        await self.session.flush()

    async def touch(
        self, digest: str, now: datetime, idle_seconds: int
    ) -> AuthSession | None:
        return await self.session.scalar(
            update(AuthSession)
            .where(
                AuthSession.token_hash == digest,
                AuthSession.revoked_at.is_(None),
                AuthSession.absolute_expires_at > now,
                AuthSession.last_activity_at > now - timedelta(seconds=idle_seconds),
            )
            .values(last_activity_at=now)
            .returning(AuthSession)
        )

    async def revoke(self, digest: str, now: datetime) -> None:
        await self.session.execute(
            update(AuthSession)
            .where(AuthSession.token_hash == digest, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
