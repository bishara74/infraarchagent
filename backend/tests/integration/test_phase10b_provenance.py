"""NFR-01 / FR-P-04: immutable approval actors and honest legacy nulls."""

import json
from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID, uuid4
from zipfile import ZipFile

import pytest
from sqlalchemy import update

from app.core.lessons import LessonService
from app.db.models import LessonRevision, PipelineRun, User
from app.db.repositories.lessons import LessonRepository
from app.db.session import make_session_factory
from app.llm.stub import StubAdapter
from tests.integration.test_phase9l_governance import close
from tests.integration.test_phase9l_transport import prepared

pytestmark = pytest.mark.req("NFR-01", "FR-P-04", "FR-UI-07")


@pytest.mark.parametrize("direct", [True, False])
async def test_new_approval_actor_matches_result_archive_and_governance_event(
    db_engines, direct
):
    app, run, clients, lesson, config = await prepared(db_engines, self_approved=direct)
    try:
        adapter = StubAdapter(script=["{}"])
        app.state.lesson_runtime.bind(adapter, config, "architect")
        await adapter.complete_json("base")
        manifest = (await clients[0].get(f"/api/pipeline/{run}/results")).json()["run"][
            "lessons"
        ]
        entry = manifest["entries"][0]
        assert entry["approval"] == ("admin_direct" if direct else "admin_reviewed")
        assert entry["self_approved"] is False
        assert entry["approval_actor"]["username"] == "curator"
        event = next(
            e
            for e in (await clients[0].get("/api/lessons/history")).json()["items"]
            if e["action"] == "approved"
        )
        assert event["payload"]["approval_actor"] == entry["approval_actor"]
        assert event["payload"]["approval"] == entry["approval"]
        assert event["actor_id"] == entry["approval_actor"]["user_id"]
        await clients[0].post(
            f"/api/pipeline/{run}/packages/cost/review",
            json={
                "action": "reject",
                "category": "other",
                "reason": "Retain provenance evidence.",
            },
        )
        response = await clients[0].get(f"/api/pipeline/{run}/download/cost")
        assert response.status_code == 200
        with ZipFile(BytesIO(response.content)) as archive:
            stored = json.loads(archive.read("_infraarchagent/LESSONS.json"))
        assert stored["entries"] == manifest["entries"]
    finally:
        await close(clients)


async def test_legacy_actor_join_never_rewrites_immutable_snapshot(db_engines):
    app, run, clients, direct, config = await prepared(db_engines, self_approved=True)
    try:
        now = datetime.now(UTC)
        identity = uuid4()
        actor = UUID(direct["approval_actor"]["user_id"])
        owner = make_session_factory(db_engines[1])
        async with owner() as session, session.begin():
            # Owner-only import of a synthetic pre-migration record; app grants
            # and immutable approval triggers are never relaxed for this test.
            session.add(
                LessonRevision(
                    id=identity,
                    lesson_id=uuid4(),
                    revision=1,
                    decision_id=UUID(direct["decision_id"]),
                    proposer_id=actor,
                    scope_role="architect",
                    applies_to=[],
                    category="operability",
                    text="Prefer clear legacy operational notes.",
                    status="approved",
                    self_approved=True,
                    approval="self_approved",
                    approval_actor=None,
                    filter_result={"version": "1", "passed": True, "reasons": []},
                    approval_filter_result={
                        "version": "1",
                        "passed": True,
                        "reasons": [],
                    },
                    approved_by=actor,
                    created_at=now,
                    approved_at=now,
                )
            )
            await session.flush()
            repo = LessonRepository(session)
            control = await repo.control()
            await repo.new_set(control)
            await session.execute(
                update(User).where(User.id == actor).values(username="renamed-curator")
            )
        snapshot = await LessonService(
            app.state.session_factory, app.state.settings, app.state.event_log
        ).snapshot("account")
        async with app.state.session_factory() as session, session.begin():
            row = await session.get(PipelineRun, run)
            row.lessons = snapshot
        detail = (await clients[0].get(f"/api/lessons/{identity}")).json()["lesson"]
        assert detail["approver"] == "renamed-curator"
        assert detail["approval_actor"] is None and detail["self_approved"] is True
        config = config.model_copy(update={"lessons": snapshot})
        adapter = StubAdapter(script=["{}"])
        app.state.lesson_runtime.bind(adapter, config, "architect")
        await adapter.complete_json("base")
        manifest = (await clients[0].get(f"/api/pipeline/{run}/results")).json()["run"][
            "lessons"
        ]
        legacy = next(e for e in manifest["entries"] if e["id"] == str(identity))
        assert (
            legacy["approval"] == "self_approved" and legacy["approval_actor"] is None
        )
        modern = next(e for e in manifest["entries"] if e["id"] == direct["id"])
        assert modern["approval_actor"]["username"] == "curator"  # Frozen at approval.
        await clients[0].post(
            f"/api/pipeline/{run}/packages/cost/review",
            json={
                "action": "reject",
                "category": "other",
                "reason": "Retain legacy evidence.",
            },
        )
        response = await clients[0].get(f"/api/pipeline/{run}/download/cost")
        with ZipFile(BytesIO(response.content)) as archive:
            stored = json.loads(archive.read("_infraarchagent/LESSONS.json"))
        assert next(e for e in stored["entries"] if e["id"] == str(identity)) == legacy
    finally:
        await close(clients)
