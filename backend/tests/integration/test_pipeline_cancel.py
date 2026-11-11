# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Cancellation authorization, lifecycle, and isolation on PostgreSQL."""

import asyncio
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.core.auth import COOKIE_NAME
from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.repositories.users import UserRepository
from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.domain.run_config import RunConfig
from app.main import create_app
from app.pipeline.orchestrator import PipelineOrchestrator
from tests.integration.test_phase9g_auth import KEY, ORIGIN, client
from tests.integration.test_pipeline_auth import LLM_CANARY

pytestmark = pytest.mark.req("FR-P-01", "FR-P-04", "NFR-01")


async def create_run(app, owner=None):
    async with app.state.session_factory() as session, session.begin():
        row = await RunRepository(session).create(
            "Deploy AWS web service", LLMProvider.STUB, 2, user_id=owner
        )
        return row.run_id


async def seed_packages(app, run_id):
    async with app.state.session_factory() as session, session.begin():
        for variant in Variant:
            await PackageRepository(session).create(run_id, variant)
    paths = {
        Variant.COST: (
            PackageStatus.GENERATED,
            PackageStatus.VALIDATING,
            PackageStatus.INVALID,
            PackageStatus.PENDING_REVIEW,
        ),
        Variant.PERFORMANCE: (
            PackageStatus.GENERATED,
            PackageStatus.VALIDATING,
            PackageStatus.VALID,
            PackageStatus.CHECKS_PASSED,
        ),
        Variant.SECURITY: (PackageStatus.GENERATED, PackageStatus.SCANNING),
    }
    for variant, statuses in paths.items():
        for status in statuses:
            await app.state.writer.package_transition(
                run_id, variant, status, message="fixture"
            )


@pytest.mark.parametrize("actor", ["owner", "admin"])
async def test_cancel_authorization_idempotency_and_run_isolation(
    db_engines, monkeypatch, actor
):
    app = create_app(get_settings(), db_engines[0])
    async with app.state.session_factory() as session, session.begin():
        users = UserRepository(session)
        admin = await users.create("admin", "fixture", first=True)
        owner = await users.create("owner", "fixture")
        other = await users.create("other", "fixture")
    selected = owner if actor == "owner" else admin
    caller_token = await app.state.auth.login(selected.id)
    other_token = await app.state.auth.login(other.id)
    run_id = await create_run(app, owner.id)
    other_id = await create_run(app, other.id)
    await seed_packages(app, run_id)
    run_started = asyncio.Event()
    other_started = asyncio.Event()
    other_finish = asyncio.Event()
    cleaning = asyncio.Event()
    finish_cleanup = asyncio.Event()

    async def core(self):
        await self.writer.run_transition(
            self.run_id, RunStatus.RUNNING, message="started"
        )
        if self.run_id == other_id:
            other_started.set()
            await other_finish.wait()
            await self.writer.run_transition(
                other_id, RunStatus.SUCCESS, message="completed"
            )
            return RunStatus.SUCCESS
        run_started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cleaning.set()
            await finish_cleanup.wait()
            raise

    monkeypatch.setattr(PipelineOrchestrator, "_run_core", core)
    runner = app.state.runner
    for identity in (run_id, other_id):
        assert runner.reserve()
        runner.start(identity, "Deploy AWS web service", RunConfig())
    task, other_task = runner.tasks[run_id], runner.tasks[other_id]
    url = f"/api/pipeline/{run_id}/cancel"
    try:
        async with asyncio.timeout(10), client(app) as http:
            await run_started.wait()
            await other_started.wait()
            http.cookies.set(COOKIE_NAME, other_token)
            assert (await http.post(url, headers=ORIGIN)).status_code == 403
            http.cookies.set(COOKIE_NAME, caller_token)
            missing = await http.post(f"/api/pipeline/{uuid4()}/cancel", headers=ORIGIN)
            assert missing.status_code == 404
            assert (await http.post(url, headers=ORIGIN)).status_code == 202
            await cleaning.wait()
            assert (await http.post(url, headers=ORIGIN)).status_code == 202
            assert not other_task.done() and runner._reserved == 2
            finish_cleanup.set()
            assert isinstance(
                (await asyncio.gather(task, return_exceptions=True))[0],
                asyncio.CancelledError,
            )
            assert runner._reserved == 1
            terminal = await http.post(url, headers=ORIGIN)
            assert (
                terminal.status_code == 409
                and terminal.json()["error"] == "not_cancellable"
            )
            stream = await http.get(f"/api/pipeline/{run_id}/stream")
            assert f"cancelled by {selected.username}" in stream.text
            other_finish.set()
            assert await other_task == RunStatus.SUCCESS and runner._reserved == 0
    finally:
        finish_cleanup.set()
        other_finish.set()
        await runner.shutdown()

    async with app.state.session_factory() as session:
        run = await RunRepository(session).get(run_id)
        rows = await PackageRepository(session).list_for_run(run_id)
    assert run.status == "cancelled" and run.end_time is not None
    assert run.error_message == f"cancelled by {selected.username}"
    assert {row.variant: row.status for row in rows} == {
        "cost": "pending_review",
        "performance": "checks_passed",
        "security": "failed",
    }
    assert (
        next(row.error for row in rows if row.variant == "security")
        == "cancelled by user"
    )
    events = await app.state.event_log.list_after(run_id, None)
    assert [event.new_state for event in events[-2:]] == ["failed", "cancelled"]
    assert sum(event.new_state == "cancelled" for event in events) == 1


@pytest.mark.parametrize("shared_key", [False, True])
async def test_ownerless_cancel_before_task_entry(db_engines, monkeypatch, shared_key):
    settings = get_settings().model_copy(
        update={
            "api_key": SecretStr(KEY) if shared_key else None,
            "llm_api_key": SecretStr(LLM_CANARY),
        }
    )
    app = create_app(settings, db_engines[0])
    run_id = await create_run(app)
    runner = app.state.runner
    original_own = runner._own
    enter = asyncio.Event()

    def delay_entry(task_id, coroutine, *, name):
        async def delayed():
            try:
                await enter.wait()
                return await coroutine
            finally:
                coroutine.close()

        original_own(task_id, delayed(), name=name)

    monkeypatch.setattr(runner, "_own", delay_entry)
    assert runner.reserve()
    runner.start(run_id, "Deploy AWS web service", RunConfig())
    task = runner.tasks[run_id]
    headers = {"X-API-Key": KEY} if shared_key else {}
    try:
        async with asyncio.timeout(5), client(app) as http:
            url = f"/api/pipeline/{run_id}/cancel"
            assert (await http.post(url, headers=headers)).status_code == 400
            response = await http.post(
                url,
                headers=headers,
                json={"reviewer_name": f"  Local engineer {LLM_CANARY}  "},
            )
            assert response.status_code == 202 and LLM_CANARY not in response.text
            assert not runner._pipelines[run_id].entered
            enter.set()
            await asyncio.gather(task, return_exceptions=True)
    finally:
        enter.set()
        await runner.shutdown()
    (event,) = await app.state.event_log.list_after(run_id, None)
    assert event.previous_state == "created" and event.new_state == "cancelled"
    assert event.message == "cancelled by Local engineer [REDACTED]"
    assert runner._reserved == 0


async def test_cancel_settlement_rolls_back_packages_and_events(
    db_engines, monkeypatch
):
    app = create_app(get_settings(), db_engines[0])
    run_id = await create_run(app)
    await seed_packages(app, run_id)
    log = app.state.event_log
    cursor = (await log.list_after(run_id, None))[-1].seq

    async def after_insert(record):
        if record.new_state == "cancelled":
            raise RuntimeError("injected cancellation fault")

    monkeypatch.setattr(log, "_after_insert", after_insert)
    with pytest.raises(RuntimeError, match="injected cancellation fault"):
        await app.state.writer.cancel_run(run_id, "fixture")
    async with app.state.session_factory() as session:
        run = await RunRepository(session).get(run_id)
        package = await PackageRepository(session).get(run_id, Variant.SECURITY)
    assert run.status == "created" and run.end_time is None
    assert package.status == "scanning" and package.error is None
    assert await log.list_after(run_id, cursor) == []


async def test_cancel_observes_terminal_commit_before_publication(
    db_engines, monkeypatch
):
    app = create_app(get_settings(), db_engines[0])
    run_id = await create_run(app)
    publishing, cancel_waiting, release = (
        asyncio.Event(),
        asyncio.Event(),
        asyncio.Event(),
    )
    serialize = app.state.event_log.serialize_run

    def observe_serialize(candidate):
        if publishing.is_set():
            cancel_waiting.set()
        return serialize(candidate)

    async def before_publish(record):
        if record.new_state == "success":
            publishing.set()
            await release.wait()

    async def core(self):
        await self.writer.run_transition(run_id, RunStatus.RUNNING, message="started")
        await self.writer.run_transition(run_id, RunStatus.SUCCESS, message="finished")
        return RunStatus.SUCCESS

    monkeypatch.setattr(PipelineOrchestrator, "_run_core", core)
    monkeypatch.setattr(app.state.event_log, "_before_publish", before_publish)
    monkeypatch.setattr(app.state.event_log, "serialize_run", observe_serialize)
    runner = app.state.runner
    assert runner.reserve()
    runner.start(run_id, "Deploy AWS web service", RunConfig())
    task = runner.tasks[run_id]
    try:
        async with (
            asyncio.timeout(5),
            client(app) as http,
            asyncio.TaskGroup() as group,
        ):
            await publishing.wait()
            cancel = group.create_task(
                http.post(
                    f"/api/pipeline/{run_id}/cancel", json={"reviewer_name": "Engineer"}
                )
            )
            await cancel_waiting.wait()
            release.set()
        assert cancel.result().status_code == 409
        assert await task == RunStatus.SUCCESS
    finally:
        release.set()
        await runner.shutdown()
