"""FR-S-08/10: approval is evidence-bearing and never claims passed checks."""

from io import BytesIO
from zipfile import ZipFile

import pytest

from tests.integration.test_pipeline_review import client_for, pending_app, review_url


@pytest.mark.req("FR-S-08", "FR-S-10", "FR-UI-06")
@pytest.mark.parametrize("action", ["approve", "reject"])
async def test_decision_provenance_and_failed_checks_everywhere(db_engines, action):
    app, run_id = await pending_app(db_engines[0], blocking=True)
    async with client_for(app) as client:
        for name, reason in [("", "reason"), ("Engineer", "  ")]:
            response = await client.post(
                review_url(run_id),
                json={"action": action, "reviewer_name": name, "reason": reason},
            )
            assert response.status_code == 400
        response = await client.post(
            review_url(run_id),
            json={
                "action": action,
                "reviewer_name": " Ada ",
                "reason": " Explicitly accept remaining risks ",
            },
        )
        assert response.json()["status"] == (
            "engineer_approved" if action == "approve" else "rejected"
        )
        result = (await client.get(f"/api/pipeline/{run_id}/results")).json()[
            "packages"
        ][0]
        assert result["readiness_label"] != "checks_passed"
        assert result["review_decision"]["reviewer_name"] == "Ada"
        assert (
            result["review_decision"]["reason"] == "Explicitly accept remaining risks"
        )
        assert result["security_report"]["final"]["remaining_blocking"]
        assert result["validation_report"]["summary"]["result"] == "invalid"
        response = await client.get(f"/api/pipeline/{run_id}/download/cost")
        with ZipFile(BytesIO(response.content)) as archive:
            text = archive.read("INFRAARCHAGENT_READINESS.md").decode()
        for expected in [
            "Ada",
            "Explicitly accept remaining risks",
            "reference.test",
            "CKV_1",
            "No label implies a successful cloud deployment",
        ]:
            assert expected in text
        events = (await client.get(f"/api/pipeline/{run_id}/stream")).text
        assert '"reviewer_name": "Ada"' in events
        assert '"status": "checks_passed"' not in events


@pytest.mark.req("FR-S-08", "FR-S-10")
async def test_legacy_migration_preserves_events_and_counts(db_engines, monkeypatch):
    import importlib.util
    import json
    from datetime import UTC, datetime
    from pathlib import Path
    from uuid import uuid4

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import text

    path = (
        Path(__file__).resolve().parents[2]
        / "app/db/migrations/versions/0004_honest_labels.py"
    )
    spec = importlib.util.spec_from_file_location("migration_labels", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    async with db_engines[1].begin() as connection:
        await connection.execute(
            text(
                "CREATE TEMP TABLE generated_packages (package_id uuid, run_id uuid, "
                "variant text, status text, security_report jsonb, validation_report "
                "jsonb, review_feedback text, CONSTRAINT ck_package_status CHECK "
                "(status IN ('production_ready','not_production_ready'))) ON COMMIT "
                "DROP"
            )
        )
        await connection.execute(
            text(
                "CREATE TEMP TABLE agent_events (seq bigint, run_id uuid, timestamp "
                "timestamptz, payload jsonb, new_state text) ON COMMIT DROP"
            )
        )
        for index, kind in enumerate(["automatic", "approve", "reject", "unknown"], 1):
            run = uuid4()
            status = "not_production_ready" if kind == "reject" else "production_ready"
            await connection.execute(
                text(
                    "INSERT INTO generated_packages VALUES "
                    "(:id,:run,'cost',:status,CAST(:security AS jsonb),"
                    "CAST(:validation AS "
                    "jsonb),'legacy reason')"
                ),
                {
                    "id": uuid4(),
                    "run": run,
                    "status": status,
                    "security": json.dumps(
                        {"final": {"outcome": "clean", "remaining_blocking": []}}
                    )
                    if kind == "automatic"
                    else None,
                    "validation": json.dumps({"summary": {"result": "valid"}})
                    if kind == "automatic"
                    else None,
                },
            )
            await connection.execute(
                text(
                    "INSERT INTO agent_events VALUES (:seq,:run,:now,CAST(:payload AS "
                    "jsonb),:status)"
                ),
                {
                    "seq": index,
                    "run": run,
                    "now": datetime.now(UTC),
                    "payload": json.dumps(
                        {
                            "kind": "package_status",
                            "variant": "cost",
                            **(
                                {"review_action": kind}
                                if kind in {"approve", "reject"}
                                else {}
                            ),
                        }
                    ),
                    "status": status,
                },
            )
        before = (
            await connection.execute(text("SELECT * FROM agent_events ORDER BY seq"))
        ).all()

        def upgrade(sync):
            monkeypatch.setattr(
                migration, "op", Operations(MigrationContext.configure(sync))
            )
            migration.upgrade()

        await connection.run_sync(upgrade)
        rows = (
            await connection.execute(
                text("SELECT status, review_decision FROM generated_packages")
            )
        ).all()
        assert {r.status for r in rows} == {
            "checks_passed",
            "engineer_approved",
            "rejected",
            "pending_review",
        }
        decision = next(
            r.review_decision for r in rows if r.status == "engineer_approved"
        )
        assert (
            decision["reason"] == "legacy reason" and decision["reviewer_name"] is None
        )
        assert (
            await connection.execute(text("SELECT * FROM agent_events ORDER BY seq"))
        ).all() == before


@pytest.mark.req("FR-S-08", "FR-P-04")
async def test_ambiguous_legacy_sse_closes_without_claiming_passed_checks(
    db_engines, monkeypatch
):
    import asyncio

    from app.domain.enums import AgentName
    from app.events import log

    app, run_id = await pending_app(db_engines[0], blocking=True)
    monkeypatch.setattr(log, "STATE_VALUES", log.STATE_VALUES | {"production_ready"})
    await app.state.event_log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        "production_ready",
        previous_state="valid",
        payload={"kind": "package_status", "variant": "cost"},
    )
    async with client_for(app) as client:
        response = await asyncio.wait_for(
            client.get(f"/api/pipeline/{run_id}/stream"), 5
        )
    assert '"status": "checks_passed"' not in response.text
    assert '"status": "pending_review"' in response.text
    assert '"legacy_label_interpretation"' in response.text


@pytest.mark.req("FR-S-08", "FR-S-10")
async def test_legacy_reconciliation_requires_recorded_automatic_transition(
    db_engines, monkeypatch
):
    import importlib.util
    import json
    from pathlib import Path
    from uuid import uuid4

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import text

    path = (
        Path(__file__).resolve().parents[2]
        / "app/db/migrations/versions/0007_legacy_label_provenance.py"
    )
    spec = importlib.util.spec_from_file_location("migration_provenance", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    async with db_engines[1].begin() as connection:
        await connection.execute(
            text(
                "CREATE TEMP TABLE generated_packages (package_id uuid,run_id uuid,"
                "variant text,status text) ON COMMIT DROP"
            )
        )
        await connection.execute(
            text(
                "CREATE TEMP TABLE agent_events (seq bigint,run_id uuid,"
                "new_state text,previous_state text,payload jsonb) ON COMMIT DROP"
            )
        )
        for index, kind in enumerate(
            ["automatic", "modern", "approve", "missing", "unknown", "contradiction"]
        ):
            run = uuid4()
            status = "engineer_approved" if kind == "approve" else "checks_passed"
            await connection.execute(
                text("INSERT INTO generated_packages VALUES (:id,:run,'cost',:status)"),
                {"id": uuid4(), "run": run, "status": status},
            )
            if kind != "missing":
                await connection.execute(
                    text(
                        "INSERT INTO agent_events VALUES "
                        "(:seq,:run,:state,:previous,CAST(:payload AS jsonb))"
                    ),
                    {
                        "seq": index,
                        "run": run,
                        "state": "checks_passed"
                        if kind == "modern"
                        else "production_ready",
                        "previous": None if kind == "unknown" else "valid",
                        "payload": json.dumps(
                            {
                                "kind": "package_status",
                                "variant": "cost",
                                **(
                                    {"review_action": "approve"}
                                    if kind in {"approve", "contradiction"}
                                    else {}
                                ),
                            }
                        ),
                    },
                )
        before = (
            await connection.execute(text("SELECT * FROM agent_events ORDER BY seq"))
        ).all()

        def upgrade(sync):
            monkeypatch.setattr(
                migration, "op", Operations(MigrationContext.configure(sync))
            )
            migration.upgrade()

        await connection.run_sync(upgrade)
        counts = dict(
            (
                await connection.execute(
                    text(
                        "SELECT status,count(*) FROM generated_packages GROUP BY status"
                    )
                )
            ).all()
        )
        assert counts == {
            "checks_passed": 2,
            "engineer_approved": 1,
            "pending_review": 3,
        }
        assert (
            await connection.execute(text("SELECT * FROM agent_events ORDER BY seq"))
        ).all() == before
