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
| deterministic_repairs | 12 | 0.00390467550005269 | 0.0062029069995332975 | 0.006746593000571011 |
| final_security_scan | 12 | 13.587466777999907 | 15.393764793000628 | 16.00957942599962 |
| final_validation | 12 | 0.005081114000404341 | 0.02404791600019962 | 0.036550861000250734 |
| generation_gate | 12 | 0.5652191475001018 | 0.7102553760005321 | 0.761094729999968 |
| initial_validation | 12 | 0.004191366999748425 | 0.005173968999770295 | 0.005411717999777466 |
| post_security_validation | 12 | 0.004841024000143079 | 0.02241900799981522 | 0.029135855000276933 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 12, 'init_reused': 36, 'reinitializations': 0, 'init_seconds': 1.9554615350007225, 'validate_seconds': 2.1676567300000897}
Gate outcomes: {'valid': 12}
Init categories: {'initialized': 12}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security iteration outcomes by class: []

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 12 | 0.00390467550005269 | 0.0062029069995332975 | 0.006746593000571011 |
| final_security_scan | 12 | 13.587466777999907 | 15.393764793000628 | 16.00957942599962 |
| final_validation | 12 | 0.005081114000404341 | 0.02404791600019962 | 0.036550861000250734 |
| generation_gate | 12 | 0.5652191475001018 | 0.7102553760005321 | 0.761094729999968 |
| initial_validation | 12 | 0.004191366999748425 | 0.005173968999770295 | 0.005411717999777466 |
| post_security_validation | 12 | 0.004841024000143079 | 0.02241900799981522 | 0.029135855000276933 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 34.84260837250031, "p90": 35.207176423999954, "max": 35.207176423999954}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "17f95809-efbb-4bd1-98ab-959dec631869", "ratio_to_baseline": 2.0547566630422223, "ratio_to_pr01_prompt_median": 2.2335792637544203, "pr01_prompt_median_seconds": 15.733003533499868, "pr01_reference_count": 4}

Cohort references: {"run_id": "a2ba7c61-22d9-4a7b-b616-dad2abdfc0f2", "ratio_to_baseline": 2.0586313621300865, "ratio_to_pr01_prompt_median": 2.237791172488727, "pr01_prompt_median_seconds": 15.733003533499868, "pr01_reference_count": 4}

Cohort references: {"run_id": "6fc09a93-feb2-49ae-b2e2-2073e27c7a0b", "ratio_to_baseline": 2.0198720700447073, "ratio_to_pr01_prompt_median": 2.1956587133820955, "pr01_prompt_median_seconds": 15.733003533499868, "pr01_reference_count": 4}

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

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["a2ba7c61-22d9-4a7b-b616-dad2abdfc0f2", "6fc09a93-feb2-49ae-b2e2-2073e27c7a0b", "17f95809-efbb-4bd1-98ab-959dec631869"], "before_remaining_usd": null, "after_remaining_usd": null}
