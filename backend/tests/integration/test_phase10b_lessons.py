"""FR-S-02/07, FR-A-05, NFR-01: optional Fixer advisory scope and dispatch."""

import json
from uuid import uuid4

import pytest

from app.agents.budget import AgentBudget
from app.agents.security.fix import FixAgent
from app.core.lesson_runtime import LessonRuntime
from app.domain.enums import Variant
from app.domain.fixer_context import with_fixer_lessons
from app.domain.lessons import content_hash, empty_snapshot, render_lessons
from app.domain.run_config import RunConfig
from app.llm.stub import StubAdapter
from app.scanners.scan import ScanResult
from app.security.acceptance import CandidateGuard
from tests.integration.test_phase9l_governance import close
from tests.integration.test_phase9l_transport import prepared
from tests.unit.test_phase10b_conformance import finding, plan
from tests.unit.test_phase10b_fixer_wire import GOLDEN, capture
from tests.unit.test_security_partial import Scanner, Verifier

pytestmark = pytest.mark.req("FR-S-02", "FR-S-07", "FR-A-05", "NFR-01")


def test_explicit_scope_never_crosses_generator_fixer_boundary():
    rows = [
        {
            "id": str(i),
            "lesson_id": str(i),
            "revision": 1,
            "scope_role": role,
            "text": "Prefer operational clarity.",
        }
        for i, role in enumerate(["fixer", "all_generators", "generator_cost"])
    ]
    assert render_lessons(rows, "fixer")[1] == ["0"]
    assert render_lessons(rows, "generator_cost")[1] == ["1", "2"]
    assert render_lessons(rows, "architect")[1] == []


@pytest.mark.parametrize(
    "reason", ["benchmark", "server_disabled", "unconfigured", "empty_role"]
)
@pytest.mark.parametrize("mode", ["json_schema", "json_object", "off"])
async def test_no_fixer_lesson_preserves_version_8_wire_bytes(
    monkeypatch, reason, mode
):
    monkeypatch.setattr("app.agents.prompts.security_fix.token_hex", lambda _: "0" * 32)

    def forbidden(*args, **kwargs):
        pytest.fail("Empty Fixer scope must not query lesson governance")

    runtime = LessonRuntime(forbidden, None)
    snapshot = empty_snapshot(reason)
    if reason == "empty_role":
        entries = [
            {
                "id": "generator",
                "lesson_id": "generator",
                "revision": 1,
                "scope_role": "all_generators",
                "text": "Prefer clear names.",
                "self_approved": False,
            }
        ]
        snapshot.update(
            lessons_enabled=True,
            entries=entries,
            set_hash=content_hash(entries),
            disable_generation=0,
        )
    assert (
        await capture(
            mode,
            "security_fixer",
            runtime,
            RunConfig(lessons=snapshot, lesson_run_id=uuid4()),
        )
        == json.loads(GOLDEN.read_text())[mode + ":security_fixer"]
    )


@pytest.mark.parametrize(
    "kind", ["security_fixer", "validation_repair", "syntax_repair"]
)
async def test_fixer_call_records_scoped_provenance_and_context(db_engines, kind):
    app, run, clients, lesson, config = await prepared(
        db_engines, self_approved=True, role="fixer"
    )
    try:
        # Factory wiring and transport-level use must agree on the explicit role.
        assert (
            app.state.runner.factory.create_security_agent(
                config
            ).fix_agent.adapter.lesson_hook
            is not None
        )
        body = json.loads(
            await capture("json_schema", kind, app.state.lesson_runtime, config)
        )
        user = body["messages"][1]["content"]
        assert (
            user.index("<fixer_advisory")
            < user.index("<reviewer_lessons>")
            < user.index("</fixer_advisory")
        )
        assert lesson["text"] in user
        result = (await clients[0].get(f"/api/pipeline/{run}/results")).json()["run"][
            "lessons"
        ]
        assert result["used_lesson_ids"] == [lesson["id"]]
        assert all(
            c["role"] == "fixer"
            and c["block_hash"]
            == content_hash(render_lessons(config.lessons["entries"], "fixer")[0])
            for c in result["calls"]
        )
        await clients[0].put("/api/lessons/control", json={"enabled": False})
        again = json.loads(
            await capture("json_schema", kind, app.state.lesson_runtime, config)
        )
        assert "<reviewer_lessons>" not in again["messages"][1]["content"]
    finally:
        await close(clients)


async def test_advisory_cannot_authorize_an_exposure_violation(db_engines):
    app, _, clients, lesson, config = await prepared(
        db_engines,
        self_approved=True,
        role="fixer",
        text=(
            "Prefer internal load balancers even for services "
            "with planned internet access."
        ),
    )
    try:
        files = {"terraform/main.tf": 'resource "aws_lb" "edge" { internal = false }\n'}
        patch = {
            "file": {
                "path": "terraform/main.tf",
                "content": files["terraform/main.tf"].replace("false", "true"),
            },
            "edits": {},
            "new_files": {},
            "fixes": [],
        }
        adapter = StubAdapter(script=[json.dumps(patch)])
        app.state.lesson_runtime.bind(adapter, config, "fixer")
        proposal = await FixAgent(adapter, structured_output="off").propose(
            path="terraform/main.tf",
            files=files,
            findings=[finding()],
            plan=plan(),
            directive="Preserve exposure",
            remaining=30,
        )
        assert proposal.accepted and lesson["text"] in adapter.prompts[0]
        guard = CandidateGuard(
            Verifier(),
            Scanner(),
            Variant.SECURITY,
            AgentBudget(60),
            {
                "terraform_verification_seconds": 0.0,
                "security_verification_seconds": 0.0,
            },
            plan=plan(),
            targeted=[finding()],
        )
        result = await guard.evaluate(
            files,
            {"terraform/main.tf": proposal.content},
            [],
            ScanResult([finding()], {}),
        )
        assert result.reason is None
        from app.security.plan_conformance import assess_plan_conformance

        assert assess_plan_conformance(
            plan(), files, {"terraform/main.tf": proposal.content}
        ).conflicts
    finally:
        await close(clients)


def test_missing_or_ambiguous_context_never_gets_lessons():
    with pytest.raises(ValueError):
        with_fixer_lessons("untrusted source marker", "lesson")
