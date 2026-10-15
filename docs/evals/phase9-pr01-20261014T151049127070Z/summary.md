# Phase 9 benchmark

Status: **FAIL**

Mode: real

pr01: {"count": 3, "median": 87.99509044500155, "p90": 145.36303806499927, "max": 145.36303806499927}; failed/incomplete: 0.

pr01 threshold: INCOMPLETE.

PR-05 individual thresholds: FAIL. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | performance#1:3445, security#1:3726, cost#1:3634 | {} | {} |
| 2 | 6 | {"none": 6} | cost#1:1715, cost#2:2842, security#1:2672, security#2:4148, performance#1:1686, performance#2:2789 | {} | {} |
| 3 | 3 | {"none": 3} | performance#1:945, security#1:1553, cost#1:1331 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.132056; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.0408134, "remaining_credit_usd": 1.3998264900000006, "planned_runs_remaining": 2, "run_cap_remaining": null, "projected_further_runs": 2, "assumption": "Projection at first measured cost; fresh guard checks decide."}
