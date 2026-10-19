"""Selection, authenticated metadata, attempt reports and smoke scheduling."""

import argparse
import csv
import json

import httpx
import pytest
from pydantic import SecretStr

from app.core.generator_settings import GeneratorSettings
from scripts.benchmark import (
    Harness,
    arguments,
    normalized_event,
    parse_prompt_indices,
    prompts,
)
from scripts.phase9c_metrics import generator_evidence
from scripts.run_phase9_benchmarks import execute


def settings():
    return GeneratorSettings(
        max_output_tokens=8000,
        structured_output="json_schema",
        attempt_timeout_seconds=90.0,
        completion_timeout_seconds=150.0,
        generator_budget_seconds=150.0,
        llm_max_attempts=3,
        max_package_attempts=2,
    ).model_dump()


@pytest.mark.req("PR-01")
def test_prompt_cli_selection_and_validation():
    assert arguments().parse_args(
        ["pr01", "--prompts", "2,0", "--runs", "3"]
    ).prompts == [2, 0]
    for invalid in ("", "-1", "3", "0,0", "0,x", "0,"):
        with pytest.raises(argparse.ArgumentTypeError):
            parse_prompt_indices(invalid)


@pytest.mark.req("PR-01")
async def test_selected_prompts_cycle_in_order():
    selected = []
    async with httpx.AsyncClient() as client:
        harness = Harness(client)

        async def sequential(text, measurement, schedule, **kwargs):
            selected.append((text, kwargs["prompt_index"]))

        harness.sequential = sequential
        await harness.pr01(3, prompt_indices=[2, 0])
    assert selected == [(prompts()[2], 2), (prompts()[0], 0), (prompts()[2], 2)]


@pytest.mark.req("PR-01", "PR-05", "NFR-01")
@pytest.mark.parametrize("case", ["ok", "unauthorized", "malformed", "missing_key"])
async def test_benchmark_reads_authenticated_server_settings(case, tmp_path):
    (tmp_path / "environment.json").write_text("{}")
    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.path == "/api/benchmark/settings"
        assert request.headers["X-API-Key"] == "canary-placeholder"
        if case == "unauthorized":
            return httpx.Response(401, json={"message": "PRIVATE_BODY"})
        body = settings()
        if case == "malformed":
            body["max_output_tokens"] = "PRIVATE_BODY"
        return httpx.Response(200, json=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        harness = Harness(
            client,
            output=tmp_path,
            api_key=None if case == "missing_key" else SecretStr("canary-placeholder"),
        )
        accepted = await harness.capture_settings()
        harness.flush()
    assert accepted == (case == "ok")
    if accepted:
        assert (
            json.loads((tmp_path / "environment.json").read_text())[
                "generator_settings"
            ]
            == settings()
        )
    else:
        assert harness.stop_reason
        assert "generator_settings" not in json.loads(
            (tmp_path / "environment.json").read_text()
        )
    assert not requests if case == "missing_key" else len(requests) == 1
    assert all(
        "PRIVATE_BODY" not in p.read_text()
        and "canary-placeholder" not in p.read_text()
        for p in tmp_path.rglob("*")
        if p.is_file()
    )


def terminal(variant, outcome, reason, tokens, elapsed=1.0, overrun=0.0):
    return normalized_event(
        {
            "seq": 1,
            "kind": "agent_state",
            "agent": "generator_" + variant,
            "variant": variant,
            "status": "failed" if outcome != "success" else "completed",
            "timestamp": "2026-10-14T00:00:01+00:00",
            "payload": {
                "failure_category": "invalid_response"
                if outcome != "success"
                else None,
                "metrics": {
                    "llm_attempts": 1,
                    "elapsed_seconds": elapsed,
                    "deadline_exceeded": overrun > 0,
                    "overrun_seconds": overrun,
                    "llm_attempt_details": [
                        {
                            "attempt": 1,
                            "package_attempt": 1,
                            "outcome": outcome,
                            "category": "invalid_response"
                            if reason == "truncated"
                            else "success",
                            "format_reason": reason,
                            "output_tokens": tokens,
                            "input_tokens": 10,
                            "elapsed_seconds": 1.0,
                            "deadline_exceeded": overrun > 0,
                            "overrun_seconds": overrun,
                            "raw_text": "PRIVATE_BODY",
                        }
                    ],
                },
                "raw_text": "PRIVATE_BODY",
            },
        }
    )


@pytest.mark.req("PR-01", "PR-05", "NFR-01")
async def test_attempt_reports_include_failed_and_salvaged_generators(tmp_path):
    events = [
        terminal("cost", "truncated", "truncated", 8000),
        terminal("performance", "success", "salvaged", 100),
        terminal("security", "success", None, None, 151.0, 1.0),
    ]
    evidence = generator_evidence(events)
    assert evidence["generator_attempt_count"] == 3
    assert evidence["generator_attempts_by_format_reason"] == {
        "truncated": 1,
        "salvaged": 1,
        "none": 1,
    }
    assert evidence["failure_categories"] == {"cost": "invalid_response"}
    assert evidence["generator_deadlines"]["security"]["overrun_seconds"] == 1
    async with httpx.AsyncClient() as client:
        harness = Harness(client, output=tmp_path)
        harness.rows = [
            {
                "measurement": "pr01",
                "run_id": "fixture",
                "complete": True,
                "run_status": "partial_success",
                "seconds": 151.0,
                **evidence,
            }
        ]
        harness.events = events
        harness.flush()
    with (tmp_path / "results.csv").open(newline="") as handle:
        row = next(csv.DictReader(handle))
    assert json.loads(row["generator_attempts_by_format_reason"])["salvaged"] == 1
    assert (
        json.loads(row["generator_output_tokens_per_attempt"])[-1]["output_tokens"]
        is None
    )
    assert "invalid_response" in (tmp_path / "summary.md").read_text()
    assert "salvaged" in (tmp_path / "summary.md").read_text()
    assert all(
        "PRIVATE_BODY" not in p.read_text() for p in tmp_path.rglob("*") if p.is_file()
    )
    legacy = terminal("cost", "success", None, 10)
    legacy["metrics"].pop("llm_attempt_details")
    assert generator_evidence([legacy])["generator_attempt_count"] is None


@pytest.mark.req("PR-01", "NFR-01")
async def test_smoke_has_three_examples_and_no_other_measurements():
    calls = []

    class FakeHarness:
        stop_reason = None

        async def pr01(self, runs, **kwargs):
            calls.append((runs, kwargs))

        def flush(self):
            calls.append("flush")

    await execute(FakeHarness(), smoke=True)
    assert calls == [(3, {"following": [], "prompt_indices": [0, 1, 2]}), "flush"]
