"""Offline fixed-input replay and explicitly counterfactual PR-01 estimates."""

import argparse
import asyncio
import hashlib
import json
import os
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings

# This command never resolves operator settings or reads dotenv.
Settings.model_config["env_file"] = None

from app.domain.enums import Variant  # noqa: E402
from app.scanners.runner import ProcessToolRunner  # noqa: E402
from app.scanners.scan import Scanner  # noqa: E402
from app.validation.documents import PackageDocuments  # noqa: E402
from app.validation.engine import BoundedRunner  # noqa: E402
from app.validation.terraform import validate_terraform  # noqa: E402
from app.validation.workspace import ValidationWorkspace  # noqa: E402


def estimate(benchmark, results, factor=1.0):
    """Fixed outcomes, scan proxy and generation barrier; never a measured speedup."""
    events = json.loads((benchmark / "events.json").read_text())
    runs = json.loads((benchmark / "results.json").read_text())["runs"]
    output = []
    for run in runs:
        if run["measurement"] != "pr01" or not run["complete"]:
            continue
        local = [e for e in events if e["run_id"] == run["run_id"]]
        snapshot = json.loads((results / (run["run_id"] + ".json")).read_text())
        generation = {
            e["variant"]: datetime.fromisoformat(e["timestamp"]).timestamp()
            for e in local
            if e["kind"] == "agent_state"
            and e["agent"].startswith("generator_")
            and e["status"] == "completed"
        }
        ending = {
            e["variant"]: datetime.fromisoformat(e["timestamp"]).timestamp()
            for e in local
            if e["kind"] == "package_status"
            and e["status"] in {"checks_passed", "pending_review"}
        }
        savings = {}
        avoided = 0
        for package in snapshot["packages"]:
            variant = package["variant"]
            scan = next(
                e["measurement"]["duration_seconds"]
                for e in local
                if e["variant"] == variant
                and (e.get("measurement") or {}).get("stage") == "final_security_scan"
            )
            by_phase = {
                p: 0.0 for p in ["generation", "before_security", "after_security"]
            }
            for repair in package["validation_report"]["remediation"]["rounds"]:
                count = (
                    2
                    if repair["reason"] == "no_improvement"
                    else 1
                    if repair["reason"] == "invalid_patch"
                    else 0
                )
                avoided += count
                llm = sum(
                    a["elapsed_seconds"] for a in repair.get("fixer_attempts", [])
                )
                by_phase[repair["phase"]] += min(
                    count * scan * factor, max(0, repair["duration_seconds"] - llm)
                )
            savings[variant] = by_phase
        generation_gain = max(generation.values()) - max(
            generation[v] - savings[v]["generation"] for v in generation
        )
        gain = max(ending.values()) - max(
            ending[v]
            - generation_gain
            - savings[v]["before_security"]
            - savings[v]["after_security"]
            for v in ending
        )
        output.append(
            {
                "run_id": run["run_id"],
                "recorded_seconds": run["seconds"],
                "estimated_seconds": run["seconds"] - gain,
                "avoided_scan_batches": avoided,
            }
        )
    return {
        "counterfactual": True,
        "threshold_seconds": 300,
        "required_runs": 10,
        "sample_runs": len(output),
        "proxy_factor": factor,
        "runs": output,
        "recorded_median_seconds": statistics.median(
            r["recorded_seconds"] for r in output
        ),
        "estimated_median_seconds": statistics.median(
            r["estimated_seconds"] for r in output
        ),
    }


def cpu():
    values = [
        int(v) for v in Path("/proc/stat").read_text().splitlines()[0].split()[1:9]
    ]
    return sum(values), values[3] + values[4]


async def replay(args):
    # Optional import permits running this same script against the pre-change
    # application extracted to a temporary directory (PYTHONPATH), without edits.
    try:
        from app.core.telemetry import Collector, current, safe_records, scope
    except ImportError:
        Collector = None
    if args.instrumentation == "on" and Collector is None:
        raise SystemExit("Instrumentation unavailable in selected application source.")
    packages = json.loads(args.snapshot.read_text())["packages"]
    inputs = [(p["variant"], p.get("original_files") or p["files"]) for p in packages]
    fingerprint = hashlib.sha256(
        json.dumps(inputs, sort_keys=True).encode()
    ).hexdigest()
    observations, rows = [], []
    semaphore = asyncio.Semaphore(args.concurrency)

    async def one(variant, files, repetition):
        async with semaphore:
            workspace = ValidationWorkspace()
            collector = (
                Collector() if Collector and args.instrumentation == "on" else None
            )
            token = current.set(collector) if Collector else None
            started = time.monotonic()
            try:
                with workspace.activate():
                    if collector:
                        with scope(
                            run_id=str(uuid4()),
                            variant=variant,
                            phase="offline_replay",
                            role="security",
                        ):
                            scan, checks = await check(files, variant, workspace)
                    else:
                        scan, checks = await check(files, variant, workspace)
                rows.append(
                    {
                        "variant": variant,
                        "repetition": repetition,
                        "seconds": time.monotonic() - started,
                        "blocking": sum(v.blocking for v in scan.violations),
                        "failed_checks": sum(c.status == "failed" for c in checks),
                        "skipped_checks": sum(c.status == "skipped" for c in checks),
                    }
                )
            finally:
                if collector:
                    observations.extend(safe_records(collector.records))
                if token is not None:
                    current.reset(token)
                workspace.close()

    async def check(files, variant, workspace):
        runner = ProcessToolRunner(120)
        scan = await Scanner(runner).scan(files, Variant(variant))
        async with workspace.check(files) as root:
            checks = await validate_terraform(
                root,
                set(files),
                BoundedRunner(runner, asyncio.Semaphore(3)),
                args.mirror.resolve(),
                PackageDocuments.parse(files),
            )
        return scan, checks

    versions = {
        tool: ProcessToolRunner.probe_version(tool)["version"]
        for tool in ["checkov", "trivy", "terraform"]
    }
    load_before, cpu_before = os.getloadavg(), cpu()
    started = time.monotonic()
    for repetition in range(args.repetitions):
        await asyncio.gather(*(one(v, f, repetition) for v, f in inputs))
    elapsed = time.monotonic() - started
    cpu_after = cpu()
    ticks = cpu_after[0] - cpu_before[0]
    return {
        "recorded_at": datetime.now(UTC).isoformat(),
        "input_sha256": fingerprint,
        "source_label": args.source_label,
        "instrumentation": args.instrumentation,
        "concurrency": args.concurrency,
        "repetitions": args.repetitions,
        "versions": versions,
        "load_before": load_before,
        "load_after": os.getloadavg(),
        "cpu_busy_fraction": 1 - (cpu_after[1] - cpu_before[1]) / ticks
        if ticks
        else None,
        "seconds": elapsed,
        "rows": rows,
        "telemetry": observations,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    estimation = sub.add_parser("estimate")
    estimation.add_argument("--benchmark", type=Path, required=True)
    estimation.add_argument("--results", type=Path, required=True)
    repeat = sub.add_parser("replay")
    repeat.add_argument("--snapshot", type=Path, required=True)
    repeat.add_argument("--mirror", type=Path, required=True)
    repeat.add_argument("--concurrency", type=int, choices=[1, 3], required=True)
    repeat.add_argument("--instrumentation", choices=["on", "off"], default="on")
    repeat.add_argument("--source-label", required=True)
    repeat.add_argument("--repetitions", type=int, default=1)
    for command in [estimation, repeat]:
        command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output must be a new file; existing evidence is read-only.")
    result = (
        {
            str(factor): estimate(args.benchmark, args.results, factor)
            for factor in [0.5, 1.0, 1.5]
        }
        if args.mode == "estimate"
        else asyncio.run(replay(args))
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("Offline evidence written; no LLM requests or dotenv settings used.")


if __name__ == "__main__":
    main()
