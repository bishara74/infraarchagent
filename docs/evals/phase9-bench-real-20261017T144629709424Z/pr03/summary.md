# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **1/12 (8.33%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 11 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| validation_failed | 11 |
| unresolved_security_findings | 9 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 11 |
| terraform.validate: Terraform configuration diagnostic | 5 |
| ansible-lint.lint: ansible-lint optional lint failed | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 17 |
| AWS-0164 | 15 |
| CKV_AWS_130 | 15 |
| AWS-0028 | 11 |
| AWS-0131 | 10 |
| CKV_AWS_8 | 10 |
| CKV_AWS_103 | 9 |
| AWS-0176 | 8 |
| AWS-0177 | 8 |
| CKV_AWS_129 | 8 |
| CKV_AWS_161 | 8 |
| CKV_AWS_293 | 8 |
| CKV_AWS_91 | 8 |
| AWS-0178 | 7 |
| CKV2_AWS_11 | 7 |
| CKV_AWS_260 | 7 |
| CKV_AWS_378 | 7 |
| CKV_AWS_118 | 7 |
| CKV_AWS_353 | 7 |
| AWS-0053 | 5 |

Final failure origins: {'generated': 17}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Unsupported argument | 2 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 3 |
| after_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 4 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| before_security / rejected / no_improvement | Unsupported argument | 6 |
| before_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 5 |
| generation / rejected / no_improvement | Generation syntax check failed | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported argument | 5 |
| generation / rejected / no_improvement | ansible-lint optional lint failed | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 56 | 0.07393980049982929 | 0.23413983199861832 | 0.6657897969998885 |
| final_security_scan | 12 | 5.841479719500967 | 10.366189045998908 | 14.330641795000702 |
| final_validation | 12 | 0.14505576949977694 | 0.7697538310003438 | 1.8970636089998152 |
| generation_gate | 12 | 52.51191607449982 | 81.54405851199954 | 82.31395736599916 |
| initial_validation | 12 | 0.1342736890001106 | 0.37911554200036335 | 9.249846120999791 |
| post_security_validation | 12 | 0.1414897614995425 | 5.589288845998453 | 7.703963383999508 |
| security_iteration_verification | 44 | 8.605634727000506 | 28.415884385000027 | 37.2485766389982 |
| validation_repair_round | 27 | 17.970564985000237 | 43.55415015800099 | 75.50719103099982 |

Iteration outcomes: {'attempted_fix_iterations': 44, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 15}.
Initialization: {'init_runs': 24, 'init_reused': 78, 'reinitializations': 12}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 28, 'init_reused': 120, 'reinitializations': 16, 'init_seconds': 311.30704303399943, 'validate_seconds': 500.33645689500554}
Gate outcomes: {'invalid': 11, 'valid': 1}
Init categories: {'validation_cached': 11, 'initialized': 1}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 27, 'median': 15974, 'p90': 15998, 'max': 16000}, 'security': {'count': 49, 'median': 15969, 'p90': 15999, 'max': 16000}}
Security context coverage: {'terraform': {'total': 44, 'positive': 44, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 44}}, 'other': {'total': 5, 'positive': 0, 'zero': 5, 'missing': 0, 'reasons': {'not_terraform': 5}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 4}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 13}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Cycle', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid index', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid resource type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared input variable', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared resource', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 10}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 9}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 2}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 56 | 0.07393980049982929 | 0.23413983199861832 | 0.6657897969998885 |
| final_security_scan | 12 | 5.841479719500967 | 10.366189045998908 | 14.330641795000702 |
| final_validation | 12 | 0.14505576949977694 | 0.7697538310003438 | 1.8970636089998152 |
| generation_gate | 12 | 52.51191607449982 | 81.54405851199954 | 82.31395736599916 |
| initial_validation | 12 | 0.1342736890001106 | 0.37911554200036335 | 9.249846120999791 |
| post_security_validation | 12 | 0.1414897614995425 | 5.589288845998453 | 7.703963383999508 |
| security_iteration_verification | 44 | 8.605634727000506 | 28.415884385000027 | 37.2485766389982 |
| validation_repair_round | 27 | 17.970564985000237 | 43.55415015800099 | 75.50719103099982 |

Iteration outcomes: {'attempted_fix_iterations': 44, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 15}.
Initialization: {'init_runs': 24, 'init_reused': 78, 'reinitializations': 12}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 224.20069103199967, "p90": 275.7869779339999, "max": 275.7869779339999}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "d69b92d6-99eb-4461-bba5-6b27e757a584", "ratio_to_baseline": 2.4879884101521124, "ratio_to_pr01_prompt_median": 2.9190229678099624, "pr01_prompt_median_seconds": 94.47920793199955, "pr01_reference_count": 4}

Cohort references: {"run_id": "4032c564-2c6b-4eef-b575-370a3f8dc02d", "ratio_to_baseline": 2.2004256974013665, "ratio_to_pr01_prompt_median": 2.5816411055070567, "pr01_prompt_median_seconds": 94.47920793199955, "pr01_reference_count": 4}

Cohort references: {"run_id": "8265dad1-b41d-4c79-b98d-985edd643785", "ratio_to_baseline": 1.8447886561871638, "ratio_to_pr01_prompt_median": 2.1643912954708564, "pr01_prompt_median_seconds": 94.47920793199955, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:3984, security#1:3425, performance#1:3251 | {} | {} |
| 2 | 4 | {"none": 4} | cost#1:3348, performance#1:3478, security#1:3151, security#2:4571 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:2847, performance#1:3701, security#1:3127 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:3093, security#1:3776, performance#1:4561 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.497307; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.3678592, "average_cost_usd": 0.12261973333333333, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["4032c564-2c6b-4eef-b575-370a3f8dc02d", "8265dad1-b41d-4c79-b98d-985edd643785", "d69b92d6-99eb-4461-bba5-6b27e757a584"], "before_remaining_usd": 7.79526714, "after_remaining_usd": 7.427407939999998}
