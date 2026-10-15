# Phase 9 benchmark

Status: **FAIL**

Mode: real

pr01: {"count": 10, "median": 41.62084038749981, "p90": 51.993932125000356, "max": 60.01117616299962}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 60.33354076199976, "p90": 61.86122878199967, "max": 61.86122878199967}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "ce810609-4d99-4a98-9e58-44a997598279", "ratio_to_baseline": 1.478364186984553, "ratio_to_pr01_prompt_median": 1.3836617415436532, "pr01_prompt_median_seconds": 42.554415848999724, "pr01_reference_count": 4}

Cohort references: {"run_id": "7044915b-ac94-44dd-b965-832b77192f11", "ratio_to_baseline": 1.5531929465450904, "ratio_to_pr01_prompt_median": 1.4536970499491364, "pr01_prompt_median_seconds": 42.554415848999724, "pr01_reference_count": 4}

Cohort references: {"run_id": "29e0f372-18fc-497a-9989-9289bfc15ff7", "ratio_to_baseline": 1.5513082523348636, "ratio_to_pr01_prompt_median": 1.4519330872556684, "pr01_prompt_median_seconds": 42.554415848999724, "pr01_reference_count": 4}

pr03 threshold: FAIL.

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
| 11 | 5 | {"none": 5} | security#1:4297, performance#1:3861, performance#2:2151, cost#1:2874, cost#2:2313 | {"performance": "incomplete_package", "cost": "incomplete_package"} | {} |
| 12 | 3 | {"none": 3} | cost#1:3119, performance#1:3298, security#1:3445 | {} | {} |
| 13 | 4 | {"none": 4} | performance#1:2974, security#1:2788, cost#1:2751, cost#2:3059 | {"cost": "incomplete_package"} | {} |
| 14 | 3 | {"none": 3} | cost#1:2101, performance#1:3014, security#1:3092 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.428499; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0460457, "average_cost_usd": 0.015348566666666667, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["7044915b-ac94-44dd-b965-832b77192f11", "29e0f372-18fc-497a-9989-9289bfc15ff7", "ce810609-4d99-4a98-9e58-44a997598279"], "before_remaining_usd": 0.9147948400000008, "after_remaining_usd": 0.8687491400000003}

First-run affordability advisory: {"measured_first_run_cost_usd": 0.0, "remaining_credit_usd": 1.3057054899999994, "planned_runs_remaining": 13, "run_cap_remaining": null, "projected_further_runs": 13, "assumption": "Projection at first measured cost; fresh guard checks decide."}
