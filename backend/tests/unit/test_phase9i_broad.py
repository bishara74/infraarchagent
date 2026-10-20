"""PR-01/05, NFR-01: broad schedules use shared guards and safe evidence."""

import json
import subprocess
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from scripts.benchmark import Harness
from scripts.phase9_budget import BudgetGuard
from scripts.phase9_common import ROOT
from scripts.phase9i_broad import (
    METADATA_FIELDS,
    SCENARIO_PATH,
    broad_schedule,
    execute_broad,
    registered_scenarios,
    scenario_digest,
)

pytestmark = pytest.mark.req("PR-01", "PR-05", "NFR-01")


def slots(repetitions=2):
    data, raw, _ = registered_scenarios()
    return broad_schedule(data, repetitions, scenario_digest(raw))


def test_rounds_alternate_and_registration_hash_matches():
    data, raw, revision = registered_scenarios()
    planned = slots(3)
    assert len(revision) == 40
    assert [r["scenario_id"] for r in planned[:20]] == data["schedule"]["default_order"]
    assert [r["scenario_id"] for r in planned[20:]] == list(range(1, 11))
    assert [r["sequence"] for r in planned] == list(range(1, 31))
    assert {r["scenario_sha256"] for r in planned} == {scenario_digest(raw)}
    with pytest.raises(ValueError):
        broad_schedule(data, 0, "digest")


def test_registration_rejects_dirty_and_untracked_file(tmp_path):
    def git(*args):
        subprocess.run(
            ["git", "-C", str(tmp_path), *args], check=True, capture_output=True
        )

    git("init", "-q")
    path = tmp_path / SCENARIO_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes((ROOT / SCENARIO_PATH).read_bytes())
    with pytest.raises(ValueError, match="committed"):
        registered_scenarios(tmp_path)
    git("add", SCENARIO_PATH)
    git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "registration",
    )
    registered_scenarios(tmp_path)
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="committed"):
        registered_scenarios(tmp_path)


@pytest.mark.parametrize("stop", [None, "submission", "event", "guard", "settings"])
async def test_broad_execution_evidence_and_stop_slots(tmp_path, stop):
    posts = []
    run = None

    def handler(request):
        nonlocal run
        if request.method == "POST":
            posts.append(json.loads(request.content))
            if stop == "submission":
                return httpx.Response(402, json={"error": "CANARY-RAW-BODY"})
            run = str(uuid4())
            return httpx.Response(202, json={"run_id": run})
        if request.url.path.endswith("/results"):
            return httpx.Response(
                200,
                json={
                    "run": {"status": "success", "provider": "stub", "model": "stub"},
                    "packages": [
                        {
                            "variant": v,
                            "status": "checks_passed",
                            "retry_in_progress": False,
                            "validation_report": {"summary": {"result": "valid"}},
                        }
                        for v in ("cost", "performance", "security")
                    ],
                },
            )
        frames = []
        for i, (agent, status) in enumerate(
            [
                ("architect", "running"),
                ("architect", "completed"),
                ("orchestrator", "success"),
            ],
            1,
        ):
            frames.append(
                {
                    "seq": i,
                    "kind": "run_status" if i == 3 else "agent_state",
                    "agent": agent,
                    "status": status,
                    "variant": None,
                    "timestamp": f"2026-10-21T00:00:0{i}+00:00",
                    "payload": {"failure_category": "usage_limit"}
                    if stop == "event" and i == 2
                    else {},
                }
            )
        return httpx.Response(
            200, text="".join("data: " + json.dumps(f) + "\n\n" for f in frames)
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        harness = Harness(
            client,
            output=tmp_path,
            guard=BudgetGuard(Decimal(0), 1) if stop == "guard" else None,
        )
        if stop == "settings":
            harness.stop_reason = "Settings unavailable"
        planned = slots()
        await execute_broad(harness, planned)
    expected_posts = 20 if stop is None else 0 if stop == "settings" else 1
    assert len(posts) == expected_posts
    assert len(harness.rows) == 20
    assert not harness.cohorts
    for actual, expected in zip(harness.rows, planned, strict=True):
        assert all(actual[k] == expected[k] for k in METADATA_FIELDS)
        assert actual["prompt"] == expected["prompt"]
    assert sum(r.get("execution_status") == "not_started" for r in harness.rows) == (
        20 - expected_posts
    )
    for row in harness.agent_rows + harness.events:
        assert all(k in row for k in METADATA_FIELDS)
    for path in (tmp_path / "quality").glob("*/*.json"):
        assert all(k in json.loads(path.read_text()) for k in METADATA_FIELDS)
    summary = (tmp_path / "summary.md").read_text()
    assert "pr01 threshold:" not in summary
    assert "pr03" not in summary.lower()
    assert "CANARY-RAW-BODY" not in summary
    if posts:
        assert "descriptive timing only" in summary
    if stop is None:
        assert "PR-05 individual thresholds: PASS" in summary
        assert len(json.loads((tmp_path / "results.json").read_text())["runs"]) == 20


def test_make_broad_forwards_parameters(tmp_path):
    probe = tmp_path / ".venv/bin/python"
    probe.parent.mkdir(parents=True)
    probe.write_text(
        '#!/bin/sh\nprintf "%s|%s|%s|%s" "$PHASE9_BASE_URL" '
        '"$PHASE9_BUDGET" "$PHASE9_RUNS_PER_SCENARIO" "$*"\n'
    )
    probe.chmod(0o700)
    result = subprocess.run(
        [
            "make",
            "--no-print-directory",
            "bench-broad",
            f"VENV={tmp_path / '.venv'}",
            f"BACKEND=cd {tmp_path} &&",
            "MODE=stub",
            "BASE_URL=http://127.0.0.1:9999",
            "BUDGET=3",
            "RUNS_PER_SCENARIO=4",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        "http://127.0.0.1:9999|3|4|-m scripts.run_phase9_benchmarks stub --broad"
        in result.stdout
    )


@pytest.mark.parametrize("mode,repetitions", [("real", 2), ("stub", 1), ("stub", 3)])
def test_broad_cli_has_explicit_finite_run_bound(monkeypatch, mode, repetitions):
    import sys

    from scripts import run_phase9_benchmarks as runner

    captured = []

    async def run(args):
        captured.append(args)

    monkeypatch.setattr(runner, "run", run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark",
            mode,
            "--broad",
            "--budget-usd",
            "2",
            "--runs-per-scenario",
            str(repetitions),
        ],
    )
    runner.main()
    assert captured[0].max_runs == 10 * repetitions


@pytest.mark.parametrize(
    "extra", [["--runs-per-scenario", "0"], ["--smoke"], ["--max-runs", "0"]]
)
def test_broad_cli_rejects_invalid_schedule_before_submission(monkeypatch, extra):
    import sys

    from scripts import run_phase9_benchmarks as runner

    monkeypatch.setattr(sys, "argv", ["benchmark", "stub", "--broad", *extra])
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2
