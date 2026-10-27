# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **11/57 (19.30%)**.
Legacy labels mapped: 0. Missing variants: 3; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 11/57; contextual-v1: 11/57; contextual-v2: 13/57. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 46 |
| checks_passed | 11 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 38 |
| validation_failed | 21 |
| plan_conformance_conflict | 19 |
| validation_error | 5 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 16 |
| terraform.validate: Missing required argument | 4 |
| terraform.validate: Unsupported block type | 3 |
| terraform.validate: Unsupported argument | 3 |
| helm.lint: helm optional lint failed (undefined_named_template) | 3 |
| grafana.panels: Dashboard requires panels | 1 |
| helm.lint: helm optional lint failed | 1 |
| terraform.validate: Unsupported attribute | 1 |
| terraform.var_ref: var.region is not declared | 1 |
| terraform.var_ref: var.vpc_cidr is not declared | 1 |
| terraform.var_ref: var.app_cpu is not declared | 1 |
| terraform.var_ref: var.app_memory is not declared | 1 |
| terraform.var_ref: var.app_image is not declared | 1 |
| terraform.var_ref: var.acm_certificate_arn is not declared | 1 |
| terraform.var_ref: var.db_instance_class is not declared | 1 |
| terraform.var_ref: var.db_name is not declared | 1 |
| terraform.var_ref: var.db_username is not declared | 1 |
| terraform.var_ref: var.db_password is not declared | 1 |
| terraform.var_ref: var.redis_node_type is not declared | 1 |
| terraform.var_ref: var.kms_key_id is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0053 | 22 |
| CKV_AWS_91 | 19 |
| CKV_AWS_260 | 13 |
| AWS-0164 | 13 |
| CKV_AWS_130 | 13 |
| AWS-0039 | 8 |
| CKV_AWS_58 | 8 |
| KSV-0125 | 8 |
| AWS-0040 | 7 |
| AWS-0041 | 7 |
| CKV_AWS_38 | 7 |
| CKV_AWS_39 | 7 |
| CKV_AWS_144 | 5 |
| TERRAFORM_FILE_INPUT | 5 |
| CKV_AWS_157 | 5 |
| AWS-0090 | 4 |
| CKV2_AWS_12 | 4 |
| CKV_AWS_21 | 4 |
| CKV_K8S_10 | 3 |
| CKV_K8S_11 | 3 |

Final failure origins: {'unknown': 3, 'generated': 44}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Missing required argument | 1 |
| after_security / accepted / improved | Unsupported argument | 1 |
| after_security / rejected / invalid_patch | Missing required argument | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| after_security / rejected / invalid_patch | Unsupported attribute | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 1 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| after_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 2 |
| after_security / rejected / no_improvement | Cycle | 1 |
| after_security / rejected / no_improvement | Duplicate required providers configuration | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 9 |
| after_security / rejected / no_improvement | Unsupported argument | 2 |
| after_security / rejected / no_improvement | Unsupported block type | 3 |
| after_security / rejected / plan_conformance_regression | Terraform configuration diagnostic | 3 |
| after_security / rejected / plan_conformance_regression | Unsupported argument | 1 |
| after_security / rejected / plan_conformance_regression | var.account_id is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.acm_certificate_arn is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.app_cpu is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.app_image is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.app_memory is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.db_instance_class is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.db_name is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.db_password is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.db_username is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.kms_key_id is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.redis_node_type is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.region is not declared | 1 |
| after_security / rejected / plan_conformance_regression | var.vpc_cidr is not declared | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 2 |
| before_security / accepted / improved | Unsupported argument | 1 |
| before_security / accepted / improved | Unsupported block type | 2 |
| before_security / rejected / invalid_patch | Dashboard requires panels | 1 |
| before_security / rejected / invalid_patch | Unsupported attribute | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| before_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 2 |
| before_security / rejected / no_improvement | Missing required argument | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 8 |
| before_security / rejected / no_improvement | Unsupported argument | 4 |
| before_security / rejected / plan_conformance_regression | Cycle | 1 |
| before_security / rejected / plan_conformance_regression | Missing required argument | 1 |
| before_security / rejected / plan_conformance_regression | Terraform configuration diagnostic | 3 |
| before_security / rejected / plan_conformance_regression | Unsupported argument | 1 |
| before_security / rejected / plan_conformance_regression | Unsupported block type | 2 |
| before_security / rejected / plan_conformance_regression | var.account_id is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.acm_certificate_arn is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.app_cpu is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.app_image is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.app_memory is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.db_instance_class is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.db_name is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.db_password is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.db_username is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.kms_key_id is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.redis_node_type is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.region is not declared | 1 |
| before_security / rejected / plan_conformance_regression | var.vpc_cidr is not declared | 1 |
| before_security / stopped / round_limit | unknown | 1 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Reference to undeclared resource | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 3 |
| generation / accepted / improved | Unsupported argument | 4 |
| generation / rejected / invalid_patch | Generation syntax check failed | 1 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 1 |
| generation / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| generation / rejected / new_blocking_findings | Generation syntax check failed | 3 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| generation / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 3 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 6 |
| generation / rejected / no_improvement | Unsupported argument | 2 |
| generation / rejected / no_improvement | Unsupported block type | 1 |
| generation / rejected / plan_conformance_regression | Cycle | 1 |
| generation / rejected / plan_conformance_regression | Missing required argument | 2 |
| generation / rejected / plan_conformance_regression | Terraform configuration diagnostic | 5 |
| generation / rejected / plan_conformance_regression | Unsupported argument | 3 |
| generation / rejected / plan_conformance_regression | Unsupported block type | 2 |
| generation / rejected / plan_conformance_regression | var.account_id is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.acm_certificate_arn is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.app_cpu is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.app_image is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.app_memory is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.db_instance_class is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.db_name is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.db_password is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.db_username is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.kms_key_id is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.redis_node_type is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.region is not declared | 1 |
| generation / rejected / plan_conformance_regression | var.vpc_cidr is not declared | 1 |
| generation / stopped / round_limit | unknown | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 239 | 0.05082423400017433 | 0.3219855369970901 | 1.1398911389987916 |
| final_security_scan | 57 | 5.148936584009789 | 6.888195531006204 | 9.301772567006992 |
| final_validation | 57 | 0.002972792004584335 | 0.35600186100055 | 0.5284220129979076 |
| generation_gate | 57 | 16.03914259999874 | 57.46908572099346 | 81.17320758200367 |
| initial_validation | 57 | 0.0030438179965130985 | 0.3863539430021774 | 0.4550604310061317 |
| post_security_validation | 57 | 0.003032249995158054 | 0.42403887399996165 | 4.166447647003224 |
| security_iteration_verification | 184 | 19.94871862149739 | 43.495641728979535 | 51.22917451498506 |
| validation_repair_round | 73 | 4.6563496900053 | 21.29287378200388 | 43.25782066700049 |

Iteration outcomes: {'attempted_fix_iterations': 184, 'deadline_only_rollbacks': 4, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 10, 'validity_regression_rollbacks': 10}.
Initialization: {'init_runs': 95, 'init_reused': 611, 'reinitializations': 1}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 57, 'packages_unknown': 0, 'init_runs': 118, 'init_reused': 813, 'reinitializations': 4, 'init_seconds': 362.7457127468806, 'validate_seconds': 1925.5770275840332}
Gate outcomes: {'valid': 30, 'invalid': 22, 'error': 5}
Init categories: {'initialized': 14, 'validation_cached': 35, 'unknown': 3}
Schema context sizes (characters): {'generator': {'count': 57, 'median': 4488, 'p90': 4493, 'max': 4496}, 'repair': {'count': 75, 'median': 15948, 'p90': 15993, 'max': 15999}, 'security': {'count': 210, 'median': 8973.5, 'p90': 12899, 'max': 15997}, 'generator_schema_only': {'count': 57, 'median': 4488, 'p90': 4493, 'max': 4496}}
Schema guidance overflow: {'measured_packages': 57, 'overflow_packages': 35, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_s3_bucket': 3, 'aws_dynamodb_table': 6, 'aws_ecs_service': 17, 'aws_ecs_task_definition': 9, 'aws_instance': 6, 'aws_cloudfront_distribution': 3}}}
Security context coverage: {'terraform': {'total': 182, 'positive': 181, 'zero': 1, 'missing': 0, 'reasons': {'schema_available': 181, 'not_attempted': 1}}, 'other': {'total': 28, 'positive': 0, 'zero': 28, 'missing': 0, 'reasons': {'not_terraform': 28}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Duplicate required providers configuration', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 14}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 4}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 55}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 8}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 9}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression', 'error_class': 'Missing required argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 18}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression', 'error_class': 'Unsupported argument', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression', 'error_class': 'Unsupported attribute', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression', 'error_class': 'unknown', 'count': 26}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression,iteration_deadline', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'plan_conformance_regression,iteration_deadline', 'error_class': 'unknown', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'security_control_removed', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Cycle', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared resource', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_verification_unavailable', 'error_class': 'unknown', 'count': 4}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 4 |
| 2-3 | 9 |
| 4+ | 7 |

Phase 9f measured/unknown packages: (57, 0)
Catalogue retained by rule: {'AWS-0164': 14, 'CKV_AWS_130': 14, 'CKV2_AWS_12': 6, 'AWS-0176': 1, 'CKV_AWS_161': 1, 'CKV_AWS_103': 9, 'CKV_K8S_23': 22, 'CKV_K8S_40': 22, 'KSV-0012': 22, 'KSV-0118': 22, 'KSV-0104': 22, 'CKV_K8S_10': 11, 'CKV_K8S_11': 11, 'CKV_K8S_12': 11, 'CKV_K8S_13': 11, 'CKV_K8S_20': 11, 'CKV_K8S_22': 11, 'CKV_K8S_31': 11, 'CKV_K8S_37': 11, 'KSV-0001': 11, 'KSV-0003': 11, 'KSV-0004': 11, 'KSV-0014': 11, 'KSV-0106': 11, 'AWS-0077': 4}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 94}, {'template': 'access_logs', 'status': 'retained', 'count': 6}, {'template': 'flow_logs', 'status': 'retained', 'count': 30}, {'template': 'flow_logs', 'status': 'skipped', 'count': 5}, {'template': 'kms', 'status': 'retained', 'count': 23}, {'template': 'kms', 'status': 'skipped', 'count': 8}]
Template introduced rules: {'CKV_AWS_145': 78, 'CKV_AWS_144': 42, 'CKV_AWS_18': 68, 'AWS-0132': 68}
Partial groups: {'discarded': 121, 'unevaluated': 12, 'kept': 73}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 53, 'regeneration': 1, 'normalization': 1, 'syntax_round_1': 2}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 57, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 209, 'median': 3, 'p90': 7, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 239 | 0.05082423400017433 | 0.3219855369970901 | 1.1398911389987916 |
| final_security_scan | 57 | 5.148936584009789 | 6.888195531006204 | 9.301772567006992 |
| final_validation | 57 | 0.002972792004584335 | 0.35600186100055 | 0.5284220129979076 |
| generation_gate | 57 | 16.03914259999874 | 57.46908572099346 | 81.17320758200367 |
| initial_validation | 57 | 0.0030438179965130985 | 0.3863539430021774 | 0.4550604310061317 |
| post_security_validation | 57 | 0.003032249995158054 | 0.42403887399996165 | 4.166447647003224 |
| security_iteration_verification | 184 | 19.94871862149739 | 43.495641728979535 | 51.22917451498506 |
| validation_repair_round | 73 | 4.6563496900053 | 21.29287378200388 | 43.25782066700049 |

Iteration outcomes: {'attempted_fix_iterations': 184, 'deadline_only_rollbacks': 4, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 10, 'validity_regression_rollbacks': 10}.
Initialization: {'init_runs': 95, 'init_reused': 611, 'reinitializations': 1}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 20, "median": 134.7421954954989, "p90": 258.9645234759955, "max": 293.2362817770045}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 321, "failures": 0, "missing_measurements": 0, "agents": {"architect": 20, "generator_performance": 20, "generator_cost": 20, "generator_security": 20, "security_iteration": 241}, "durations": {"count": 321, "median": 14.887573, "p90": 51.587582, "max": 85.812708}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | performance#1:700, cost#1:677, security#1:765 | {} | {} |
| 2 | 3 | {"none": 3} | security#1:2177, cost#1:2049, performance#1:1778 | {} | {} |
| 3 | 3 | {"none": 3} | performance#1:1905, security#1:1586, cost#1:2041 | {} | {} |
| 4 | 3 | {"none": 3} | security#1:1548, cost#1:1591, performance#1:1412 | {} | {} |
| 5 | 4 | {"none": 4} | performance#1:1784, security#1:2128, security#2:2164, cost#1:1928 | {} | {} |
| 6 | 3 | {"none": 3} | performance#1:2959, cost#1:3354, security#1:2566 | {} | {} |
| 7 | 3 | {"none": 3} | performance#1:4452, security#1:4446, cost#1:3732 | {} | {} |
| 8 | 8 | {"none": 8} | security#1:2627, security#2:2945, security#3:2060, cost#1:2202, cost#2:2216, cost#3:3360, performance#1:2465, performance#2:3530 | {"security": "incomplete_package", "cost": "incomplete_package"} | {} |
| 9 | 3 | {"none": 3} | cost#1:3538, security#1:3232, performance#1:3165 | {} | {} |
| 10 | 5 | {"none": 5} | cost#1:2165, cost#2:2044, cost#3:2786, security#1:4987, performance#1:3837 | {"cost": "incomplete_package"} | {} |
| 11 | 4 | {"none": 4} | performance#1:3457, security#1:5069, cost#1:2287, cost#2:2614 | {} | {} |
| 12 | 3 | {"none": 3} | performance#1:3424, security#1:4569, cost#1:3137 | {} | {} |
| 13 | 5 | {"none": 5} | cost#1:2270, cost#2:1942, cost#3:2642, security#1:2874, performance#1:2851 | {} | {} |
| 14 | 3 | {"none": 3} | security#1:3488, performance#1:3587, cost#1:3205 | {} | {} |
| 15 | 3 | {"none": 3} | security#1:2003, performance#1:3369, cost#1:2788 | {} | {} |
| 16 | 3 | {"none": 3} | cost#1:1649, performance#1:2708, security#1:1842 | {} | {} |
| 17 | 3 | {"none": 3} | security#1:2233, performance#1:1405, cost#1:2111 | {} | {} |
| 18 | 3 | {"none": 3} | cost#1:1907, performance#1:1058, security#1:2207 | {} | {} |
| 19 | 3 | {"none": 3} | performance#1:1682, cost#1:1386, security#1:1276 | {} | {} |
| 20 | 3 | {"none": 3} | performance#1:1157, security#1:1741, cost#1:1601 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.392022; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.01731535, "remaining_credit_usd": 7.286992576, "planned_runs_remaining": 19, "run_cap_remaining": 19, "projected_further_runs": 19, "assumption": "Projection at first measured cost; fresh guard checks decide."}
