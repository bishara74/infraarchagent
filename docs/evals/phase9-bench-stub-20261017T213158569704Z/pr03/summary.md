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
| deterministic_repairs | 12 | 0.0017444620025344193 | 0.002168702005292289 | 0.0022445680006057955 |
| final_security_scan | 12 | 13.435964180502197 | 14.84125173099892 | 15.129488671002036 |
| final_validation | 12 | 0.006980087000556523 | 0.024293950998981018 | 0.025142172999039758 |
| generation_gate | 12 | 0.36056773149903165 | 0.4372248709987616 | 0.4468632530042669 |
| initial_validation | 12 | 0.002576387498265831 | 0.0048285860029864125 | 0.005604857004072983 |
| post_security_validation | 12 | 0.005204809502174612 | 0.008006763004232198 | 0.008811651001451537 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 12, 'init_reused': 36, 'reinitializations': 0, 'init_seconds': 1.278847567999037, 'validate_seconds': 1.478764282022894}
Gate outcomes: {'valid': 12}
Init categories: {'initialized': 12}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 2556.0, 'p90': 2556, 'max': 2556}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security context coverage: {'terraform': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: []

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 0 |

Phase 9f measured/unknown packages: (12, 0)
Catalogue retained by rule: {}
Template outcomes: []
Template introduced rules: {}
Partial groups: {}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Fixer model limits and calls: [{'model': 'stub', 'sessions': 12, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 12 | 0.0017444620025344193 | 0.002168702005292289 | 0.0022445680006057955 |
| final_security_scan | 12 | 13.435964180502197 | 14.84125173099892 | 15.129488671002036 |
| final_validation | 12 | 0.006980087000556523 | 0.024293950998981018 | 0.025142172999039758 |
| generation_gate | 12 | 0.36056773149903165 | 0.4372248709987616 | 0.4468632530042669 |
| initial_validation | 12 | 0.002576387498265831 | 0.0048285860029864125 | 0.005604857004072983 |
| post_security_validation | 12 | 0.005204809502174612 | 0.008006763004232198 | 0.008811651001451537 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 33.313323485497676, "p90": 33.81812153200008, "max": 33.81812153200008}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "e3ec8eae-9ef2-4456-a6bf-841a40494800", "ratio_to_baseline": 2.6372263168935843, "ratio_to_pr01_prompt_median": 2.536378528114876, "pr01_prompt_median_seconds": 13.170761306999339, "pr01_reference_count": 4}

Cohort references: {"run_id": "83eec2f3-2507-43b9-8a0a-3870c895eb89", "ratio_to_baseline": 2.6697582322212963, "ratio_to_pr01_prompt_median": 2.56766641986201, "pr01_prompt_median_seconds": 13.170761306999339, "pr01_reference_count": 4}

Cohort references: {"run_id": "9c41c85f-a962-406d-b26c-461d72bafcf4", "ratio_to_baseline": 2.622587983194091, "ratio_to_pr01_prompt_median": 2.5222999657082528, "pr01_prompt_median_seconds": 13.170761306999339, "pr01_reference_count": 4}

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

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["83eec2f3-2507-43b9-8a0a-3870c895eb89", "9c41c85f-a962-406d-b26c-461d72bafcf4", "e3ec8eae-9ef2-4456-a6bf-841a40494800"], "before_remaining_usd": null, "after_remaining_usd": null}
