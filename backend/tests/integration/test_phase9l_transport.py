"""FR-P-04, FR-A-05, FR-S-07 and NFR-01: advisory dispatch and provenance."""

import asyncio
import json
from dataclasses import asdict
from io import BytesIO
from unittest.mock import AsyncMock
from uuid import UUID
from zipfile import ZipFile

import httpx
import pytest

from app.core.lessons import LessonService
from app.db.models import PipelineRun
from app.domain.enums import AgentName, AgentState
from app.domain.run_config import RunConfig
from app.llm.base import RetryPolicy
from app.llm.errors import LLMTransientError
from app.llm.stub import StubAdapter
from tests.integration.test_phase9g_auth import KEY
from tests.integration.test_phase9l_governance import (
    close,
    decision,
    proposal,
    workspace,
)
from tests.unit.test_architect import plan as architect_plan
from tests.unit.test_generators import plan as generator_plan
from tests.unit.test_phase9l_corpus import CORPUS, text_for

pytestmark = pytest.mark.req("FR-P-04", "FR-A-05", "FR-S-07", "NFR-01")


async def test_corpus_survivors_require_human_approval_before_any_hook(db_engines):
    app, run, users, clients = await workspace(db_engines)
    try:
        source = await decision(app, run, users[1])
        survivors = [case for case in CORPUS["cases"] if not case["blocked"]]
        for case in survivors:
            response = await proposal(clients[1], source, text=text_for(case))
            assert response.status_code == 201
        assert len(survivors) == 8
        await clients[0].put("/api/lessons/control", json={"enabled": True})
        snapshot = await LessonService(
            app.state.session_factory, app.state.settings, app.state.event_log
        ).snapshot("account")
        assert snapshot["entries"] == []
        adapter = StubAdapter(script=["{}"])
        app.state.lesson_runtime.bind(
            adapter, RunConfig(lessons=snapshot, lesson_run_id=run), "architect"
        )
        assert adapter.lesson_hook is None
        await adapter.complete_json("original user data")
        assert adapter.prompts == ["original user data"]
    finally:
        await close(clients)


async def prepared(db_engines, *, self_approved=False, role="architect"):
    app, run, users, clients = await workspace(
        db_engines, lessons_require_second_approver=not self_approved
    )
    actor = 0 if self_approved else 1
    source = await decision(
        app, run, users[actor], reason="RAW_REASON_MUST_NEVER_REACH_A_MODEL"
    )
    row = (await proposal(clients[actor], source, scope_role=role)).json()
    path = f"/api/lessons/{row['id']}"
    body = {}
    if self_approved:
        body = {
            "confirmation_token": (
                await clients[0].post(path + "/confirmation")
            ).json()["confirmation_token"]
        }
    assert (await clients[0].post(path + "/approve", json=body)).status_code == 200
    assert (
        await clients[0].put("/api/lessons/control", json={"enabled": True})
    ).status_code == 200
    snapshot = await LessonService(
        app.state.session_factory, app.state.settings, app.state.event_log
    ).snapshot("account")
    async with app.state.session_factory() as session, session.begin():
        saved = await session.get(PipelineRun, run)
        saved.lessons = snapshot
    return app, run, clients, row, RunConfig(lessons=snapshot, lesson_run_id=run)


async def persist_details(app, run, details):
    await app.state.event_log.append(
        run,
        AgentName.ORCHESTRATOR,
        AgentState.RUNNING,
        payload={
            "kind": "stage_notice",
            "notice": "runtime telemetry",
            "telemetry": [
                {
                    **asdict(detail),
                    "id": detail.call_id,
                    "kind": "llm",
                    "role": "architect",
                }
                for detail in details
            ],
        },
    )


async def test_role_scoping_raw_reason_isolation_and_durable_authorization(db_engines):
    app, run, clients, row, config = await prepared(db_engines)
    try:
        adapter = StubAdapter(script=["{}"])
        app.state.lesson_runtime.bind(adapter, config, "architect")
        details = []
        await adapter.complete_json(
            "base user message",
            system="UNCHANGED SYSTEM",
            attempt_observer=details.append,
        )
        assert adapter.prompts[0].startswith("base user message\n<reviewer_lessons>")
        assert row["text"] in adapter.prompts[0]
        assert "RAW_REASON" not in adapter.prompts[0]
        assert details[0].lesson_usage["lesson_ids"] == [row["id"]]
        # Authorization survives even before completed telemetry is published.
        results = (await clients[0].get(f"/api/pipeline/{run}/results")).json()
        assert results["run"]["lessons"]["used_count"] == 1
        assert results["run"]["lessons"]["calls"][0]["outcome"] == "authorized"
        await persist_details(app, run, details)
        updated = (await clients[0].get(f"/api/pipeline/{run}/results")).json()["run"][
            "lessons"
        ]
        assert (
            len(updated["calls"]) == 1 and updated["calls"][0]["outcome"] == "success"
        )
        other = StubAdapter(script=["{}"])
        app.state.lesson_runtime.bind(other, config, "generator_cost")
        assert other.lesson_hook is None
        await other.complete_json("generator base")
        assert other.prompts == ["generator base"]
    finally:
        await close(clients)


@pytest.mark.parametrize("role", ["architect", "all_generators"])
async def test_agent_correction_and_regeneration_include_one_advisory_block(
    db_engines, role
):
    from app.agents.architect import ArchitectAgent
    from app.agents.budget import AgentBudget
    from app.agents.generators.cost import CostGeneratorAgent
    from app.agents.prompts.architect import ARCHITECT_SYSTEM_PROMPT

    app, run, clients, row, config = await prepared(db_engines, role=role)
    try:
        systems = []
        if role == "architect":
            adapter = StubAdapter(script=["{}", json.dumps(architect_plan())])
            app.state.lesson_runtime.bind(adapter, config, "architect")
        else:
            first = {"files": {"terraform/main.tf": "terraform {}"}, "notes": ""}
            complete = {
                "files": {**first["files"], "docker/Dockerfile": "FROM alpine"},
                "notes": "",
            }
            adapter = StubAdapter(
                script=[json.dumps(first), json.dumps(complete), json.dumps(complete)]
            )
            app.state.lesson_runtime.bind(adapter, config, "generator_cost")
        original = adapter.send_prompt

        async def record(prompt, **kwargs):
            systems.append(kwargs.get("system"))
            return await original(prompt, **kwargs)

        adapter.send_prompt = record
        if role == "architect":
            architect = ArchitectAgent(
                adapter, deadline_seconds=150, max_plan_attempts=2
            )
            architect.parse_input("Deploy an AWS web application.")
            await architect.generate_plan()
            assert systems == [ARCHITECT_SYSTEM_PROMPT] * 2
        else:
            generator = CostGeneratorAgent(
                adapter,
                deadline_seconds=150,
                attempt_timeout=30,
                max_output_tokens=8000,
                max_package_attempts=2,
            )
            deployment = generator_plan("dockerfile")
            await generator.generate(deployment)
            await generator.regenerate(
                deployment, [{"message": "Keep the required files."}], AgentBudget(150)
            )
            assert len(systems) == 3 and len(set(systems)) == 1
        for prompt in adapter.prompts:
            assert (
                prompt.count("<reviewer_lessons>")
                == prompt.count("</reviewer_lessons>")
                == 1
            )
            assert row["text"] in prompt and "RAW_REASON" not in prompt
        assert all("<reviewer_lessons>" not in system for system in systems)
    finally:
        await close(clients)


async def test_kill_switch_detaches_before_retry_and_reenable_is_sticky(db_engines):
    app, run, clients, row, config = await prepared(db_engines)
    try:
        blocked, resume = asyncio.Event(), asyncio.Event()

        async def backoff(seconds):
            blocked.set()
            await resume.wait()

        adapter = StubAdapter(
            policy=RetryPolicy(30, 2, 150, 1, 100),
            script=[LLMTransientError("rate_limit"), "{}"],
        )
        adapter._sleep = backoff
        app.state.lesson_runtime.bind(adapter, config, "architect")
        hook = AsyncMock(wraps=adapter.lesson_hook)
        adapter.lesson_hook = hook
        details = []
        task = asyncio.create_task(
            adapter.complete_json("base", attempt_observer=details.append)
        )
        await asyncio.wait_for(blocked.wait(), timeout=10)
        assert (
            await clients[0].put("/api/lessons/control", json={"enabled": False})
        ).status_code == 200
        assert adapter.lesson_hook is None and adapter.lesson_gate is None
        assert (
            await clients[0].put("/api/lessons/control", json={"enabled": True})
        ).status_code == 200
        resume.set()
        await task
        assert "<reviewer_lessons>" in adapter.prompts[0]
        assert adapter.prompts[1] == "base"
        assert hook.await_count == 1
        assert [detail.lesson_usage["enabled"] for detail in details] == [True, False]
        assert details[1].lesson_usage["reason"] == "disabled_during_run"
        late = StubAdapter()
        app.state.lesson_runtime.bind(late, config, "architect")
        assert late.lesson_hook is None
        await persist_details(app, run, details)
        manifest = (await clients[0].get(f"/api/pipeline/{run}/results")).json()["run"][
            "lessons"
        ]
        assert manifest["used_count"] == 1 and manifest["disabled_during_run"]
    finally:
        await close(clients)


async def test_disable_does_not_wait_for_inflight_model_response(db_engines):
    app, run, clients, row, config = await prepared(db_engines)
    try:
        started, finish = asyncio.Event(), asyncio.Event()
        adapter = StubAdapter(script=["{}"])
        original = adapter.send_prompt

        async def slow(*args, **kwargs):
            started.set()
            await finish.wait()
            return await original(*args, **kwargs)

        adapter.send_prompt = slow
        app.state.lesson_runtime.bind(adapter, config, "architect")
        task = asyncio.create_task(adapter.complete_json("base"))
        await asyncio.wait_for(started.wait(), timeout=10)
        response = await asyncio.wait_for(
            clients[0].put("/api/lessons/control", json={"enabled": False}), timeout=10
        )
        assert response.status_code == 200 and not task.done()
        finish.set()
        await task
        assert adapter.lesson_hook is None
    finally:
        await close(clients)


async def test_self_approval_manifest_archive_and_unchanged_readiness(db_engines):
    app, run, clients, row, config = await prepared(db_engines, self_approved=True)
    try:
        before = (await clients[0].get(f"/api/pipeline/{run}/results")).json()[
            "packages"
        ][0]
        adapter = StubAdapter(script=["{}"])
        app.state.lesson_runtime.bind(adapter, config, "architect")
        details = []
        await adapter.complete_json("base", attempt_observer=details.append)
        await persist_details(app, run, details)
        after = (await clients[0].get(f"/api/pipeline/{run}/results")).json()
        for key in (
            "status",
            "readiness_label",
            "review_reasons",
            "security_report",
            "validation_report",
            "downloadable",
        ):
            assert after["packages"][0][key] == before[key]
        assert after["packages"][0]["readiness_label"] == "pending_review"
        assert after["run"]["lessons"]["self_approved"]
        # An engineer decision remains the only existing route to download.
        reviewed = await clients[0].post(
            f"/api/pipeline/{run}/packages/cost/review",
            json={
                "action": "reject",
                "category": "other",
                "reason": "Retain blocking evidence.",
            },
        )
        assert reviewed.status_code == 200
        response = await clients[0].get(f"/api/pipeline/{run}/download/cost")
        with ZipFile(BytesIO(response.content)) as archive:
            manifest = json.loads(archive.read("_infraarchagent/LESSONS.json"))
            assert manifest["self_approved"] and manifest["entries"][0]["self_approved"]
            assert manifest["set_hash"] == config.lessons["set_hash"]
            assert manifest["calls"][0]["lesson_ids"] == [row["id"]]
            assert (
                "four-eyes review was off"
                in archive.read("INFRAARCHAGENT_READINESS.md").decode()
            )
            assert (
                "RAW_REASON_MUST_NEVER"
                not in archive.read("_infraarchagent/LESSONS.json").decode()
            )
    finally:
        await close(clients)


async def test_header_run_is_disabled_and_private_configuration_rejected(db_engines):
    app, run, clients, row, config = await prepared(db_engines)
    try:
        captured = []
        app.state.runner.start = lambda identity, text, configured: captured.append(
            configured
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1",
            headers={"X-API-Key": KEY},
        ) as header:
            response = await header.post(
                "/api/pipeline/run",
                json={"text": "Deploy an AWS web service with Terraform."},
            )
            assert response.status_code == 202, response.text
            configured = captured[0]
            assert (
                configured.lessons["lessons_enabled"] is False
                and configured.lessons["reason"] == "benchmark"
            )
            architect = app.state.runner.factory.create_architect(configured)
            assert architect.llm_adapter.lesson_hook is None
            for field in ("lessons", "lesson_run_id"):
                assert (
                    await header.post(
                        "/api/pipeline/run",
                        json={
                            "text": "Deploy an AWS web service with Terraform.",
                            "config": {
                                field: config.lessons
                                if field == "lessons"
                                else str(run)
                            },
                        },
                    )
                ).status_code == 400
            data = (
                await header.get(f"/api/pipeline/{response.json()['run_id']}/results")
            ).json()
            assert data["run"]["lessons"]["lessons_enabled"] is False
            events = await app.state.event_log.list_after(
                UUID(response.json()["run_id"]), None
            )
            assert (
                events[0].payload["lessons"]["set_hash"]
                == configured.lessons["set_hash"]
            )
    finally:
        await close(clients)
