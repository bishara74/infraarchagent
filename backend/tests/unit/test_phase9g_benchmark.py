"""PR-01/03 and NFR-01: quota stop, account balance and finite schedules."""

import json
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from scripts.benchmark import Harness
from scripts.phase9_budget import CreditReader
from scripts.run_phase9_benchmarks import execute


@pytest.mark.req("PR-01", "NFR-01")
@pytest.mark.parametrize("account", [0, 2, 20, None])
async def test_stricter_account_key_balance_with_unknown_fallback(account):
    paths = []

    def handler(request):
        paths.append(request.url.path)
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200, json={"data": {"usage": 1, "limit_remaining": 8}}
            )
        if account is None:
            return httpx.Response(503, json={"error": "UNTRUSTED"})
        return httpx.Response(
            200, json={"data": {"total_credits": 30, "total_usage": 30 - account}}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        value = await CreditReader(
            client, "https://fake.invalid/api/v1", SecretStr("canary-placeholder")
        ).read()
    assert (
        value.remaining == Decimal(min(8, account))
        if account is not None
        else value.remaining == Decimal(8)
    )
    assert value.account_remaining == (
        Decimal(account) if account is not None else None
    )
    assert paths == ["/api/v1/key", "/api/v1/credits"]
    assert "UNTRUSTED" not in str(value)


@pytest.mark.req("PR-01", "PR-03", "NFR-01")
@pytest.mark.parametrize(
    "stage", ["architect", "generator_cost", "security", "syntax", "submission"]
)
async def test_first_usage_limit_stops_set_and_marks_remainder_not_started(
    tmp_path, stage
):
    run = str(uuid4())
    posts = []
    agent = "generator_cost" if stage == "syntax" else stage
    kind = "stage_notice" if stage in {"security", "syntax"} else "agent_state"
    failure = {
        "seq": 1,
        "kind": kind,
        "agent": agent,
        "variant": "cost"
        if stage in {"generator_cost", "security", "syntax"}
        else None,
        "status": "remediating" if stage == "security" else "failed",
        "timestamp": "2026-10-19T00:00:00+00:00",
        "payload": {"failure_category": "usage_limit"},
    }
    terminal = {
        "seq": 2,
        "kind": "run_status",
        "agent": "orchestrator",
        "variant": None,
        "status": "failed",
        "timestamp": "2026-10-19T00:00:01+00:00",
        "payload": {},
    }

    def handler(request):
        if request.method == "POST":
            posts.append(request.url.path)
            return (
                httpx.Response(402, json={"error": "UNTRUSTED"})
                if stage == "submission"
                else httpx.Response(202, json={"run_id": run})
            )
        if request.url.path.endswith("/results"):
            return httpx.Response(
                200,
                json={
                    "run": {"status": "failed", "provider": "stub", "model": "stub"},
                    "packages": [],
                    "missing_variants": [],
                },
            )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text="".join(
                "data: " + json.dumps(e) + "\n\n" for e in [failure, terminal]
            ),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        harness = Harness(client, output=tmp_path)
        await execute(harness)
    assert len(posts) == 1
    assert len(harness.rows) == 14
    assert sum(r.get("execution_status") == "not_started" for r in harness.rows) == 13
    assert all(
        r.get("run_id") is None
        and r.get("seconds") is None
        and r.get("cost_usd") is None
        for r in harness.rows
        if r.get("execution_status") == "not_started"
    )
    assert "usage_limit" in harness.stop_reason
    summary = (tmp_path / "summary.md").read_text()
    assert "usage_limit" in summary and "not_started" in summary
    assert "UNTRUSTED" not in summary


@pytest.mark.req("PR-01", "NFR-01")
@pytest.mark.parametrize("target", ["bench-real", "bench-smoke", "bench-stub"])
def test_make_forwards_all_benchmark_parameters(tmp_path, target):
    import os
    import subprocess
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    # Execute each real Make recipe with an isolated interpreter probe.
    interpreter = tmp_path / ".venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text(
        '#!/bin/sh\nprintf "%s|%s|%s" '
        '"$PHASE9_BASE_URL" "$PHASE9_BUDGET" "$PHASE9_MAX_RUNS"\n'
    )
    interpreter.chmod(0o700)
    result = subprocess.run(
        [
            "make",
            "--no-print-directory",
            target,
            "BASE_URL=http://127.0.0.1:9876",
            "BUDGET=3",
            "MAX_RUNS=2",
            f"BACKEND=cd {tmp_path} &&",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        env={"PATH": os.defpath},
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith("http://127.0.0.1:9876|3|2")


@pytest.mark.req("PR-01", "NFR-01")
@pytest.mark.parametrize("cap,expected", [(None, 3), (1, 1), (2, 2), (8, 3)])
def test_smoke_cli_respects_smaller_cap(monkeypatch, cap, expected):
    from scripts import run_phase9_benchmarks as suite

    captured = []

    async def fake_run(args):
        captured.append(args.max_runs)

    args = ["bench", "real", "--smoke", "--budget-usd", "2"]
    if cap is not None:
        args.extend(["--max-runs", str(cap)])
    monkeypatch.setenv("PHASE9_MAX_RUNS", "")
    monkeypatch.setattr("sys.argv", args)
    monkeypatch.setattr(suite, "run", fake_run)
    suite.main()
    assert captured == [expected]
