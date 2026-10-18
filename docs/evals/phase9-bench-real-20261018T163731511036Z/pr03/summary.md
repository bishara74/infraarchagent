# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **0/12 (0.00%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 12 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 12 |
| validation_failed | 9 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 5 |
| terraform.validate: Terraform configuration diagnostic | 5 |
| terraform.var_ref: var.acm_certificate_arn is not declared | 2 |
| terraform.var_ref: var.api_image is not declared | 2 |
| terraform.var_ref: var.db_name is not declared | 2 |
| terraform.var_ref: var.db_username is not declared | 2 |
| terraform.var_ref: var.db_instance_class is not declared | 2 |
| terraform.var_ref: var.db_password is not declared | 2 |
| terraform.var_ref: var.nginx_instance_type is not declared | 2 |
| terraform.validate: Reference to undeclared input variable | 2 |
| terraform.validate: Unsupported attribute | 2 |
| terraform.var_ref: var.region is not declared | 1 |
| terraform.var_ref: var.vpc_cidr is not declared | 1 |
| terraform.var_ref: var.project_name is not declared | 1 |
| terraform.var_ref: var.public_subnet_cidrs is not declared | 1 |
| terraform.var_ref: var.private_subnet_cidrs is not declared | 1 |
| terraform.var_ref: var.container_port is not declared | 1 |
| terraform.var_ref: var.ecs_task_cpu is not declared | 1 |
| terraform.var_ref: var.ecs_task_memory is not declared | 1 |
| terraform.var_ref: var.desired_count is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 32 |
| AWS-0164 | 14 |
| CKV_AWS_130 | 14 |
| CKV_AWS_260 | 10 |
| AWS-0053 | 9 |
| CKV2_AWS_12 | 9 |
| CKV_AWS_91 | 9 |
| CKV_AWS_378 | 9 |
| AWS-0054 | 6 |
| CKV2_AWS_20 | 6 |
| CKV_AWS_103 | 6 |
| CKV_AWS_2 | 6 |
| CKV_AWS_18 | 5 |
| AWS-0077 | 4 |
| CKV2_AWS_11 | 4 |
| CKV_AWS_157 | 4 |
| AWS-0132 | 3 |
| CKV_AWS_145 | 3 |
| CKV_AWS_354 | 3 |
| AWS-0090 | 3 |

Final failure origins: {'generated': 24, 'security_fix': 22}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Reference to undeclared input variable | 2 |
| after_security / rejected / invalid_patch | Reference to undeclared resource | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| after_security / rejected / invalid_patch | Unsupported argument | 3 |
| after_security / rejected / invalid_patch | Unsupported attribute | 1 |
| after_security / rejected / invalid_patch | var.acm_certificate_arn is not declared | 2 |
| after_security / rejected / invalid_patch | var.api_image is not declared | 2 |
| after_security / rejected / invalid_patch | var.aws_region is not declared | 1 |
| after_security / rejected / invalid_patch | var.container_port is not declared | 1 |
| after_security / rejected / invalid_patch | var.db_instance_class is not declared | 2 |
| after_security / rejected / invalid_patch | var.db_name is not declared | 2 |
| after_security / rejected / invalid_patch | var.db_password is not declared | 2 |
| after_security / rejected / invalid_patch | var.db_username is not declared | 2 |
| after_security / rejected / invalid_patch | var.desired_count is not declared | 1 |
| after_security / rejected / invalid_patch | var.ecs_task_cpu is not declared | 1 |
| after_security / rejected / invalid_patch | var.ecs_task_memory is not declared | 1 |
| after_security / rejected / invalid_patch | var.key_pair_name is not declared | 1 |
| after_security / rejected / invalid_patch | var.log_bucket_name is not declared | 1 |
| after_security / rejected / invalid_patch | var.max_capacity is not declared | 1 |
| after_security / rejected / invalid_patch | var.min_capacity is not declared | 1 |
| after_security / rejected / invalid_patch | var.monitor_instance_type is not declared | 1 |
| after_security / rejected / invalid_patch | var.nginx_instance_type is not declared | 2 |
| after_security / rejected / invalid_patch | var.nginx_ssh_public_key is not declared | 1 |
| after_security / rejected / invalid_patch | var.private_subnet_cidrs is not declared | 1 |
| after_security / rejected / invalid_patch | var.project_name is not declared | 1 |
| after_security / rejected / invalid_patch | var.public_subnet_cidrs is not declared | 1 |
| after_security / rejected / invalid_patch | var.region is not declared | 1 |
| after_security / rejected / invalid_patch | var.ssh_public_key is not declared | 1 |
| after_security / rejected / invalid_patch | var.vpc_cidr is not declared | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | Reference to undeclared input variable | 2 |
| before_security / rejected / invalid_patch | Reference to undeclared resource | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 4 |
| before_security / rejected / invalid_patch | Unsupported attribute | 1 |
| before_security / rejected / invalid_patch | var.acm_certificate_arn is not declared | 2 |
| before_security / rejected / invalid_patch | var.api_image is not declared | 2 |
| before_security / rejected / invalid_patch | var.aws_region is not declared | 1 |
| before_security / rejected / invalid_patch | var.container_port is not declared | 1 |
| before_security / rejected / invalid_patch | var.db_instance_class is not declared | 2 |
| before_security / rejected / invalid_patch | var.db_name is not declared | 2 |
| before_security / rejected / invalid_patch | var.db_password is not declared | 2 |
| before_security / rejected / invalid_patch | var.db_username is not declared | 2 |
| before_security / rejected / invalid_patch | var.desired_count is not declared | 1 |
| before_security / rejected / invalid_patch | var.ecs_task_cpu is not declared | 1 |
| before_security / rejected / invalid_patch | var.ecs_task_memory is not declared | 1 |
| before_security / rejected / invalid_patch | var.key_pair_name is not declared | 1 |
| before_security / rejected / invalid_patch | var.log_bucket_name is not declared | 1 |
| before_security / rejected / invalid_patch | var.max_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.min_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.monitor_instance_type is not declared | 1 |
| before_security / rejected / invalid_patch | var.nginx_instance_type is not declared | 2 |
| before_security / rejected / invalid_patch | var.nginx_ssh_public_key is not declared | 1 |
| before_security / rejected / invalid_patch | var.private_subnet_cidrs is not declared | 1 |
| before_security / rejected / invalid_patch | var.project_name is not declared | 1 |
| before_security / rejected / invalid_patch | var.public_subnet_cidrs is not declared | 1 |
| before_security / rejected / invalid_patch | var.region is not declared | 1 |
| before_security / rejected / invalid_patch | var.ssh_public_key is not declared | 1 |
| before_security / rejected / invalid_patch | var.vpc_cidr is not declared | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| before_security / rejected / no_improvement | Unsupported argument | 1 |
| generation / rejected / invalid_patch | Reference to undeclared input variable | 2 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| generation / rejected / invalid_patch | Unsupported argument | 4 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | var.acm_certificate_arn is not declared | 2 |
| generation / rejected / invalid_patch | var.api_image is not declared | 2 |
| generation / rejected / invalid_patch | var.aws_region is not declared | 1 |
| generation / rejected / invalid_patch | var.container_port is not declared | 1 |
| generation / rejected / invalid_patch | var.db_instance_class is not declared | 2 |
| generation / rejected / invalid_patch | var.db_name is not declared | 2 |
| generation / rejected / invalid_patch | var.db_password is not declared | 2 |
| generation / rejected / invalid_patch | var.db_username is not declared | 2 |
| generation / rejected / invalid_patch | var.desired_count is not declared | 1 |
| generation / rejected / invalid_patch | var.ecs_task_cpu is not declared | 1 |
| generation / rejected / invalid_patch | var.ecs_task_memory is not declared | 1 |
| generation / rejected / invalid_patch | var.key_pair_name is not declared | 1 |
| generation / rejected / invalid_patch | var.log_bucket_name is not declared | 1 |
| generation / rejected / invalid_patch | var.max_capacity is not declared | 1 |
| generation / rejected / invalid_patch | var.min_capacity is not declared | 1 |
| generation / rejected / invalid_patch | var.monitor_instance_type is not declared | 1 |
| generation / rejected / invalid_patch | var.nginx_instance_type is not declared | 2 |
| generation / rejected / invalid_patch | var.nginx_ssh_public_key is not declared | 1 |
| generation / rejected / invalid_patch | var.private_subnet_cidrs is not declared | 1 |
| generation / rejected / invalid_patch | var.project_name is not declared | 1 |
| generation / rejected / invalid_patch | var.public_subnet_cidrs is not declared | 1 |
| generation / rejected / invalid_patch | var.region is not declared | 1 |
| generation / rejected / invalid_patch | var.ssh_public_key is not declared | 1 |
| generation / rejected / invalid_patch | var.vpc_cidr is not declared | 1 |
| generation / rejected / no_improvement | Reference to undeclared resource | 1 |
| generation / rejected / no_improvement | Unsupported argument | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 50 | 0.08108470100160048 | 0.1605347860022448 | 0.5190514140012965 |
| final_security_scan | 12 | 5.9993591554994055 | 10.483691075001843 | 16.105378233998636 |
| final_validation | 12 | 0.12279307350036106 | 0.9935631600019406 | 11.91665338799794 |
| generation_gate | 12 | 53.642715109001074 | 81.83369561099971 | 81.96561143999861 |
| initial_validation | 12 | 0.22804608399928838 | 0.7437710160011193 | 2.102375608999864 |
| post_security_validation | 12 | 0.17188697150049848 | 1.919585855997866 | 2.2340280070020526 |
| security_iteration_verification | 43 | 16.84630167599971 | 34.88133416799246 | 43.87429754199911 |
| validation_repair_round | 26 | 13.224329559499893 | 24.422198224001477 | 39.67673861200092 |

Iteration outcomes: {'attempted_fix_iterations': 43, 'deadline_only_rollbacks': 5, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 13, 'init_reused': 107, 'reinitializations': 1}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 14, 'init_reused': 160, 'reinitializations': 2, 'init_seconds': 183.4436853960069, 'validate_seconds': 493.3423944360111}
Gate outcomes: {'invalid': 9, 'valid': 3}
Init categories: {'validation_cached': 9, 'initialized': 3}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 5503.0, 'p90': 5503, 'max': 5503}, 'repair': {'count': 26, 'median': 15971.0, 'p90': 15998, 'max': 15998}, 'security': {'count': 49, 'median': 9640, 'p90': 13179, 'max': 14994}}
Security context coverage: {'terraform': {'total': 39, 'positive': 39, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 39}}, 'other': {'total': 10, 'positive': 0, 'zero': 10, 'missing': 0, 'reasons': {'not_terraform': 10}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared input variable', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 4}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Reference to undeclared input variable', 'count': 4}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 12}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 7}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 9}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 3 |

Phase 9f measured/unknown packages: (12, 0)
Catalogue retained by rule: {'CKV_AWS_103': 4, 'AWS-0028': 3, 'AWS-0131': 3, 'CKV_AWS_8': 3}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 39}, {'template': 'flow_logs', 'status': 'rejected', 'count': 1}, {'template': 'flow_logs', 'status': 'retained', 'count': 5}, {'template': 'flow_logs', 'status': 'skipped', 'count': 10}, {'template': 'kms', 'status': 'rejected', 'count': 6}, {'template': 'kms', 'status': 'retained', 'count': 5}, {'template': 'kms', 'status': 'skipped', 'count': 7}]
Template introduced rules: {'AWS-0090': 37, 'AWS-0132': 39}
Partial groups: {}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 8, 'syntax_round_1': 3, 'normalization': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 12, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 49, 'median': 2, 'p90': 5, 'max': 5}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 49 | 0.07921179100230802 | 0.1605347860022448 | 0.40200969299985445 |
| final_security_scan | 12 | 5.9993591554994055 | 10.483691075001843 | 16.105378233998636 |
| final_validation | 12 | 0.12279307350036106 | 0.9935631600019406 | 11.91665338799794 |
| generation_gate | 12 | 53.642715109001074 | 81.83369561099971 | 81.96561143999861 |
| initial_validation | 12 | 0.22804608399928838 | 0.7437710160011193 | 2.102375608999864 |
| post_security_validation | 12 | 0.17188697150049848 | 1.919585855997866 | 2.2340280070020526 |
| security_iteration_verification | 43 | 16.84630167599971 | 34.88133416799246 | 43.87429754199911 |
| validation_repair_round | 26 | 13.224329559499893 | 24.422198224001477 | 39.67673861200092 |

Iteration outcomes: {'attempted_fix_iterations': 43, 'deadline_only_rollbacks': 5, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 13, 'init_reused': 107, 'reinitializations': 1}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 313.3567581775005, "p90": 333.63508423500025, "max": 333.63508423500025}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "e0f47a31-f2d3-414d-a1a8-f938300911df", "ratio_to_baseline": 2.3049106842845375, "ratio_to_pr01_prompt_median": 2.601008096804944, "pr01_prompt_median_seconds": 116.19611452699883, "pr01_reference_count": 4}

Cohort references: {"run_id": "a2ef9d64-d3a9-4153-9375-810e635a4f35", "ratio_to_baseline": 2.474670603856997, "ratio_to_pr01_prompt_median": 2.792576008017947, "pr01_prompt_median_seconds": 116.19611452699883, "pr01_reference_count": 4}

Cohort references: {"run_id": "dc7ec97f-f230-43cb-a9a1-a2976c20ba13", "ratio_to_baseline": 2.544441701132631, "ratio_to_pr01_prompt_median": 2.8713101603537545, "pr01_prompt_median_seconds": 116.19611452699883, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: FAIL. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:3382, performance#1:3652, security#1:4340 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:3959, performance#1:4782, security#1:4761 | {} | {} |
| 3 | 4 | {"none": 4} | security#1:3368, cost#1:3218, cost#2:3689, performance#1:4484 | {} | {} |
| 4 | 3 | {"none": 3} | performance#1:4735, cost#1:3916, security#1:3980 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.471898; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.3338844, "average_cost_usd": 0.1112948, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["a2ef9d64-d3a9-4153-9375-810e635a4f35", "dc7ec97f-f230-43cb-a9a1-a2976c20ba13", "e0f47a31-f2d3-414d-a1a8-f938300911df"], "before_remaining_usd": 4.650364339999999, "after_remaining_usd": 4.316479940000001}
