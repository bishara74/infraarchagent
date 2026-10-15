# Phase 9 benchmark

Status: **FAIL**

Mode: real

pr01: {"count": 2, "median": 145.4640151780004, "p90": 213.55484284900012, "max": 213.55484284900012}; failed/incomplete: 1.

pr01 threshold: INCOMPLETE.

PR-05 individual thresholds: FAIL. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 9 | {"truncated": 5, "schema_invalid": 1, "none": 3} | cost#1:8000, cost#2:7651, cost#3:unknown, performance#1:8000, performance#2:8000, performance#3:unknown, security#1:8000, security#2:8000, security#3:unknown | {"cost": "deadline", "performance": "deadline", "security": "deadline"} | {"cost": 0.0013874980013497407, "performance": 0.0010148130004381528, "security": 0.0008467460011161165} |
| 2 | 8 | {"truncated": 5, "none": 3} | performance#1:8000, performance#2:7424, cost#1:8000, cost#2:8000, cost#3:unknown, security#1:8000, security#2:8000, security#3:unknown | {"cost": "deadline", "security": "deadline"} | {"cost": 0.0008761249991948716, "security": 0.0006210800002008909} |
| 3 | 3 | {"none": 3} | cost#1:3090, performance#1:3306, security#1:3624 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.349312; unknown costs stay unknown.
