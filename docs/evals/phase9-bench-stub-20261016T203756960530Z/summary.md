# Phase 9 benchmark

Status: **FAIL**

Mode: stub rehearsal; system overhead only.

Production-ready rate among generated packages: **42/42 (100.00%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| production_ready | 42 |

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
| deterministic_repairs | 42 | 0.0011834400002044276 | 0.001714502000140783 | 0.3353612279997833 |
| final_security_scan | 42 | 6.5603481984999235 | 17.72079135199965 | 18.983286636999765 |
| final_validation | 42 | 0.002797913500216964 | 0.014526216999911412 | 0.04365620899989153 |
| generation_gate | 42 | 0.2329764900000555 | 0.4618664359995819 | 0.7330201710001347 |
| initial_validation | 42 | 0.0026324065001972485 | 0.0060809269998571835 | 0.00951887000064744 |
| post_security_validation | 42 | 0.0032835515003171167 | 0.011140466999677301 | 0.029028246000052604 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 42, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 42 | 0.0011834400002044276 | 0.001714502000140783 | 0.3353612279997833 |
| final_security_scan | 42 | 6.5603481984999235 | 17.72079135199965 | 18.983286636999765 |
| final_validation | 42 | 0.002797913500216964 | 0.014526216999911412 | 0.04365620899989153 |
| generation_gate | 42 | 0.2329764900000555 | 0.4618664359995819 | 0.7330201710001347 |
| initial_validation | 42 | 0.0026324065001972485 | 0.0060809269998571835 | 0.00951887000064744 |
| post_security_validation | 42 | 0.0032835515003171167 | 0.011140466999677301 | 0.029028246000052604 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 42, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Separate scripted-fix offline verification rehearsal (excluded from quality rates and PR thresholds).

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 0 | unknown | unknown | unknown |
| final_security_scan | 0 | unknown | unknown | unknown |
| final_validation | 0 | unknown | unknown | unknown |
| generation_gate | 0 | unknown | unknown | unknown |
| initial_validation | 0 | unknown | unknown | unknown |
| post_security_validation | 0 | unknown | unknown | unknown |
| security_iteration_verification | 6 | 13.382556630499494 | 27.587816081999335 | 27.587816081999335 |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 6, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 3, 'init_reused': 9, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 14.03245393249972, "p90": 15.433307364999564, "max": 16.531596990000253}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 38.132688284499636, "p90": 38.54774219199953, "max": 38.54774219199953}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "e874bf41-5b5a-4fe9-9f21-50e2f908ff1a", "ratio_to_baseline": 2.5320842671310455, "ratio_to_pr01_prompt_median": 2.674573096455914, "pr01_prompt_median_seconds": 14.343737062499713, "pr01_reference_count": 4}

Cohort references: {"run_id": "aa16c68d-b0eb-43af-bd1d-f69f624a8b06", "ratio_to_baseline": 2.5442531057351, "ratio_to_pr01_prompt_median": 2.6874267162062533, "pr01_prompt_median_seconds": 14.343737062499713, "pr01_reference_count": 4}

Cohort references: {"run_id": "e149c835-f070-499d-a355-f8c4bdee9373", "ratio_to_baseline": 2.5016326294192646, "ratio_to_pr01_prompt_median": 2.642407843496449, "pr01_prompt_median_seconds": 14.343737062499713, "pr01_reference_count": 4}

pr03 threshold: FAIL.

pr04: {"count": 10, "median": 1.0599221775000842, "p90": 1.3116065700005493, "max": 1.4202599210002518}; failed/incomplete: 0.

pr04 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 5 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 6 | 3 | {"none": 3} | cost#1:10, security#1:10, performance#1:10 | {} | {} |
| 7 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 8 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 9 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 10 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 11 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 12 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 13 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 14 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["aa16c68d-b0eb-43af-bd1d-f69f624a8b06", "e149c835-f070-499d-a355-f8c4bdee9373", "e874bf41-5b5a-4fe9-9f21-50e2f908ff1a"], "before_remaining_usd": null, "after_remaining_usd": null}
