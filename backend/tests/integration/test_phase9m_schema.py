"""NFR-01: schema incompatibility blocks API dependencies without migrations."""

import logging
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.db.repositories.runs import RunRepository
from app.db.schema import migration_graph, schema_status
from app.main import create_app

pytestmark = pytest.mark.req("NFR-01")


@pytest.mark.parametrize(
    "revision", ["0012_inspection_role", "9999_future", "unknown", ""]
)
async def test_mismatch_blocks_every_api_before_auth_and_keeps_health_ui(
    db_engines, tmp_path, caplog, monkeypatch, revision
):
    engine, owner = db_engines
    expected = migration_graph().get_current_head()
    async with owner.begin() as connection:
        await connection.execute(text("DELETE FROM alembic_version"))
        if revision:
            await connection.execute(
                text("INSERT INTO alembic_version VALUES (:value)"), {"value": revision}
            )
    try:
        (tmp_path / "index.html").write_text("<html>synthetic UI</html>")
        app = create_app(get_settings(), engine, frontend_dist=tmp_path)
        auth = AsyncMock(side_effect=AssertionError("normal API dependency called"))
        monkeypatch.setattr(app.state.auth, "has_users", auth)
        recovery = AsyncMock(
            side_effect=AssertionError("recovery queried incompatible schema")
        )
        monkeypatch.setattr(RunRepository, "list_interrupted", recovery)
        with caplog.at_level(logging.ERROR, logger="app.core.schema_gate"):
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    for method, path in [
                        ("GET", "/api/auth/session"),
                        ("GET", "/api/me/preferences"),
                        ("POST", "/api/pipeline/run"),
                        ("GET", "/api/unknown"),
                    ]:
                        response = await client.request(method, path)
                        assert response.status_code == 503
                        assert response.json()["error"] == "database_schema_mismatch"
                        assert response.json()["expected_revision"] == expected
                        assert (
                            "make migrate" in response.json()["message"]
                            if revision in {"0012_inspection_role", ""}
                            else "matching code" in response.json()["message"]
                        )
                    for _ in range(2):
                        health = await client.get("/api/health")
                        assert (
                            health.status_code == 503
                            and not health.json()["schema"]["compatible"]
                        )
                    assert (await client.get("/")).status_code == 200
        assert (
            len([row for row in caplog.records if row.name == "app.core.schema_gate"])
            == 1
        )
        auth.assert_not_called()
        recovery.assert_not_called()
    finally:
        async with owner.begin() as connection:
            await connection.execute(text("DELETE FROM alembic_version"))
            await connection.execute(
                text("INSERT INTO alembic_version VALUES (:value)"), {"value": expected}
            )


async def test_current_schema_and_health_are_ready(db_engines):
    engine, _ = db_engines
    status = await schema_status(engine)
    assert status.compatible and status.current == status.expected
    app = create_app(get_settings(), engine)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            health = (await client.get("/api/health")).json()
            assert health["schema"]["compatible"] and health["status"] == "ok"
            assert (await client.get("/api/auth/session")).status_code == 200


async def test_missing_unreadable_and_multiple_revisions_are_closed(db_engines):
    engine, owner = db_engines
    async with owner.begin() as connection:
        await connection.execute(
            text("ALTER TABLE alembic_version RENAME TO phase9m_hidden_version")
        )
    try:
        assert (await schema_status(engine)).state == "missing"
    finally:
        async with owner.begin() as connection:
            await connection.execute(
                text("ALTER TABLE phase9m_hidden_version RENAME TO alembic_version")
            )
    async with owner.begin() as connection:
        await connection.execute(
            text("REVOKE SELECT ON alembic_version FROM infraarch_app")
        )
    try:
        status = await schema_status(engine)
        assert status.state == "unreadable" and "make migrate" in status.message
    finally:
        async with owner.begin() as connection:
            await connection.execute(
                text("GRANT SELECT ON alembic_version TO infraarch_app")
            )
    async with owner.begin() as connection:
        await connection.execute(
            text("INSERT INTO alembic_version VALUES ('other_branch')")
        )
    try:
        assert not (await schema_status(engine)).compatible
    finally:
        async with owner.begin() as connection:
            await connection.execute(
                text("DELETE FROM alembic_version WHERE version_num='other_branch'")
            )


async def test_after_migration_requires_restart_before_recovery(
    db_engines, monkeypatch
):
    engine, _ = db_engines
    from app.core import schema_gate
    from app.db.schema import SchemaStatus

    expected = migration_graph().get_current_head()
    probe = AsyncMock(return_value=SchemaStatus("0013_lessons", expected, "behind"))
    monkeypatch.setattr(schema_gate, "schema_status", probe)
    app = create_app(get_settings(), engine)
    async with app.router.lifespan_context(app):
        probe.return_value = SchemaStatus(expected, expected, "current")
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            health = await client.get("/api/health")
            assert health.status_code == 503
            assert health.json()["schema"]["restart_required"]
            assert (await client.get("/api/auth/session")).status_code == 503
