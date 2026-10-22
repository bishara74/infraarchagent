"""NFR-01: public account metadata and admin-only enable without session revival."""

from datetime import datetime
from uuid import uuid4

import httpx
import pytest

from tests.integration.test_phase9g_auth import KEY, authenticated
from tests.integration.test_phase9h_accounts import ORIGIN, PASSWORD


def connection(app):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=("127.0.0.1", 123)),
        base_url="http://127.0.0.1",
        headers=ORIGIN,
    )


async def admin_and_reviewer(app, client):
    await client.post(
        "/api/auth/setup", json={"username": "admin", "password": PASSWORD}
    )
    response = await client.post(
        "/api/auth/users", json={"username": "reviewer", "password": PASSWORD}
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.req("NFR-01", "FR-UI-07")
async def test_account_public_metadata_and_no_secrets(db_engines):
    app, _ = await authenticated(db_engines[0])
    async with connection(app) as admin:
        reviewer_id = await admin_and_reviewer(app, admin)
        me = (await admin.get("/api/auth/session")).json()["user"]
        assert set(me) == {"id", "username", "role", "created_at", "last_login_at"}
        assert me["last_login_at"] is None
        assert datetime.fromisoformat(me["created_at"]).tzinfo is not None
        response = await admin.get("/api/auth/users")
        rows = response.json()
        assert all(
            set(row)
            == {"id", "username", "role", "disabled", "created_at", "last_login_at"}
            for row in rows
        )
        assert (
            next(row for row in rows if row["id"] == reviewer_id)["last_login_at"]
            is None
        )
        async with connection(app) as reviewer:
            await reviewer.post(
                "/api/auth/login", json={"username": "reviewer", "password": PASSWORD}
            )
            response = await reviewer.get("/api/auth/session")
            own = response.json()["user"]
            assert own["id"] == reviewer_id and own["role"] == "reviewer"
            assert datetime.fromisoformat(own["last_login_at"]).tzinfo is not None
            assert (
                "scrypt$" not in response.text
                and PASSWORD not in response.text
                and KEY not in response.text
            )
        response = await admin.get("/api/auth/users")
        assert (
            "scrypt$" not in response.text
            and PASSWORD not in response.text
            and KEY not in response.text
        )
        assert (
            next(row for row in response.json() if row["id"] == reviewer_id)[
                "last_login_at"
            ]
            is not None
        )


@pytest.mark.req("NFR-01")
async def test_enable_reviewer_requires_fresh_login_and_never_revives_sessions(
    db_engines,
):
    app, _ = await authenticated(db_engines[0])
    async with connection(app) as admin, connection(app) as reviewer:
        identity = await admin_and_reviewer(app, admin)
        assert (
            await reviewer.post(
                "/api/auth/login", json={"username": "reviewer", "password": PASSWORD}
            )
        ).status_code == 200
        old = reviewer.cookies.get("infraarch_session")
        assert (await admin.post(f"/api/auth/users/{identity}/disable")).json() == {
            "updated": True
        }
        assert (await reviewer.get("/api/models")).status_code == 401
        assert (
            await reviewer.post(
                "/api/auth/login", json={"username": "reviewer", "password": PASSWORD}
            )
        ).status_code == 401
        assert (await admin.post(f"/api/auth/users/{identity}/enable")).json() == {
            "updated": True
        }
        reviewer.cookies.clear()
        reviewer.cookies.set("infraarch_session", old)
        assert (await reviewer.get("/api/auth/session")).json()[
            "authenticated"
        ] is False
        assert (await reviewer.get("/api/models")).status_code == 401
        reviewer.cookies.clear()
        assert (
            await reviewer.post(
                "/api/auth/login", json={"username": "reviewer", "password": PASSWORD}
            )
        ).status_code == 200
        assert reviewer.cookies.get("infraarch_session") != old
        assert (await reviewer.get("/api/models")).status_code == 200
        admin_id = (await admin.get("/api/auth/session")).json()["user"]["id"]
        assert (await admin.post(f"/api/auth/users/{admin_id}/enable")).json() == {
            "updated": False
        }
        assert (await admin.post(f"/api/auth/users/{uuid4()}/enable")).json() == {
            "updated": False
        }
        # Repeated enable leaves the newly issued session intact too.
        assert (await admin.post(f"/api/auth/users/{identity}/enable")).json() == {
            "updated": True
        }
        assert (await reviewer.get("/api/models")).status_code == 200


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("role", ["anonymous", "reviewer"])
async def test_every_user_management_operation_is_admin_only(db_engines, role):
    app, _ = await authenticated(db_engines[0])
    async with connection(app) as admin, connection(app) as denied:
        identity = await admin_and_reviewer(app, admin)
        if role == "reviewer":
            await denied.post(
                "/api/auth/login", json={"username": "reviewer", "password": PASSWORD}
            )
        expected = 403 if role == "reviewer" else 401
        responses = [await denied.get("/api/auth/users")]
        responses.append(
            await denied.post(
                "/api/auth/users", json={"username": "extra", "password": PASSWORD}
            )
        )
        for action in ("password", "disable", "enable"):
            responses.append(
                await denied.post(
                    f"/api/auth/users/{identity}/{action}", json={"password": PASSWORD}
                )
            )
        for response in responses:
            assert response.status_code == expected
            assert PASSWORD not in response.text and "scrypt$" not in response.text
        assert (await admin.get("/api/auth/users")).json()[1]["disabled"] is False
