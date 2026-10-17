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
| deterministic_repairs | 42 | 0.006659464999984266 | 0.018014602999983254 | 0.7438376439999956 |
| final_security_scan | 42 | 12.37238090050002 | 21.222076362000053 | 22.85192581800004 |
| final_validation | 42 | 0.003949391999981344 | 0.016442263999920215 | 0.035330971000007594 |
| generation_gate | 42 | 0.48265514649997954 | 1.8248042029999851 | 2.3240231319999793 |
| initial_validation | 42 | 0.004305360999978802 | 0.016465406000008898 | 0.08282517999998618 |
| post_security_validation | 42 | 0.00407140299998332 | 0.009872445999974389 | 0.02971352700001262 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 42, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 42, 'packages_unknown': 0, 'init_runs': 42, 'init_reused': 126, 'reinitializations': 0, 'init_seconds': 9.710189274000243, 'validate_seconds': 11.694157072999872}
Gate outcomes: {'valid': 42}
Init categories: {'initialized': 42}
Schema context sizes (characters): {'generator': {'count': 42, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security context coverage: {'terraform': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: []

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 42 | 0.006659464999984266 | 0.018014602999983254 | 0.7438376439999956 |
| final_security_scan | 42 | 12.37238090050002 | 21.222076362000053 | 22.85192581800004 |
| final_validation | 42 | 0.003949391999981344 | 0.016442263999920215 | 0.035330971000007594 |
| generation_gate | 42 | 0.48265514649997954 | 1.8248042029999851 | 2.3240231319999793 |
| initial_validation | 42 | 0.004305360999978802 | 0.016465406000008898 | 0.08282517999998618 |
| post_security_validation | 42 | 0.00407140299998332 | 0.009872445999974389 | 0.02971352700001262 |
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
| security_iteration_verification | 6 | 14.890497087000028 | 31.47903976000009 | 31.47903976000009 |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 6, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 3, 'init_reused': 9, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 25.999990739499992, "p90": 35.096279912, "max": 41.67383260499997}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 51.273975412499965, "p90": 51.869445533999965, "max": 51.869445533999965}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "4492deb5-c7da-4bd8-bd3d-6dec3bf5408b", "ratio_to_baseline": 1.6849251322097714, "ratio_to_pr01_prompt_median": 1.6183783018899758, "pr01_prompt_median_seconds": 31.415194181500055, "pr01_reference_count": 4}

Cohort references: {"run_id": "3c4ee32a-8f49-4c4a-9cc8-f6f81a6d755c", "ratio_to_baseline": 1.7189863109975851, "ratio_to_pr01_prompt_median": 1.6510942200237972, "pr01_prompt_median_seconds": 31.415194181500055, "pr01_reference_count": 4}

Cohort references: {"run_id": "3a4b2f8d-cd6d-4779-ba1c-0157146f4df3", "ratio_to_baseline": 1.713578975058531, "ratio_to_pr01_prompt_median": 1.6459004491033542, "pr01_prompt_median_seconds": 31.415194181500055, "pr01_reference_count": 4}

pr03 threshold: FAIL.

pr04: {"count": 10, "median": 2.1626707144999955, "p90": 3.329731934999927, "max": 3.4380098000000316}; failed/incomplete: 0.

pr04 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:10, cost#1:10, performance#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 5 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 6 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 7 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 8 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 9 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 10 | 3 | {"none": 3} | security#1:10, cost#1:10, performance#1:10 | {} | {} |
| 11 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 12 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 13 | 3 | {"none": 3} | performance#1:10, cost#1:10, security#1:10 | {} | {} |
| 14 | 3 | {"none": 3} | cost#1:10, security#1:10, performance#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["3c4ee32a-8f49-4c4a-9cc8-f6f81a6d755c", "3a4b2f8d-cd6d-4779-ba1c-0157146f4df3", "4492deb5-c7da-4bd8-bd3d-6dec3bf5408b"], "before_remaining_usd": null, "after_remaining_usd": null}
