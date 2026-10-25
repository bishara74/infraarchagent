# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **24/56 (42.86%)**.
Legacy labels mapped: 0. Missing variants: 4; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 24/56; contextual-v1: 24/56; contextual-v2: 24/56. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 32 |
| checks_passed | 24 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 31 |
| validation_failed | 18 |
| validation_error | 2 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 15 |
| terraform.validate: Unsupported argument | 5 |
| helm.lint: helm optional lint failed (undefined_named_template) | 4 |
| terraform.validate: Unsupported block type | 1 |
| terraform.var_ref: var.aws_region is not declared | 1 |
| terraform.var_ref: var.vpc_cidr is not declared | 1 |
| terraform.var_ref: var.public_subnet_cidrs is not declared | 1 |
| terraform.var_ref: var.private_subnet_cidrs is not declared | 1 |
| terraform.var_ref: var.eks_cluster_name is not declared | 1 |
| terraform.var_ref: var.eks_role_arn is not declared | 1 |
| terraform.var_ref: var.node_instance_type is not declared | 1 |
| terraform.var_ref: var.node_iam_instance_profile is not declared | 1 |
| terraform.var_ref: var.node_max_size is not declared | 1 |
| terraform.var_ref: var.node_min_size is not declared | 1 |
| terraform.var_ref: var.rds_identifier is not declared | 1 |
| terraform.var_ref: var.rds_username is not declared | 1 |
| terraform.var_ref: var.rds_password is not declared | 1 |
| terraform.var_ref: var.rds_monitoring_role_arn is not declared | 1 |
| terraform.var_ref: var.acm_certificate_arn is not declared | 1 |
| terraform.var_ref: var.eks_role_name is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0053 | 27 |
| CKV_AWS_130 | 24 |
| AWS-0164 | 21 |
| CKV_AWS_91 | 17 |
| CKV_AWS_21 | 15 |
| AWS-0090 | 14 |
| AWS-0104 | 12 |
| CKV_AWS_144 | 11 |
| CKV_AWS_18 | 10 |
| CKV2_AWS_12 | 9 |
| AWS-0052 | 7 |
| AWS-0039 | 6 |
| CKV_AWS_38 | 6 |
| CKV_AWS_39 | 6 |
| AWS-0031 | 6 |
| CKV_AWS_378 | 6 |
| CKV_AWS_58 | 5 |
| AWS-0040 | 5 |
| AWS-0041 | 5 |
| AWS-0130 | 5 |

Final failure origins: {'generated': 45, 'unknown': 3}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Reference to undeclared resource | 1 |
| after_security / accepted / improved | Terraform configuration diagnostic | 1 |
| after_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| after_security / rejected / new_blocking_findings | Invalid single-argument block definition | 1 |
| after_security / rejected / new_blocking_findings | Missing required argument | 1 |
| after_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| after_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 1 |
| after_security / rejected / new_blocking_findings | var.acm_certificate_arn is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.aws_region is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.eks_cluster_name is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.eks_role_arn is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.eks_role_name is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.node_iam_instance_profile is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.node_iam_role_name is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.node_instance_type is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.node_max_size is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.node_min_size is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.private_subnet_cidrs is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.project_name is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.public_subnet_cidrs is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.rds_identifier is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.rds_monitoring_role_arn is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.rds_password is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.rds_username is not declared | 1 |
| after_security / rejected / new_blocking_findings | var.vpc_cidr is not declared | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 8 |
| after_security / rejected / no_improvement | Unsupported argument | 3 |
| after_security / rejected / no_improvement | Unsupported block type | 1 |
| after_security / stopped / deadline | Dashboard requires panels | 1 |
| after_security / stopped / deadline | Terraform configuration diagnostic | 2 |
| after_security / stopped / deadline | Unsupported argument | 2 |
| after_security / stopped / deadline | Values must be a YAML mapping | 1 |
| after_security / stopped / deadline | helm optional lint failed (undefined_named_template) | 3 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Missing required argument | 2 |
| before_security / accepted / improved | Reference to undeclared resource | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 4 |
| before_security / accepted / improved | Unsupported argument | 4 |
| before_security / rejected / invalid_patch | Dashboard requires panels | 1 |
| before_security / rejected / invalid_patch | Missing required argument | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 2 |
| before_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 2 |
| before_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| before_security / rejected / new_blocking_findings | Invalid single-argument block definition | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| before_security / rejected / new_blocking_findings | var.acm_certificate_arn is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.aws_region is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.eks_cluster_name is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.eks_role_arn is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.eks_role_name is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.node_iam_instance_profile is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.node_iam_role_name is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.node_instance_type is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.node_max_size is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.node_min_size is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.private_subnet_cidrs is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.project_name is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.public_subnet_cidrs is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.rds_identifier is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.rds_monitoring_role_arn is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.rds_password is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.rds_username is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.vpc_cidr is not declared | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 8 |
| before_security / rejected / no_improvement | Unsupported argument | 2 |
| before_security / rejected / no_improvement | Unsupported attribute | 1 |
| before_security / rejected / no_improvement | Unsupported block type | 1 |
| before_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 1 |
| before_security / rejected / verification_unavailable | Terraform configuration diagnostic | 1 |
| before_security / rejected / verification_unavailable | helm optional lint failed (undefined_named_template) | 1 |
| before_security / stopped / deadline | Reference to undeclared resource | 1 |
| before_security / stopped / deadline | Terraform configuration diagnostic | 1 |
| before_security / stopped / deadline | Unsupported argument | 2 |
| before_security / stopped / deadline | Values must be a YAML mapping | 1 |
| generation / accepted / improved | Generation syntax check failed | 1 |
| generation / accepted / improved | Invalid resource type | 1 |
| generation / accepted / improved | Missing required argument | 4 |
| generation / accepted / improved | Terraform configuration diagnostic | 5 |
| generation / accepted / improved | Unsupported argument | 4 |
| generation / accepted / improved | Unsupported block type | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 4 |
| generation / rejected / invalid_patch | Reference to undeclared resource | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 4 |
| generation / rejected / invalid_patch | Unsupported argument | 2 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 1 |
| generation / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| generation / rejected / new_blocking_findings | Generation syntax check failed | 3 |
| generation / rejected / new_blocking_findings | Missing required argument | 1 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| generation / rejected / new_blocking_findings | Unsupported argument | 2 |
| generation / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 3 |
| generation / rejected / no_improvement | Missing required argument | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 7 |
| generation / rejected / no_improvement | Unsupported argument | 3 |
| generation / stopped / round_limit | unknown | 4 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 190 | 0.12347506250080187 | 0.6485669240064453 | 2.2362786610028706 |
| final_security_scan | 56 | 8.087227267991693 | 13.48217041400494 | 22.672448455006815 |
| final_validation | 56 | 0.03427418749924982 | 1.052406571994652 | 5.166486571994028 |
| generation_gate | 56 | 37.20532201749302 | 133.37991307800985 | 140.8463788980007 |
| initial_validation | 56 | 0.04628544850129401 | 0.9927179130027071 | 6.559744504993432 |
| post_security_validation | 56 | 0.024409343997831456 | 1.7477294630079996 | 13.116250345003209 |
| security_iteration_verification | 170 | 34.067309200509044 | 50.57895503702457 | 54.592880663010874 |
| validation_repair_round | 74 | 17.091104243998416 | 54.6173803480051 | 69.62616977999278 |

Iteration outcomes: {'attempted_fix_iterations': 170, 'deadline_only_rollbacks': 54, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 8, 'validity_regression_rollbacks': 19}.
Initialization: {'init_runs': 166, 'init_reused': 597, 'reinitializations': 10}.
Repair deadline stops (measured rounds): {'after_security': 4, 'before_security': 3}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 56, 'packages_unknown': 0, 'init_runs': 229, 'init_reused': 823, 'reinitializations': 13, 'init_seconds': 971.0951784029603, 'validate_seconds': 2861.9803959579876}
Gate outcomes: {'valid': 28, 'invalid': 24, 'deadline': 2, 'error': 2}
Init categories: {'validation_cached': 30, 'initialized': 13, 'invalid_required_providers': 1, 'unknown': 5, 'reused': 3, 'missing_required_providers': 1, 'syntax': 1, 'mirror_constraint_unavailable': 2}
Schema context sizes (characters): {'generator': {'count': 56, 'median': 4473.0, 'p90': 4485, 'max': 4488}, 'repair': {'count': 79, 'median': 15959, 'p90': 15999, 'max': 21702}, 'security': {'count': 197, 'median': 7285, 'p90': 14199, 'max': 15999}, 'generator_schema_only': {'count': 56, 'median': 4473.0, 'p90': 4485, 'max': 4488}}
Schema guidance overflow: {'measured_packages': 56, 'overflow_packages': 32, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_cloudfront_distribution': 6, 'aws_ecs_service': 15, 'aws_ecs_task_definition': 15, 'aws_db_instance': 13, 'aws_elasticache_cluster': 5, 'aws_elasticache_replication_group': 5, 'aws_lb_listener': 11, 'aws_autoscaling_group': 5, 'aws_launch_template': 5, 'aws_instance': 8, 'aws_lb': 6}}}
Security context coverage: {'terraform': {'total': 138, 'positive': 137, 'zero': 1, 'missing': 0, 'reasons': {'schema_available': 133, 'unparseable_document': 4, 'not_attempted': 1}}, 'other': {'total': 59, 'positive': 0, 'zero': 59, 'missing': 0, 'reasons': {'not_terraform': 59}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 19}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 47}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 54}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'reference_regression,iteration_deadline', 'error_class': 'Invalid single-argument block definition', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 10}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 12}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported attribute', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 8}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Invalid resource type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_verification_unavailable', 'error_class': 'unknown', 'count': 4}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 3 |
| 2-3 | 4 |
| 4+ | 5 |

Phase 9f measured/unknown packages: (56, 0)
Catalogue retained by rule: {'AWS-0164': 19, 'CKV_AWS_130': 21, 'CKV2_AWS_12': 9, 'CKV_K8S_23': 8, 'CKV_K8S_40': 8, 'KSV-0012': 8, 'KSV-0118': 8, 'KSV-0104': 8, 'CKV_K8S_10': 4, 'CKV_K8S_11': 4, 'CKV_K8S_12': 4, 'CKV_K8S_13': 4, 'CKV_K8S_20': 4, 'CKV_K8S_22': 4, 'CKV_K8S_31': 4, 'CKV_K8S_37': 4, 'KSV-0001': 4, 'KSV-0003': 4, 'KSV-0004': 4, 'KSV-0014': 4, 'KSV-0106': 4, 'AWS-0077': 3, 'AWS-0028': 2, 'AWS-0038': 2, 'CKV_AWS_38': 2, 'AWS-0176': 2, 'CKV_AWS_161': 2}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 88}, {'template': 'access_logs', 'status': 'retained', 'count': 7}, {'template': 'flow_logs', 'status': 'rejected', 'count': 6}, {'template': 'flow_logs', 'status': 'retained', 'count': 26}, {'template': 'kms', 'status': 'rejected', 'count': 17}, {'template': 'kms', 'status': 'retained', 'count': 28}, {'template': 'kms', 'status': 'skipped', 'count': 11}, {'template': 'monitoring', 'status': 'retained', 'count': 1}]
Template introduced rules: {'CKV_AWS_145': 69, 'CKV_AWS_144': 33, 'CKV_AWS_18': 32, 'AWS-0132': 32}
Partial groups: {'unevaluated': 23, 'discarded': 45, 'kept': 23}
Existing-file proposal recovery: {'normalized': 2, 'retained': 0}
Generation syntax recovery: {'unchanged': 43, 'syntax_round_1': 7, 'normalization': 3, 'unresolved': 1, 'syntax_round_2': 2}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 56, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 196, 'median': 2.0, 'p90': 7, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 190 | 0.12347506250080187 | 0.6485669240064453 | 2.2362786610028706 |
| final_security_scan | 56 | 8.087227267991693 | 13.48217041400494 | 22.672448455006815 |
| final_validation | 56 | 0.03427418749924982 | 1.052406571994652 | 5.166486571994028 |
| generation_gate | 56 | 37.20532201749302 | 133.37991307800985 | 140.8463788980007 |
| initial_validation | 56 | 0.04628544850129401 | 0.9927179130027071 | 6.559744504993432 |
| post_security_validation | 56 | 0.024409343997831456 | 1.7477294630079996 | 13.116250345003209 |
| security_iteration_verification | 170 | 34.067309200509044 | 50.57895503702457 | 54.592880663010874 |
| validation_repair_round | 74 | 17.091104243998416 | 54.6173803480051 | 69.62616977999278 |

Iteration outcomes: {'attempted_fix_iterations': 170, 'deadline_only_rollbacks': 54, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 8, 'validity_regression_rollbacks': 19}.
Initialization: {'init_runs': 166, 'init_reused': 597, 'reinitializations': 10}.
Repair deadline stops (measured rounds): {'after_security': 4, 'before_security': 3}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 20, "median": 245.64977153999644, "p90": 481.32222832499247, "max": 578.6945247340045}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 301, "failures": 0, "missing_measurements": 0, "agents": {"architect": 20, "generator_security": 20, "generator_performance": 20, "generator_cost": 20, "security_iteration": 221}, "durations": {"count": 301, "median": 27.650557, "p90": 55.362746, "max": 145.16085}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:945, performance#1:1155, cost#1:1250 | {} | {} |
| 2 | 3 | {"none": 3} | security#1:2094, cost#1:1919, performance#1:2166 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:1877, performance#1:1944, security#1:1626 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:1468, performance#1:1426, security#1:2032 | {} | {} |
| 5 | 3 | {"none": 3} | cost#1:2621, security#1:2848, performance#1:2634 | {} | {} |
| 6 | 7 | {"none": 7} | cost#1:2281, cost#2:2145, cost#3:2912, security#1:3123, security#2:3299, performance#1:2461, performance#2:2990 | {"cost": "incomplete_package"} | {} |
| 7 | 6 | {"none": 6} | cost#1:3027, cost#2:4198, cost#3:3241, security#1:3376, security#2:3721, performance#1:4082 | {"cost": "incomplete_package"} | {} |
| 8 | 5 | {"none": 5} | security#1:3595, performance#1:3408, cost#1:2654, cost#2:2547, cost#3:3041 | {} | {} |
| 9 | 6 | {"none": 6} | security#1:4698, cost#1:4025, cost#2:6614, cost#3:6296, performance#1:5068, performance#2:5457 | {} | {} |
| 10 | 6 | {"none": 6} | cost#1:2715, cost#2:4157, cost#3:3877, performance#1:5742, security#1:2761, security#2:5730 | {} | {} |
| 11 | 7 | {"none": 7} | cost#1:4285, performance#1:3588, performance#2:3839, performance#3:3680, security#1:3265, security#2:3210, security#3:4019 | {} | {} |
| 12 | 7 | {"none": 7} | security#1:5073, security#2:4370, security#3:5257, performance#1:5876, performance#2:6657, cost#1:5631, cost#2:6765 | {"security": "incomplete_package"} | {} |
| 13 | 6 | {"none": 6} | cost#1:2300, cost#2:2759, cost#3:2692, security#1:3289, security#2:3525, performance#1:3446 | {"cost": "incomplete_package"} | {} |
| 14 | 3 | {"none": 3} | cost#1:3988, performance#1:4348, security#1:4126 | {} | {} |
| 15 | 5 | {"none": 5} | security#1:3447, security#2:3040, cost#1:3264, performance#1:2651, performance#2:3111 | {} | {} |
| 16 | 3 | {"none": 3} | cost#1:2795, performance#1:2371, security#1:2868 | {} | {} |
| 17 | 3 | {"none": 3} | cost#1:1704, performance#1:1937, security#1:2022 | {} | {} |
| 18 | 3 | {"none": 3} | performance#1:1832, security#1:1798, cost#1:1523 | {} | {} |
| 19 | 3 | {"none": 3} | cost#1:1937, security#1:2012, performance#1:2035 | {} | {} |
| 20 | 3 | {"none": 3} | performance#1:797, security#1:1061, cost#1:903 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.852098; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.02988845, "remaining_credit_usd": 7.997004596, "planned_runs_remaining": 19, "run_cap_remaining": 19, "projected_further_runs": 19, "assumption": "Projection at first measured cost; fresh guard checks decide."}
