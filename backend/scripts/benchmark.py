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

from app.core.generator_settings import GeneratorSettings
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
from scripts.phase9c_metrics import (
    FAILURES,
    attempt_details,
    completeness_details,
    generator_evidence,
    number,
)
from scripts.phase9d_quality import quality_snapshot, quality_table, recompute_quality
from scripts.phase9e_metrics import measurement as safe_measurement
from scripts.phase9e_metrics import measurement_summary
from scripts.phase9f_workloads import pr05_workloads
from scripts.phase9g_metrics import fixer_evidence

TERMINAL = {"success", "partial_success", "failed"}
SETTLED = {
    "pending_review",
    "checks_passed",
    "engineer_approved",
    "rejected",
    "scan_error",
    "production_ready",
    "not_production_ready",
}
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
    status = {
        "production_ready": "checks_passed",
        "not_production_ready": "rejected",
    }.get(item.get("status"), item.get("status"))
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
    safe_metrics = {
        name: value if type(value) is int and value >= 0 else None
        for name, value in metrics.items()
        if name
        in {"llm_attempts", "input_tokens", "output_tokens", "cached_input_tokens"}
    }
    for name in ("elapsed_seconds", "overrun_seconds"):
        if name in metrics:
            safe_metrics[name] = number(metrics[name])
    if "deadline_exceeded" in metrics:
        safe_metrics["deadline_exceeded"] = (
            metrics["deadline_exceeded"]
            if type(metrics["deadline_exceeded"]) is bool
            else None
        )
    if type(metrics.get("prepared_report")) is bool:
        safe_metrics["prepared_report"] = metrics["prepared_report"]
    if "llm_attempt_details" in metrics:
        safe_metrics["llm_attempt_details"] = attempt_details(
            metrics["llm_attempt_details"]
        )
    if "completeness" in metrics:
        safe_metrics["completeness"] = completeness_details(metrics["completeness"])
    failure = payload.get("failure_category")
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
        "metrics": safe_metrics,
        "measurement": safe_measurement(payload.get("measurement")),
        "failure_category": failure
        if isinstance(failure, str) and failure in FAILURES
        else None,
    }


def duration(start: str, end: str) -> float | None:
    value = (
        datetime.fromisoformat(end) - datetime.fromisoformat(start)
    ).total_seconds()
    return value if value >= 0 else None


def timings(run_id: str, events: list[dict]) -> list[dict]:
    starts, scans, rows, indexes = {}, {}, [], {}
    for event in sorted(events, key=lambda event: event["seq"]):
        measured = event.get("measurement")
        if measured is not None:
            rows.append(
                {
                    "run_id": run_id,
                    "agent": measured["stage"],
                    "variant": event["variant"],
                    "iteration": measured.get("iteration"),
                    "seconds": measured["duration_seconds"],
                    "complete": measured["duration_seconds"] is not None,
                    "threshold_seconds": None,
                    "pass": None,
                    **measured,
                }
            )
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
                        "agent": "validator_persistence"
                        if event["agent"] == "validator"
                        and event["metrics"].get("prepared_report")
                        else event["agent"],
                        "variant": event["variant"],
                        "iteration": None,
                        "seconds": elapsed,
                        "generator_elapsed_seconds": event["metrics"].get(
                            "elapsed_seconds"
                        )
                        if event["agent"].startswith("generator_")
                        else None,
                        "deadline_exceeded": event["metrics"].get("deadline_exceeded"),
                        "overrun_seconds": event["metrics"].get("overrun_seconds"),
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
        self.quality_inputs = {}
        self.resolved_agent_selections = {}

    async def credit(self) -> CreditSnapshot:
        return (
            await self.credit_reader.read() if self.credit_reader else CreditSnapshot()
        )

    def mark_not_started(self, planned: list[tuple[str, str | None]]) -> None:
        from collections import Counter

        existing = Counter((r["measurement"], r.get("role")) for r in self.rows)
        for measurement, role in planned:
            key = (measurement, role)
            if existing[key]:
                existing[key] -= 1
                continue
            self.rows.append(
                {
                    "measurement": measurement,
                    "role": role,
                    "mode": self.mode,
                    "execution_status": "not_started",
                    "complete": False,
                    "run_id": None,
                    "seconds": None,
                    "cost_usd": None,
                }
            )
        self.flush()

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
                "pr05_workloads": pr05_workloads(self.rows, self.agent_rows),
            },
        )
        write_json(self.output / "events.json", self.events)
        write_csv(
            self.output / "results.csv",
            [
                {
                    key: json.dumps(value, sort_keys=True)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
                for row in self.rows
            ],
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
                        "generator_attempt_count",
                        "generator_attempts_by_format_reason",
                        "generator_output_tokens_per_attempt",
                        "generator_deadlines",
                        "failure_categories",
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
        quality_packages = [
            p for variants in self.quality_inputs.values() for p in variants.values()
        ]
        quality, quality_markdown = quality_table(
            quality_packages,
            missing=sum(3 - len(variants) for variants in self.quality_inputs.values()),
        )
        if self.quality_inputs:
            for run_id, variants in self.quality_inputs.items():
                directory = self.output / "quality" / str(UUID(run_id))
                directory.mkdir(parents=True, exist_ok=True)
                for variant, package in variants.items():
                    write_json(directory / f"{variant}.json", package)
            write_json(self.output / "quality.json", quality)
        lines, checks = ([quality_markdown] if self.quality_inputs else []), []
        descriptive, descriptive_table = measurement_summary(
            [
                r
                for r in self.agent_rows
                if r.get("evidence_scope") != "scripted_verification_rehearsal"
            ]
        )
        write_json(self.output / "measurements.json", descriptive)
        lines.append(descriptive_table)
        rehearsal_rows = [
            r
            for r in self.agent_rows
            if r.get("evidence_scope") == "scripted_verification_rehearsal"
        ]
        if rehearsal_rows:
            rehearsal_summary, rehearsal_table = measurement_summary(rehearsal_rows)
            write_json(
                self.output / "verification-rehearsal-summary.json", rehearsal_summary
            )
            lines += [
                "Separate scripted-fix offline verification rehearsal "
                "(excluded from quality rates and PR thresholds).",
                rehearsal_table,
            ]
        for measurement in ("pr01", "pr03", "pr04"):
            planned = [row for row in self.rows if row["measurement"] == measurement]
            not_started = sum(
                row.get("execution_status") == "not_started" for row in planned
            )
            if not_started:
                lines.append(
                    f"{measurement}: not_started={not_started} "
                    "(excluded from failures and measurements)."
                )
            rows = [
                row for row in planned if row.get("execution_status") != "not_started"
            ]
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
        for workload, data in pr05_workloads(self.rows, self.agent_rows).items():
            lines.append(
                f"PR-05 workload {workload} (additional view): " + json.dumps(data)
            )
        generator_rows = [
            row for row in self.rows if row["measurement"] in {"pr01", "pr03"}
        ]
        if generator_rows:
            table = [
                "| Run | Attempts | Format reasons | Output tokens / attempt | "
                "Failures | Overruns |",
                "|---|---:|---|---|---|---|",
            ]
            for index, row in enumerate(generator_rows, 1):
                count = row.get("generator_attempt_count")
                count_label = count if count is not None else "unknown"
                tokens = row.get("generator_output_tokens_per_attempt")
                token_label = (
                    ", ".join(
                        f"{item['variant']}#{item['attempt']}:"
                        + (
                            str(item["output_tokens"])
                            if item["output_tokens"] is not None
                            else "unknown"
                        )
                        for item in (tokens or [])
                    )
                    or "unknown"
                )
                overruns = {
                    variant: data.get("overrun_seconds")
                    for variant, data in row.get("generator_deadlines", {}).items()
                    if data.get("deadline_exceeded") is True
                }
                table.append(
                    f"| {index} | {count_label} | "
                    + json.dumps(row.get("generator_attempts_by_format_reason"))
                    + " | "
                    + token_label
                    + " | "
                    + json.dumps(row.get("failure_categories", {}))
                    + " | "
                    + json.dumps(overruns)
                    + " |"
                )
            lines.append(
                "Generator attempts (missing historical metrics remain unknown):\n\n"
                + "\n".join(table)
            )
            lines.append(
                "Output tokens per attempt are in results.csv/results.json; "
                "event seconds and internal generator seconds are in agents.csv. "
                "PR-05 remains 150 seconds regardless of configured budgets."
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

    async def capture_settings(self) -> bool:
        if not self.headers.get("X-API-Key"):
            self.stop_reason = (
                "Authenticated benchmark settings require API_KEY on server and client."
            )
            return False
        try:
            response = await self.client.get(
                self.base_url + "/api/benchmark/settings", headers=self.headers
            )
            if response.status_code != 200:
                raise ValueError("Settings unavailable")
            effective = GeneratorSettings.model_validate(response.json()).model_dump()
            if self.output is not None:
                path = self.output / "environment.json"
                metadata = json.loads(path.read_text())
                metadata["generator_settings"] = effective
                write_json(path, metadata)
            return True
        except (httpx.HTTPError, ValueError, OSError):
            self.stop_reason = (
                "Authenticated generator settings unavailable or malformed; "
                "no benchmark submitted."
            )
            return False

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
        if self.stop_reason:
            row = {
                "measurement": measurement,
                "mode": self.mode,
                **extra,
                "execution_status": "not_started",
                "complete": False,
                "run_id": None,
                "seconds": None,
                "cost_usd": None,
            }
            self.rows.append(row)
            return row
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
            if response.status_code == 402:
                row["failure_categories"] = {"run": "usage_limit"}
                self.stop_reason = (
                    "Provider usage_limit (HTTP 402); no further runs submitted."
                )
                return row
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
                                    if event["failure_category"] == "usage_limit":
                                        self.stop_reason = (
                                            "Provider usage_limit (HTTP 402); "
                                            "no further runs submitted."
                                        )
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
            row["failure_categories"] = {"run": "observation_incomplete"}
            self.stop_reason = row["failure"]
        finally:
            if not row["complete"] and row["run_id"]:
                failure = row.get("failure_categories", {})
                row.update(generator_evidence(local))
                row["failure_categories"].update(failure)
                self.agent_rows.extend(timings(row["run_id"], local))
            self.flush()
        return row

    def finish(
        self, row: dict, snapshot: dict, local: list[dict], elapsed: float
    ) -> None:
        self.resolved_agent_selections[row["run_id"]] = (
            self.redactor.value(snapshot["run"].get("agent_models"))
            if hasattr(self.redactor, "value")
            else snapshot["run"].get("agent_models")
        )
        if self.output and (self.output / "environment.json").exists():
            path = self.output / "environment.json"
            metadata = json.loads(path.read_text())
            metadata["resolved_agent_selections"] = self.resolved_agent_selections
            write_json(path, metadata)
        self.quality_inputs[row["run_id"]] = {
            p["variant"]: quality_snapshot(p, self.redactor)
            for p in snapshot.get("packages", [])
            if p.get("variant") in VARIANTS
        }
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
            policy_profile=run.get("policy_profile", "strict"),
            provider=provider,
            model=self.redactor.redact(run.get("model") or ""),
        )
        for variant in VARIANTS:
            package = next(
                (p for p in snapshot["packages"] if p["variant"] == variant), None
            )
            last_status = next(
                (
                    event["status"]
                    for event in reversed(local)
                    if event["kind"] == "package_status" and event["variant"] == variant
                ),
                None,
            )
            missing = any(
                item.get("variant") == variant
                for item in snapshot.get("missing_variants", [])
            )
            row[variant + "_variant_status"] = (
                package["status"]
                if package
                else last_status or ("failed" if missing else "not_generated")
            )
        self.agent_rows.extend(timings(row["run_id"], local))
        row.update(generator_evidence(local))
        for event in local:
            if event.get("failure_category") and not (
                event["agent"].startswith("generator_")
                and event["kind"] == "agent_state"
            ):
                key = event["agent"] + (
                    ":" + event["variant"] if event.get("variant") else ""
                )
                row["failure_categories"][key] = event["failure_category"]
        if "usage_limit" in row["failure_categories"].values():
            self.stop_reason = (
                "Provider usage_limit (HTTP 402); no further runs submitted."
            )
        if row["run_status"] == "failed" and not row["failure_categories"]:
            row["failure_categories"] = {"run": "unknown"}
        generated = [e["metrics"] for e in local if e["kind"] == "package_generated"]
        for field in ("llm_attempts", "input_tokens", "output_tokens"):
            values = [numeric(m.get(field)) for m in generated]
            row["generator_" + field] = (
                int(sum(values))
                if values and all(v is not None for v in values)
                else None
            )
        if row["generator_attempt_count"] is not None:
            row["generator_llm_attempts"] = row["generator_attempt_count"]
            for field in ("input_tokens", "output_tokens"):
                values = [item[field] for item in row["generator_attempt_details"]]
                row["generator_" + field] = (
                    sum(values) if all(v is not None for v in values) else None
                )
        evidence = [fixer_evidence(p) for p in snapshot["packages"]]
        row["fixer_attempt_details"] = [
            {"variant": p["variant"], **a}
            for p, measured in zip(snapshot["packages"], evidence, strict=True)
            for a in measured["attempt_details"] or []
        ] or None
        row["fixer_attempt_count"] = (
            sum(e["attempt_count"] for e in evidence)
            if evidence and all(e["attempt_count"] is not None for e in evidence)
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
                cost_usd=float(cost) if cost is not None and row["complete"] else None,
                observed_usage_delta_usd=float(cost) if cost is not None else None,
                cost_attribution="sequential" if self.mode == "real" else "stub free",
                account_remaining_before_usd=float(before.account_remaining)
                if before.account_remaining is not None
                else None,
                account_balance_status="known"
                if before.account_remaining is not None
                else "unknown",
                key_remaining_before_usd=float(before.key_remaining)
                if before.key_remaining is not None
                else None,
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
                if row["complete"]:
                    self.guard.observe(cost)
                if (
                    cost is None
                    and self.guard.max_runs is None
                    and not self.stop_reason
                ):
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
            self.stop_reason = self.stop_reason or str(error)
            self.flush()
            return None

    async def pr01(
        self,
        runs: int = 10,
        *,
        following: list[int] | None = None,
        prompt_indices: list[int] | None = None,
    ) -> None:
        texts = prompts()
        indices = list(range(len(texts))) if prompt_indices is None else prompt_indices
        if (
            not indices
            or len(set(indices)) != len(indices)
            or any(type(i) is not int or not 0 <= i < len(texts) for i in indices)
        ):
            raise ValueError("Invalid prompt selection")
        for index in range(runs):
            if self.stop_reason:
                break
            await self.sequential(
                texts[indices[index % len(indices)]],
                "pr01",
                [1] * (runs - index - 1) + (following or []),
                prompt_index=indices[index % len(indices)],
            )

        if self.stop_reason:
            self.mark_not_started([("pr01", None)] * runs)

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
                    "average_cost_usd": float(cost / 3)
                    if cost is not None and all(r["run_id"] for r in cohort)
                    else None,
                    "average_label": "Total / 3 average; per-run costs not attributed"
                    if all(r["run_id"] for r in cohort)
                    else "Incomplete cohort; per-run cost unavailable",
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
            self.stop_reason = (
                self.stop_reason
                or "PR-03 prerequisite or credit check failed; stopping."
            )
            self.flush()
        finally:
            if self.stop_reason:
                self.mark_not_started([("pr03", "baseline")] + [("pr03", "cohort")] * 3)

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
    if path.resolve().name.startswith(".env") or path.suffix not in {".json", ".csv"}:
        raise ValueError("Reference must be a CSV or JSON measurement report")
    if path.suffix == ".json":
        return json.loads(path.read_text())["runs"]
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["complete"] = row["complete"] == "True"
        row["seconds"] = float(row["seconds"]) if row["seconds"] else None
    return rows


def parse_prompt_indices(value: str) -> list[int]:
    try:
        indices = [int(item) for item in value.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Prompts must be comma-separated indices"
        ) from None
    if (
        not indices
        or len(set(indices)) != len(indices)
        or any(not 0 <= i < len(prompts()) for i in indices)
    ):
        raise argparse.ArgumentTypeError("Prompt indices must be unique and in range")
    return indices


def arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--mode", choices=["real", "stub"], default="stub")
    parser.add_argument("--budget-usd", type=Decimal)
    parser.add_argument("--max-runs", type=int)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--output-dir", type=Path)
    subs = parser.add_subparsers(dest="command", required=True)
    pr01 = subs.add_parser("pr01")
    pr01.add_argument("--runs", type=int, default=10)
    pr01.add_argument("--prompts", type=parse_prompt_indices)
    subs.add_parser("pr03").add_argument("--pr01-results", type=Path)
    download = subs.add_parser("pr04")
    download.add_argument("--run-id", required=True)
    download.add_argument("--repeat", type=int, default=10)
    quality = subs.add_parser("quality")
    quality.add_argument("--results-dir", type=Path, required=True)
    quality.add_argument("--snapshots-dir", type=Path)
    quality.add_argument(
        "--output-dir", type=Path, required=True, dest="quality_output_dir"
    )
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
        from app.core.safety import PublicDataSafety

        harness.redactor = PublicDataSafety(settings).redactor
        harness.expected_provider = settings.llm_provider.value
        metadata = json.loads((directory / "environment.json").read_text())
        metadata.update(
            provider=settings.llm_provider.value,
            model=harness.redactor.redact(settings.llm_model or ""),
            fixing_model=harness.redactor.redact(settings.security_fix_model or ""),
        )
        write_json(directory / "environment.json", metadata)
    await harness.capture_settings()
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
        if harness.stop_reason:
            harness.flush()
        elif args.command == "pr01":
            await harness.pr01(args.runs, prompt_indices=args.prompts)
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
    if args.command == "quality":
        recompute_quality(
            args.results_dir,
            args.snapshots_dir or args.results_dir / "quality",
            args.quality_output_dir,
        )
        print(args.quality_output_dir)
        return
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
