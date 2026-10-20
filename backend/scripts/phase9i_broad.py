"""Pre-registered broad quality schedule; no settings or provider calls here."""

import hashlib
import json
import subprocess
from pathlib import Path

from scripts.phase9_common import ROOT

SCENARIO_PATH = "docs/evals/scenarios/broad-v1.json"
METADATA_FIELDS = (
    "benchmark_kind",
    "scenario_sha256",
    "scenario_id",
    "complexity",
    "round",
    "sequence",
)


def registered_scenarios(root: Path = ROOT) -> tuple[dict, bytes, str]:
    """Reject uncommitted edits before any pipeline submission."""
    raw = (root / SCENARIO_PATH).read_bytes()
    try:
        committed = subprocess.check_output(
            ["git", "-C", str(root), "show", f"HEAD:{SCENARIO_PATH}"],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        raise ValueError(
            "Scenario registration must be committed before running"
        ) from None
    if raw != committed:
        raise ValueError("Scenario registration differs from its committed bytes")
    data = json.loads(raw)
    scenarios = data["scenarios"]
    if (
        data["version"] != "broad-v1"
        or [s["id"] for s in scenarios] != list(range(1, 11))
        or [s["complexity"] for s in scenarios] != [1, 2, 2, 3, 3, 4, 4, 4, 5, 5]
        or any(not isinstance(s["prompt"], str) or not s["prompt"] for s in scenarios)
        or data["schedule"]["round_order"] != "alternating_forward_reverse"
        or data["schedule"]["default_runs_per_scenario"] != 2
        or data["schedule"]["default_order"]
        != list(range(1, 11)) + list(range(10, 0, -1))
    ):
        raise ValueError("Invalid broad-v1 registration")
    revision = (
        subprocess.check_output(
            ["git", "-C", str(root), "log", "-1", "--format=%H", "--", SCENARIO_PATH],
            stderr=subprocess.PIPE,
        )
        .decode()
        .strip()
    )
    return data, raw, revision


def broad_schedule(data: dict, repetitions: int, digest: str) -> list[dict]:
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError("RUNS_PER_SCENARIO must be positive")
    slots = []
    for index in range(repetitions):
        scenarios = data["scenarios"]
        for scenario in scenarios if index % 2 == 0 else reversed(scenarios):
            slots.append(
                {
                    "measurement": "pr01",
                    "benchmark_kind": "broad",
                    "scenario_sha256": digest,
                    "scenario_id": scenario["id"],
                    "complexity": scenario["complexity"],
                    "prompt": scenario["prompt"],
                    "round": index + 1,
                    "sequence": len(slots) + 1,
                }
            )
    return slots


def scenario_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


async def execute_broad(harness, slots: list[dict]) -> None:
    """Use the shared sequential guard and retain each unsubmitted slot."""
    harness.benchmark_kind = "broad"
    try:
        for index, slot in enumerate(slots):
            if harness.stop_reason:
                break
            extra = {
                k: v for k, v in slot.items() if k not in {"prompt", "measurement"}
            }
            await harness.sequential(
                slot["prompt"], "pr01", [1] * (len(slots) - index - 1), **extra
            )
    finally:
        mark_broad_not_started(harness, slots)


def mark_broad_not_started(harness, slots: list[dict]) -> None:
    recorded = {row["sequence"] for row in harness.rows}
    for slot in slots:
        if slot["sequence"] not in recorded:
            harness.rows.append(
                {
                    **slot,
                    "mode": harness.mode,
                    "execution_status": "not_started",
                    "complete": False,
                    "run_id": None,
                    "seconds": None,
                    "cost_usd": None,
                }
            )
    harness.flush()
