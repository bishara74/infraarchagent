# Phase 9 benchmark

Status: **PASS**

Mode: real

Production-ready rate among generated packages: **0/28 (0.00%)**.
Missing variants: 2; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 28 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 26 |
| validation_failed | 22 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 16 |
| helm.lint: helm optional lint failed | 8 |
| terraform.validate: Reference to undeclared resource | 8 |
| terraform.validate: Terraform configuration diagnostic | 3 |
| terraform.validate: Invalid resource type | 3 |
| ansible-lint.lint: ansible-lint optional lint failed | 2 |
| terraform.validate: Missing required argument | 2 |
| document.parse: Document could not be parsed | 1 |
| terraform.validate: Invalid single-argument block definition | 1 |
| k8s.configmap_ref: ConfigMap reference must resolve in its namespace | 1 |
| terraform.validate: Unsupported attribute | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0038 | 35 |
| AWS-0104 | 33 |
| CKV_AWS_130 | 26 |
| AWS-0164 | 25 |
| AWS-0132 | 21 |
| AWS-0028 | 19 |
| CKV_AWS_145 | 19 |
| CKV_AWS_18 | 18 |
| CKV_AWS_129 | 15 |
| CKV_AWS_161 | 15 |
| CKV_AWS_293 | 15 |
| AWS-0176 | 14 |
| AWS-0177 | 14 |
| CKV_AWS_103 | 14 |
| AWS-0090 | 13 |
| CKV_AWS_21 | 13 |
| CKV_AWS_8 | 12 |
| CKV_AWS_91 | 12 |
| CKV_AWS_118 | 12 |
| CKV_AWS_353 | 12 |

Final failure origins: {'generated': 39, 'unknown': 7}

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
| after_security / rejected / invalid_patch | Unsupported argument | 3 |
| after_security / rejected / invalid_patch | Unsupported attribute | 1 |
| after_security / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 2 |
| after_security / rejected / no_improvement | Reference to undeclared resource | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 5 |
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
| before_security / rejected / invalid_patch | Unsupported argument | 7 |
| before_security / rejected / invalid_patch | Unsupported attribute | 1 |
| before_security / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 2 |
| before_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| before_security / rejected / new_blocking_findings | Unsupported argument | 1 |
| before_security / rejected / new_blocking_findings | helm optional lint failed | 1 |
| before_security / rejected / no_improvement | Reference to undeclared resource | 2 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 2 |
| before_security / rejected / no_improvement | Unsupported argument | 8 |
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
| generation / rejected / invalid_patch | Unsupported argument | 8 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 8 |
| generation / rejected / new_blocking_findings | Missing required argument | 1 |
| generation / rejected / no_improvement | Invalid resource type | 1 |
| generation / rejected / no_improvement | Reference to undeclared resource | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 2 |
| generation / rejected / no_improvement | Unsupported argument | 5 |
| generation / stopped / round_limit | unknown | 4 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 138 | 0.03117677500085847 | 0.06954338200011989 | 0.45552168500034895 |
| final_security_scan | 28 | 4.224598085999787 | 5.704858311999487 | 7.307076950999544 |
| final_validation | 28 | 0.07958658750067116 | 0.564634489999662 | 9.119828795001013 |
| generation_gate | 28 | 23.302399310499823 | 31.976216212999134 | 33.26110379500096 |
| initial_validation | 28 | 0.05614981750022707 | 0.5100211019998824 | 5.083646015998966 |
| post_security_validation | 28 | 0.06618570599948725 | 6.860377191000225 | 12.54974291200051 |
| security_iteration_verification | 110 | 2.6695260765009152 | 11.156888944000457 | 19.535220629000833 |
| validation_repair_round | 60 | 14.150522876499963 | 22.956934106001427 | 31.323414275000687 |

Iteration outcomes: {'attempted_fix_iterations': 110, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 33}.
Initialization: {'init_runs': 53, 'init_reused': 182, 'reinitializations': 7}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 28, 'packages_unknown': 0, 'init_runs': 69, 'init_reused': 271, 'reinitializations': 14, 'init_seconds': 236.08028226500574, 'validate_seconds': 447.33313634500155}
Gate outcomes: {'invalid': 23, 'valid': 5}
Init categories: {'validation_cached': 22, 'unknown': 1, 'syntax': 1, 'initialized': 3, 'reused': 1}
Schema context sizes (characters): {'generator': {'count': 28, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 65, 'median': 15960, 'p90': 15999, 'max': 23909}, 'security': {'count': 138, 'median': 15938.5, 'p90': 15998, 'max': 16000}}
Security context coverage: {'terraform': {'total': 111, 'positive': 111, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 110, 'no_schema_entries': 1}}, 'other': {'total': 27, 'positive': 0, 'zero': 27, 'missing': 0, 'reasons': {'not_terraform': 27}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 4}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 48}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Reference to undeclared resource', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 9}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid resource type', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared input variable', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared resource', 'count': 7}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 17}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 21}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 8}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 138 | 0.03117677500085847 | 0.06954338200011989 | 0.45552168500034895 |
| final_security_scan | 28 | 4.224598085999787 | 5.704858311999487 | 7.307076950999544 |
| final_validation | 28 | 0.07958658750067116 | 0.564634489999662 | 9.119828795001013 |
| generation_gate | 28 | 23.302399310499823 | 31.976216212999134 | 33.26110379500096 |
| initial_validation | 28 | 0.05614981750022707 | 0.5100211019998824 | 5.083646015998966 |
| post_security_validation | 28 | 0.06618570599948725 | 6.860377191000225 | 12.54974291200051 |
| security_iteration_verification | 110 | 2.6695260765009152 | 11.156888944000457 | 19.535220629000833 |
| validation_repair_round | 60 | 14.150522876499963 | 22.956934106001427 | 31.323414275000687 |

Iteration outcomes: {'attempted_fix_iterations': 110, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 33}.
Initialization: {'init_runs': 53, 'init_reused': 182, 'reinitializations': 7}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 94.47920793199955, "p90": 154.7232911810006, "max": 161.34975938699972}; failed/incomplete: 0.

pr01 threshold: PASS.

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

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.062245; unknown costs stay unknown.
