"""NFR-01 / FR-UI-07 account binding and bootstrap security."""

import httpx
import pytest
from app.core.passwords import hash_password, verify_password
from tests.integration.test_phase9g_auth import authenticated

ORIGIN = {"Origin": "http://127.0.0.1"}
PASSWORD = "phase9h-password-only"


@pytest.mark.req("NFR-01", "FR-UI-07")
async def test_bootstrap_accounts_roles_and_revocation(db_engines):
    app, run = await authenticated(db_engines[0])
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 123))
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1"
    ) as client:
        details = {"username": "Admin", "password": PASSWORD}
        assert (await client.post("/api/auth/setup", json=details)).status_code == 403
        assert (
            await client.post(
                "/api/auth/setup",
                json=details,
                headers={**ORIGIN, "X-Forwarded-For": "127.0.0.1"},
            )
        ).status_code == 403
        assert (
            await client.post("/api/auth/setup", json=details, headers=ORIGIN)
        ).status_code == 200
        assert (await client.get("/api/auth/session")).json()["user"][
            "username"
        ] == "Admin"
        assert (
            await client.post("/api/auth/setup", json=details, headers=ORIGIN)
        ).status_code == 409
        reviewer = await client.post(
            "/api/auth/users",
            json={"username": "Reviewer", "password": PASSWORD},
            headers=ORIGIN,
        )
        assert reviewer.status_code == 201
        user_id = reviewer.json()["id"]
        assert (
            await client.post(
                "/api/auth/users",
                json={"username": "reviewer", "password": PASSWORD},
                headers=ORIGIN,
            )
        ).status_code == 400
        await client.post("/api/auth/logout", headers=ORIGIN)
        assert (
            await client.post(
                "/api/auth/login",
                json={"username": "reviewer", "password": "incorrect-password"},
                headers=ORIGIN,
            )
        ).status_code == 401
        assert (
            await client.post(
                "/api/auth/login",
                json={"username": "reviewer", "password": PASSWORD},
                headers=ORIGIN,
            )
        ).status_code == 200
        assert (await client.get("/api/auth/users")).status_code == 403
        response = await client.post(
            f"/api/pipeline/{run}/packages/cost/review",
            json={"action": "approve", "reason": "Reviewed", "reviewer_name": "forged"},
            headers=ORIGIN,
        )
        assert response.status_code == 200
        result = (await client.get(f"/api/pipeline/{run}/results")).json()
        assert result["packages"][0]["review_decision"]["user_id"] == user_id
        assert result["packages"][0]["review_decision"]["reviewer_name"] == "Reviewer"
        assert PASSWORD not in str(result)
        token = client.cookies.get("infraarch_session")
        assert (
            await client.post(
                "/api/auth/password",
                json={"current_password": PASSWORD, "password": PASSWORD + "-new"},
                headers=ORIGIN,
            )
        ).status_code == 200
        assert (await client.get(f"/api/pipeline/{run}/results")).status_code == 401
        client.cookies.set("infraarch_session", token)
        assert (await client.get("/api/auth/session")).json()["authenticated"] is False


@pytest.mark.req("NFR-01")
def test_hash_salt_parameters():
    one, two = hash_password(PASSWORD), hash_password(PASSWORD)
    assert one != two and one.startswith("scrypt$32768$8$1$")
    assert verify_password(PASSWORD, one)
    assert not verify_password("wrong", one)
    assert not verify_password(PASSWORD, "invalid")
