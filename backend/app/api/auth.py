"""Account HTTP endpoints; passwords never enter public validation errors."""

from uuid import UUID

import anyio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
)
from starlette.requests import ClientDisconnect

from app.api.deps import require_admin, require_api_key
from app.core.auth import COOKIE_NAME, key_matches, origin_allowed
from app.core.logging import register_secret
from app.core.passwords import DUMMY_HASH, hash_password, verify_password
from app.core.safety import PublicDataSafety
from app.db.repositories.users import UserRepository

router = APIRouter(prefix="/api/auth")


class AccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,120}$")
    password: SecretStr

    @field_validator("password")
    @classmethod
    def bounded(cls, value: SecretStr) -> SecretStr:
        if not 12 <= len(value.get_secret_value()) <= 1024:
            raise ValueError("Password must contain 12 to 1024 characters.")
        return value


class PasswordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: SecretStr
    current_password: SecretStr | None = None

    @field_validator("password")
    @classmethod
    def bounded(cls, value: SecretStr) -> SecretStr:
        return AccountInput.bounded(value)


def failure(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


def cookie_response(request: Request, token: str) -> JSONResponse:
    response = JSONResponse(
        {"authenticated": True}, headers={"Cache-Control": "no-store"}
    )
    settings = request.app.state.settings
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="strict",
        path="/api",
        secure=settings.auth_cookie_secure,
        max_age=settings.auth_absolute_seconds,
    )
    return response


def permitted(request: Request) -> bool:
    return origin_allowed(
        request,
        required=not key_matches(
            request.app.state.settings, request.headers.get("X-API-Key")
        ),
    )


@router.get("/session")
async def session_status(request: Request) -> JSONResponse:
    return JSONResponse(
        await request.app.state.auth.status(request),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/setup")
async def setup(request: Request) -> JSONResponse:
    local = (
        request.client is not None
        and request.client.host == "127.0.0.1"
        and request.url.hostname in {"127.0.0.1", "localhost"}
        and not any(
            h in request.headers
            for h in ("forwarded", "x-forwarded-for", "x-forwarded-host")
        )
    )
    if not permitted(request) or not (
        local
        or key_matches(request.app.state.settings, request.headers.get("X-API-Key"))
    ):
        return failure(
            403,
            "forbidden",
            "Create the first admin from 127.0.0.1 or use the bootstrap header.",
        )
    if not request.app.state.auth.allow_attempt(
        request.client.host if request.client else "unknown"
    ):
        return failure(429, "rate_limited", "Too many attempts. Try again later.")
    try:
        body = AccountInput.model_validate(await request.json())
        if (
            body.username == body.password.get_secret_value()
            or PublicDataSafety(request.app.state.settings).text(body.username)
            != body.username
        ):
            raise ValueError("Invalid username")
        encoded = await anyio.to_thread.run_sync(
            hash_password, body.password.get_secret_value()
        )
        async with request.app.state.session_factory() as session, session.begin():
            user = await UserRepository(session).create(
                body.username, encoded, first=True
            )
    except (ValueError, ValidationError, ClientDisconnect):
        return failure(
            409,
            "setup_unavailable",
            "Setup is complete or account details are invalid. "
            "Use a password of at least 12 characters.",
        )
    register_secret(body.password.get_secret_value())
    return cookie_response(request, await request.app.state.auth.login(user.id))


@router.post("/login")
async def login(request: Request) -> JSONResponse:
    auth = request.app.state.auth
    if not permitted(request):
        return failure(403, "forbidden", "Same-origin request required.")
    if not auth.allow_attempt(request.client.host if request.client else "unknown"):
        response = failure(
            429, "rate_limited", "Too many login attempts. Try again later."
        )
        response.headers["Retry-After"] = "60"
        return response
    try:
        raw = await request.json()
        # Transitional pre-account API compatibility; never presented by the UI.
        if (
            isinstance(raw, dict)
            and set(raw) == {"api_key"}
            and isinstance(raw["api_key"], str)
            and not await auth.has_users()
        ):
            if key_matches(auth.settings, raw["api_key"]):
                return cookie_response(request, await auth.login())
            return failure(401, "unauthorized", "Invalid username or password.")
        body = AccountInput.model_validate(raw)
    except (ValueError, ValidationError, ClientDisconnect):
        return failure(401, "unauthorized", "Invalid username or password.")
    async with auth.sessions() as session, session.begin():
        user = await UserRepository(session).find(body.username)
        valid = await anyio.to_thread.run_sync(
            verify_password,
            body.password.get_secret_value(),
            user.password_hash if user else DUMMY_HASH,
        )
        if not valid or user is None or user.disabled_at is not None:
            return failure(401, "unauthorized", "Invalid username or password.")
        register_secret(body.password.get_secret_value())
        await UserRepository(session).record_login(user.id)
    return cookie_response(request, await auth.login(user.id))


@router.get("/users", dependencies=[Depends(require_admin)])
async def users(request: Request) -> list[dict[str, object]]:
    async with request.app.state.session_factory() as session:
        return [
            {
                "id": str(u.id),
                "username": u.username,
                "role": u.role,
                "disabled": u.disabled_at is not None,
                "created_at": u.created_at.isoformat(),
                "last_login_at": u.last_login_at.isoformat()
                if u.last_login_at
                else None,
            }
            for u in await UserRepository(session).list()
        ]


@router.post("/users", dependencies=[Depends(require_admin)])
async def create_user(request: Request) -> JSONResponse:
    try:
        body = AccountInput.model_validate(await request.json())
        if (
            body.username == body.password.get_secret_value()
            or PublicDataSafety(request.app.state.settings).text(body.username)
            != body.username
        ):
            raise ValueError("Invalid username")
        encoded = await anyio.to_thread.run_sync(
            hash_password, body.password.get_secret_value()
        )
        async with request.app.state.session_factory() as session, session.begin():
            user = await UserRepository(session).create(body.username, encoded)
        register_secret(body.password.get_secret_value())
        return JSONResponse(
            {"id": str(user.id), "username": user.username}, status_code=201
        )
    except (ValueError, ValidationError, ClientDisconnect):
        return failure(
            400,
            "invalid_request",
            "Account cannot be created. Check username and password length.",
        )


@router.post("/users/{user_id}/disable", dependencies=[Depends(require_admin)])
async def disable(user_id: UUID, request: Request) -> JSONResponse:
    async with request.app.state.session_factory() as session, session.begin():
        done = await UserRepository(session).modify(user_id, disable=True)
    return JSONResponse({"updated": done})


@router.post("/users/{user_id}/enable", dependencies=[Depends(require_admin)])
async def enable(user_id: UUID, request: Request) -> JSONResponse:
    async with request.app.state.session_factory() as session, session.begin():
        done = await UserRepository(session).enable(user_id)
    return JSONResponse({"updated": done})


@router.post("/users/{user_id}/password", dependencies=[Depends(require_admin)])
async def reset_password(user_id: UUID, request: Request) -> JSONResponse:
    return await change(request, user_id)


async def change(request: Request, user_id: UUID, *, own: bool = False) -> JSONResponse:
    try:
        body = PasswordInput.model_validate(await request.json())
        async with request.app.state.session_factory() as session, session.begin():
            user = await UserRepository(session).get(user_id, lock=True)
            if user is None or (
                own
                and not await anyio.to_thread.run_sync(
                    verify_password,
                    body.current_password.get_secret_value()
                    if body.current_password
                    else "",
                    user.password_hash,
                )
            ):
                return failure(401, "unauthorized", "Password could not be changed.")
            register_secret(body.password.get_secret_value())
            encoded = await anyio.to_thread.run_sync(
                hash_password, body.password.get_secret_value()
            )
            await UserRepository(session).modify(user_id, password_hash=encoded)
        return JSONResponse({"updated": True})
    except (ValueError, ValidationError, ClientDisconnect):
        return failure(
            400, "invalid_request", "Use a password of at least 12 characters."
        )


@router.post("/password", dependencies=[Depends(require_api_key)])
async def own_password(request: Request) -> JSONResponse:
    if request.state.user is None:
        return failure(401, "unauthorized", "Log in with an account.")
    return await change(request, request.state.user.id, own=True)


@router.post("/logout")
async def logout(request: Request) -> JSONResponse:
    if not permitted(request):
        return failure(403, "forbidden", "Same-origin request required.")
    if token := request.cookies.get(COOKIE_NAME):
        await request.app.state.auth.revoke(token)
    response = JSONResponse(
        {"authenticated": False}, headers={"Cache-Control": "no-store"}
    )
    response.delete_cookie(
        COOKIE_NAME,
        path="/api",
        httponly=True,
        samesite="strict",
        secure=request.app.state.settings.auth_cookie_secure,
    )
    return response
