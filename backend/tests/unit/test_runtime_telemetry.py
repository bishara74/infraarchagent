"""PR-01/05, FR-P-04, NFR-01: exact, isolated and source-free diagnostics."""

import asyncio
import json
import logging
import stat
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.telemetry import (
    Collector,
    current,
    interval_union,
    safe_records,
    scope,
    span,
    summary,
)
from app.domain.enums import Variant
from app.llm.base import LLMAdapter, LLMResponse, RetryPolicy
from app.scanners.runner import ToolFailure, ToolResult
from app.scanners.scan import Scanner, ScanResult
from app.validation.engine import BoundedRunner
from scripts.phase9c_metrics import attempt_details

pytestmark = pytest.mark.req("PR-01", "PR-05", "FR-P-04", "NFR-01")


@pytest.fixture
def collector():
    value = Collector()
    token = current.set(value)
    with scope(run_id=str(uuid4()), variant="cost", phase="security", role="fixer"):
        yield value
    current.reset(token)


class Adapter(LLMAdapter):
    provider = "openai"

    def __init__(self, responses):
        super().__init__(
            "synthetic", RetryPolicy(10, 2, 30, 0, 100), reasoning_effort="low"
        )
        self.responses = iter(responses)

    async def send_prompt(self, prompt, **kwargs):
        result = next(self.responses)
        if isinstance(result, BaseException):
            raise result
        return result

    def parse_response(self, response):
        return json.loads(response.text)


@pytest.mark.parametrize("tokens", [0, 17, None])
async def test_reasoning_survives_attempt_observer_and_export(collector, tokens):
    adapter = Adapter(
        [LLMResponse("{}", reasoning_tokens=tokens, served_by="synthetic")]
    )
    details = []
    await adapter.complete_json(
        "do not persist this prompt", attempt_observer=details.append
    )
    assert details[0].reasoning_tokens == tokens
    assert details[0].requested_effort == "low"  # legacy + capability false
    assert details[0].call_id == collector.records[0]["id"]
    assert details[0].run_id and details[0].phase == "security"
    exported = attempt_details([asdict(details[0])])[0]
    assert exported["reasoning_tokens"] == tokens
    assert exported["call_id"] == details[0].call_id
    assert "do not persist" not in json.dumps(collector.records)


async def test_failed_and_cancelled_llm_attempts_are_observed(collector):
    details = []
    adapter = Adapter(
        [
            LLMResponse("truncated", stop_reason="max_tokens", reasoning_tokens=9),
            LLMResponse("{}", reasoning_tokens=0),
        ]
    )
    await adapter.complete_json("test", attempt_observer=details.append)
    assert [d.reasoning_tokens for d in details] == [9, 0]
    assert [d.outcome for d in details] == ["truncated", "success"]
    entered = asyncio.Event()

    async def wait(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    adapter.send_prompt = wait
    task = asyncio.create_task(
        adapter.complete_json("test", attempt_observer=details.append)
    )
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert details[-1].outcome == "cancelled"
    assert details[-1].reasoning_tokens is None
    assert collector.records[-1]["outcome"] == "cancelled"


@pytest.mark.parametrize(
    "style,expected_effort,expected_format",
    [
        ("legacy", None, "off"),
        ("anthropic", "low", "json_schema"),
    ],
)
async def test_native_anthropic_metadata_reports_sent_options(
    collector, style, expected_effort, expected_format
):
    adapter = Adapter([LLMResponse("{}")])
    adapter.provider = "anthropic"
    adapter.request_style = style
    adapter.reasoning_capable = True
    adapter.structured_output = "json_schema"
    details = []
    await adapter.complete_json(
        "test", response_validator=lambda data: data, attempt_observer=details.append
    )
    assert details[0].requested_effort == expected_effort
    assert details[0].response_format == expected_format


def test_log_file_is_allowlisted_redacted_optional_and_idempotent(tmp_path):
    root = logging.getLogger()
    original = list(root.handlers)
    settings = get_settings().model_copy(
        update={
            "log_file": tmp_path / "calls.jsonl",
            "llm_api_key": SecretStr("private-canary"),
        }
    )
    try:
        configure_logging(settings)
        configure_logging(settings)
        logger = logging.getLogger("app.llm.base")
        record = {
            "kind": "llm",
            "model": "private-canary",
            "reasoning_tokens": 0,
            "prompt": "never write this",
            "headers": {"secret": "never write this"},
        }
        logger.info("raw private-canary body", extra={"llm_diagnostic": record})
        logger.error("never write this")
        logging.getLogger("other").info(
            "never write this", extra={"llm_diagnostic": record}
        )
        rows = [json.loads(line) for line in settings.log_file.read_text().splitlines()]
        assert rows == [{"kind": "llm", "model": "[REDACTED]", "reasoning_tokens": 0}]
        assert stat.S_IMODE(settings.log_file.stat().st_mode) == 0o600
        configure_logging(settings.model_copy(update={"log_file": None}))
        logger.info("disabled", extra={"llm_diagnostic": record})
        assert len(settings.log_file.read_text().splitlines()) == 1
    finally:
        for handler in list(root.handlers):
            if handler not in original:
                root.removeHandler(handler)
                handler.close()


def test_relative_log_path_and_write_failure_are_source_free(tmp_path, monkeypatch):
    from app.core import logging as log_module

    original = list(logging.getLogger().handlers)
    monkeypatch.setattr(log_module, "ROOT", tmp_path)
    settings = get_settings().model_copy(update={"log_file": Path("calls.jsonl")})
    try:
        configure_logging(settings)
        assert (tmp_path / "calls.jsonl").exists()
        handler = next(
            h
            for h in logging.getLogger().handlers
            if isinstance(h, log_module.LLMFileHandler)
        )

        def fail(value):
            raise OSError("untrusted disk message")

        monkeypatch.setattr(handler.stream, "write", fail)
        logging.getLogger("app.llm.base").info(
            "untrusted body",
            extra={"llm_diagnostic": {"kind": "llm", "reasoning_tokens": 0}},
        )
    finally:
        for handler in list(logging.getLogger().handlers):
            if handler not in original:
                logging.getLogger().removeHandler(handler)
                handler.close()


async def test_queue_cancellation_and_concurrent_variants_do_not_mix(collector):
    entered, release = asyncio.Event(), asyncio.Event()

    class Runner:
        async def run_command(self, *args, **kwargs):
            entered.set()
            await release.wait()
            return ToolResult("", "", 0, 0)

    semaphore = asyncio.Semaphore(1)
    bounded = BoundedRunner(Runner(), semaphore)

    async def one(variant):
        with scope(variant=variant):
            await bounded.run_command(
                "terraform", ["terraform", "validate"], Path("/tmp")
            )

    first = asyncio.create_task(one("cost"))
    await entered.wait()
    queued = asyncio.Event()
    original_acquire = semaphore.acquire

    async def acquire():
        queued.set()
        return await original_acquire()

    semaphore.acquire = acquire
    second = asyncio.create_task(one("security"))
    await queued.wait()
    second.cancel()
    with pytest.raises(asyncio.CancelledError):
        await second
    release.set()
    await first
    rows = {r["variant"]: r for r in collector.records if r["kind"] == "tool"}
    assert set(rows) == {"cost", "security"}
    assert rows["security"]["outcome"] == "cancelled"
    assert rows["security"]["executed"] is False
    assert rows["security"]["execution_seconds"] == 0
    assert rows["security"]["queue_seconds"] > 0
    assert rows["cost"]["executed"] and rows["cost"]["completed"]
    assert rows["cost"]["execution_seconds"] > 0


async def test_scan_retries_record_every_tool_attempt(collector):
    class Runner:
        def __init__(self):
            self.failed = False

        async def run(self, tool, root):
            if tool == "checkov" and not self.failed:
                self.failed = True
                raise ToolFailure(tool, "crash")
            return ToolResult("", "", 0, 0)

    scanner = Scanner(Runner())

    async def once(files, variant, iteration, attempt):
        results = await asyncio.gather(
            *(
                scanner.run_tool(
                    tool, Path("/tmp"), iteration=iteration, attempt=attempt
                )
                for tool in ["checkov", "trivy", "terraform"]
            ),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, BaseException):
                raise result
        return ScanResult([], {})

    scanner._once = once
    await scanner.scan({}, Variant.COST, iteration=3)
    tools = [r for r in collector.records if r["kind"] == "tool"]
    assert len(tools) == 6
    assert {r["attempt"] for r in tools} == {1, 2}
    assert all(r["iteration"] == 3 for r in tools)
    assert sum(r["outcome"] == "crash" for r in tools) == 1
    assert sum(r["kind"] == "scan" for r in collector.records) == 1
    collector.records.clear()
    with scope(iteration=4):
        await scanner.scan({}, Variant.COST)
    assert all(r["iteration"] == 4 for r in collector.records if r["kind"] == "tool")


def test_overlapping_intervals_and_nested_groups_are_not_added():
    def row(kind, start, finish):
        return {
            "kind": kind,
            "executed": True,
            "completed": True,
            "started_at": f"2026-10-20T00:00:{start:02d}+00:00",
            "finished_at": f"2026-10-20T00:00:{finish:02d}+00:00",
            "elapsed_seconds": finish - start,
        }

    tools = [row("tool", 0, 10), row("tool", 2, 7), row("tool", 12, 14)]
    assert interval_union(tools) == 12
    result = summary([*tools, row("partial_group", 0, 15)])
    assert result["tool_invocation_seconds"] == 17
    assert result["tool_wall_seconds"] == 12
    assert result["partial_group_seconds"] == 15


def test_partial_group_timing_cancellation_and_safe_fields(collector):
    with (
        pytest.raises(asyncio.CancelledError),
        span("partial_group", action="partial_group"),
    ):
        raise asyncio.CancelledError
    record = safe_records(
        [{**collector.records[-1], "stdout": "untrusted", "args": ["secret"]}]
    )[0]
    assert record["outcome"] == "cancelled" and record["completed"] is False
    assert record["elapsed_seconds"] >= 0
    assert "stdout" not in record and "args" not in record
    assert len(safe_records([record, record])) == 1


async def test_partial_group_report_counts_and_existing_cache(collector):
    from app.security.partial import accept_groups
    from tests.unit.test_security_partial import setup

    before = {
        "k8s/config.yaml": (
            "apiVersion: v1\nkind: ConfigMap\nmetadata:\n"
            "  name: test\ndata:\n  x: before\n"
        )
    }
    after = {"k8s/config.yaml": before["k8s/config.yaml"].replace("before", "after")}
    guard, checkpoint = setup(before)
    groups = []
    retained, _, _ = await accept_groups(
        guard, before, after, [], checkpoint.scan, 6, groups, checkpoint
    )
    assert retained == after
    assert groups[0]["evaluation_started"] and groups[0]["evaluation_completed"]
    assert groups[0]["evaluation_seconds"] >= 0
    assert summary(collector.records)["partial_groups_started"] == 1
    assert summary(collector.records)["partial_groups_completed"] == 1
    await guard.evaluate(before, after, [], ScanResult([], {}))
    assert guard.scanner.calls == 1
    assert any(r["kind"] == "cache" for r in collector.records)
    groups = []
    await accept_groups(
        guard, before, after, [], checkpoint.scan, 0, groups, checkpoint
    )
    assert not groups[0]["evaluation_started"]
    assert groups[0]["evaluation_seconds"] is None
    assert summary(collector.records)["partial_groups_unevaluated"] == 1


def test_legacy_capability_reporting_never_changes_frozen_settings():
    from app.domain.agent_selection import AgentSelection, reported_selections

    selection = AgentSelection(
        model="gpt-oss",
        provider="openai",
        thinking_mode="low",
        configured_thinking="low",
    )
    raw = {"fixer": selection.model_dump()}
    result = reported_selections(raw)
    assert result["fixer"]["reasoning_capable"] is None
    assert result["fixer"]["reasoning_capability_source"] == "unprobed"
    assert result["fixer"]["thinking_mode"] == "low"
    assert raw["fixer"]["reasoning_capable"] is False


def test_monotonic_invocation_times_separate_wait_and_execution(collector, monkeypatch):
    from app.core import telemetry

    clock = [0.0]
    monkeypatch.setattr(telemetry, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    with telemetry.invocation("terraform.init"):
        clock[0] = 4
        telemetry.queue_wait.get().append(4)
        telemetry.execution_started()
        clock[0] = 10
    row = collector.records[0]
    assert row["elapsed_seconds"] == 10
    assert row["queue_seconds"] == 4
    assert row["execution_seconds"] == 6
    assert row["attempt"] == 1


def test_estimate_accounts_for_generator_barrier_and_parallel_finishes(tmp_path):
    from scripts.phase9_runtime import estimate

    run_id = str(uuid4())
    events = []
    packages = []
    for variant, generated, finished in [
        ("cost", 10, 100),
        ("performance", 8, 98),
        ("security", 6, 96),
    ]:

        def stamp(seconds):
            from datetime import UTC, datetime, timedelta

            return (
                datetime(2026, 10, 20, tzinfo=UTC) + timedelta(seconds=seconds)
            ).isoformat()

        base = {"run_id": run_id, "variant": variant}
        events.extend(
            [
                {
                    **base,
                    "kind": "agent_state",
                    "agent": "generator_" + variant,
                    "status": "completed",
                    "timestamp": stamp(generated),
                },
                {
                    **base,
                    "kind": "package_status",
                    "status": "pending_review",
                    "timestamp": stamp(finished),
                },
                {
                    **base,
                    "kind": "stage_notice",
                    "measurement": {
                        "stage": "final_security_scan",
                        "duration_seconds": 2,
                    },
                },
            ]
        )
        rounds = (
            [
                {
                    "phase": phase,
                    "reason": "no_improvement",
                    "duration_seconds": 10,
                    "fixer_attempts": [{"elapsed_seconds": 2}],
                }
                for phase in ["generation", "before_security"]
            ]
            if variant == "cost"
            else []
        )
        packages.append(
            {
                "variant": variant,
                "validation_report": {"remediation": {"rounds": rounds}},
            }
        )
    (tmp_path / "events.json").write_text(json.dumps(events))
    (tmp_path / "results.json").write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": run_id,
                        "measurement": "pr01",
                        "complete": True,
                        "seconds": 100,
                    }
                ]
            }
        )
    )
    (tmp_path / (run_id + ".json")).write_text(json.dumps({"packages": packages}))
    result = estimate(tmp_path, tmp_path)
    assert result["estimated_median_seconds"] == 96
    assert result["runs"][0]["avoided_scan_batches"] == 4
    assert result["threshold_seconds"] == 300 and result["required_runs"] == 10
