"""FR-S-08/10, FR-UI-07 and NFR-01: deterministic retained review insights."""

from uuid import UUID

import httpx
import pytest
from sqlalchemy import delete, select

from app.db.models import AgentEvent, GeneratedPackage, LessonRevision
from app.domain.enums import AgentName, PackageStatus, Variant
from app.events.kinds import package_status_payload
from tests.integration.test_phase9g_auth import KEY
from tests.integration.test_phase9l_governance import close, workspace

pytestmark = pytest.mark.req("FR-S-08", "FR-S-10", "FR-UI-07", "NFR-01")


async def record(
    app,
    run,
    *,
    action="reject",
    variant=Variant.COST,
    category="too_expensive",
    rules=None,
):
    details = {"category": category, "reason": "<script>not executable</script>"}
    if rules is not None:
        details["remaining_blocking_rules"] = rules
    return await app.state.event_log.append(
        run,
        AgentName.ORCHESTRATOR,
        PackageStatus.REJECTED
        if action == "reject"
        else PackageStatus.ENGINEER_APPROVED,
        PackageStatus.PENDING_REVIEW,
        payload={
            **(
                package_status_payload(variant)
                if variant
                else {"kind": "package_status"}
            ),
            "review_action": action,
            "review_decision": details,
        },
    )


async def test_aggregates_count_rules_once_and_link_to_filtered_decisions(db_engines):
    app, run, _, clients = await workspace(db_engines)
    admin = clients[0]
    try:
        first = await record(app, run, rules=["AWS-0053", "AWS-0053", "CKV_1"])
        await record(
            app,
            run,
            variant=Variant.SECURITY,
            category="security_concern",
            rules=["AWS-0053"],
        )
        await record(app, run, category=None)
        await record(
            app,
            run,
            action="approve",
            variant=Variant.PERFORMANCE,
            category="operability",
            rules=[],
        )
        response = await admin.get("/api/reviews/history/insights")
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"] == "no-store"
        data = response.json()
        assert data["total"] == 4
        assert {row["value"]: row["count"] for row in data["by_variant"]} == {
            "cost": 2,
            "security": 1,
            "performance": 1,
        }
        assert {row["value"]: row["count"] for row in data["by_decision"]} == {
            "reject": 3,
            "approve": 1,
        }
        assert (
            data["blocking_snapshot_available"] == 2
            and data["blocking_snapshot_unavailable"] == 1
        )
        assert [(row["rule_id"], row["count"]) for row in data["blocking_rules"]] == [
            ("AWS-0053", 2),
            ("CKV_1", 1),
        ]
        for group in ("by_category", "by_variant", "by_decision", "blocking_rules"):
            for row in data[group]:
                linked = await admin.get("/api/reviews/history", params=row["filters"])
                assert linked.status_code == 200
                assert linked.json()["total"] == row["count"]
        specific = (
            await admin.get(
                "/api/reviews/history", params={"decision_id": str(first.event_id)}
            )
        ).json()
        assert specific["total"] == 1 and specific["items"][0]["decision_id"] == str(
            first.event_id
        )
        assert "not executable" not in response.text
        async with app.state.session_factory() as session:
            assert not list(await session.scalars(select(LessonRevision)))
    finally:
        await close(clients)


async def test_real_decision_snapshots_blockers_and_survives_package_retention(
    db_engines,
):
    app, run, _, clients = await workspace(db_engines)
    admin, reviewer, _ = clients
    try:
        response = await reviewer.post(
            f"/api/pipeline/{run}/packages/cost/review",
            json={
                "action": "reject",
                "category": "security_concern",
                "reason": "Remaining checks require review.",
            },
        )
        assert response.status_code == 200
        item = (await reviewer.get(f"/api/pipeline/{run}/results")).json()["packages"][
            0
        ]
        identity = item["review_decision"]["decision_id"]
        assert item["review_decision"]["remaining_blocking_rules"] == ["CKV_1"]
        async with app.state.session_factory() as session, session.begin():
            event = await session.get(AgentEvent, UUID(identity))
            assert event.payload["review_decision"]["remaining_blocking_rules"] == [
                "CKV_1"
            ]
            await session.execute(
                delete(GeneratedPackage).where(GeneratedPackage.run_id == run)
            )
        result = (await admin.get("/api/reviews/history/insights")).json()
        assert result["blocking_rules"][0]["rule_id"] == "CKV_1"
        history = (
            await admin.get("/api/reviews/history", params={"decision_id": identity})
        ).json()
        assert history["items"][0]["reason"] == "Remaining checks require review."
    finally:
        await close(clients)


async def test_insights_named_admin_only_and_history_exports_keep_their_contract(
    db_engines,
):
    app, run, _, clients = await workspace(db_engines)
    admin, reviewer, _ = clients
    try:
        await record(app, run, rules=[])
        assert (await reviewer.get("/api/reviews/history/insights")).status_code == 403
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1",
            headers={"X-API-Key": KEY},
        ) as shared:
            assert (
                await shared.get("/api/reviews/history/insights")
            ).status_code == 403
            assert (await shared.get("/api/reviews/history")).status_code == 200
        exported = (
            await admin.get("/api/reviews/history/export?format=json&variant=cost")
        ).json()
        assert len(exported["decisions"][0]) == 9
        assert exported["metadata"]["filters"] == {"variant": "cost"}
        assert (
            await admin.get(
                "/api/reviews/history/insights?date_from=2026-10-26&date_to=2026-10-25"
            )
        ).status_code == 400
        assert (
            await admin.get("/api/reviews/history/insights?variant=unknown")
        ).status_code == 422
        assert (
            await admin.get("/api/reviews/history?decision_id=not-a-uuid")
        ).status_code == 422
    finally:
        await close(clients)


async def test_historical_unknowns_stay_unknown_and_empty_filter_is_explicit(
    db_engines,
):
    app, run, _, clients = await workspace(db_engines)
    try:
        await record(app, run, category="unknown-historical-value", variant=None)
        data = (await clients[0].get("/api/reviews/history/insights")).json()
        assert data["by_category"][0]["value"] == "not_recorded"
        assert data["by_variant"][0]["value"] == "not_recorded"
        assert (
            data["blocking_snapshot_unavailable"] == 1 and data["blocking_rules"] == []
        )
        linked = (
            await clients[0].get(
                "/api/reviews/history", params=data["by_category"][0]["filters"]
            )
        ).json()
        assert linked["total"] == 1
        unknown_variant = (
            await clients[0].get(
                "/api/reviews/history", params=data["by_variant"][0]["filters"]
            )
        ).json()
        assert unknown_variant["total"] == 1
        empty = (
            await clients[0].get("/api/reviews/history/insights?variant=security")
        ).json()
        assert (
            empty["total"] == 0
            and empty["by_category"] == empty["blocking_rules"] == []
        )
    finally:
        await close(clients)
