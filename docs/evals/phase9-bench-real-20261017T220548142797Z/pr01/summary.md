# Phase 9 benchmark

Status: **PASS**

Mode: real

Production-ready rate among generated packages: **3/29 (10.34%)**.
Missing variants: 1; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 25 |
| production_ready | 3 |
| scan_error | 1 |

| Review reason | Count |
|---|---:|
| validation_failed | 23 |
| unresolved_security_findings | 22 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 17 |
| terraform.validate: Terraform configuration diagnostic | 14 |
| terraform.validate: Missing required argument | 7 |
| document.parse: Document could not be parsed | 5 |
| terraform.validate: Invalid single-argument block definition | 3 |
| terraform.validate: Invalid multi-line string | 3 |
| terraform.validate: Reference to undeclared resource | 2 |
| helm.lint: helm optional lint failed | 2 |
| k8s.configmap_ref: ConfigMap reference must resolve in its namespace | 2 |
| terraform.validate: Unsupported block type | 2 |
| terraform.var_ref: var.eks_name is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 19 |
| KSV-0118 | 18 |
| CKV_AWS_130 | 14 |
| CKV_AWS_91 | 13 |
| AWS-0164 | 12 |
| CKV_AWS_145 | 12 |
| AWS-0053 | 11 |
| CKV_AWS_378 | 11 |
| CKV_AWS_18 | 11 |
| CKV_AWS_21 | 11 |
| AWS-0132 | 10 |
| AWS-0090 | 9 |
| CKV_K8S_10 | 9 |
| CKV_K8S_11 | 9 |
| CKV_K8S_12 | 9 |
| CKV_K8S_13 | 9 |
| CKV_K8S_20 | 9 |
| CKV_K8S_23 | 9 |
| CKV_K8S_40 | 9 |
| KSV-0001 | 9 |

Final failure origins: {'generated': 42, 'unknown': 16}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 2 |
| after_security / rejected / invalid_patch | Document could not be parsed | 3 |
| after_security / rejected / invalid_patch | Invalid single-argument block definition | 2 |
| after_security / rejected / invalid_patch | Missing required argument | 4 |
| after_security / rejected / invalid_patch | Reference to undeclared resource | 2 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 8 |
| after_security / rejected / invalid_patch | Unsupported argument | 8 |
| after_security / rejected / invalid_patch | Unsupported block type | 2 |
| after_security / rejected / invalid_patch | helm optional lint failed | 2 |
| after_security / rejected / invalid_patch | var.eks_name is not declared | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| before_security / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 2 |
| before_security / rejected / invalid_patch | Document could not be parsed | 5 |
| before_security / rejected / invalid_patch | Invalid multi-line string | 1 |
| before_security / rejected / invalid_patch | Invalid single-argument block definition | 3 |
| before_security / rejected / invalid_patch | Missing required argument | 5 |
| before_security / rejected / invalid_patch | Reference to undeclared resource | 2 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 9 |
| before_security / rejected / invalid_patch | Unsupported argument | 8 |
| before_security / rejected / invalid_patch | Unsupported block type | 2 |
| before_security / rejected / invalid_patch | helm optional lint failed | 2 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 4 |
| before_security / rejected / no_improvement | Unsupported argument | 1 |
| before_security / rejected / verification_unavailable | Missing required argument | 1 |
| before_security / rejected / verification_unavailable | Unsupported argument | 1 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 2 |
| generation / accepted / improved | Unsupported argument | 2 |
| generation / accepted / improved | Unsupported block type | 1 |
| generation / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 2 |
| generation / rejected / invalid_patch | Document could not be parsed | 4 |
| generation / rejected / invalid_patch | Generation syntax check failed | 2 |
| generation / rejected / invalid_patch | Invalid single-argument block definition | 3 |
| generation / rejected / invalid_patch | Missing required argument | 3 |
| generation / rejected / invalid_patch | Reference to undeclared resource | 2 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 8 |
| generation / rejected / invalid_patch | Unsupported argument | 6 |
| generation / rejected / invalid_patch | Unsupported block type | 2 |
| generation / rejected / invalid_patch | helm optional lint failed | 2 |
| generation / rejected / no_improvement | Document could not be parsed | 1 |
| generation / rejected / no_improvement | Invalid multi-line string | 1 |
| generation / rejected / no_improvement | Missing required argument | 2 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported argument | 2 |
| generation / rejected / verification_unavailable | Missing required argument | 1 |
| generation / rejected / verification_unavailable | Unsupported argument | 1 |
| generation / stopped / round_limit | unknown | 3 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 127 | 0.04057444999489235 | 0.09647727599804057 | 0.47447153399843955 |
| final_security_scan | 28 | 4.11539803749838 | 5.313481798999419 | 5.656024903997604 |
| final_validation | 28 | 0.05514536800183123 | 0.3832898040054715 | 0.39880052900116425 |
| generation_gate | 29 | 18.675616829998035 | 24.744474796003487 | 26.988204781002423 |
| initial_validation | 29 | 0.05841853399761021 | 0.4617155450032442 | 0.7235247680000612 |
| post_security_validation | 28 | 0.06992908800020814 | 0.4051176009961637 | 0.9659065080049913 |
| security_iteration_verification | 98 | 8.77676220700232 | 25.954133469997032 | 39.315632216996164 |
| validation_repair_round | 68 | 7.940661270000419 | 14.626694379003311 | 23.15111312999943 |

Iteration outcomes: {'attempted_fix_iterations': 98, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 3}.
Initialization: {'init_runs': 63, 'init_reused': 243, 'reinitializations': 2}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 29, 'packages_unknown': 0, 'init_runs': 77, 'init_reused': 321, 'reinitializations': 2, 'init_seconds': 167.23811776100774, 'validate_seconds': 415.56292813798063}
Gate outcomes: {'invalid': 24, 'valid': 5}
Init categories: {'validation_cached': 19, 'syntax': 4, 'unknown': 1, 'initialized': 5}
Schema context sizes (characters): {'generator': {'count': 29, 'median': 4012, 'p90': 5313, 'max': 5313}, 'repair': {'count': 71, 'median': 15960, 'p90': 15990, 'max': 24536}, 'security': {'count': 118, 'median': 10231.0, 'p90': 13544, 'max': 15974}}
Security context coverage: {'terraform': {'total': 98, 'positive': 90, 'zero': 8, 'missing': 0, 'reasons': {'schema_available': 90, 'unparseable_document': 8}}, 'other': {'total': 20, 'positive': 0, 'zero': 20, 'missing': 0, 'reasons': {'not_terraform': 20}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 5}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 9}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 10}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 5}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Invalid multi-line string', 'count': 3}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 10}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Missing required argument', 'count': 10}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 6}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 33}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 19}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 10}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 5}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Reference to undeclared input variable', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 2 |

Phase 9f measured/unknown packages: (29, 0)
Catalogue retained by rule: {'CKV_AWS_8': 3, 'CKV_AWS_103': 6}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 62}, {'template': 'access_logs', 'status': 'skipped', 'count': 4}, {'template': 'flow_logs', 'status': 'retained', 'count': 1}, {'template': 'kms', 'status': 'rejected', 'count': 21}, {'template': 'kms', 'status': 'retained', 'count': 5}, {'template': 'kms', 'status': 'skipped', 'count': 39}]
Template introduced rules: {'AWS-0090': 62, 'AWS-0132': 83}
Partial groups: {'discarded': 14, 'kept': 27, 'unevaluated': 8}
Existing-file proposal recovery: {'normalized': 1, 'retained': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 29, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 118, 'median': 3.0, 'p90': 12, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 127 | 0.04057444999489235 | 0.09647727599804057 | 0.47447153399843955 |
| final_security_scan | 28 | 4.11539803749838 | 5.313481798999419 | 5.656024903997604 |
| final_validation | 28 | 0.05514536800183123 | 0.3832898040054715 | 0.39880052900116425 |
| generation_gate | 29 | 18.675616829998035 | 24.744474796003487 | 26.988204781002423 |
| initial_validation | 29 | 0.05841853399761021 | 0.4617155450032442 | 0.7235247680000612 |
| post_security_validation | 28 | 0.06992908800020814 | 0.4051176009961637 | 0.9659065080049913 |
| security_iteration_verification | 98 | 8.77676220700232 | 25.954133469997032 | 39.315632216996164 |
| validation_repair_round | 68 | 7.940661270000419 | 14.626694379003311 | 23.15111312999943 |

Iteration outcomes: {'attempted_fix_iterations': 98, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 3}.
Initialization: {'init_runs': 63, 'init_reused': 243, 'reinitializations': 2}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 133.92153543949826, "p90": 153.54062278699712, "max": 157.25570357299875}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:4301, performance#1:4741, cost#1:3581 | {} | {} |
| 2 | 3 | {"none": 3} | performance#1:3946, security#1:4029, cost#1:3222 | {} | {} |
| 3 | 3 | {"none": 3} | security#1:604, cost#1:1360, performance#1:1625 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:3916, security#1:4557, performance#1:3487 | {} | {} |
| 5 | 4 | {"none": 4} | security#1:2856, security#2:3016, cost#1:3750, performance#1:4339 | {"security": "incomplete_package"} | {} |
| 6 | 3 | {"none": 3} | cost#1:1152, security#1:1390, performance#1:1385 | {} | {} |
| 7 | 3 | {"none": 3} | security#1:4647, cost#1:4217, performance#1:5230 | {} | {} |
| 8 | 4 | {"none": 4} | cost#1:4263, security#1:5351, performance#1:3868, performance#2:5034 | {} | {} |
| 9 | 3 | {"none": 3} | performance#1:1634, security#1:1870, cost#1:1840 | {} | {} |
| 10 | 3 | {"none": 3} | cost#1:3945, performance#1:3613, security#1:4080 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.150260; unknown costs stay unknown.
