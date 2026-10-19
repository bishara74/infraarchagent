"""NFR-01 encrypted storage, rotation and mocked provider presets."""

import base64
import json
from uuid import uuid4
import httpx
import pytest
from pydantic import SecretStr
from app.core.credentials import CredentialError, CredentialMaterial, CredentialVault
from app.db.repositories.providers import ProviderRepository
from app.llm.catalog import PRESETS, probe
from tests.integration.test_phase9g_auth import authenticated, KEY

SECRET = "phase9h-provider-canary-not-a-real-key"
MASTER = base64.b64encode(bytes(range(32))).decode()


@pytest.mark.req("NFR-01")
def test_authenticated_encryption_and_missing_key(monkeypatch):
    monkeypatch.delenv("CREDENTIAL_ENCRYPTION_KEY", raising=False)
    with pytest.raises(CredentialError):
        CredentialVault()
    vault = CredentialVault(MASTER)
    identity = uuid4()
    ciphertext, nonce = vault.encrypt("openrouter", identity, SecretStr(SECRET))
    assert SECRET.encode() not in ciphertext
    assert (
        vault.decrypt("openrouter", identity, ciphertext, nonce).get_secret_value()
        == SECRET
    )
    for provider, ident, value in [
        ("other", identity, ciphertext),
        ("openrouter", uuid4(), ciphertext),
        ("openrouter", identity, ciphertext[:-1] + bytes([ciphertext[-1] ^ 1])),
    ]:
        with pytest.raises(CredentialError):
            vault.decrypt(provider, ident, value, nonce)
    with pytest.raises(CredentialError):
        CredentialVault(base64.b64encode(b"x" * 32).decode()).decrypt(
            "openrouter", identity, ciphertext, nonce
        )


@pytest.mark.req("NFR-01")
async def test_database_rotation_revoke_and_public_metadata(db_engines, monkeypatch):
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", MASTER)
    app, _ = await authenticated(db_engines[0])
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        response = await client.post(
            "/api/providers", json={"provider": "openrouter", "api_key": SECRET}
        )
        assert response.status_code == 201
        identity = response.json()["id"]
        assert (
            await client.post(f"/api/providers/{identity}/default")
        ).status_code == 200
        listing = (await client.get("/api/providers")).json()
        assert SECRET not in json.dumps(listing)
        async with app.state.session_factory() as session, session.begin():
            repository = ProviderRepository(session)
            rows = await repository.list()
            assert rows[0].ciphertext != SECRET.encode()
            assert (
                await repository.material(rows[0].id)
            ).secret.get_secret_value() == SECRET
            new = base64.b64encode(b"n" * 32).decode()
            assert (
                await repository.rotate(CredentialVault(), CredentialVault(new), 2) == 1
            )
        monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", new)
        assert (
            await client.post(f"/api/providers/{identity}/revoke")
        ).status_code == 200
        assert (await client.post(f"/api/providers/{identity}/test")).status_code == 409


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("preset", ["openrouter", "openai", "anthropic", "custom"])
async def test_mocked_presets(preset):
    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "data": {"limit_remaining": 0}
                if request.url.path.endswith("/key")
                else [
                    {
                        "id": "test-model",
                        "supported_parameters": ["reasoning", "structured_outputs"],
                        "context_length": 8192,
                        "pricing": {"prompt": "0.001"},
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        result = await probe(
            CredentialMaterial(
                preset,
                "messages" if preset == "anthropic" else "chat_completions",
                PRESETS.get(preset, ("https://custom.invalid/v1",))[0],
                SecretStr(SECRET),
            ),
            client,
        )
    assert result["models"][0]["id"] == "test-model"
    assert result["status"] == ("no_credit" if preset == "openrouter" else "ok")
    assert ("x-api-key" in seen[0].headers) == (preset == "anthropic")
