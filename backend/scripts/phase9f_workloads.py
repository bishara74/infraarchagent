"""Additional PR-05 workload views; aggregate verdict calculation is unchanged."""

from collections import Counter

from scripts.phase9_report import statistics_for


def pr05_workloads(runs: list[dict], agents: list[dict]) -> dict:
    groups = {
        name: []
        for name in (
            "isolated_pr01",
            "isolated_pr03_baseline",
            "concurrent_pr03_cohort",
            "unclassified",
        )
    }
    membership = {}
    for run in runs:
        group = (
            "isolated_pr01"
            if run.get("measurement") == "pr01"
            else "concurrent_pr03_cohort"
            if run.get("measurement") == "pr03" and run.get("role") == "cohort"
            else "isolated_pr03_baseline"
            if run.get("measurement") == "pr03" and run.get("role") == "baseline"
            else "unclassified"
        )
        membership[run.get("run_id")] = group
    for row in agents:
        if row.get("threshold_seconds") is not None:
            groups[membership.get(row.get("run_id"), "unclassified")].append(row)
    result = {}
    for name, rows in groups.items():
        failed = [r for r in rows if r.get("pass") is False]
        unknown = [r for r in rows if r.get("pass") is None]
        result[name] = {
            "verdict": "FAIL"
            if failed
            else "INCOMPLETE"
            if unknown or not rows
            else "PASS",
            "observations": len(rows),
            "failures": len(failed),
            "missing_measurements": len(unknown),
            "agents": dict(Counter(r["agent"] for r in rows)),
            "durations": statistics_for(
                [r["seconds"] for r in rows if type(r.get("seconds")) in {int, float}]
            ),
            "failed_observations": [
                {
                    k: r.get(k)
                    for k in (
                        "run_id",
                        "agent",
                        "variant",
                        "iteration",
                        "seconds",
                        "threshold_seconds",
                    )
                }
                for r in failed
            ],
        }
    return result
