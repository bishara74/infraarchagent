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

Final failure origins: {}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 12 | 0.0010384834999968007 | 0.0014014899998073815 | 0.0019061240000155522 |
| final_security_scan | 12 | 17.451734958499856 | 18.471340633999716 | 18.983286636999765 |
| final_validation | 12 | 0.009152182499747141 | 0.0268036529996607 | 0.04365620899989153 |
| generation_gate | 12 | 0.38797899749988574 | 0.4732765050002854 | 0.5008643390001453 |
| initial_validation | 12 | 0.00555539349988976 | 0.008329236999998102 | 0.00951887000064744 |
| post_security_validation | 12 | 0.004407433500091429 | 0.023486345000492292 | 0.029028246000052604 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 12 | 0.0010384834999968007 | 0.0014014899998073815 | 0.0019061240000155522 |
| final_security_scan | 12 | 17.451734958499856 | 18.471340633999716 | 18.983286636999765 |
| final_validation | 12 | 0.009152182499747141 | 0.0268036529996607 | 0.04365620899989153 |
| generation_gate | 12 | 0.38797899749988574 | 0.4732765050002854 | 0.5008643390001453 |
| initial_validation | 12 | 0.00555539349988976 | 0.008329236999998102 | 0.00951887000064744 |
| post_security_validation | 12 | 0.004407433500091429 | 0.023486345000492292 | 0.029028246000052604 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 38.132688284499636, "p90": 38.54774219199953, "max": 38.54774219199953}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "e874bf41-5b5a-4fe9-9f21-50e2f908ff1a", "ratio_to_baseline": 2.5320842671310455, "ratio_to_pr01_prompt_median": 2.674573096455914, "pr01_prompt_median_seconds": 14.343737062499713, "pr01_reference_count": 4}

Cohort references: {"run_id": "aa16c68d-b0eb-43af-bd1d-f69f624a8b06", "ratio_to_baseline": 2.5442531057351, "ratio_to_pr01_prompt_median": 2.6874267162062533, "pr01_prompt_median_seconds": 14.343737062499713, "pr01_reference_count": 4}

Cohort references: {"run_id": "e149c835-f070-499d-a355-f8c4bdee9373", "ratio_to_baseline": 2.5016326294192646, "ratio_to_pr01_prompt_median": 2.642407843496449, "pr01_prompt_median_seconds": 14.343737062499713, "pr01_reference_count": 4}

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

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["aa16c68d-b0eb-43af-bd1d-f69f624a8b06", "e149c835-f070-499d-a355-f8c4bdee9373", "e874bf41-5b5a-4fe9-9f21-50e2f908ff1a"], "before_remaining_usd": null, "after_remaining_usd": null}
