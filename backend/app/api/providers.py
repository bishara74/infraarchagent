"""Admin provider management; secret request fields are never echoed."""

from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    model_validator,
)

from app.api.auth import failure
from app.api.deps import require_admin
from app.core.credentials import CredentialError, CredentialMaterial, CredentialVault
from app.core.safety import PublicDataSafety
from app.db.repositories.providers import ProviderRepository
from app.llm.catalog import PRESETS, probe

router = APIRouter(prefix="/api/providers", dependencies=[Depends(require_admin)])


class ProviderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["openrouter", "openai", "anthropic", "custom"]
    label: str = Field(default="My provider", min_length=1, max_length=120)
    base_url: str = ""
    api_key: SecretStr = Field(min_length=1, max_length=4096)

    @model_validator(mode="after")
    def preset(self) -> "ProviderInput":
        if self.provider in PRESETS:
            self.base_url = PRESETS[self.provider][0]
        url = urlsplit(self.base_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ValueError("Invalid provider URL")
        return self

    def material(self) -> CredentialMaterial:
        return CredentialMaterial(
            self.provider,
            "messages" if self.provider == "anthropic" else "chat_completions",
            self.base_url,
            self.api_key,
        )


@router.get("")
async def listing(request: Request) -> dict[str, object]:
    try:
        CredentialVault()
        enabled = True
    except CredentialError:
        enabled = False
    async with request.app.state.session_factory() as session, session.begin():
        repository = ProviderRepository(session)
        config = await repository.settings()
        return {
            "storage_enabled": enabled,
            "default_credential_id": str(config.default_credential_id)
            if config.default_credential_id
            else None,
            "credentials": [
                {
                    "id": str(r.id),
                    "provider": r.provider,
                    "label": r.label,
                    "base_url": r.base_url,
                    "last4": r.last4,
                    "revoked": r.revoked_at is not None,
                    "credential_type": r.credential_type,
                    "api_protocol": r.api_protocol,
                }
                for r in await repository.list()
            ],
        }


@router.post("/probe")
async def probe_entered(request: Request) -> JSONResponse:
    try:
        body = ProviderInput.model_validate(await request.json())
        # Register even unsaved keys before inspecting provider responses.
        from app.core.logging import register_secret

        register_secret(body.api_key.get_secret_value())
        result = await probe(
            body.material(), getattr(request.app.state, "provider_http", None)
        )
        return JSONResponse(PublicDataSafety(request.app.state.settings).value(result))
    except (ValueError, ValidationError):
        return failure(400, "invalid_request", "Check provider URL and key.")


@router.post("")
async def create(request: Request) -> JSONResponse:
    try:
        body = ProviderInput.model_validate(await request.json())
        async with request.app.state.session_factory() as session, session.begin():
            row = await ProviderRepository(session).create(
                body.provider,
                PublicDataSafety(request.app.state.settings).text(body.label),
                body.base_url,
                body.material().api_protocol,
                body.api_key,
                request.state.user.id if request.state.user else None,
            )
        return JSONResponse({"id": str(row.id), "last4": row.last4}, status_code=201)
    except CredentialError:
        return failure(
            409,
            "encryption_unavailable",
            "Set CREDENTIAL_ENCRYPTION_KEY to a base64-encoded 32-byte key "
            "before saving credentials.",
        )
    except (ValueError, ValidationError):
        return failure(400, "invalid_request", "Check provider URL and key.")


@router.post("/{credential_id}/test")
async def test_saved(credential_id: UUID, request: Request) -> JSONResponse:
    try:
        async with request.app.state.session_factory() as session, session.begin():
            material = await ProviderRepository(session).material(credential_id)
        return JSONResponse(
            PublicDataSafety(request.app.state.settings).value(
                await probe(material, getattr(request.app.state, "provider_http", None))
            )
        )
    except CredentialError:
        return failure(
            409,
            "credential_unavailable",
            "Select an active credential and check the encryption key.",
        )


@router.post("/{credential_id}/default")
async def select_default(credential_id: UUID, request: Request) -> JSONResponse:
    try:
        async with request.app.state.session_factory() as session, session.begin():
            await ProviderRepository(session).select(credential_id)
        request.app.state.catalog_cache = {}
        return JSONResponse({"selected": True})
    except CredentialError:
        return failure(
            409,
            "credential_unavailable",
            "Select an active credential and check the encryption key.",
        )


@router.post("/{credential_id}/revoke")
async def revoke(credential_id: UUID, request: Request) -> dict[str, bool]:
    async with request.app.state.session_factory() as session, session.begin():
        await ProviderRepository(session).revoke(credential_id)
    request.app.state.catalog_cache = {}
    return {"revoked": True}
