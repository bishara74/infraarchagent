"""HTTP measurement harness. Real mode is author-only; tests use fake transports."""

import argparse
import asyncio
import csv
import json
import math
import os
import statistics
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.core.logging import RedactingFilter
from app.domain.enums import AgentName, PackageStatus, RunStatus
from scripts.phase9_budget import (
    BudgetGuard,
    CreditError,
    CreditReader,
    CreditSnapshot,
    affordability,
    measured_cost,
    numeric,
)
from scripts.phase9_common import ROOT, evidence_directory, safe_main, write_json
from scripts.phase9_report import statistics_for, summary, write_csv

TERMINAL = {"success", "partial_success", "failed"}
SETTLED = {"pending_review", "production_ready", "not_production_ready", "scan_error"}
EVENT_KINDS = {
    "agent_state",
    "package_status",
    "run_status",
    "package_generated",
    "stage_notice",
    "plan_created",
}
VARIANTS = ("cost", "performance", "security")


def prompts() -> list[str]:
    return json.loads((ROOT / "docs/phase9-prompts.json").read_text())["prompts"]


def settled(snapshot: dict) -> bool:
    return snapshot.get("run", {}).get("status") in TERMINAL and all(
        package.get("status") in SETTLED and package.get("retry_in_progress") is False
        for package in snapshot.get("packages", [])
    )


def normalized_event(item: dict) -> dict:
    if (
        type(item.get("seq")) is not int
        or item["seq"] < 1
        or item.get("kind") not in EVENT_KINDS
    ):
        raise ValueError("Invalid event")
    if item.get("agent") not in {name.value for name in AgentName}:
        raise ValueError("Invalid agent")
    variant = item.get("variant")
    if variant not in (*VARIANTS, None):
        raise ValueError("Invalid variant")
    status = item.get("status")
    if status not in {value.value for value in PackageStatus} | {
        value.value for value in RunStatus
    } | {"pending", "running", "completed", "failed"}:
        raise ValueError("Invalid status")
    timestamp = datetime.fromisoformat(item["timestamp"])
    if timestamp.tzinfo is None:
        raise ValueError("Naive timestamp")
    payload = item.get("payload", {})
    payload = payload if isinstance(payload, dict) else {}
    metrics = payload.get("metrics", {})
    metrics = metrics if isinstance(metrics, dict) else {}
    return {
        "seq": item["seq"],
        "kind": item["kind"],
        "agent": item["agent"],
        "variant": variant,
        "status": status,
        "timestamp": timestamp.isoformat(),
        "iteration": payload.get("iteration")
        if type(payload.get("iteration")) is int
        else None,
        "metrics": {
            name: value if type(value) is int and value >= 0 else None
            for name, value in metrics.items()
            if name
            in {"llm_attempts", "input_tokens", "output_tokens", "cached_input_tokens"}
        },
    }


def duration(start: str, end: str) -> float | None:
    value = (
        datetime.fromisoformat(end) - datetime.fromisoformat(start)
    ).total_seconds()
    return value if value >= 0 else None


def timings(run_id: str, events: list[dict]) -> list[dict]:
    starts, scans, rows, indexes = {}, {}, [], {}
    for event in sorted(events, key=lambda event: event["seq"]):
        key = (event["agent"], event["variant"])
        if event["kind"] == "agent_state":
            if event["status"] == "running":
                starts[key] = event["timestamp"]
            elif event["status"] in {"completed", "failed"} and key in starts:
                elapsed = duration(starts.pop(key), event["timestamp"])
                limit = (
                    150
                    if event["agent"] == "architect"
                    or event["agent"].startswith("generator_")
                    else None
                )
                rows.append(
                    {
                        "run_id": run_id,
                        "agent": event["agent"],
                        "variant": event["variant"],
                        "iteration": None,
                        "seconds": elapsed,
                        "complete": elapsed is not None,
                        "threshold_seconds": limit,
                        "pass": elapsed <= limit
                        if limit is not None and elapsed is not None
                        else None,
                    }
                )
        if event["kind"] == "package_status" and event["variant"] is not None:
            variant = event["variant"]
            if event["status"] == "scanning":
                if variant in scans:
                    elapsed = duration(scans.pop(variant), event["timestamp"])
                    rows.append(
                        {
                            "run_id": run_id,
                            "agent": "security_iteration",
                            "variant": variant,
                            "iteration": indexes.get(variant, 0),
                            "seconds": elapsed,
                            "complete": elapsed is not None,
                            "terminal_scan_only": False,
                            "threshold_seconds": 60,
                            "pass": elapsed <= 60 if elapsed is not None else None,
                        }
                    )
                    indexes[variant] = indexes.get(variant, 0) + 1
                scans[variant] = event["timestamp"]
            elif (
                event["status"] in {"scan_clean", "scan_exhausted", "scan_error"}
                and variant in scans
            ):
                elapsed = duration(scans.pop(variant), event["timestamp"])
                rows.append(
                    {
                        "run_id": run_id,
                        "agent": "security_iteration",
                        "variant": variant,
                        "iteration": indexes.get(variant, 0),
                        "seconds": elapsed,
                        "complete": elapsed is not None,
                        "terminal_scan_only": True,
                        "threshold_seconds": 60,
                        "pass": elapsed <= 60 if elapsed is not None else None,
                    }
                )
    for agent, variant in starts:
        rows.append(
            {
                "run_id": run_id,
                "agent": agent,
                "variant": variant,
                "seconds": None,
                "complete": False,
            }
        )
    for variant in scans:
        rows.append(
            {
                "run_id": run_id,
                "agent": "security_iteration",
                "variant": variant,
                "iteration": indexes.get(variant, 0),
                "seconds": None,
                "complete": False,
            }
        )
    return rows


def eligible(row: dict) -> bool:
    return row.get("complete") is True and row.get("run_status") in {
        "success",
        "partial_success",
    }


def prompt_reference(
    rows: list[dict], text: str, mode: str, provider: str, model: str | None
) -> dict:
    selected = [
        row
        for row in rows
        if eligible(row)
        and row.get("prompt") == text
        and row.get("mode") == mode
        and row.get("provider") == provider
        and row.get("model") == model
        and row.get("measurement") == "pr01"
    ]
    values = [
        row["seconds"]
        for row in selected
        if isinstance(row.get("seconds"), (float, int)) and row["seconds"] > 0
    ]
    return {
        "pr01_prompt_median_seconds": statistics.median(values) if values else None,
        "pr01_reference_count": len(values),
        "pr01_reference_run_ids": [row["run_id"] for row in selected],
    }


class Harness:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str = "http://127.0.0.1:8000",
        mode: str = "stub",
        timeout: float = 1800,
        clock=time.perf_counter,
        sleep=asyncio.sleep,
        guard: BudgetGuard | None = None,
        credit_reader: CreditReader | None = None,
        api_key: SecretStr | None = None,
        output: Path | None = None,
    ):
        self.client, self.base_url, self.mode = client, base_url.rstrip("/"), mode
        self.timeout, self.clock, self.sleep = timeout, clock, sleep
        self.guard, self.credit_reader, self.output = guard, credit_reader, output
        self.headers = {"X-API-Key": api_key.get_secret_value()} if api_key else {}
        self.redactor = RedactingFilter(
            api_key.get_secret_value() if api_key else None,
            credit_reader.key.get_secret_value() if credit_reader else "",
        )
        self.rows, self.agent_rows, self.events, self.cohorts = [], [], [], []
        self.stop_reason = None
        self.advisory = None
        self.capacity = None
        self.fixing_model = None
        self.expected_provider = None

    async def credit(self) -> CreditSnapshot:
        return (
            await self.credit_reader.read() if self.credit_reader else CreditSnapshot()
        )

    def flush(self) -> None:
        if self.output is None:
            return
        metadata_path = self.output / "environment.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
            measured = next((row for row in self.rows if row.get("provider")), None)
            if measured:
                metadata.update(
                    provider=measured["provider"],
                    model=measured["model"],
                    fixing_model=self.fixing_model,
                )
            write_json(metadata_path, metadata)
        write_json(
            self.output / "results.json",
            {
                "runs": self.rows,
                "cohorts": self.cohorts,
                "runner_capacity": self.capacity,
                "stop_reason": self.stop_reason,
            },
        )
        write_json(self.output / "events.json", self.events)
        write_csv(
            self.output / "results.csv",
            self.rows,
            list(
                dict.fromkeys(
                    [
                        "measurement",
                        "run_id",
                        "prompt",
                        "mode",
                        "seconds",
                        "complete",
                        "run_status",
                        "provider",
                        "model",
                        "cost_usd",
                        "cost_attribution",
                        "cost_before_usd",
                        "cost_after_usd",
                        "remaining_before_usd",
                        "remaining_after_usd",
                        "ratio_to_baseline",
                        "ratio_to_pr01_prompt_median",
                        "pr01_prompt_median_seconds",
                        "pr01_reference_count",
                        "cost_variant_status",
                        "performance_variant_status",
                        "security_variant_status",
                        "generator_llm_attempts",
                        "generator_input_tokens",
                        "generator_output_tokens",
                        "fixer_input_tokens",
                        "fixer_output_tokens",
                    ]
                    + [key for row in self.rows for key in row]
                )
            ),
        )
        write_csv(
            self.output / "agents.csv",
            self.agent_rows,
            list(
                dict.fromkeys(
                    [
                        "run_id",
                        "agent",
                        "variant",
                        "iteration",
                        "seconds",
                        "complete",
                        "threshold_seconds",
                        "pass",
                        "terminal_scan_only",
                    ]
                    + [key for row in self.agent_rows for key in row]
                )
            ),
        )
        lines, checks = [], []
        for measurement in ("pr01", "pr03", "pr04"):
            rows = [row for row in self.rows if row["measurement"] == measurement]
            if not rows:
                continue
            valid = [
                row
                for row in rows
                if eligible(row) or measurement == "pr04" and row["complete"]
            ]
            stats = statistics_for([row["seconds"] for row in valid])
            lines.append(
                f"{measurement}: {json.dumps(stats)}; "
                f"failed/incomplete: {len(rows) - len(valid)}."
            )
            if measurement == "pr01":
                verdict = (
                    "INCOMPLETE"
                    if len(valid) < 10
                    else "PASS"
                    if stats["median"] <= 300
                    else "FAIL"
                )
            elif measurement == "pr03":
                cohort = [row for row in rows if row.get("role") == "cohort"]
                verdict = (
                    "INCOMPLETE"
                    if len(cohort) != 3
                    or not all(
                        eligible(row) and row.get("ratio_to_baseline") is not None
                        for row in cohort
                    )
                    else "PASS"
                    if all(row["ratio_to_baseline"] <= 1.5 for row in cohort)
                    else "FAIL"
                )
                lines.append(
                    "PR-03 uses the isolated baseline; PR-01 ratios are secondary."
                )
                for row in cohort:
                    lines.append(
                        "Cohort references: "
                        + json.dumps(
                            {
                                key: row.get(key)
                                for key in (
                                    "run_id",
                                    "ratio_to_baseline",
                                    "ratio_to_pr01_prompt_median",
                                    "pr01_prompt_median_seconds",
                                    "pr01_reference_count",
                                )
                            }
                        )
                    )
            else:
                verdict = (
                    "INCOMPLETE"
                    if len(valid) != len(rows)
                    else "PASS"
                    if stats["max"] <= 2
                    else "FAIL"
                )
            checks.append(verdict)
            lines.append(f"{measurement} threshold: {verdict}.")
        limited = [
            row for row in self.agent_rows if row.get("threshold_seconds") is not None
        ]
        if limited:
            verdict = (
                "FAIL"
                if any(row.get("pass") is False for row in limited)
                else "INCOMPLETE"
                if any(row.get("pass") is None for row in limited)
                else "PASS"
            )
            checks.append(verdict)
            lines.append(
                f"PR-05 individual thresholds: {verdict}. "
                "Missing metrics unknown; Validator descriptive."
            )
        known = sum(row.get("cost_usd") or 0 for row in self.rows) + sum(
            cohort.get("cost_usd") or 0 for cohort in self.cohorts
        )
        lines.append(f"Measured known cost: ${known:.6f}; unknown costs stay unknown.")
        for cohort in self.cohorts:
            lines.append("Concurrent costs: " + json.dumps(cohort))
        if self.advisory:
            write_json(self.output / "first_real_run_advisory.json", self.advisory)
            lines.append(
                "First-run affordability advisory: " + json.dumps(self.advisory)
            )
        if self.stop_reason:
            lines.append("Stopped: " + self.stop_reason)
        status = (
            "INCOMPLETE"
            if self.stop_reason
            else "FAIL"
            if "FAIL" in checks
            else "INCOMPLETE"
            if "INCOMPLETE" in checks or not checks
            else "PASS"
        )
        summary(
            self.output / "summary.md",
            "Phase 9 benchmark",
            status,
            [
                "Mode: "
                + (
                    "stub rehearsal; system overhead only."
                    if self.mode == "stub"
                    else "real"
                ),
                *lines,
            ],
        )

    async def snapshot(self, run_id: str) -> dict:
        response = await self.client.get(
            f"{self.base_url}/api/pipeline/{run_id}/results", headers=self.headers
        )
        if response.status_code != 200:
            raise RuntimeError("Results check failed")
        value = response.json()
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("run"), dict)
            or not isinstance(value.get("packages"), list)
        ):
            raise ValueError("Results response unusable")
        return value

    async def observe(self, text: str, measurement: str, **extra: Any) -> dict:
        started = self.clock()
        row = {
            "measurement": measurement,
            "prompt": text,
            "mode": self.mode,
            "run_id": None,
            "seconds": None,
            "complete": False,
            "submitted_at": datetime.now(UTC).isoformat(),
            **extra,
        }
        local = []
        self.rows.append(row)
        try:
            body = {"text": text}
            if self.mode == "stub":
                body["config"] = {"provider": "stub"}
            response = await self.client.post(
                self.base_url + "/api/pipeline/run", json=body, headers=self.headers
            )
            if response.status_code != 202:
                raise RuntimeError("Pipeline submission rejected")
            run_id = str(UUID(response.json()["run_id"]))
            row["run_id"] = run_id
            if self.guard:
                self.guard.submitted += 1
            cursor = 0
            async with asyncio.timeout(self.timeout):
                while True:
                    headers = {
                        **self.headers,
                        **({"Last-Event-ID": str(cursor)} if cursor else {}),
                    }
                    try:
                        async with self.client.stream(
                            "GET",
                            f"{self.base_url}/api/pipeline/{run_id}/stream",
                            headers=headers,
                        ) as stream:
                            if stream.status_code != 200:
                                raise RuntimeError("Stream request rejected")
                            data = []
                            async for line in stream.aiter_lines():
                                if line.startswith("data:"):
                                    data.append(line[5:].lstrip(" "))
                                elif line == "" and data:
                                    event = normalized_event(
                                        json.loads("\n".join(data))
                                    )
                                    data = []
                                    if event["seq"] <= cursor:
                                        continue
                                    cursor = event["seq"]
                                    local.append(event)
                                    self.events.append({"run_id": run_id, **event})
                                    if (
                                        event["kind"] == "run_status"
                                        and event["status"] in TERMINAL
                                    ):
                                        snapshot = await self.snapshot(run_id)
                                        if settled(snapshot):
                                            self.finish(
                                                row,
                                                snapshot,
                                                local,
                                                self.clock() - started,
                                            )
                                            return row
                        snapshot = await self.snapshot(run_id)
                        if settled(snapshot):
                            self.finish(row, snapshot, local, self.clock() - started)
                            return row
                    except (httpx.HTTPError, RuntimeError):
                        pass
                    await self.sleep(0.5)
        except (TimeoutError, httpx.HTTPError, RuntimeError, ValueError, KeyError):
            row["failure"] = "Run could not be observed to confirmed settlement."
            self.stop_reason = row["failure"]
        finally:
            if not row["complete"] and row["run_id"]:
                self.agent_rows.extend(timings(row["run_id"], local))
            self.flush()
        return row

    def finish(
        self, row: dict, snapshot: dict, local: list[dict], elapsed: float
    ) -> None:
        run = snapshot["run"]
        provider = run.get("provider")
        if (
            provider not in {"stub", "openai", "anthropic"}
            or self.mode == "stub"
            and provider != "stub"
        ):
            raise ValueError("Provider mismatch")
        if self.expected_provider and provider != self.expected_provider:
            raise ValueError("Server provider differs from measurement configuration")
        row.update(
            seconds=elapsed,
            settled_at=datetime.now(UTC).isoformat(),
            complete=True,
            run_status=run["status"],
            provider=provider,
            model=self.redactor.redact(run.get("model") or ""),
        )
        for variant in VARIANTS:
            package = next(
                (p for p in snapshot["packages"] if p["variant"] == variant), None
            )
            row[variant + "_variant_status"] = (
                package["status"] if package else "not_generated"
            )
        self.agent_rows.extend(timings(row["run_id"], local))
        generated = [e["metrics"] for e in local if e["kind"] == "package_generated"]
        for field in ("llm_attempts", "input_tokens", "output_tokens"):
            values = [numeric(m.get(field)) for m in generated]
            row["generator_" + field] = (
                int(sum(values))
                if values and all(v is not None for v in values)
                else None
            )
        fixes = []
        for package in snapshot["packages"]:
            report = package.get("security_report")
            if isinstance(report, dict):
                for session in report.get("sessions", []):
                    if session.get("kind") == "automated":
                        model = session.get("fixing_model")
                        if isinstance(model, str):
                            self.fixing_model = self.redactor.redact(model)
                        fixes.extend(
                            fix
                            for iteration in session.get("iterations", [])
                            for fix in iteration.get("fixes", [])
                        )
        for field in ("input_tokens", "output_tokens"):
            values = [numeric(fix.get(field)) for fix in fixes]
            row["fixer_" + field] = (
                int(sum(values))
                if values and all(v is not None for v in values)
                else None
            )

    async def sequential(
        self, text: str, measurement: str, schedule: list[int], **extra: Any
    ) -> dict | None:
        try:
            before = await self.credit() if self.mode == "real" else CreditSnapshot()
            reason = self.guard.reason(before) if self.guard else None
            if reason:
                self.stop_reason = reason
                self.flush()
                return None
            row = await self.observe(text, measurement, **extra)
            after = await self.credit() if self.mode == "real" else CreditSnapshot()
            cost = measured_cost(before, after) if self.mode == "real" else Decimal(0)
            row.update(
                cost_usd=float(cost) if cost is not None else None,
                cost_attribution="sequential" if self.mode == "real" else "stub free",
                cost_before_usd=float(before.usage)
                if before.usage is not None
                else None,
                cost_after_usd=float(after.usage) if after.usage is not None else None,
                remaining_before_usd=float(before.remaining)
                if before.remaining is not None
                else None,
                remaining_after_usd=float(after.remaining)
                if after.remaining is not None
                else None,
            )
            if self.guard:
                self.guard.observe(cost)
                if cost is None and self.guard.max_runs is None:
                    self.stop_reason = (
                        "Cost delta unknown; explicit --max-runs required."
                    )
            if (
                self.mode == "real"
                and self.advisory is None
                and row["complete"]
                and self.guard
            ):
                self.advisory = affordability(self.guard, after, cost, schedule)
                print(
                    "First real run measured cost: "
                    + str(self.advisory["measured_first_run_cost_usd"])
                    + "; remaining credit: "
                    + str(self.advisory["remaining_credit_usd"])
                    + "; projected further planned runs: "
                    + str(self.advisory["projected_further_runs"])
                    + "/"
                    + str(self.advisory["planned_runs_remaining"])
                    + ". Projection only; fresh guard checks decide."
                )
            self.flush()
            return row
        except CreditError as error:
            self.stop_reason = str(error)
            self.flush()
            return None

    async def pr01(self, runs: int = 10, *, following: list[int] | None = None) -> None:
        texts = prompts()
        for index in range(runs):
            if self.stop_reason:
                break
            await self.sequential(
                texts[index % len(texts)],
                "pr01",
                [1] * (runs - index - 1) + (following or []),
            )

    async def pr03(self, reference_rows: list[dict] | None = None) -> None:
        try:
            response = await self.client.get(self.base_url + "/api/health")
            health = response.json() if response.status_code == 200 else {}
            self.capacity = health.get("runner_capacity")
            if type(self.capacity) is not int or self.capacity < 3:
                self.stop_reason = (
                    "PR-03 requires reported server runner capacity of at least 3."
                )
                self.flush()
                return
            baseline = await self.sequential(prompts()[0], "pr03", [3], role="baseline")
            if (
                self.stop_reason
                or not baseline
                or not eligible(baseline)
                or baseline["seconds"] <= 0
            ):
                self.stop_reason = (
                    self.stop_reason or "PR-03 baseline did not complete successfully."
                )
                self.flush()
                return
            before = await self.credit() if self.mode == "real" else CreditSnapshot()
            reason = self.guard.reason(before, 3) if self.guard else None
            if reason:
                self.stop_reason = reason
                self.flush()
                return
            barrier = asyncio.Barrier(3)

            async def one():
                await barrier.wait()
                return await self.observe(
                    prompts()[0],
                    "pr03",
                    role="cohort",
                    cost_usd=None,
                    cost_attribution="not attributed",
                )

            cohort = await asyncio.gather(*(one() for _ in range(3)))
            after = await self.credit() if self.mode == "real" else CreditSnapshot()
            cost = measured_cost(before, after) if self.mode == "real" else Decimal(0)
            self.cohorts.append(
                {
                    "cost_usd": float(cost) if cost is not None else None,
                    "average_cost_usd": float(cost / 3) if cost is not None else None,
                    "average_label": "Total / 3 average; per-run costs not attributed",
                    "run_ids": [row["run_id"] for row in cohort],
                    "before_remaining_usd": float(before.remaining)
                    if before.remaining is not None
                    else None,
                    "after_remaining_usd": float(after.remaining)
                    if after.remaining is not None
                    else None,
                }
            )
            reference = prompt_reference(
                reference_rows if reference_rows is not None else self.rows,
                prompts()[0],
                self.mode,
                baseline["provider"],
                baseline["model"],
            )
            for row in cohort:
                row.update(reference)
                row["cost_usd"] = None
                row["cost_attribution"] = "not attributed"
                row["ratio_to_baseline"] = (
                    row["seconds"] / baseline["seconds"] if eligible(row) else None
                )
                median = reference["pr01_prompt_median_seconds"]
                row["ratio_to_pr01_prompt_median"] = (
                    row["seconds"] / median if eligible(row) and median else None
                )
            self.flush()
        except (CreditError, httpx.HTTPError, ValueError, KeyError):
            self.stop_reason = "PR-03 prerequisite or credit check failed; stopping."
            self.flush()

    async def pr04(self, run_id: str, repeat: int = 10) -> None:
        run_id = str(UUID(run_id))
        for index in range(repeat):
            row = {
                "measurement": "pr04",
                "run_id": run_id,
                "request": index + 1,
                "mode": "synthetic",
                "complete": False,
                "seconds": None,
            }
            self.rows.append(row)
            start = self.clock()
            try:
                response = await self.client.get(
                    f"{self.base_url}/api/pipeline/{run_id}/download/cost",
                    headers=self.headers,
                )
                row.update(
                    seconds=self.clock() - start,
                    http_status=response.status_code,
                    archive_bytes=len(response.content),
                    complete=response.status_code == 200
                    and response.headers.get("content-type", "").startswith(
                        "application/zip"
                    ),
                )
            except httpx.HTTPError:
                self.stop_reason = "Download request failed."
            self.flush()
            if self.stop_reason:
                break


def load_reference(path: Path | None) -> list[dict] | None:
    if path is None:
        return None
    if path.suffix == ".json":
        return json.loads(path.read_text())["runs"]
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["complete"] = row["complete"] == "True"
        row["seconds"] = float(row["seconds"]) if row["seconds"] else None
    return rows


def arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--mode", choices=["real", "stub"], default="stub")
    parser.add_argument("--budget-usd", type=Decimal)
    parser.add_argument("--max-runs", type=int)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--output-dir", type=Path)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("pr01").add_argument("--runs", type=int, default=10)
    subs.add_parser("pr03").add_argument("--pr01-results", type=Path)
    download = subs.add_parser("pr04")
    download.add_argument("--run-id", required=True)
    download.add_argument("--repeat", type=int, default=10)
    return parser


async def configured_harness(
    args, directory: Path, client: httpx.AsyncClient
) -> Harness:
    guard = BudgetGuard(Decimal(0), args.max_runs) if args.max_runs else None
    reader = None
    api_key = SecretStr(os.environ["API_KEY"]) if os.environ.get("API_KEY") else None
    if args.mode == "real" and args.command != "pr04":
        from app.core.config import Settings

        settings = Settings(_env_file=None)
        if settings.llm_provider.value == "stub":
            raise ValueError("Real mode requires a configured real provider")
        if (
            args.budget_usd is None
            or not args.budget_usd.is_finite()
            or args.budget_usd <= 0
        ):
            raise ValueError("Real mode requires a positive --budget-usd reserve")
        guard = BudgetGuard(args.budget_usd, args.max_runs)
        if (
            settings.llm_provider.value == "openai"
            and urlparse(settings.llm_base_url or "").hostname == "openrouter.ai"
        ):
            if not settings.llm_api_key:
                raise ValueError("Real mode needs configured credentials")
            reader = CreditReader(client, settings.llm_base_url, settings.llm_api_key)
        elif args.max_runs is None:
            raise ValueError("Unknown cost provider requires explicit --max-runs")
    harness = Harness(
        client,
        base_url=args.base_url,
        mode=args.mode,
        timeout=args.timeout,
        guard=guard,
        credit_reader=reader,
        api_key=api_key,
        output=directory,
    )
    if args.mode == "real" and args.command != "pr04":
        harness.expected_provider = settings.llm_provider.value
        metadata = json.loads((directory / "environment.json").read_text())
        metadata.update(
            provider=settings.llm_provider.value,
            model=harness.redactor.redact(settings.llm_model or ""),
            fixing_model=harness.redactor.redact(settings.security_fix_model or ""),
        )
        write_json(directory / "environment.json", metadata)
    return harness


async def run(args) -> None:
    directory = evidence_directory(args.command, args.output_dir, mode=args.mode)
    summary(
        directory / "summary.md",
        "Phase 9 benchmark",
        "INCOMPLETE",
        ["Measurement has not completed."],
    )
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(60, connect=5), follow_redirects=False
    ) as client:
        harness = await configured_harness(args, directory, client)
        if args.command == "pr01":
            await harness.pr01(args.runs)
        elif args.command == "pr03":
            await harness.pr03(load_reference(args.pr01_results))
        else:
            await harness.pr04(args.run_id, args.repeat)
        harness.flush()
    print(directory)
    if harness.stop_reason:
        raise SystemExit(2)


def main() -> None:
    parser = arguments()
    args = parser.parse_args()
    if (
        not math.isfinite(args.timeout)
        or args.timeout <= 0
        or args.max_runs is not None
        and args.max_runs < 1
        or getattr(args, "runs", 1) < 1
        or getattr(args, "repeat", 1) < 1
    ):
        parser.error("Run counts and observation timeout must be positive and finite.")
    asyncio.run(run(args))


if __name__ == "__main__":
    safe_main(main)
