"""FR-UI-01 / FR-P-04 preference authority, isolation and event hydration."""

import httpx
import pytest

from tests.integration.test_phase9g_auth import authenticated
from tests.integration.test_phase9h_accounts import ORIGIN, PASSWORD


@pytest.mark.req("NFR-01", "FR-UI-01", "FR-P-04")
async def test_authoritative_preferences_conflicts_and_history(db_engines):
    app, run = await authenticated(db_engines[0])
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 123))
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1", headers=ORIGIN
    ) as client:
        assert (
            await client.post(
                "/api/auth/setup", json={"username": "admin", "password": PASSWORD}
            )
        ).status_code == 200
        first = (await client.get("/api/me/preferences")).json()
        assert first == {"revision": 0, "data": {}}
        document = {
            "revision": 0,
            "data": {
                "prompt_draft": "Deploy an AWS web service",
                "role_defaults": {"generators": {"model": "stub"}},
                "ui": {"auto_scroll": False},
            },
        }
        assert (
            await client.put("/api/me/preferences", json=document)
        ).status_code == 200
        from datetime import datetime

        stamp = (await client.get("/api/me/preferences")).json()["updated_at"]
        assert datetime.fromisoformat(stamp).utcoffset() is not None
        assert (
            await client.put("/api/me/preferences", json=document)
        ).status_code == 409
        # Another browser gets the server copy, with no local storage dependency.
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1", headers=ORIGIN
        ) as other:
            await other.post(
                "/api/auth/login", json={"username": "admin", "password": PASSWORD}
            )
            saved = (await other.get("/api/me/preferences")).json()
            assert (
                saved["revision"] == 1
                and saved["data"]["prompt_draft"] == document["data"]["prompt_draft"]
            )
        assert (
            await client.put(f"/api/me/recent-runs/{run}", json={"seq": 2**31})
        ).status_code == 200
        recent = (await client.get("/api/me/recent-runs")).json()
        history = (
            await client.get(
                f"/api/pipeline/{run}/events?through={recent[0]['last_seq']}"
            )
        ).json()
        assert history["events"] and len({e["seq"] for e in history["events"]}) == len(
            history["events"]
        )
        assert recent[0]["last_seq"] == history["events"][-1]["seq"]
        bad = await client.put(
            "/api/me/preferences",
            json={"revision": 1, "data": {"password": "not-allowed"}},
        )
        assert bad.status_code == 400 and "not-allowed" not in bad.text
        await client.post(
            "/api/auth/users", json={"username": "reviewer", "password": PASSWORD}
        )
        await client.post("/api/auth/logout")
        await client.post(
            "/api/auth/login", json={"username": "reviewer", "password": PASSWORD}
        )
        assert (await client.get("/api/me/preferences")).json()["data"] == {}
        assert (await client.get("/api/me/recent-runs")).json() == []


@pytest.mark.req("FR-UI-01", "NFR-01")
async def test_discard_draft_is_durable_and_preserves_configuration(db_engines):
    app, _ = await authenticated(db_engines[0])
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 123))
    async with httpx.AsyncClient(
        transport=transport, base_url="http://127.0.0.1", headers=ORIGIN
    ) as client:
        await client.post(
            "/api/auth/setup", json={"username": "admin", "password": PASSWORD}
        )
        saved = await client.put(
            "/api/me/preferences",
            json={
                "revision": 0,
                "data": {
                    "prompt_draft": "Deploy an AWS web service",
                    "draft_config": {"max_iterations": 3},
                },
            },
        )
        document = saved.json()
        document["data"]["prompt_draft"] = ""
        discarded = await client.put(
            "/api/me/preferences",
            json={"revision": document["revision"], "data": document["data"]},
        )
        assert discarded.status_code == 200
        loaded = (await client.get("/api/me/preferences")).json()
        assert loaded == discarded.json()
        assert loaded["data"]["prompt_draft"] == ""
        assert loaded["data"]["draft_config"] == {"max_iterations": 3}
        assert loaded["updated_at"] >= document["updated_at"]
