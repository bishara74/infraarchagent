# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Fault injection at the commit boundary for run and review events."""

import asyncio
from unittest.mock import Mock

import httpx
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import PipelineRun
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.events.publisher import RecordingPublisher
from app.main import create_app
from tests.integration.test_pipeline_orchestrator import (
    FakeFactory,
    FakeGenerator,
    make_orchestrator,
)
from tests.integration.test_pipeline_review import (
    client_for,
    pending_app,
    review_url,
    state,
)

pytestmark = pytest.mark.req("FR-P-01", "FR-P-04")
APPROVAL = {
    "action": "approve",
    "reviewer_name": "Test engineer",
    "reason": "Reviewed findings",
    "category": "other",
}
RETRY = {
    "action": "retry",
    "feedback": "Fix this file",
    "target_files": ["terraform/main.tf"],
}


async def injected_fault(record):
    raise RuntimeError("injected event boundary fault")


@pytest.mark.parametrize("before_commit", [True, False])
async def test_transition_and_event_share_commit(
    db_engines, monkeypatch, before_commit
):
    app = create_app(get_settings(), db_engines[0])
    async with app.state.session_factory() as session, session.begin():
        run = await RunRepository(session).create("Deploy web app", LLMProvider.STUB, 2)
        run_id = run.run_id
    log = app.state.event_log
    seam = "_after_insert" if before_commit else "_before_publish"
    with monkeypatch.context() as patch:
        patch.setattr(log, seam, injected_fault)
        if before_commit:
            with pytest.raises(RuntimeError, match="boundary fault"):
                await app.state.writer.run_transition(
                    run_id, RunStatus.FAILED, message="failed"
                )
        else:
            await app.state.writer.run_transition(
                run_id, RunStatus.FAILED, message="failed"
            )
    async with app.state.session_factory() as session:
        assert (await RunRepository(session).get(run_id)).status == (
            "created" if before_commit else "failed"
        )
    events = await log.list_after(run_id, None)
    assert [event.new_state for event in events] == (
        [] if before_commit else ["failed"]
    )
    if not before_commit:
        async with client_for(app) as client:
            replay = await client.get(
                f"/api/pipeline/{run_id}/stream", headers={"Last-Event-ID": "0"}
            )
        assert replay.status_code == 200 and f"id: {events[0].seq}\n" in replay.text
        assert '"status": "failed"' in replay.text


@pytest.mark.req("FR-S-08", "FR-S-09")
@pytest.mark.parametrize("body", [APPROVAL, RETRY], ids=["approve", "retry"])
@pytest.mark.parametrize("before_commit", [True, False])
async def test_review_acceptance_and_event_share_commit(
    db_engines, monkeypatch, body, before_commit
):
    app, run_id = await pending_app(db_engines[0])
    log = app.state.event_log
    seam = "_after_insert" if before_commit else "_before_publish"
    monkeypatch.setattr(log, seam, injected_fault)
    launch = Mock()
    monkeypatch.setattr(app.state.runner, "start_review_retry", launch)
    cursor = (await log.list_after(run_id, None))[-1].seq
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.post(review_url(run_id), json=body)
    _, row = await state(app, run_id)
    events = await log.list_after(run_id, cursor)
    if before_commit:
        assert response.status_code == 500
        assert row.status == "pending_review"
        assert row.review_decision is None and row.review_retry_started_at is None
        assert row.review_feedback is None
        assert not events and not launch.called and app.state.runner._reserved == 0
    elif body["action"] == "approve":
        assert response.status_code == 200 and row.status == "engineer_approved"
        (event,) = events
        assert str(event.event_id) == row.review_decision["decision_id"]
        assert event.payload["review_decision"] == row.review_decision
    else:
        assert response.status_code == 202 and row.status == "remediating"
        assert (
            row.review_retry_started_at is not None
            and row.review_feedback == RETRY["feedback"]
        )
        (event,) = events
        assert (
            event.payload["review_action"] == "retry" and event.new_state == row.status
        )
        launch.assert_called_once()


async def test_startup_recovery_commits_interruption_and_event(db_engines, monkeypatch):
    app, run_id = await pending_app(db_engines[0], terminal=False)
    log = app.state.event_log
    cursor = (await log.list_after(run_id, None))[-1].seq
    with monkeypatch.context() as patch:
        patch.setattr(log, "_after_insert", injected_fault)
        async with app.router.lifespan_context(app):
            assert (await state(app, run_id))[0].status == "running"
            assert await log.list_after(run_id, cursor) == []
    async with app.router.lifespan_context(app):
        run, _ = await state(app, run_id)
        (event,) = await log.list_after(run_id, cursor)
        assert run.status == event.new_state == "failed"
        assert run.error_message == event.message == "interrupted by server restart"


@pytest.mark.req("FR-S-08")
async def test_concurrent_review_and_pipeline_transition_commit_in_seq_order(
    db_engines, monkeypatch
):
    app, run_id = await pending_app(db_engines[0])
    log = app.state.event_log
    publisher = RecordingPublisher()
    monkeypatch.setattr(log, "publisher", publisher)
    async with app.state.session_factory() as session, session.begin():
        packages = PackageRepository(session)
        await packages.create(run_id, Variant.SECURITY)
        for status in (
            PackageStatus.GENERATED,
            PackageStatus.VALIDATING,
            PackageStatus.VALID,
        ):
            await packages.transition_status(run_id, Variant.SECURITY, status)
    first_inserted, review_waiting, release = (
        asyncio.Event(),
        asyncio.Event(),
        asyncio.Event(),
    )
    cursor = (await log.list_after(run_id, None))[-1].seq

    async def after_insert(record):
        if record.new_state == "pending_review":
            first_inserted.set()
            await release.wait()
        else:
            (committed,) = await log.list_after(run_id, cursor)
            assert (
                committed.new_state == "pending_review" and committed.seq < record.seq
            )

    serialize = log.serialize_run

    def observe_serialize(candidate):
        if first_inserted.is_set():
            review_waiting.set()
        return serialize(candidate)

    monkeypatch.setattr(log, "_after_insert", after_insert)
    monkeypatch.setattr(log, "serialize_run", observe_serialize)
    async with (
        asyncio.timeout(5),
        client_for(app) as client,
        asyncio.TaskGroup() as group,
    ):
        group.create_task(
            app.state.writer.package_transition(
                run_id,
                Variant.SECURITY,
                PackageStatus.PENDING_REVIEW,
                message="ready for review",
            )
        )
        await first_inserted.wait()
        review = group.create_task(
            client.post(review_url(run_id, "security"), json=APPROVAL)
        )
        await review_waiting.wait()
        assert await log.list_after(run_id, cursor) == []
        release.set()
    assert review.result().status_code == 200
    events = await log.list_after(run_id, cursor)
    assert [event.new_state for event in events] == [
        "pending_review",
        "engineer_approved",
    ]
    assert events == publisher.events


async def test_failed_acceptance_insert_rolls_back_run_creation(
    db_engines, monkeypatch
):
    app = create_app(get_settings(), db_engines[0])
    monkeypatch.setattr(app.state.event_log, "_after_insert", injected_fault)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/pipeline/run", json={"text": "Deploy AWS web app"}
        )
    assert response.status_code == 500
    async with app.state.session_factory() as session:
        assert await session.scalar(select(PipelineRun.run_id)) is None
    assert app.state.runner.tasks == {} and app.state.runner._reserved == 0


@pytest.mark.parametrize("kind", ["package_status", "package_generated"])
async def test_package_creation_and_files_roll_back_with_their_events(
    db_engines, monkeypatch, kind
):
    orchestrator, run_id, writer = await make_orchestrator(
        db_engines[0], FakeFactory([FakeGenerator(Variant.COST)])
    )

    async def after_insert(record):
        if record.payload["kind"] == kind and record.new_state in {
            "generating",
            "generated",
        }:
            raise RuntimeError("injected package event fault")

    monkeypatch.setattr(writer.event_log, "_after_insert", after_insert)
    assert await orchestrator.run() == RunStatus.FAILED
    async with writer.session_factory() as session:
        rows = await PackageRepository(session).list_for_run(run_id)
    events = await writer.event_log.list_after(run_id, None)
    if kind == "package_status":
        assert not rows
        assert not any(event.new_state == "generating" for event in events)
    else:
        assert all(not row.files for row in rows)
        assert not any(event.new_state == "generated" for event in events)
