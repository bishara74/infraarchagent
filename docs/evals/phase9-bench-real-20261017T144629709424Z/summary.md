# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **1/40 (2.50%)**.
Missing variants: 2; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 39 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 35 |
| validation_failed | 33 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 27 |
| terraform.validate: Terraform configuration diagnostic | 8 |
| helm.lint: helm optional lint failed | 8 |
| terraform.validate: Reference to undeclared resource | 8 |
| ansible-lint.lint: ansible-lint optional lint failed | 3 |
| terraform.validate: Invalid resource type | 3 |
| terraform.validate: Missing required argument | 2 |
| document.parse: Document could not be parsed | 1 |
| terraform.validate: Invalid single-argument block definition | 1 |
| k8s.configmap_ref: ConfigMap reference must resolve in its namespace | 1 |
| terraform.validate: Unsupported attribute | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 50 |
| CKV_AWS_130 | 41 |
| AWS-0164 | 40 |
| AWS-0038 | 35 |
| AWS-0028 | 30 |
| AWS-0132 | 24 |
| CKV_AWS_103 | 23 |
| CKV_AWS_129 | 23 |
| CKV_AWS_161 | 23 |
| CKV_AWS_293 | 23 |
| AWS-0176 | 22 |
| AWS-0177 | 22 |
| CKV_AWS_8 | 22 |
| CKV_AWS_145 | 21 |
| CKV_AWS_91 | 20 |
| AWS-0131 | 19 |
| CKV_AWS_18 | 19 |
| CKV_AWS_118 | 19 |
| CKV_AWS_353 | 19 |
| AWS-0178 | 17 |

Final failure origins: {'generated': 56, 'unknown': 7}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | ConfigMap reference must resolve in its namespace | 1 |
| after_security / accepted / improved | Invalid resource type | 1 |
| after_security / accepted / improved | Reference to undeclared resource | 1 |
| after_security / accepted / improved | Unsupported argument | 1 |
| after_security / accepted / improved | helm optional lint failed | 1 |
| after_security / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 1 |
| after_security / rejected / invalid_patch | Invalid single-argument block definition | 1 |
| after_security / rejected / invalid_patch | Reference to undeclared resource | 2 |
| after_security / rejected / invalid_patch | Unsupported argument | 5 |
| after_security / rejected / invalid_patch | Unsupported attribute | 1 |
| after_security / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 2 |
| after_security / rejected / no_improvement | Reference to undeclared resource | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 8 |
| after_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| after_security / rejected / no_improvement | helm optional lint failed | 3 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 1 |
| before_security / accepted / improved | Unsupported argument | 2 |
| before_security / accepted / improved | Unsupported attribute | 1 |
| before_security / accepted / improved | Unsupported block type | 1 |
| before_security / accepted / improved | helm optional lint failed | 1 |
| before_security / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 2 |
| before_security / rejected / invalid_patch | Invalid resource type | 2 |
| before_security / rejected / invalid_patch | Invalid single-argument block definition | 1 |
| before_security / rejected / invalid_patch | Missing required argument | 1 |
| before_security / rejected / invalid_patch | Reference to undeclared resource | 2 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 11 |
| before_security / rejected / invalid_patch | Unsupported attribute | 1 |
| before_security / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 2 |
| before_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| before_security / rejected / new_blocking_findings | Unsupported argument | 1 |
| before_security / rejected / new_blocking_findings | helm optional lint failed | 1 |
| before_security / rejected / no_improvement | Reference to undeclared resource | 2 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 5 |
| before_security / rejected / no_improvement | Unsupported argument | 14 |
| before_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| before_security / rejected / no_improvement | helm optional lint failed | 5 |
| generation / accepted / improved | Reference to undeclared resource | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 5 |
| generation / accepted / improved | Unsupported argument | 2 |
| generation / accepted / improved | Unsupported attribute | 1 |
| generation / accepted / improved | Unsupported block type | 5 |
| generation / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 2 |
| generation / rejected / invalid_patch | Document could not be parsed | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 8 |
| generation / rejected / invalid_patch | Invalid resource type | 1 |
| generation / rejected / invalid_patch | Invalid single-argument block definition | 1 |
| generation / rejected / invalid_patch | Reference to undeclared resource | 3 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 13 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 8 |
| generation / rejected / new_blocking_findings | Missing required argument | 1 |
| generation / rejected / no_improvement | Generation syntax check failed | 1 |
| generation / rejected / no_improvement | Invalid resource type | 1 |
| generation / rejected / no_improvement | Reference to undeclared resource | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 5 |
| generation / rejected / no_improvement | Unsupported argument | 10 |
| generation / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| generation / stopped / round_limit | unknown | 4 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 194 | 0.037618906500938465 | 0.10966694899980212 | 0.6657897969998885 |
| final_security_scan | 40 | 4.461502938999729 | 7.8274434249997284 | 14.330641795000702 |
| final_validation | 40 | 0.10006491300100606 | 0.564634489999662 | 9.119828795001013 |
| generation_gate | 40 | 25.370663541499198 | 61.52644023100038 | 82.31395736599916 |
| initial_validation | 40 | 0.1134167330001219 | 0.37911554200036335 | 9.249846120999791 |
| post_security_validation | 40 | 0.12344601950007927 | 5.589288845998453 | 12.54974291200051 |
| security_iteration_verification | 154 | 3.9419845355005236 | 15.027524714001629 | 37.2485766389982 |
| validation_repair_round | 87 | 14.769448056000329 | 31.323414275000687 | 75.50719103099982 |

Iteration outcomes: {'attempted_fix_iterations': 154, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 48}.
Initialization: {'init_runs': 77, 'init_reused': 260, 'reinitializations': 19}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 40, 'packages_unknown': 0, 'init_runs': 97, 'init_reused': 391, 'reinitializations': 30, 'init_seconds': 547.3873252990052, 'validate_seconds': 947.6695932400071}
Gate outcomes: {'invalid': 34, 'valid': 6}
Init categories: {'validation_cached': 33, 'unknown': 1, 'syntax': 1, 'initialized': 4, 'reused': 1}
Schema context sizes (characters): {'generator': {'count': 40, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 92, 'median': 15960.0, 'p90': 15999, 'max': 23909}, 'security': {'count': 187, 'median': 15957, 'p90': 15999, 'max': 16000}}
Security context coverage: {'terraform': {'total': 155, 'positive': 155, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 154, 'no_schema_entries': 1}}, 'other': {'total': 32, 'positive': 0, 'zero': 32, 'missing': 0, 'reasons': {'not_terraform': 32}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 7}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 8}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 61}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Cycle', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Reference to undeclared resource', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 8}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 13}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid index', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid resource type', 'count': 7}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared input variable', 'count': 7}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared resource', 'count': 8}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 27}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 30}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 10}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 194 | 0.037618906500938465 | 0.10966694899980212 | 0.6657897969998885 |
| final_security_scan | 40 | 4.461502938999729 | 7.8274434249997284 | 14.330641795000702 |
| final_validation | 40 | 0.10006491300100606 | 0.564634489999662 | 9.119828795001013 |
| generation_gate | 40 | 25.370663541499198 | 61.52644023100038 | 82.31395736599916 |
| initial_validation | 40 | 0.1134167330001219 | 0.37911554200036335 | 9.249846120999791 |
| post_security_validation | 40 | 0.12344601950007927 | 5.589288845998453 | 12.54974291200051 |
| security_iteration_verification | 154 | 3.9419845355005236 | 15.027524714001629 | 37.2485766389982 |
| validation_repair_round | 87 | 14.769448056000329 | 31.323414275000687 | 75.50719103099982 |

Iteration outcomes: {'attempted_fix_iterations': 154, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 48}.
Initialization: {'init_runs': 77, 'init_reused': 260, 'reinitializations': 19}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 94.47920793199955, "p90": 154.7232911810006, "max": 161.34975938699972}; failed/incomplete: 0.

pr01 threshold: PASS.

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
| 1 | 3 | {"none": 3} | security#1:4847, cost#1:3447, performance#1:3942 | {} | {} |
| 2 | 4 | {"none": 4} | security#1:3668, cost#1:2600, cost#2:3157, performance#1:3534 | {} | {} |
| 3 | 3 | {"none": 3} | security#1:1152, cost#1:1158, performance#1:959 | {} | {} |
| 4 | 3 | {"none": 3} | performance#1:3172, security#1:2977, cost#1:2682 | {} | {} |
| 5 | 4 | {"none": 4} | cost#1:3328, security#1:3100, security#2:4696, performance#1:4753 | {} | {} |
| 6 | 3 | {"none": 3} | performance#1:1064, security#1:1019, cost#1:1462 | {} | {} |
| 7 | 6 | {"none": 6} | cost#1:3729, cost#2:2573, security#1:2684, security#2:3365, performance#1:3464, performance#2:4270 | {"cost": "incomplete_package"} | {} |
| 8 | 5 | {"none": 5} | security#1:2556, security#2:2059, performance#1:3564, cost#1:2496, cost#2:3400 | {"security": "incomplete_package"} | {} |
| 9 | 3 | {"none": 3} | performance#1:1103, security#1:1134, cost#1:1154 | {} | {} |
| 10 | 3 | {"none": 3} | performance#1:3591, cost#1:3583, security#1:4218 | {} | {} |
| 11 | 3 | {"none": 3} | cost#1:3984, security#1:3425, performance#1:3251 | {} | {} |
| 12 | 4 | {"none": 4} | cost#1:3348, performance#1:3478, security#1:3151, security#2:4571 | {} | {} |
| 13 | 3 | {"none": 3} | cost#1:2847, performance#1:3701, security#1:3127 | {} | {} |
| 14 | 3 | {"none": 3} | cost#1:3093, security#1:3776, performance#1:4561 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.559552; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.3678592, "average_cost_usd": 0.12261973333333333, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["4032c564-2c6b-4eef-b575-370a3f8dc02d", "8265dad1-b41d-4c79-b98d-985edd643785", "d69b92d6-99eb-4461-bba5-6b27e757a584"], "before_remaining_usd": 7.79526714, "after_remaining_usd": 7.427407939999998}

First-run affordability advisory: {"measured_first_run_cost_usd": 0.07286755, "remaining_credit_usd": 8.91409234, "planned_runs_remaining": 13, "run_cap_remaining": null, "projected_further_runs": 13, "assumption": "Projection at first measured cost; fresh guard checks decide."}
