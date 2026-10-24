"""NFR-01: cookie/session/CSRF checks against real PostgreSQL, no real keys."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr

from app.core.auth import COOKIE_NAME, token_hash
from app.db.models import AuthSession
from tests.integration.test_pipeline_review import pending_app, review_url

KEY = "phase9g-auth-test-only"
ORIGIN = {"Origin": "http://127.0.0.1"}


async def authenticated(engine, **settings):
    app, run = await pending_app(engine, blocking=True)
    configured = app.state.settings.model_copy(
        update={"api_key": SecretStr(KEY), **settings}
    )
    app.state.settings = configured
    app.state.auth.settings = configured
    return app, run


def client(app):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
    )


@pytest.mark.req("NFR-01", "FR-P-04", "FR-UI-06")
async def test_cookie_login_sse_download_logout_header_and_canary(db_engines, caplog):
    app, run = await authenticated(db_engines[0])
    async with client(app) as c:
        assert not (await c.get("/api/auth/session")).json()["authenticated"]
        response = await c.post(
            "/api/auth/login", json={"api_key": KEY}, headers=ORIGIN
        )
        assert response.status_code == 200
        cookie = response.headers["set-cookie"]
        for expected in ["HttpOnly", "SameSite=strict", "Path=/api"]:
            assert expected in cookie
        assert KEY not in cookie and KEY not in response.text
        raw = c.cookies[COOKIE_NAME]
        async with app.state.session_factory() as session:
            row = await session.get(AuthSession, token_hash(raw))
            assert row is not None and row.token_hash != raw
        assert (await c.get(f"/api/pipeline/{run}/stream")).status_code == 200
        body = {
            "action": "approve",
            "reviewer_name": "Ada",
            "category": "other",
            "reason": "Reviewed risks",
        }
        assert (await c.post(review_url(run), json=body)).status_code == 403
        assert (
            await c.post(
                review_url(run), json=body, headers={"Origin": "https://evil.invalid"}
            )
        ).status_code == 403
        assert (
            await c.post(review_url(run), json=body, headers=ORIGIN)
        ).status_code == 200
        assert (await c.get(f"/api/pipeline/{run}/download/cost")).status_code == 200
        assert (await c.post("/api/auth/logout", headers=ORIGIN)).status_code == 200
        c.cookies.set(COOKIE_NAME, raw)
        assert (await c.get(f"/api/pipeline/{run}/results")).status_code == 401
        assert (
            await c.get(f"/api/pipeline/{run}/results", headers={"X-API-Key": KEY})
        ).status_code == 200
        assert KEY not in caplog.text


@pytest.mark.req("NFR-01")
async def test_failures_rate_limit_and_tampering(db_engines):
    app, run = await authenticated(db_engines[0])
    async with client(app) as c:
        assert (
            await c.post("/api/auth/login", json={"api_key": KEY})
        ).status_code == 403
        for _ in range(5):
            response = await c.post(
                "/api/auth/login", json={"api_key": "wrong"}, headers=ORIGIN
            )
            assert response.status_code == 401 and "wrong" not in response.text
        response = await c.post(
            "/api/auth/login", json={"api_key": KEY}, headers=ORIGIN
        )
        assert response.status_code == 429 and response.headers["retry-after"] == "60"
        c.cookies.set(COOKIE_NAME, "tampered")
        assert (await c.get(f"/api/pipeline/{run}/results")).status_code == 401


@pytest.mark.req("NFR-01", "FR-P-04")
async def test_activity_renews_idle_but_never_absolute_expiry(db_engines):
    app, run = await authenticated(
        db_engines[0], auth_idle_seconds=10, auth_absolute_seconds=30
    )
    now = [datetime.now(UTC)]
    app.state.auth.clock = lambda: now[0]
    async with client(app) as c:
        await c.post("/api/auth/login", json={"api_key": KEY}, headers=ORIGIN)
        digest = token_hash(c.cookies[COOKIE_NAME])
        # SSE emits/heartbeats call exactly this atomic activity operation.
        for _ in range(3):
            now[0] += timedelta(seconds=9)
            assert await app.state.auth.activity(digest) is not None
        now[0] += timedelta(seconds=3)
        assert await app.state.auth.activity(digest) is None
        assert (await c.get(f"/api/pipeline/{run}/results")).status_code == 401
        await c.post("/api/auth/login", json={"api_key": KEY}, headers=ORIGIN)
        now[0] += timedelta(seconds=10)
        assert (await c.get(f"/api/pipeline/{run}/results")).status_code == 401


@pytest.mark.req("NFR-01")
async def test_secure_cookie_and_local_session_status(db_engines):
    app, _ = await authenticated(db_engines[0], auth_cookie_secure=True)
    async with client(app) as c:
        response = await c.post(
            "/api/auth/login", json={"api_key": KEY}, headers=ORIGIN
        )
        assert "Secure" in response.headers["set-cookie"]
        app.state.auth.settings = app.state.settings.model_copy(
            update={"api_key": None}
        )
        status = (await c.get("/api/auth/session")).json()
        assert (
            status["mode"] == "local"
            and status["message"] == "No authentication (local mode)"
        )


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("host", [None, "0.0.0.0", "::", "192.0.2.1"])
def test_unset_key_refuses_unknown_or_nonlocal_bind(monkeypatch, host):
    from app.core import bind

    monkeypatch.setattr(bind, "validated_open_bind", host)
    with pytest.raises(RuntimeError, match="127.0.0.1"):
        bind.check_open_bind(None)
    # Direct uvicorn/debugpy startup remains unrestricted when a key is set.
    bind.check_open_bind(SecretStr(KEY))


@pytest.mark.req("NFR-01", "FR-P-04")
async def test_sse_events_refresh_activity_and_stop_on_revocation(db_engines):
    app, run = await authenticated(db_engines[0], auth_idle_seconds=10)
    now = [datetime.now(UTC)]
    app.state.auth.clock = lambda: now[0]
    async with client(app) as c:
        await c.post("/api/auth/login", json={"api_key": KEY}, headers=ORIGIN)
        raw = c.cookies[COOKIE_NAME]
        original = app.state.auth.activity
        calls = [0]

        async def watching(digest):
            calls[0] += 1
            now[0] += timedelta(seconds=9)
            return await original(digest)

        app.state.auth.activity = watching
        response = await c.get(f"/api/pipeline/{run}/stream")
        assert response.status_code == 200 and calls[0] > 3
        assert '"status": "partial_success"' in response.text
        calls[0] = 0

        async def revoke_while_watching(digest):
            calls[0] += 1
            if calls[0] == 3:
                await app.state.auth.revoke(raw)
            return await original(digest)

        app.state.auth.activity = revoke_while_watching
        stopped = await c.get(f"/api/pipeline/{run}/stream")
        assert '"status": "partial_success"' not in stopped.text
        assert calls[0] == 3


@pytest.mark.req("NFR-01", "FR-P-04")
async def test_idle_stream_heartbeats_keep_session_alive(db_engines):
    from fastapi import Request

    from app.api.pipeline import stream_run

    app, run = await authenticated(db_engines[0], auth_idle_seconds=10)
    app.state.settings = app.state.settings.model_copy(
        update={"sse_keepalive_seconds": 0.01}
    )
    now = [datetime.now(UTC)]
    app.state.auth.clock = lambda: now[0]
    async with client(app) as c:
        await c.post("/api/auth/login", json={"api_key": KEY}, headers=ORIGIN)
        raw = c.cookies[COOKIE_NAME]
    request = Request(
        {
            "type": "http",
            "app": app,
            "headers": [],
            "state": {"session_hash": token_hash(raw)},
        }
    )
    # Keep the event-history prerequisite unsettled without modifying persisted data.
    response = await stream_run(
        str(run), request, app.state.event_log, app.state.broker, None
    )
    iterator = response.body_iterator
    # This fixture is settled, so use a fresh active run instead for idle heartbeats.
    from app.db.repositories.runs import RunRepository
    from app.domain.enums import LLMProvider

    async with app.state.session_factory() as session, session.begin():
        fresh = await RunRepository(session).create(
            "Deploy AWS service", LLMProvider.STUB, 1
        )
        active_id = fresh.run_id
    await iterator.aclose()
    response = await stream_run(
        str(active_id), request, app.state.event_log, app.state.broker, None
    )
    iterator = response.body_iterator
    for _ in range(3):
        now[0] += timedelta(seconds=9)
        assert await anext(iterator) == ": keepalive\n\n"
    await app.state.auth.revoke(raw)
    with pytest.raises(StopAsyncIteration):
        await anext(iterator)
    await iterator.aclose()


@pytest.mark.req("NFR-01")
async def test_configured_key_startup_needs_no_bind_context(db_engines, monkeypatch):
    from app.core import bind
    from app.core.config import get_settings
    from app.main import create_app

    monkeypatch.setattr(bind, "validated_open_bind", None)
    app = create_app(
        get_settings().model_copy(update={"api_key": SecretStr(KEY)}), db_engines[0]
    )
    async with app.router.lifespan_context(app):
        async with client(app) as c:
            assert (await c.get("/api/health")).status_code == 200


@pytest.mark.req("NFR-01")
async def test_originless_header_scripts_can_login_logout_but_bad_origins_fail(
    db_engines,
):
    app, _ = await authenticated(db_engines[0])
    async with client(app) as c:
        headers = {"X-API-Key": KEY}
        assert (
            await c.post("/api/auth/login", json={"api_key": KEY}, headers=headers)
        ).status_code == 200
        assert (await c.post("/api/auth/logout", headers=headers)).status_code == 200
        headers["Origin"] = "https://evil.invalid"
        assert (
            await c.post("/api/auth/login", json={"api_key": KEY}, headers=headers)
        ).status_code == 403
        assert (await c.post("/api/auth/logout", headers=headers)).status_code == 403


@pytest.mark.req("NFR-01", "FR-P-04")
async def test_sse_disconnect_finishes_owned_session_renewal(db_engines, monkeypatch):
    import anyio

    from app.db.repositories.sessions import SessionRepository

    app, _ = await authenticated(db_engines[0])
    token = await app.state.auth.login()
    entered, release, finished = anyio.Event(), anyio.Event(), anyio.Event()
    original = SessionRepository.touch
    completed = []
    holder = []

    async def blocked(*args):
        value = await original(*args)
        entered.set()
        await release.wait()
        completed.append(value is not None)
        return value

    async def watch():
        try:
            with anyio.CancelScope() as scope:
                holder.append(scope)
                await app.state.auth.activity(token_hash(token))
                await anyio.lowlevel.checkpoint()
        finally:
            finished.set()

    monkeypatch.setattr(SessionRepository, "touch", blocked)
    async with anyio.create_task_group() as group:
        group.start_soon(watch)
        with anyio.fail_after(3):
            await entered.wait()
        holder[0].cancel()
        release.set()
        with anyio.fail_after(3):
            await finished.wait()
    assert completed == [True]
    assert app.state.engine.sync_engine.pool.checkedout() == 0
