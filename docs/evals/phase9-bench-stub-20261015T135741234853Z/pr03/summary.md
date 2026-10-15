# Phase 9 benchmark

Status: **FAIL**

Mode: stub rehearsal; system overhead only.

Production-ready rate among generated packages: **12/12 (100.00%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| production_ready | 12 |

| Review reason | Count |
|---|---:|

| Failed check | Count |
|---|---:|

| Remaining blocking rule | Count |
|---|---:|

pr03: {"count": 4, "median": 37.62663126000007, "p90": 38.07467315399845, "max": 38.07467315399845}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "de6d1dd6-fa96-45e6-9c07-6ccb0dcdf70a", "ratio_to_baseline": 2.616546046950503, "ratio_to_pr01_prompt_median": 2.6345555810767096, "pr01_prompt_median_seconds": 14.45202880800025, "pr01_reference_count": 4}

Cohort references: {"run_id": "33ef6322-5528-4cb6-8d7f-4dce0c9e68fa", "ratio_to_baseline": 2.571281873840183, "ratio_to_pr01_prompt_median": 2.588979857297799, "pr01_prompt_median_seconds": 14.45202880800025, "pr01_reference_count": 4}

Cohort references: {"run_id": "2fbfdfaf-3ac8-420a-9fcc-8a414cfc6bc6", "ratio_to_baseline": 2.600230059313649, "ratio_to_pr01_prompt_median": 2.618127291446741, "pr01_prompt_median_seconds": 14.45202880800025, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | performance#1:10, cost#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["33ef6322-5528-4cb6-8d7f-4dce0c9e68fa", "2fbfdfaf-3ac8-420a-9fcc-8a414cfc6bc6", "de6d1dd6-fa96-45e6-9c07-6ccb0dcdf70a"], "before_remaining_usd": null, "after_remaining_usd": null}
