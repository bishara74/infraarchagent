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
| deterministic_repairs | 42 | 0.002111378500558203 | 0.0028264819993637502 | 0.8361034050030867 |
| final_security_scan | 42 | 6.765108182498807 | 16.751418580999598 | 18.26927741200052 |
| final_validation | 42 | 0.0027787230028479826 | 0.0077519439946627244 | 0.03032834800251294 |
| generation_gate | 42 | 0.24710530399897834 | 0.5808713509977679 | 0.653253014999791 |
| initial_validation | 42 | 0.0025324725029349793 | 0.0037012120010331273 | 0.007725217998086009 |
| post_security_validation | 42 | 0.00295594099588925 | 0.005256800002825912 | 0.030560187995433807 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 42, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 42, 'packages_unknown': 0, 'init_runs': 42, 'init_reused': 126, 'reinitializations': 0, 'init_seconds': 3.102862660991377, 'validate_seconds': 3.3935669700294966}
Gate outcomes: {'valid': 42}
Init categories: {'initialized': 42}
Schema context sizes (characters): {'generator': {'count': 42, 'median': 2746.0, 'p90': 2746, 'max': 2746}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security context coverage: {'terraform': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: []

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 0 |

Phase 9f measured/unknown packages: (42, 0)
Catalogue retained by rule: {}
Template outcomes: []
Template introduced rules: {}
Partial groups: {}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 42}
Fixer model limits and calls: [{'model': 'stub', 'sessions': 42, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 42 | 0.002111378500558203 | 0.0028264819993637502 | 0.8361034050030867 |
| final_security_scan | 42 | 6.765108182498807 | 16.751418580999598 | 18.26927741200052 |
| final_validation | 42 | 0.0027787230028479826 | 0.0077519439946627244 | 0.03032834800251294 |
| generation_gate | 42 | 0.24710530399897834 | 0.5808713509977679 | 0.653253014999791 |
| initial_validation | 42 | 0.0025324725029349793 | 0.0037012120010331273 | 0.007725217998086009 |
| post_security_validation | 42 | 0.00295594099588925 | 0.005256800002825912 | 0.030560187995433807 |
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
| security_iteration_verification | 6 | 14.421172749505786 | 29.660632250008348 | 29.660632250008348 |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 6, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 3, 'init_reused': 9, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 14.703492901498976, "p90": 16.130179091000173, "max": 18.832189420005307}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 43.090283357498265, "p90": 43.2479923350038, "max": 43.2479923350038}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "6776bfcb-29ab-49cc-b6ba-c24879a18e0b", "ratio_to_baseline": 2.4538211908284264, "ratio_to_pr01_prompt_median": 2.8007312647239395, "pr01_prompt_median_seconds": 15.414046695499565, "pr01_reference_count": 4}

Cohort references: {"run_id": "7eaa7063-da68-4f1a-8f72-2e0f50c2a8fb", "ratio_to_baseline": 2.4446904957400837, "ratio_to_pr01_prompt_median": 2.7903097135130506, "pr01_prompt_median_seconds": 15.414046695499565, "pr01_reference_count": 4}

Cohort references: {"run_id": "69df0e74-e218-4512-9a5c-86b8a71a9a8b", "ratio_to_baseline": 2.458220036707843, "ratio_to_pr01_prompt_median": 2.805751999416928, "pr01_prompt_median_seconds": 15.414046695499565, "pr01_reference_count": 4}

pr03 threshold: FAIL.

pr04: {"count": 10, "median": 1.4159573645010823, "p90": 1.6525250210033846, "max": 1.6955894269995042}; failed/incomplete: 0.

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
| 6 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
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

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["7eaa7063-da68-4f1a-8f72-2e0f50c2a8fb", "69df0e74-e218-4512-9a5c-86b8a71a9a8b", "6776bfcb-29ab-49cc-b6ba-c24879a18e0b"], "before_remaining_usd": null, "after_remaining_usd": null}
