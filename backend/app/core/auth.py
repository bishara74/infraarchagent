"""Shared-key authentication with revocable, hashed browser sessions."""

import hashlib
import hmac
import secrets
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import anyio
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.models import AuthSession, User
from app.db.repositories.sessions import SessionRepository
from app.db.repositories.users import UserRepository

COOKIE_NAME = "infraarch_session"


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def key_matches(settings: Settings, supplied: str | None) -> bool:
    return settings.api_key is not None and hmac.compare_digest(
        (supplied or "").encode(), settings.api_key.get_secret_value().encode()
    )


def origin_allowed(request: Request, *, required: bool) -> bool:
    origin = request.headers.get("origin")
    if origin is None:
        return not required
    return origin == f"{request.url.scheme}://{request.headers.get('host', '')}"


class AuthService:
    def __init__(self, sessions: async_sessionmaker[AsyncSession], settings: Settings):
        self.sessions, self.settings = sessions, settings
        self.clock: Callable[[], datetime] = lambda: datetime.now(UTC)
        self.attempts: dict[str, deque[float]] = {}

    def allow_attempt(self, peer: str) -> bool:
        now = self.clock().timestamp()
        self.attempts = {
            k: v for k, v in self.attempts.items() if v and v[-1] > now - 60
        }
        if peer not in self.attempts and len(self.attempts) >= 4096:
            return False
        attempts = self.attempts.setdefault(peer, deque())
        while attempts and attempts[0] <= now - 60:
            attempts.popleft()
        if len(attempts) >= self.settings.auth_login_attempts_per_minute:
            return False
        attempts.append(now)
        return True

    async def login(self, user_id: UUID | None = None) -> str:
        token = secrets.token_urlsafe(32)
        now = self.clock()
        async with self.sessions() as session, session.begin():
            await SessionRepository(session).create(
                token_hash(token),
                now,
                now + timedelta(seconds=self.settings.auth_absolute_seconds),
                user_id,
            )
        return token

    async def activity(self, digest: str) -> AuthSession | None:
        # StreamingResponse uses level-triggered cancellation on disconnect.
        # Finish the owned transaction and return its connection before exiting.
        with anyio.CancelScope(shield=True):
            async with self.sessions() as session, session.begin():
                return await SessionRepository(session).touch(
                    digest, self.clock(), self.settings.auth_idle_seconds
                )
        return None

    async def revoke(self, token: str) -> None:
        async with self.sessions() as session, session.begin():
            await SessionRepository(session).revoke(token_hash(token), self.clock())

    async def has_users(self) -> bool:
        async with self.sessions() as session:
            return await UserRepository(session).any()

    async def user(self, user_id: UUID | None) -> User | None:
        async with self.sessions() as session:
            return await session.get(User, user_id) if user_id else None

    async def status(self, request: Request) -> dict[str, object]:
        setup = not await self.has_users()
        token = request.cookies.get(COOKIE_NAME)
        row = await self.activity(token_hash(token)) if token else None
        user = await self.user(row.user_id) if row else None
        local = setup and self.settings.api_key is None
        return {
            "auth_required": not local,
            "authenticated": row is not None
            or key_matches(self.settings, request.headers.get("X-API-Key")),
            "setup_required": setup,
            "mode": "local" if local else "account" if not setup else "shared_key",
            "message": "No authentication (local mode)" if local else None,
            "user": {"id": str(user.id), "username": user.username, "role": user.role}
            if user
            else None,
        }
