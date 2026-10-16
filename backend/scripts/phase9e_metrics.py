"""Strict, source-free Phase 9e descriptive measurements and summaries."""

from collections import Counter

from scripts.phase9_report import statistics_for
from scripts.phase9c_metrics import number

STAGES = {
    "deterministic_repairs",
    "generation_gate",
    "initial_validation",
    "validation_repair_round",
    "post_security_validation",
    "final_validation",
    "final_security_scan",
    "security_iteration_verification",
}
REASONS = {
    "terraform_regression",
    "terraform_verification_unavailable",
    "new_blocking_findings",
    "iteration_deadline",
    "invalid_patch",
    "no_improvement",
    "verification_unavailable",
    "improved",
    "deadline",
    "round_limit",
    "no_targets",
}


def measurement(raw: object) -> dict | None:
    if not isinstance(raw, dict) or raw.get("stage") not in STAGES:
        return None
    result = {
        "stage": raw["stage"],
        "duration_seconds": number(raw.get("duration_seconds")),
    }
    phase = raw.get("phase")
    result["phase"] = (
        phase
        if phase in {"generation", "before_security", "after_security", "security", ""}
        else "unknown"
    )
    for key in (
        "iteration",
        "count",
        "before_failed",
        "after_failed",
        "init_runs",
        "init_reused",
        "reinitializations",
    ):
        if key in raw:
            result[key] = raw[key] if type(raw[key]) is int and raw[key] >= 0 else None
    for key in (
        "init_seconds",
        "validate_seconds",
        "terraform_verification_seconds",
        "security_verification_seconds",
    ):
        if key in raw:
            result[key] = number(raw[key])
    for key in ("attempted", "deadline_only", "candidate_created", "fix_started"):
        if key in raw:
            result[key] = raw[key] if type(raw[key]) is bool else None
    outcome = raw.get("outcome")
    if outcome in {
        "accepted",
        "rejected",
        "stopped",
        "rolled_back",
        "no_change",
        "passed",
        "failed",
        "error",
    }:
        result["outcome"] = outcome
    if raw.get("reason") in REASONS:
        result["reason"] = raw["reason"]
    if isinstance(raw.get("reasons"), list):
        result["reasons"] = sorted(
            {r for r in raw["reasons"] if isinstance(r, str) and r in REASONS}
        )
    return result


def measurement_summary(records: list[dict]) -> tuple[dict, str]:
    records = [m for raw in records if (m := measurement(raw)) is not None]
    timings = {
        stage: statistics_for(
            [
                m["duration_seconds"]
                for m in records
                if m["stage"] == stage and m["duration_seconds"] is not None
            ]
        )
        for stage in sorted(STAGES)
    }
    iterations = [m for m in records if m["stage"] == "security_iteration_verification"]
    counts = {
        "attempted_fix_iterations": sum(
            m.get("fix_started") is True for m in iterations
        ),
        "deadline_only_rollbacks": sum(
            m.get("deadline_only") is True for m in iterations
        ),
        "deadline_before_candidate": sum(
            "iteration_deadline" in m.get("reasons", [])
            and m.get("candidate_created") is False
            for m in iterations
        ),
        "multiple_cause_deadline_rollbacks": sum(
            "iteration_deadline" in m.get("reasons", []) and len(m["reasons"]) > 1
            for m in iterations
        ),
        "validity_regression_rollbacks": sum(
            "terraform_regression" in m.get("reasons", []) for m in iterations
        ),
    }
    # Initialization metrics occur in gate/iteration rows; repair/final validation
    # rows may also record them. Never infer runs from absent historical fields.
    initialization = {
        key: sum(m.get(key) or 0 for m in records)
        for key in ("init_runs", "init_reused", "reinitializations")
    }
    reasons = Counter(
        m["phase"]
        for m in records
        if m["stage"] == "validation_repair_round" and m.get("reason") == "deadline"
    )
    lines = [
        "Descriptive durations (seconds; no new thresholds):",
        "",
        "| Stage | Count | Median | p90 | Maximum |",
        "|---|---:|---:|---:|---:|",
    ]
    for stage, stats in timings.items():
        values = [
            str(stats[k]) if stats[k] is not None else "unknown"
            for k in ("count", "median", "p90", "max")
        ]
        lines.append("| " + stage + " | " + " | ".join(values) + " |")
    lines += [
        "",
        f"Iteration outcomes: {counts}.",
        f"Initialization: {initialization}.",
        f"Repair deadline stops (measured rounds): {dict(reasons)}.",
        "Historical 9d stops: four initial / nine post-security "
        "(separate historical evidence). A deadline-only rollback does not establish "
        "that the candidate would have passed verification.",
    ]
    return {
        "durations": timings,
        "iterations": counts,
        "initialization": initialization,
        "repair_deadline_stops": dict(reasons),
    }, "\n".join(lines)
