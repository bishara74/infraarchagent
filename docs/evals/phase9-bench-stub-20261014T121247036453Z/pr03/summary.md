# Phase 9 benchmark

Status: **FAIL**

Mode: stub rehearsal; system overhead only.

pr03: {"count": 4, "median": 18.114408149499923, "p90": 18.30096994900032, "max": 18.30096994900032}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "3580716b-51c7-49a5-90fb-5a62bc4453fb", "ratio_to_baseline": 2.21272032800305, "ratio_to_pr01_prompt_median": 2.7301670748879805, "pr01_prompt_median_seconds": 6.618459620000067, "pr01_reference_count": 4}

Cohort references: {"run_id": "9f2e9baf-a67d-4e98-857d-7498655717ed", "ratio_to_baseline": 2.2410651659376377, "ratio_to_pr01_prompt_median": 2.7651403800511716, "pr01_prompt_median_seconds": 6.618459620000067, "pr01_reference_count": 4}

Cohort references: {"run_id": "d475409c-2412-4545-85b9-ba9cacf83cb3", "ratio_to_baseline": 2.2237187480185634, "ratio_to_pr01_prompt_median": 2.743737485853221, "pr01_prompt_median_seconds": 6.618459620000067, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["9f2e9baf-a67d-4e98-857d-7498655717ed", "d475409c-2412-4545-85b9-ba9cacf83cb3", "3580716b-51c7-49a5-90fb-5a62bc4453fb"], "before_remaining_usd": null, "after_remaining_usd": null}
