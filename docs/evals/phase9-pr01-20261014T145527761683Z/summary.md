# Phase 9 benchmark

Status: **FAIL**

Mode: real

pr01: {"count": 2, "median": 245.2106573994988, "p90": 254.711210726, "max": 254.711210726}; failed/incomplete: 0.

pr01 threshold: INCOMPLETE.

PR-05 individual thresholds: FAIL. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 4 | {"none": 3, "truncated": 1} | cost#1:12630, performance#1:13939, security#1:16000, security#2:unknown | {"security": "deadline"} | {"security": 0.00102077100018505} |
| 2 | 4 | {"none": 3, "truncated": 1} | cost#1:10791, performance#1:11263, security#1:16000, security#2:unknown | {"security": "deadline"} | {"security": 0.0020894940025755204} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.022995; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.5280741, "remaining_credit_usd": 1.9430499399999999, "planned_runs_remaining": 1, "run_cap_remaining": null, "projected_further_runs": 1, "assumption": "Projection at first measured cost; fresh guard checks decide."}
