"""Recorded/fake HTTP benchmark observations, without network services."""

import json
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from scripts.benchmark import (
    Harness,
    normalized_event,
    prompt_reference,
    prompts,
    settled,
    timings,
)
from scripts.phase9_budget import BudgetGuard, CreditSnapshot


def event(seq, agent, status, timestamp, kind="agent_state", variant=None):
    return normalized_event(
        {
            "seq": seq,
            "agent": agent,
            "status": status,
            "timestamp": timestamp,
            "kind": kind,
            "variant": variant,
            "payload": {"message": "canary-provider-body"},
        }
    )


def snapshot(status="production_ready", retry=False):
    return {
        "run": {"status": "partial_success", "provider": "stub", "model": "stub"},
        "packages": [{"variant": "cost", "status": status, "retry_in_progress": retry}],
    }


@pytest.mark.req("PR-01", "FR-P-04")
@pytest.mark.parametrize(
    "status,retry,expected",
    [
        ("scanning", False, False),
        ("valid", False, False),
        ("pending_review", False, True),
        ("pending_review", True, False),
        ("validating", False, False),
    ],
)
def test_settlement(status, retry, expected):
    assert settled(snapshot(status, retry)) is expected


@pytest.mark.req("PR-05")
def test_actual_orchestrator_package_events_and_agent_intervals():
    events = [
        event(1, "architect", "running", "2026-01-01T00:00:00+00:00"),
        event(2, "architect", "completed", "2026-01-01T00:00:10+00:00"),
        event(
            3,
            "orchestrator",
            "scanning",
            "2026-01-01T00:00:10+00:00",
            "package_status",
            "cost",
        ),
        event(
            4,
            "orchestrator",
            "remediating",
            "2026-01-01T00:00:20+00:00",
            "package_status",
            "cost",
        ),
        event(
            5,
            "orchestrator",
            "scanning",
            "2026-01-01T00:00:30+00:00",
            "package_status",
            "cost",
        ),
        event(
            6,
            "orchestrator",
            "scan_clean",
            "2026-01-01T00:00:40+00:00",
            "package_status",
            "cost",
        ),
    ]
    rows = timings("fixture", events)
    assert [row["seconds"] for row in rows] == [10, 20, 10]
    assert [row.get("terminal_scan_only") for row in rows] == [None, False, True]
    assert "canary-provider-body" not in json.dumps(events)


@pytest.mark.req("PR-01", "NFR-01")
async def test_early_terminal_snapshot_then_eof_active_and_replay(tmp_path):
    run_id = str(uuid4())
    states = iter([snapshot("scanning"), snapshot("pending_review", True), snapshot()])
    frames = [
        event(
            1,
            "orchestrator",
            "partial_success",
            "2026-01-01T00:00:00+00:00",
            "run_status",
        )
    ]
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "POST":
            assert json.loads(request.content)["config"] == {"provider": "stub"}
            return httpx.Response(202, json={"run_id": run_id})
        if request.url.path.endswith("/results"):
            return httpx.Response(200, json=next(states))
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text="id: 1\ndata: " + json.dumps(frames[0]) + "\n\n",
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        harness = Harness(client, output=tmp_path, sleep=lambda value: no_sleep())
        row = await harness.observe("AWS web service", "pr01")
    assert row["complete"] and len(harness.events) == 1
    assert any(request.headers.get("last-event-id") == "1" for request in requests)
    assert all(
        "canary-provider-body" not in path.read_text() for path in tmp_path.iterdir()
    )


async def no_sleep():
    pass


@pytest.mark.req("PR-03")
def test_secondary_prompt_reference_requires_matching_metadata():
    rows = [
        {
            "measurement": "pr01",
            "complete": True,
            "run_status": "partial_success",
            "mode": "stub",
            "provider": "stub",
            "model": "stub",
            "prompt": prompts()[0],
            "seconds": seconds,
            "run_id": str(index),
        }
        for index, seconds in enumerate([10, 20, 30, 40])
    ]
    reference = prompt_reference(rows, prompts()[0], "stub", "stub", "stub")
    assert reference["pr01_prompt_median_seconds"] == 25
    assert reference["pr01_reference_count"] == 4
    assert (
        prompt_reference(rows, prompts()[1], "stub", "stub", "stub")[
            "pr01_prompt_median_seconds"
        ]
        is None
    )
    rows[0]["complete"] = False
    assert (
        prompt_reference(rows, prompts()[0], "stub", "stub", "stub")[
            "pr01_prompt_median_seconds"
        ]
        == 30
    )


@pytest.mark.req("PR-03")
async def test_capacity_stops_before_submission():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"runner_capacity": 2})
        )
    ) as client:
        harness = Harness(client)
        await harness.pr03()
    assert not harness.rows and "capacity" in harness.stop_reason


@pytest.mark.req("PR-01", "NFR-01")
async def test_low_guard_stops_without_request_and_partial_summary(tmp_path):
    guard = BudgetGuard(Decimal(1))
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: pytest.fail("No pipeline request permitted")
        )
    ) as client:
        harness = Harness(client, mode="real", guard=guard, output=tmp_path)

        async def credit():
            return CreditSnapshot(Decimal(0), Decimal(".9"), True)

        harness.credit = credit
        await harness.pr01()
    assert not harness.rows and harness.stop_reason
    assert "INCOMPLETE" in (tmp_path / "summary.md").read_text()


@pytest.mark.req("PR-03")
def test_secondary_reference_does_not_change_spec_verdict(tmp_path):
    harness = Harness(None, output=tmp_path)
    baseline = {
        "measurement": "pr03",
        "run_id": "baseline",
        "role": "baseline",
        "seconds": 10,
        "complete": True,
        "run_status": "success",
    }
    harness.rows = [
        baseline,
        *[
            {
                "measurement": "pr03",
                "run_id": str(index),
                "role": "cohort",
                "seconds": 14,
                "complete": True,
                "run_status": "success",
                "ratio_to_baseline": 1.4,
                "ratio_to_pr01_prompt_median": 2.0,
                "pr01_prompt_median_seconds": 7,
                "pr01_reference_count": 4,
            }
            for index in range(3)
        ],
    ]
    harness.flush()
    text = (tmp_path / "summary.md").read_text()
    assert "pr03 threshold: PASS" in text and "secondary" in text


@pytest.mark.req("PR-01", "NFR-01")
async def test_first_cost_advisory_once_and_later_guard_overrides(tmp_path, capsys):
    from pydantic import SecretStr

    from scripts.phase9_budget import CreditReader

    run_id = str(uuid4())
    usage = 0
    posts = 0

    def handler(request):
        nonlocal usage, posts
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "usage": usage,
                        "limit_remaining": 50 - usage,
                        "label": "budget-canary-key",
                    }
                },
            )
        if request.method == "POST":
            posts += 1
            usage += 2 if posts == 1 else 20
            assert "config" not in json.loads(request.content)
            return httpx.Response(202, json={"run_id": run_id})
        if request.url.path.endswith("/results"):
            value = snapshot()
            value["run"].update(provider="openai", model="test-model")
            return httpx.Response(200, json=value)
        return httpx.Response(
            200, text="", headers={"content-type": "text/event-stream"}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        reader = CreditReader(
            client, "https://openrouter.ai/api/v1", SecretStr("budget-canary-key")
        )
        harness = Harness(
            client,
            mode="real",
            output=tmp_path,
            guard=BudgetGuard(Decimal(1), 14),
            credit_reader=reader,
        )
        await harness.pr01(10, following=[1, 3])
    assert posts == 2 and harness.stop_reason
    assert harness.advisory["measured_first_run_cost_usd"] == 2
    assert harness.advisory["projected_further_runs"] == 13
    captured = capsys.readouterr().out
    assert captured.count("First real run") == 1 and "remaining credit: 48" in captured
    assert all(
        "budget-canary-key" not in path.read_text() for path in tmp_path.iterdir()
    )
