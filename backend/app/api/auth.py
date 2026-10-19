"""Safe browser login/session HTTP endpoints (NFR-01)."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError

from app.core.auth import COOKIE_NAME, key_matches, origin_allowed

router = APIRouter(prefix="/api/auth")


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: SecretStr


def failure(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


@router.get("/session")
async def session_status(request: Request) -> JSONResponse:
    return JSONResponse(
        await request.app.state.auth.status(request),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/login")
async def login(request: Request) -> JSONResponse:
    auth = request.app.state.auth
    if not origin_allowed(request, required=True):
        return failure(403, "forbidden", "Same-origin request required.")
    if not auth.allow_attempt(request.client.host if request.client else "unknown"):
        response = failure(
            429, "rate_limited", "Too many login attempts. Try again later."
        )
        response.headers["Retry-After"] = "60"
        return response
    try:
        body = LoginRequest.model_validate(await request.json())
    except (ValidationError, ValueError, UnicodeDecodeError):
        return failure(400, "invalid_request", "Invalid login request.")
    if not key_matches(auth.settings, body.api_key.get_secret_value()):
        return failure(401, "unauthorized", "API authentication required.")
    token = await auth.login()
    response = JSONResponse(
        {"authenticated": True, "mode": "shared_key"},
        headers={"Cache-Control": "no-store"},
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="strict",
        path="/api",
        secure=auth.settings.auth_cookie_secure,
        max_age=auth.settings.auth_absolute_seconds,
    )
    return response


@router.post("/logout")
async def logout(request: Request) -> JSONResponse:
    if not origin_allowed(request, required=True):
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
