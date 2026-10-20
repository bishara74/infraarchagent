"""FR-P-04/NFR-01: telemetry is durable, deduplicated and returned by results."""

from uuid import uuid4

import httpx
import pytest

from app.core.config import get_settings
from app.core.telemetry import Collector, current, scope, span
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider
from app.llm.base import LLMResponse
from app.main import create_app
from app.pipeline.telemetry import publish
from tests.unit.test_runtime_telemetry import Adapter


@pytest.mark.req("FR-P-04", "NFR-01", "PR-01")
async def test_observed_calls_and_tools_survive_events_results_and_exports(db_engines):
    app = create_app(get_settings(), db_engines[0])
    sessions = make_session_factory(db_engines[0])
    async with sessions() as session, session.begin():
        run = await RunRepository(session).create(
            "Deploy an AWS web app", LLMProvider.STUB, 3
        )
        run_id = run.run_id
    collector = Collector()
    token = current.set(collector)
    try:
        with scope(run_id=str(run_id), role="architect", phase="pipeline"):
            await Adapter([LLMResponse("{}", reasoning_tokens=0)]).complete_json(
                "private input"
            )
        with scope(
            run_id=str(run_id), role="security", variant="cost", phase="security"
        ):
            with span("partial_group"):
                with span(
                    "tool",
                    operation="checkov",
                    queue_seconds=0,
                    execution_started_at="2026-10-20T00:00:00+00:00",
                ):
                    pass
        await publish(app.state.writer, run_id)
        await publish(app.state.writer, run_id)
    finally:
        current.reset(token)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        data = (await client.get(f"/api/pipeline/{run_id}/results")).json()
        other = await client.get(f"/api/pipeline/{uuid4()}/results")
    rows = data["telemetry"]
    assert len(rows) == 3
    assert len({r["id"] for r in rows}) == 3
    assert all(r["run_id"] == str(run_id) for r in rows)
    assert next(r for r in rows if r["kind"] == "llm")["reasoning_tokens"] == 0
    assert "private input" not in str(data)
    assert other.status_code == 404
    from scripts.benchmark import Harness, normalized_event

    harness = Harness(None)
    row = {"run_id": str(run_id)}
    harness.finish(row, data, [], 1)
    assert row["runtime_attribution"]["tool_invocations"] == 1
    assert row["telemetry"] == rows
    exported = normalized_event(
        {
            "seq": 1,
            "kind": "stage_notice",
            "agent": "orchestrator",
            "status": "running",
            "variant": None,
            "timestamp": "2026-10-20T00:00:00+00:00",
            "payload": {"telemetry": rows},
        }
    )
    assert exported["telemetry"] == rows
