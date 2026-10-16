# Phase 9 benchmark

Status: **PASS**

Mode: real

Production-ready rate among generated packages: **1/28 (3.57%)**.
Missing variants: 2; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 27 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 27 |
| validation_failed | 20 |
| validation_error | 1 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 15 |
| helm.lint: helm optional lint failed | 7 |
| terraform.validate: Terraform configuration diagnostic | 6 |
| terraform.validate: Reference to undeclared input variable | 6 |
| terraform.validate: Invalid multi-line string | 3 |
| terraform.validate: Invalid index | 3 |
| document.parse: Document could not be parsed | 2 |
| terraform.validate: Unsupported block type | 2 |
| terraform.validate: Unsupported attribute | 1 |
| terraform.var_ref: var.nginx_max_capacity is not declared | 1 |
| terraform.var_ref: var.nginx_min_capacity is not declared | 1 |
| terraform.var_ref: var.prometheus_max_capacity is not declared | 1 |
| terraform.var_ref: var.prometheus_min_capacity is not declared | 1 |
| terraform.var_ref: var.grafana_max_capacity is not declared | 1 |
| terraform.var_ref: var.grafana_min_capacity is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 35 |
| AWS-0038 | 35 |
| AWS-0164 | 27 |
| CKV_AWS_130 | 27 |
| CKV_AWS_145 | 20 |
| AWS-0176 | 18 |
| AWS-0177 | 18 |
| CKV_AWS_129 | 18 |
| CKV_AWS_161 | 18 |
| CKV_AWS_293 | 18 |
| AWS-0132 | 18 |
| AWS-0178 | 17 |
| CKV2_AWS_11 | 17 |
| CKV_AWS_21 | 16 |
| AWS-0028 | 15 |
| AWS-0090 | 15 |
| AWS-0053 | 14 |
| CKV_AWS_103 | 14 |
| CKV_AWS_18 | 14 |
| CKV_AWS_118 | 13 |

Final failure origins: {'unknown': 5, 'generated': 34, 'repair': 12}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 1 |
| before_security / accepted / improved | Missing required argument | 1 |
| before_security / accepted / improved | Unsupported argument | 3 |
| before_security / accepted / improved | helm optional lint failed | 2 |
| before_security / rejected / invalid_patch | Document could not be parsed | 1 |
| before_security / rejected / invalid_patch | Reference to undeclared input variable | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| before_security / rejected / invalid_patch | Unsupported argument | 4 |
| before_security / rejected / invalid_patch | Unsupported attribute | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 4 |
| before_security / rejected / invalid_patch | var.grafana_max_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.grafana_min_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.nginx_max_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.nginx_min_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.prometheus_max_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.prometheus_min_capacity is not declared | 1 |
| before_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| before_security / rejected / new_blocking_findings | Invalid multi-line string | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| before_security / rejected / no_improvement | Invalid index | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| before_security / rejected / no_improvement | Unsupported argument | 8 |
| before_security / rejected / no_improvement | Unsupported block type | 2 |
| before_security / stopped / round_limit | unknown | 1 |
| generation / accepted / improved | Document could not be parsed | 1 |
| generation / accepted / improved | Invalid single-argument block definition | 1 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 5 |
| generation / accepted / improved | Unsupported argument | 2 |
| generation / accepted / improved | Unsupported block type | 3 |
| generation / accepted / improved | var.api_desired_count is not declared | 1 |
| generation / accepted / improved | var.api_image is not declared | 1 |
| generation / accepted / improved | var.api_max_capacity is not declared | 1 |
| generation / accepted / improved | var.api_min_capacity is not declared | 1 |
| generation / accepted / improved | var.aws_region is not declared | 1 |
| generation / accepted / improved | var.db_name is not declared | 1 |
| generation / accepted / improved | var.db_password is not declared | 1 |
| generation / accepted / improved | var.db_username is not declared | 1 |
| generation / accepted / improved | var.grafana_desired_count is not declared | 1 |
| generation / accepted / improved | var.grafana_image is not declared | 1 |
| generation / accepted / improved | var.nginx_desired_count is not declared | 1 |
| generation / accepted / improved | var.nginx_image is not declared | 1 |
| generation / accepted / improved | var.project_name is not declared | 1 |
| generation / accepted / improved | var.prometheus_desired_count is not declared | 1 |
| generation / accepted / improved | var.prometheus_image is not declared | 1 |
| generation / accepted / improved | var.vpc_cidr is not declared | 1 |
| generation / rejected / invalid_patch | Document could not be parsed | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 5 |
| generation / rejected / invalid_patch | Invalid index | 1 |
| generation / rejected / invalid_patch | Missing required argument | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| generation / rejected / invalid_patch | Unsupported argument | 5 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 5 |
| generation / rejected / new_blocking_findings | Document could not be parsed | 1 |
| generation / rejected / new_blocking_findings | Invalid multi-line string | 1 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported argument | 7 |
| generation / rejected / no_improvement | Unsupported block type | 2 |
| generation / stopped / round_limit | unknown | 2 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 60 | 0.037351855500219244 | 0.10240312199857726 | 0.5786761919998753 |
| final_security_scan | 28 | 4.527199288000247 | 6.10617639100019 | 8.390769371000715 |
| final_validation | 28 | 0.09016057800045019 | 0.4744300909997037 | 4.08563557800062 |
| generation_gate | 28 | 26.47287490899953 | 34.824743707999914 | 35.98419042900059 |
| initial_validation | 28 | 0.08721934850018442 | 0.5245776930005377 | 7.310586949000026 |
| post_security_validation | 28 | 0.11413370299987946 | 0.49826080999991973 | 5.93382687599933 |
| security_iteration_verification | 32 | 5.100029132499003 | 13.72547048999877 | 18.22897263699997 |
| validation_repair_round | 49 | 17.11937191799916 | 24.44396070000039 | 31.3290522770003 |

Iteration outcomes: {'attempted_fix_iterations': 32, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 9}.
Initialization: {'init_runs': 46, 'init_reused': 75, 'reinitializations': 9}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 28, 'packages_unknown': 0, 'init_runs': 58, 'init_reused': 165, 'reinitializations': 12, 'init_seconds': 277.6324377560031, 'validate_seconds': 281.12332247500126}
Gate outcomes: {'invalid': 21, 'valid': 6, 'error': 1}
Init categories: {'syntax': 1, 'validation_cached': 22, 'missing_required_providers': 1, 'mirror_constraint_unavailable': 1, 'initialized': 2, 'reused': 1}
Schema context sizes (characters): {'generator': {'count': 28, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 52, 'median': 15978.5, 'p90': 15999, 'max': 23405}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security iteration outcomes by class: []

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 60 | 0.037351855500219244 | 0.10240312199857726 | 0.5786761919998753 |
| final_security_scan | 28 | 4.527199288000247 | 6.10617639100019 | 8.390769371000715 |
| final_validation | 28 | 0.09016057800045019 | 0.4744300909997037 | 4.08563557800062 |
| generation_gate | 28 | 26.47287490899953 | 34.824743707999914 | 35.98419042900059 |
| initial_validation | 28 | 0.08721934850018442 | 0.5245776930005377 | 7.310586949000026 |
| post_security_validation | 28 | 0.11413370299987946 | 0.49826080999991973 | 5.93382687599933 |
| security_iteration_verification | 32 | 5.100029132499003 | 13.72547048999877 | 18.22897263699997 |
| validation_repair_round | 49 | 17.11937191799916 | 24.44396070000039 | 31.3290522770003 |

Iteration outcomes: {'attempted_fix_iterations': 32, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 9}.
Initialization: {'init_runs': 46, 'init_reused': 75, 'reinitializations': 9}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 75.51232989599976, "p90": 96.55747091600006, "max": 123.97397773300054}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:2465, cost#1:2499, performance#1:3537 | {} | {} |
| 2 | 4 | {"none": 4} | security#1:2486, security#2:3573, performance#1:4082, cost#1:3013 | {"security": "incomplete_package"} | {} |
| 3 | 3 | {"none": 3} | performance#1:1928, cost#1:1627, security#1:2159 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:3391, performance#1:3233, security#1:4249 | {} | {} |
| 5 | 4 | {"none": 4} | cost#1:3226, security#1:3804, performance#1:2591, performance#2:3473 | {} | {} |
| 6 | 3 | {"none": 3} | cost#1:1031, security#1:1773, performance#1:1095 | {} | {} |
| 7 | 3 | {"none": 3} | cost#1:2632, performance#1:4609, security#1:4088 | {} | {} |
| 8 | 4 | {"none": 4} | cost#1:2060, cost#2:2303, security#1:3418, performance#1:3580 | {"cost": "incomplete_package"} | {} |
| 9 | 3 | {"none": 3} | cost#1:1601, performance#1:1634, security#1:1361 | {} | {} |
| 10 | 3 | {"none": 3} | cost#1:2348, security#1:3279, performance#1:3954 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.
