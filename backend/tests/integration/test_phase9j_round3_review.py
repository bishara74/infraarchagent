"""FR-S-08/10, FR-UI-07 and NFR-01: categories and retained admin history."""

import asyncio
import csv
import io
from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZipFile

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import delete

from app.db.models import GeneratedPackage
from app.db.session import make_session_factory
from app.domain.enums import AgentName, PackageStatus, Variant
from app.domain.review_categories import CATEGORIES
from app.events.kinds import package_status_payload
from tests.integration.test_phase9g_auth import KEY, authenticated
from tests.integration.test_phase9h_accounts import ORIGIN, PASSWORD
from tests.integration.test_pipeline_review import (
    client_for,
    pending_app,
    review_url,
    state,
)


@pytest.mark.req("FR-S-08", "FR-S-10", "FR-UI-07")
@pytest.mark.parametrize("category", CATEGORIES)
@pytest.mark.parametrize("action", ["approve", "reject"])
async def test_categories_persist_in_results_events_and_archive(
    db_engines, category, action
):
    app, run = await pending_app(db_engines[0])
    async with client_for(app) as client:
        response = await client.post(
            review_url(run),
            json={
                "action": action,
                "reviewer_name": "Engineer",
                "reason": "Engineering judgement",
                "category": category,
            },
        )
        assert response.status_code == 200
        item = (await client.get(f"/api/pipeline/{run}/results")).json()["packages"][0]
        assert item["review_decision"]["category"] == category
        archive = await client.get(f"/api/pipeline/{run}/download/cost")
        with ZipFile(BytesIO(archive.content)) as zipped:
            document = zipped.read("INFRAARCHAGENT_READINESS.md").decode()
            assert f"Category: {category}" in document
            assert "Reason: Engineering judgement" in document
            assert (
                zipped.read("terraform/main.tf").decode()
                == item["files"]["terraform/main.tf"]
            )
        assert (
            await client.get(f"/api/pipeline/{run}/download/cost")
        ).content == archive.content
    event = (await app.state.event_log.list_after(run, None))[-1]
    assert event.payload["review_decision"]["category"] == category
    assert not app.state.runner.tasks


@pytest.mark.req("FR-S-08", "FR-S-10")
@pytest.mark.parametrize("category", [None, "", "invented", 3])
@pytest.mark.parametrize("action", ["approve", "reject"])
async def test_categories_required_and_fixed(db_engines, category, action):
    app, run = await pending_app(db_engines[0])
    body = {"action": action, "reviewer_name": "Engineer", "reason": "Reviewed"}
    if category is not None:
        body["category"] = category
    async with client_for(app) as client:
        assert (await client.post(review_url(run), json=body)).status_code == 400
    assert (await state(app, run))[1].status == "pending_review"


@pytest.mark.req("FR-S-10", "FR-UI-06", "FR-UI-07")
async def test_checks_passed_only_allows_rejection_preserving_reports(db_engines):
    app, run = await pending_app(db_engines[0], result="valid", checks_passed=True)
    async with client_for(app) as client:
        before = (await client.get(f"/api/pipeline/{run}/results")).json()["packages"][
            0
        ]
        assert before["review_available"] is False and before["review_actions"] == [
            "reject"
        ]
        body = {
            "reviewer_name": "Engineer",
            "reason": "Too expensive",
            "category": "too_expensive",
        }
        for action in ("approve", "retry"):
            assert (
                await client.post(review_url(run), json={**body, "action": action})
            ).status_code == 409
        responses = await asyncio.gather(
            *(
                client.post(review_url(run), json={**body, "action": "reject"})
                for _ in range(2)
            )
        )
        assert sorted(r.status_code for r in responses) == [200, 409]
        after = (await client.get(f"/api/pipeline/{run}/results")).json()["packages"][0]
        assert after["readiness_label"] == "rejected" and after["downloadable"]
        for key in ("files", "original_files", "security_report", "validation_report"):
            assert after[key] == before[key]
        assert (await state(app, run))[0].status == "partial_success"


@pytest.mark.req("FR-UI-07", "NFR-01")
async def test_history_filters_pagination_export_redaction_and_retention(db_engines):
    app, run = await authenticated(db_engines[0])
    secret = "round3-history-synthetic-canary"
    app.state.settings = app.state.settings.model_copy(
        update={"llm_api_key": SecretStr(secret)}
    )
    for i in range(31):
        details = {
            "reviewer_name": "Engineer",
            "reason": "=2+3, " + secret,
            "password_hash": "must-never-export",
            "files": {"private.tf": "not exported"},
        }
        if i:
            details["category"] = "too_expensive"
        await app.state.event_log.append(
            run,
            AgentName.ORCHESTRATOR,
            PackageStatus.ENGINEER_APPROVED,
            PackageStatus.PENDING_REVIEW,
            payload={
                **package_status_payload(Variant.COST),
                "review_action": "approve",
                "review_decision": details,
            },
        )
    today = datetime.now(UTC).date().isoformat()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://127.0.0.1",
        headers={"X-API-Key": KEY},
    ) as client:
        response = await client.get("/api/reviews/history")
        assert response.status_code == 200
        first = response.json()
        assert first["total"] == 31 and len(first["items"]) == 25
        second = (await client.get("/api/reviews/history?page=2")).json()
        assert len(second["items"]) == 6
        assert first["items"][0]["timestamp"] >= second["items"][0]["timestamp"]
        filters = {
            "category": "too_expensive",
            "decision": "approve",
            "date_from": today,
            "date_to": today,
        }
        filtered = (await client.get("/api/reviews/history", params=filters)).json()
        assert filtered["total"] == 30
        export = await client.get(
            "/api/reviews/history/export", params={**filters, "format": "json"}
        )
        result = export.json()
        assert result["metadata"]["filters"] == filters
        assert result["metadata"]["count"] == len(result["decisions"]) == 30
        assert set(result["decisions"][0]) == {
            "run_id",
            "variant",
            "label_before",
            "label_after",
            "decision",
            "category",
            "reason",
            "reviewer",
            "timestamp",
        }
        for forbidden in (
            secret,
            "password_hash",
            "must-never-export",
            "private.tf",
            "files",
        ):
            assert forbidden not in export.text
        csv_response = await client.get(
            "/api/reviews/history/export", params={**filters, "format": "csv"}
        )
        assert csv_response.text.startswith("# schema_version: 1")
        assert (
            "# count: 30" in csv_response.text
            and '"category": "too_expensive"' in csv_response.text
        )
        records = list(
            csv.DictReader(
                io.StringIO(
                    "\n".join(
                        line
                        for line in csv_response.text.splitlines()
                        if not line.startswith("#")
                    )
                )
            )
        )
        assert len(records) == 30 and records[0]["reason"].startswith("'=2+3,")
        legacy = (await client.get("/api/reviews/history?category=not_recorded")).json()
        assert legacy["total"] == 1 and legacy["items"][0]["category"] is None
        assert (await client.get("/api/reviews/history?decision=reject")).json()[
            "total"
        ] == 0
        for query in (
            "category=bad",
            "decision=bad",
            "date_from=bad",
            "page=0",
            "date_from=2026-10-24&date_to=2026-10-01",
        ):
            assert (await client.get("/api/reviews/history?" + query)).status_code in {
                400,
                422,
            }
        assert (
            await client.get(
                "/api/reviews/history/export?date_from=2026-10-24&date_to=2026-10-01"
            )
        ).status_code == 400
        async with make_session_factory(db_engines[1])() as session, session.begin():
            await session.execute(
                delete(GeneratedPackage).where(GeneratedPackage.run_id == run)
            )
        assert (await client.get("/api/reviews/history")).json()["total"] == 31
        assert export.headers["cache-control"] == "no-store"


@pytest.mark.req("NFR-01", "FR-UI-07")
async def test_history_requires_admin_and_denies_reviewers(db_engines):
    app, _ = await authenticated(db_engines[0])
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=("127.0.0.1", 123)),
        base_url="http://127.0.0.1",
    ) as client:
        for path in (
            "/api/reviews/history",
            "/api/reviews/history/export?format=csv",
            "/api/reviews/history/export?format=json",
        ):
            assert (await client.get(path)).status_code == 401
        assert (
            await client.post(
                "/api/auth/setup",
                headers=ORIGIN,
                json={"username": "Admin", "password": PASSWORD},
            )
        ).status_code == 200
        assert (await client.get("/api/reviews/history")).status_code == 200
        assert (
            await client.post(
                "/api/auth/users",
                headers=ORIGIN,
                json={"username": "Reviewer", "password": PASSWORD},
            )
        ).status_code == 201
        await client.post("/api/auth/logout", headers=ORIGIN)
        await client.post(
            "/api/auth/login",
            headers=ORIGIN,
            json={"username": "Reviewer", "password": PASSWORD},
        )
        for path in (
            "/api/reviews/history",
            "/api/reviews/history/export?format=csv",
            "/api/reviews/history/export?format=json",
        ):
            assert (await client.get(path)).status_code == 403


@pytest.mark.req("FR-S-10", "FR-UI-07")
async def test_historical_category_is_null_without_rewriting_decision(db_engines):
    app, run = await pending_app(db_engines[0])
    legacy = {
        "action": "reject",
        "reviewer_name": "Legacy engineer",
        "reason": "Historical judgement",
        "identity_basis": "self-declared",
        "decided_at": datetime.now(UTC).isoformat(),
    }
    async with app.state.session_factory() as session, session.begin():
        from app.db.repositories.packages import PackageRepository

        row = await PackageRepository(session).get_for_update(run, Variant.COST)
        row.review_decision = legacy
        await app.state.writer.review_action(session, run, Variant.COST, "reject", None)
    async with client_for(app) as client:
        item = (await client.get(f"/api/pipeline/{run}/results")).json()["packages"][0]
        assert item["review_decision"]["category"] is None
        document = await client.get(f"/api/pipeline/{run}/download/cost")
        with ZipFile(BytesIO(document.content)) as zipped:
            assert (
                "Category: not recorded"
                in zipped.read("INFRAARCHAGENT_READINESS.md").decode()
            )
    assert "category" not in (await state(app, run))[1].review_decision
