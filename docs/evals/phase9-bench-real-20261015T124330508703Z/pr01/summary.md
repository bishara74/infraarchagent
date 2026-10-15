# Phase 9 benchmark

Status: **PASS**

Mode: real

pr01: {"count": 10, "median": 41.62084038749981, "p90": 51.993932125000356, "max": 60.01117616299962}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | performance#1:2742, security#1:3209, cost#1:4095 | {} | {} |
| 2 | 4 | {"none": 4} | cost#1:2516, security#1:3588, performance#1:1749, performance#2:1307 | {"performance": "incomplete_package"} | {} |
| 3 | 3 | {"none": 3} | cost#1:1415, security#1:1067, performance#1:1245 | {} | {} |
| 4 | 3 | {"none": 3} | security#1:3741, cost#1:2998, performance#1:3329 | {} | {} |
| 5 | 4 | {"none": 4} | security#1:1895, performance#1:2947, cost#1:1315, cost#2:1309 | {"cost": "incomplete_package"} | {} |
| 6 | 3 | {"none": 3} | performance#1:934, cost#1:1042, security#1:984 | {} | {} |
| 7 | 6 | {"none": 6} | cost#1:2864, cost#2:2016, performance#1:2992, performance#2:2794, security#1:3211, security#2:2831 | {"cost": "incomplete_package"} | {} |
| 8 | 4 | {"none": 4} | cost#1:2973, security#1:4088, performance#1:2005, performance#2:3307 | {} | {} |
| 9 | 3 | {"none": 3} | cost#1:1344, security#1:1555, performance#1:1180 | {} | {} |
| 10 | 3 | {"none": 3} | performance#1:3526, cost#1:4800, security#1:3695 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.363189; unknown costs stay unknown.
