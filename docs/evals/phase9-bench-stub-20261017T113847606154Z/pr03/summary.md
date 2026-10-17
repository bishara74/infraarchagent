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
| deterministic_repairs | 12 | 0.009898802499947124 | 0.02403583599993908 | 0.026627458999996634 |
| final_security_scan | 12 | 20.442015825499936 | 21.74048449399993 | 22.85192581800004 |
| final_validation | 12 | 0.005241255999976602 | 0.03308126899992203 | 0.035330971000007594 |
| generation_gate | 12 | 1.5674307995000163 | 1.826464265000027 | 1.9467629260000194 |
| initial_validation | 12 | 0.011220540500005427 | 0.02364486500005114 | 0.08282517999998618 |
| post_security_validation | 12 | 0.005002240999999685 | 0.006486756999947829 | 0.02971352700001262 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 12, 'init_reused': 36, 'reinitializations': 0, 'init_seconds': 4.758048183000028, 'validate_seconds': 5.396061642999939}
Gate outcomes: {'valid': 12}
Init categories: {'initialized': 12}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security context coverage: {'terraform': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: []

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 12 | 0.009898802499947124 | 0.02403583599993908 | 0.026627458999996634 |
| final_security_scan | 12 | 20.442015825499936 | 21.74048449399993 | 22.85192581800004 |
| final_validation | 12 | 0.005241255999976602 | 0.03308126899992203 | 0.035330971000007594 |
| generation_gate | 12 | 1.5674307995000163 | 1.826464265000027 | 1.9467629260000194 |
| initial_validation | 12 | 0.011220540500005427 | 0.02364486500005114 | 0.08282517999998618 |
| post_security_validation | 12 | 0.005002240999999685 | 0.006486756999947829 | 0.02971352700001262 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 51.273975412499965, "p90": 51.869445533999965, "max": 51.869445533999965}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "4492deb5-c7da-4bd8-bd3d-6dec3bf5408b", "ratio_to_baseline": 1.6849251322097714, "ratio_to_pr01_prompt_median": 1.6183783018899758, "pr01_prompt_median_seconds": 31.415194181500055, "pr01_reference_count": 4}

Cohort references: {"run_id": "3c4ee32a-8f49-4c4a-9cc8-f6f81a6d755c", "ratio_to_baseline": 1.7189863109975851, "ratio_to_pr01_prompt_median": 1.6510942200237972, "pr01_prompt_median_seconds": 31.415194181500055, "pr01_reference_count": 4}

Cohort references: {"run_id": "3a4b2f8d-cd6d-4779-ba1c-0157146f4df3", "ratio_to_baseline": 1.713578975058531, "ratio_to_pr01_prompt_median": 1.6459004491033542, "pr01_prompt_median_seconds": 31.415194181500055, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | performance#1:10, cost#1:10, security#1:10 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:10, security#1:10, performance#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["3c4ee32a-8f49-4c4a-9cc8-f6f81a6d755c", "3a4b2f8d-cd6d-4779-ba1c-0157146f4df3", "4492deb5-c7da-4bd8-bd3d-6dec3bf5408b"], "before_remaining_usd": null, "after_remaining_usd": null}
