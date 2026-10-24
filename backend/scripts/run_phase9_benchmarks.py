"""One author command, one shared guard, and per-measurement raw evidence."""

import argparse
import asyncio
import json
import math
import os
from decimal import Decimal
from pathlib import Path

import httpx

from scripts.benchmark import Harness, configured_harness
from scripts.phase9_common import evidence_directory, safe_main, write_json
from scripts.phase9_report import summary
from scripts.phase9i_broad import (
    broad_schedule,
    execute_broad,
    mark_broad_not_started,
    registered_scenarios,
    scenario_digest,
)
from scripts.seed_benchmark_package import SeedConfigurationError, load_seed_settings


def architect_override(args) -> dict:
    model = getattr(args, "architect_model", None)
    thinking = getattr(args, "architect_thinking", None)
    if thinking and not model:
        raise ValueError("ARCHITECT_THINKING requires explicit ARCHITECT_MODEL")
    if not model:
        return {}
    return {"agent_models": {"architect": {"model": model, "thinking_mode": thinking}}}


def schedule(runs: int = 10) -> list[int]:
    return [1] * runs + [1, 3]


def section_reports(harness: Harness, directory: Path) -> None:
    for name in ("pr01", "pr03", "pr04"):
        rows = [row for row in harness.rows if row["measurement"] == name]
        if not rows:
            continue
        output = directory / name
        output.mkdir(exist_ok=True)
        write_json(
            output / "environment.json",
            json.loads((directory / "environment.json").read_text()),
        )
        view = Harness(harness.client, mode=harness.mode, output=output)
        view.rows = rows
        ids = {row["run_id"] for row in rows}
        view.agent_rows = [row for row in harness.agent_rows if row["run_id"] in ids]
        view.events = [event for event in harness.events if event["run_id"] in ids]
        view.cohorts = harness.cohorts if name == "pr03" else []
        view.quality_inputs = {
            run_id: data
            for run_id, data in harness.quality_inputs.items()
            if run_id in ids
        }
        view.capacity = harness.capacity
        view.fixing_model = harness.fixing_model
        view.stop_reason = harness.stop_reason
        view.flush()


async def execute(harness: Harness, *, seeder=None, smoke: bool = False) -> None:
    if smoke:
        await harness.pr01(3, following=[], prompt_indices=[0, 1, 2])
        if harness.stop_reason and hasattr(harness, "mark_not_started"):
            harness.mark_not_started([("pr01", None)] * 3)
        harness.flush()
        return
    await harness.pr01(10, following=[1, 3])
    if not harness.stop_reason:
        await harness.pr03()
    if harness.mode == "stub" and not harness.stop_reason and seeder is not None:
        report = await seeder()
        if harness.output:
            seed_directory = harness.output / "seed"
            seed_directory.mkdir()
            write_json(
                seed_directory / "environment.json",
                json.loads((harness.output / "environment.json").read_text()),
            )
            write_json(seed_directory / "seed.json", report)
            summary(
                seed_directory / "summary.md",
                "Synthetic PR-04 fixture",
                "PASS",
                [report["measurement"], f"Run: {report['run_id']}."],
            )
        await harness.pr04(report["run_id"], 10)
    if harness.stop_reason and hasattr(harness, "mark_not_started"):
        harness.mark_not_started(
            [("pr01", None)] * 10 + [("pr03", "baseline")] + [("pr03", "cohort")] * 3
        )
    harness.flush()


async def run(args) -> None:
    broad = getattr(args, "broad", False)
    registration = registered_scenarios() if broad else None
    directory = evidence_directory(
        "bench-broad"
        if broad
        else "bench-smoke"
        if args.smoke
        else "bench-" + args.mode,
        mode=args.mode,
        provider="stub" if args.mode == "stub" else None,
        model="stub" if args.mode == "stub" else None,
    )
    slots = []
    if registration:
        data, raw, revision = registration
        digest = scenario_digest(raw)
        slots = broad_schedule(data, args.runs_per_scenario, digest)
        (directory / "broad-v1.json").write_bytes(raw)
        metadata_path = directory / "environment.json"
        metadata = json.loads(metadata_path.read_text())
        metadata.update(
            benchmark_kind="broad",
            scenario_sha256=digest,
            registration_commit=revision,
            runs_per_scenario=args.runs_per_scenario,
            planned_runs=len(slots),
        )
        write_json(metadata_path, metadata)
    summary(
        directory / "summary.md",
        "Phase 9 benchmark set",
        "INCOMPLETE",
        ["Rehearsal/measurement started."],
    )
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(60, connect=5), follow_redirects=False
    ) as client:
        harness = await configured_harness(args, directory, client)
        harness.run_config = architect_override(args)
        if broad:
            harness.benchmark_kind = "broad"

        async def seed():
            from app.db.session import make_database_engine, make_session_factory
            from scripts.seed_benchmark_package import (
                load_seed_settings,
                seed_package,
            )

            settings = load_seed_settings()
            engine = make_database_engine(settings.database_url)
            try:
                return await seed_package(make_session_factory(engine))
            finally:
                await engine.dispose()

        try:
            # Do not submit a rehearsal to a backend lacking its local tool chain.
            if args.mode == "stub":
                if not broad:
                    load_seed_settings()
                response = await client.get(args.base_url.rstrip("/") + "/api/health")
                health = response.json()
                if (
                    response.status_code != 200
                    or not health.get("provider_mirror_present")
                    or not all(
                        health.get("scanners", {}).get(name, {}).get("available")
                        for name in ("checkov", "trivy", "terraform")
                    )
                ):
                    harness.stop_reason = (
                        "Stub rehearsal requires healthy PostgreSQL, "
                        "scanners and provider mirror."
                    )
            if not harness.stop_reason:
                if broad:
                    await execute_broad(harness, slots)
                else:
                    await execute(harness, seeder=seed, smoke=args.smoke)
                if args.mode == "stub" and not harness.stop_reason and not broad:
                    from scripts.phase9e_rehearsal import verification_rehearsal

                    rehearsal = await verification_rehearsal()
                    write_json(directory / "verification-rehearsal.json", rehearsal)
                    for raw in rehearsal["records"]:
                        harness.agent_rows.append(
                            {
                                **raw,
                                "run_id": "verification-rehearsal",
                                "agent": "scripted_security_iteration_verification",
                                "seconds": raw["duration_seconds"],
                                "complete": raw.get("outcome") != "stopped",
                                "threshold_seconds": None,
                                "pass": None,
                                "evidence_scope": "scripted_verification_rehearsal",
                            }
                        )
        except SeedConfigurationError as error:
            harness.stop_reason = str(error)
        except (OSError, ValueError, RuntimeError, httpx.HTTPError):
            harness.stop_reason = (
                "Benchmark prerequisite or fixture preparation failed."
            )
        finally:
            if broad:
                # Also persist the entire schedule after prerequisite failures.
                mark_broad_not_started(harness, slots)
            harness.flush()
            if not broad:
                section_reports(harness, directory)
    print(directory)
    if harness.stop_reason:
        raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["stub", "real"])
    parser.add_argument(
        "--base-url",
        default=os.environ.get("PHASE9_BASE_URL") or "http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--budget-usd", type=Decimal, default=os.environ.get("PHASE9_BUDGET") or None
    )
    parser.add_argument(
        "--max-runs", type=int, default=os.environ.get("PHASE9_MAX_RUNS") or None
    )
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--broad", action="store_true")
    parser.add_argument(
        "--architect-model",
        default=os.environ.get("PHASE9_ARCHITECT_MODEL")
        or os.environ.get("ARCHITECT_MODEL")
        or None,
    )
    parser.add_argument(
        "--architect-thinking",
        choices=["off", "low", "medium", "high"],
        default=os.environ.get("PHASE9_ARCHITECT_THINKING")
        or os.environ.get("ARCHITECT_THINKING")
        or None,
    )
    parser.add_argument(
        "--runs-per-scenario",
        type=int,
        default=os.environ.get("PHASE9_RUNS_PER_SCENARIO") or 2,
    )
    args = parser.parse_args()
    if (args.architect_model or args.architect_thinking) and not args.broad:
        parser.error("Architect experiment overrides require --broad")
    try:
        architect_override(args)
    except ValueError as error:
        parser.error(str(error))
    if args.broad:
        if args.smoke or args.runs_per_scenario < 1:
            parser.error("Broad requires positive RUNS_PER_SCENARIO and no --smoke")
        planned = 10 * args.runs_per_scenario
        args.max_runs = (
            min(args.max_runs, planned) if args.max_runs is not None else planned
        )
    if args.smoke:
        if args.mode != "real":
            parser.error("Smoke is real mode only")
        args.max_runs = min(args.max_runs if args.max_runs is not None else 3, 3)
    args.command = "suite"
    if args.mode == "real" and (
        args.budget_usd is None
        or not args.budget_usd.is_finite()
        or args.budget_usd <= 0
    ):
        parser.error("bench-real requires a positive BUDGET minimum-credit reserve.")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("Observation timeout must be positive and finite.")
    if args.max_runs is not None and args.max_runs < 1:
        parser.error("MAX_RUNS must be positive.")
    asyncio.run(run(args))


if __name__ == "__main__":
    safe_main(main)
