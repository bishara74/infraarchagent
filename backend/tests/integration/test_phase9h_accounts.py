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
        from tests.integration.test_phase9g_auth import KEY

        denied_name = await client.post(
            "/api/auth/users",
            json={"username": KEY, "password": PASSWORD},
            headers=ORIGIN,
        )
        assert denied_name.status_code == 400 and KEY not in denied_name.text
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
            json={
                "action": "approve",
                "category": "other",
                "reason": "Reviewed",
                "reviewer_name": "forged",
            },
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


@pytest.mark.req("NFR-01")
async def test_concurrent_setup_and_disabled_user(db_engines):
    import asyncio

    from sqlalchemy import func, select

    from app.db.models import User
    from tests.integration.test_phase9g_auth import KEY

    app, run = await authenticated(db_engines[0])
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 321))
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1", headers=ORIGIN
    ) as client:
        responses = await asyncio.gather(
            *(
                client.post(
                    "/api/auth/setup", json={"username": name, "password": PASSWORD}
                )
                for name in ("first", "second")
            )
        )
        assert sorted(r.status_code for r in responses) == [200, 409]
        async with app.state.session_factory() as session:
            assert await session.scalar(select(func.count()).select_from(User)) == 1
        admin_headers = {**ORIGIN, "X-API-Key": KEY}
        response = await client.post(
            "/api/auth/users",
            json={"username": "reviewer", "password": PASSWORD},
            headers=admin_headers,
        )
        user_id = response.json()["id"]
        await client.post("/api/auth/logout")
        assert (
            await client.post(
                "/api/auth/login", json={"username": "reviewer", "password": PASSWORD}
            )
        ).status_code == 200
        assert (
            await client.post(
                f"/api/auth/users/{user_id}/disable", headers=admin_headers
            )
        ).status_code == 200
        assert (await client.get(f"/api/pipeline/{run}/results")).status_code == 401
        denied = await client.post(
            "/api/auth/login", json={"username": "reviewer", "password": PASSWORD}
        )
        assert (
            denied.status_code == 401
            and denied.json()["message"] == "Invalid username or password."
        )


@pytest.mark.req("NFR-01", "FR-P-04")
async def test_bootstrap_closes_existing_anonymous_stream(db_engines):
    from fastapi import Request

    from app.api.pipeline import stream_run
    from app.db.repositories.runs import RunRepository
    from app.db.repositories.users import UserRepository
    from app.domain.enums import LLMProvider
    from tests.integration.test_pipeline_review import pending_app

    app, _ = await pending_app(db_engines[0])
    app.state.settings = app.state.settings.model_copy(
        update={"sse_keepalive_seconds": 0.01}
    )
    async with app.state.session_factory() as session, session.begin():
        run = await RunRepository(session).create(
            "Deploy an AWS web service", LLMProvider.STUB, 1
        )
    request = Request(
        {
            "type": "http",
            "app": app,
            "headers": [],
            "state": {"auth_mode": "local", "session_hash": None},
        }
    )
    response = await stream_run(
        str(run.run_id), request, app.state.event_log, app.state.broker, None
    )
    iterator = response.body_iterator
    assert await anext(iterator) == ": keepalive\n\n"
    async with app.state.session_factory() as session, session.begin():
        await UserRepository(session).create(
            "admin", hash_password(PASSWORD), first=True
        )
    with pytest.raises(StopAsyncIteration):
        await anext(iterator)
    await iterator.aclose()
