"""FR-S-08/09/10 locked reviews and real-agent retries with offline adapters."""

import asyncio
import json
from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixAgent
from app.agents.validator import ValidatorAgent
from app.core.config import get_settings
from app.db.models import AgentEvent
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import (
    AgentName,
    AgentState,
    LLMProvider,
    PackageStatus,
    RunStatus,
    Variant,
)
from app.domain.validation import ValidationCheck, ValidationReport
from app.events.kinds import plan_created_payload
from app.llm.stub import StubAdapter
from app.main import create_app
from app.scanners.runner import ToolFailure
from tests.integration.test_security_agent import ScriptedScanner, finding
from tests.unit.test_generators import plan


def validation_report(result="invalid"):
    return ValidationReport.build(
        [
            ValidationCheck(
                check_id="reference.test",
                category="reference",
                tool="builtin",
                status="failed",
                file_path="terraform/main.tf",
                message="broken reference",
            )
        ]
        if result == "invalid"
        else [],
        terraform_required=result == "error",
    )


async def pending_app(
    engine, *, result="invalid", blocking=False, terminal=True, persist_plan=True
):
    app = create_app(get_settings(), engine)
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            run = await RunRepository(session).create(
                "Deploy AWS web app", LLMProvider.STUB, 2, model="stub"
            )
            run_id = run.run_id
            repo = PackageRepository(session)
            await repo.create(run_id, Variant.COST)
            await repo.save_files(
                run_id, Variant.COST, {"terraform/main.tf": "terraform {}\n"}
            )
            await repo.save_security_results(
                run_id,
                Variant.COST,
                original_files={"terraform/main.tf": "terraform {}\n"},
                files={"terraform/main.tf": "terraform {}\n"},
                session_report={
                    "kind": "automated",
                    "final": {
                        "outcome": "exhausted" if blocking else "clean",
                        "remaining_blocking": [finding("CKV_1").model_dump(mode="json")]
                        if blocking
                        else [],
                    },
                },
                iteration_count=2,
                policy_version="2",
                prompt_version="1",
                tools={},
            )
    writer = app.state.writer
    await writer.run_transition(run_id, RunStatus.RUNNING, message="started")
    if persist_plan:
        await app.state.event_log.append(
            run_id,
            AgentName.ARCHITECT,
            AgentState.COMPLETED,
            payload=plan_created_payload(plan()),
        )
    for target in (
        PackageStatus.GENERATED,
        PackageStatus.SCANNING,
        PackageStatus.SCAN_CLEAN,
        PackageStatus.VALIDATING,
    ):
        await writer.package_transition(run_id, Variant.COST, target, message="fixture")
    async with sessions() as session:
        async with session.begin():
            await PackageRepository(session).save_validation_results(
                run_id, Variant.COST, validation_report(result)
            )
    outcome = {
        "invalid": PackageStatus.INVALID,
        "valid": PackageStatus.VALID,
        "error": PackageStatus.VALIDATION_ERROR,
    }[result]
    await writer.package_transition(run_id, Variant.COST, outcome, message="fixture")
    await writer.package_transition(
        run_id, Variant.COST, PackageStatus.PENDING_REVIEW, message="fixture"
    )
    if terminal:
        await writer.run_transition(
            run_id, RunStatus.PARTIAL_SUCCESS, message="finished"
        )
    return app, run_id


def client_for(app):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    )


def review_url(run_id, variant="cost"):
    return f"/api/pipeline/{run_id}/packages/{variant}/review"


def install_retry(app, monkeypatch, *, result="valid", scanner=None, adapter=None):
    runner = app.state.runner
    scanner = scanner or ScriptedScanner([[]])
    adapter = adapter or StubAdapter(
        script=[
            json.dumps(
                {
                    "file": {
                        "path": "terraform/main.tf",
                        "content": "terraform {}\n# fixed\n",
                    },
                    "new_files": {},
                    "fixes": [],
                }
            )
        ]
    )
    security = SecurityAgent(
        scanner, FixAgent(adapter), runner.session_factory, runner.factory.settings
    )
    monkeypatch.setattr(
        runner.factory, "create_security_agent", lambda config: security
    )

    class Engine:
        async def validate(self, _plan, _files):
            return validation_report(result)

    runner.validation_stage = ValidatorAgent(
        Engine(), runner.session_factory, settings=runner.factory.settings
    )
    return adapter, security


async def state(app, run_id):
    async with app.state.session_factory() as session:
        return await RunRepository(session).get(run_id), await PackageRepository(
            session
        ).get(run_id, Variant.COST)


@pytest.mark.req("FR-S-08", "FR-S-10", "FR-UI-07")
@pytest.mark.parametrize(
    "action,expected",
    [("approve", "production_ready"), ("reject", "not_production_ready")],
)
async def test_decision_without_agents_and_frozen_run(
    db_engines, monkeypatch, action, expected
):
    app, run_id = await pending_app(db_engines[0], blocking=True)
    before, _ = await state(app, run_id)
    security = Mock(side_effect=AssertionError("must not scan"))
    monkeypatch.setattr(app.state.runner.factory, "create_security_agent", security)
    validator = Mock(side_effect=AssertionError("must not validate"))
    monkeypatch.setattr(app.state.runner.validation_stage, "run", validator)
    async with client_for(app) as client:
        response = await client.post(
            review_url(run_id), json={"action": action, "feedback": "  Reviewed  "}
        )
        assert response.status_code == 200 and response.json()["status"] == expected
        assert (
            await client.post(review_url(run_id), json={"action": action})
        ).status_code == 409
    run, row = await state(app, run_id)
    assert (run.status, run.end_time) == (before.status, before.end_time)
    assert row.review_retry_started_at is None
    assert row.review_feedback == ("Reviewed" if action == "reject" else None)
    security.assert_not_called()
    validator.assert_not_called()
    async with app.state.session_factory() as session:
        events = list(
            await session.scalars(select(AgentEvent).order_by(AgentEvent.seq))
        )
    assert events[-1].payload["review_reasons"] == [
        "unresolved_security_findings",
        "validation_failed",
    ]


@pytest.mark.req("FR-S-09", "FR-UI-07")
@pytest.mark.parametrize("action", ["approve", "reject", "retry"])
async def test_review_waits_for_run_completion(db_engines, action):
    app, run_id = await pending_app(db_engines[0], terminal=False)
    async with client_for(app) as client:
        response = await client.post(review_url(run_id), json={"action": action})
        assert (
            response.status_code == 409
            and response.json()["error"] == "run_in_progress"
        )
        data = (await client.get(f"/api/pipeline/{run_id}/results")).json()
    assert data["packages"][0]["review_available"] is False
    assert (await state(app, run_id))[1].status == "pending_review"


@pytest.mark.req("FR-S-09")
@pytest.mark.parametrize("result", ["valid", "invalid", "error"])
async def test_retry_reset_prompt_and_option_c(db_engines, monkeypatch, result):
    app, run_id = await pending_app(db_engines[0])
    adapter, security = install_retry(app, monkeypatch, result=result)
    original_propose = security.fix_agent.propose

    async def observed_propose(**kwargs):
        _, row = await state(app, run_id)
        assert (
            row.iteration_count == 0 and row.review_retry_started_at.tzinfo is not None
        )
        return await original_propose(**kwargs)

    monkeypatch.setattr(security.fix_agent, "propose", observed_propose)
    before, _ = await state(app, run_id)
    async with client_for(app) as client:
        response = await client.post(
            review_url(run_id),
            json={"action": "retry", "feedback": "Repair the reference"},
        )
    assert response.status_code == 202 and response.json()["stream_url"].endswith(
        "/stream"
    )
    await asyncio.gather(*app.state.runner.tasks.values())
    run, row = await state(app, run_id)
    assert row.status == ("production_ready" if result == "valid" else "pending_review")
    assert (
        "Repair the reference" in adapter.prompts[0]
        and "broken reference" in adapter.prompts[0]
    )
    assert row.iteration_count == 1 and row.review_retry_started_at is None
    assert row.original_files == {"terraform/main.tf": "terraform {}\n"}
    assert len(row.security_report["sessions"]) == 2
    assert row.files["terraform/main.tf"].endswith("# fixed\n")
    assert (run.status, run.end_time) == (before.status, before.end_time)
    assert app.state.runner._reserved == 0
    if result == "error":
        assert row.error.startswith("review retry aborted:")


@pytest.mark.req("FR-S-09")
async def test_feedback_only_explicit_target_and_missing_plan(db_engines, monkeypatch):
    app, run_id = await pending_app(db_engines[0], result="valid")
    adapter, _ = install_retry(app, monkeypatch)
    async with client_for(app) as client:
        response = await client.post(
            review_url(run_id),
            json={
                "action": "retry",
                "feedback": "Improve file",
                "target_files": ["terraform/main.tf", "terraform/main.tf"],
            },
        )
    assert response.status_code == 202
    await asyncio.gather(*app.state.runner.tasks.values())
    assert len(adapter.prompts) == 1 and "Improve file" in adapter.prompts[0]


@pytest.mark.req("FR-S-09")
@pytest.mark.parametrize(
    "feedback,code",
    [("Please fix", "feedback_needs_target"), ("  ", "nothing_to_retry")],
)
async def test_targetless_retry_never_mutates(db_engines, feedback, code):
    app, run_id = await pending_app(db_engines[0], result="valid")
    _, before = await state(app, run_id)
    events = await app.state.event_log.list_after(run_id, None)
    async with client_for(app) as client:
        response = await client.post(
            review_url(run_id), json={"action": "retry", "feedback": feedback}
        )
    assert response.status_code == 422 and response.json()["error"] == code
    _, after = await state(app, run_id)
    assert (
        after.status,
        after.review_feedback,
        after.iteration_count,
        after.review_retry_started_at,
    ) == (before.status, before.review_feedback, before.iteration_count, None)
    assert len(await app.state.event_log.list_after(run_id, None)) == len(events)
    assert app.state.runner._reserved == 0


@pytest.mark.req("FR-S-09")
async def test_capacity_and_bad_targets_leave_pending(db_engines):
    app, run_id = await pending_app(db_engines[0])
    app.state.runner._reserved = app.state.runner.capacity
    async with client_for(app) as client:
        for body, status, code in [
            ({"action": "retry"}, 429, "too_many_runs"),
            (
                {"action": "retry", "target_files": ["missing.tf"]},
                400,
                "invalid_request",
            ),
            (
                {"action": "retry", "target_files": ["../main.tf"]},
                400,
                "invalid_request",
            ),
        ]:
            response = await client.post(review_url(run_id), json=body)
            assert response.status_code == status and response.json()["error"] == code
    _, row = await state(app, run_id)
    assert (
        row.status == "pending_review"
        and row.review_retry_started_at is None
        and row.review_feedback is None
    )


@pytest.mark.req("FR-S-08", "FR-S-09", "FR-S-10")
@pytest.mark.parametrize(
    "actions",
    [
        ("approve", "approve"),
        ("reject", "reject"),
        ("approve", "reject"),
        ("retry", "retry"),
        ("approve", "retry"),
        ("reject", "retry"),
    ],
)
async def test_concurrent_reviews_one_acceptance(db_engines, monkeypatch, actions):
    app, run_id = await pending_app(db_engines[0])
    gate = asyncio.Event()

    class WaitingScanner(ScriptedScanner):
        async def scan(self, *args, **kwargs):
            await gate.wait()
            return await super().scan(*args, **kwargs)

    install_retry(app, monkeypatch, scanner=WaitingScanner([[]]))
    barrier = asyncio.Barrier(2)
    original_lock = PackageRepository.get_for_update

    async def synchronized(self, *args):
        if not self.session.info.get("review_barrier"):
            self.session.info["review_barrier"] = True
            await barrier.wait()
        return await original_lock(self, *args)

    monkeypatch.setattr(PackageRepository, "get_for_update", synchronized)
    try:
        async with client_for(app) as client:
            responses = await asyncio.wait_for(
                asyncio.gather(
                    *(
                        client.post(review_url(run_id), json={"action": action})
                        for action in actions
                    )
                ),
                timeout=5,
            )
        assert sorted(response.status_code for response in responses) in (
            [200, 409],
            [202, 409],
        )
        assert (
            next(r for r in responses if r.status_code == 409).json()["error"]
            == "not_pending_review"
        )
    finally:
        monkeypatch.setattr(PackageRepository, "get_for_update", original_lock)
        gate.set()
        await asyncio.gather(*app.state.runner.tasks.values())


@pytest.mark.req("FR-S-09")
@pytest.mark.parametrize("failure", ["scan", "validator", "plan"])
async def test_retry_failure_returns_to_review(db_engines, monkeypatch, failure):
    app, run_id = await pending_app(db_engines[0], persist_plan=failure != "plan")

    class BrokenScanner:
        async def scan(self, *_args, **_kwargs):
            raise ToolFailure("checkov", "timeout")

    install_retry(
        app, monkeypatch, scanner=BrokenScanner() if failure == "scan" else None
    )
    if failure == "validator":

        async def broken(*args):
            raise RuntimeError("private validator detail")

        monkeypatch.setattr(app.state.runner.validation_stage, "run", broken)
    async with client_for(app) as client:
        assert (
            await client.post(review_url(run_id), json={"action": "retry"})
        ).status_code == 202
    await asyncio.gather(*app.state.runner.tasks.values())
    run, row = await state(app, run_id)
    assert row.status == "pending_review" and row.review_retry_started_at is None
    assert row.error.startswith("review retry aborted:") and "private" not in row.error
    assert run.status == "partial_success"
    events = await app.state.event_log.list_after(run_id, None)
    assert not any(e.new_state == "scan_error" for e in events)


@pytest.mark.req("FR-S-08", "FR-S-09", "FR-S-10")
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"action": "other"},
        {"action": "approve", "extra": 1},
        {"action": "retry", "feedback": 2},
        {"action": "retry", "feedback": None},
        {"action": "retry", "feedback": "x" * 2001},
        {"action": "approve", "target_files": []},
        {"action": "retry", "target_files": ["terraform/main.tf"] * 6},
        {"action": "retry", "target_files": [2]},
    ],
)
async def test_bad_body_is_400(db_engines, body):
    app, run_id = await pending_app(db_engines[0])
    async with client_for(app) as client:
        assert (await client.post(review_url(run_id), json=body)).status_code == 400
        assert (
            await client.post(review_url("bad"), json={"action": "approve"})
        ).status_code == 400
        assert (
            await client.post(review_url(run_id, "unknown"), json={"action": "approve"})
        ).status_code == 400
        assert (
            await client.post(review_url(uuid4()), json={"action": "approve"})
        ).status_code == 404
