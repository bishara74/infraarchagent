"""Account persistence and atomic bootstrap; no raw passwords."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuthSession, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID, *, lock: bool = False) -> User | None:
        return await self.session.get(User, user_id, with_for_update=lock)

    async def record_login(self, user_id: UUID) -> None:
        user = await self.get(user_id)
        if user:
            user.last_login_at = datetime.now(UTC)

    async def any(self) -> bool:
        return bool(await self.session.scalar(select(User.id).limit(1)))

    async def find(self, username: str) -> User | None:
        return await self.session.scalar(
            select(User).where(func.lower(User.username) == username.lower())
        )

    async def create(
        self, username: str, password_hash: str, *, first: bool = False
    ) -> User:
        await self.session.execute(text("SELECT pg_advisory_xact_lock(904001)"))
        if (first and await self.any()) or await self.find(username):
            raise ValueError("Account cannot be created.")
        if first:
            await self.session.execute(
                update(AuthSession)
                .where(AuthSession.user_id.is_(None))
                .values(revoked_at=datetime.now(UTC))
            )
        row = User(
            id=uuid4(),
            username=username,
            password_hash=password_hash,
            role="admin" if first else "reviewer",
            created_at=datetime.now(UTC),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list(self) -> list[User]:
        return list(await self.session.scalars(select(User).order_by(User.username)))

    async def modify(
        self, user_id: UUID, *, password_hash: str | None = None, disable: bool = False
    ) -> bool:
        row = await self.session.get(User, user_id, with_for_update=True)
        if row is None or (disable and row.role != "reviewer"):
            return False
        if password_hash:
            row.password_hash = password_hash
        if disable:
            row.disabled_at = datetime.now(UTC)
        await self.session.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id)
            .values(revoked_at=datetime.now(UTC))
        )
        return True

    async def enable(self, user_id: UUID) -> bool:
        row = await self.get(user_id, lock=True)
        if row is None or row.role != "reviewer":
            return False
        # Disabling revoked all sessions; enabling never changes those records.
        row.disabled_at = None
        return True
