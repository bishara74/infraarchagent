# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **1/36 (2.78%)**.
Missing variants: 6; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 35 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 34 |
| validation_failed | 27 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 16 |
| terraform.validate: Terraform configuration diagnostic | 14 |
| helm.lint: helm optional lint failed | 10 |
| terraform.validate: Missing required argument | 6 |
| ansible-lint.lint: ansible-lint optional lint failed | 5 |
| terraform.validate: Unsupported attribute | 4 |
| terraform.validate: Unsupported block type | 4 |
| terraform.validate: Reference to undeclared resource | 4 |
| grafana.panels: Dashboard requires panels | 2 |
| terraform.var_ref: var.acm_certificate_arn is not declared | 2 |
| terraform.var_ref: var.api_image is not declared | 2 |
| terraform.var_ref: var.db_name is not declared | 2 |
| terraform.var_ref: var.db_username is not declared | 2 |
| terraform.var_ref: var.db_instance_class is not declared | 2 |
| terraform.var_ref: var.db_password is not declared | 2 |
| terraform.var_ref: var.nginx_instance_type is not declared | 2 |
| terraform.validate: Reference to undeclared input variable | 2 |
| terraform.var_ref: var.region is not declared | 1 |
| terraform.var_ref: var.vpc_cidr is not declared | 1 |
| terraform.var_ref: var.project_name is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 52 |
| AWS-0164 | 26 |
| CKV_AWS_130 | 26 |
| CKV2_AWS_12 | 22 |
| KSV-0118 | 18 |
| AWS-0053 | 17 |
| CKV2_AWS_11 | 16 |
| CKV_AWS_260 | 16 |
| CKV_AWS_91 | 16 |
| CKV_AWS_18 | 16 |
| CKV_AWS_378 | 15 |
| AWS-0054 | 12 |
| CKV_AWS_103 | 12 |
| CKV_AWS_2 | 12 |
| CKV_AWS_144 | 12 |
| CKV2_AWS_20 | 11 |
| CKV_AWS_157 | 10 |
| AWS-0132 | 10 |
| CKV_AWS_145 | 10 |
| CKV_K8S_40 | 10 |

Final failure origins: {'generated': 76, 'security_fix': 22}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Terraform configuration diagnostic | 1 |
| after_security / accepted / improved | Unsupported argument | 1 |
| after_security / accepted / improved | Unsupported block type | 1 |
| after_security / rejected / invalid_patch | Dashboard requires panels | 2 |
| after_security / rejected / invalid_patch | Missing required argument | 1 |
| after_security / rejected / invalid_patch | Reference to undeclared input variable | 2 |
| after_security / rejected / invalid_patch | Reference to undeclared resource | 3 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 4 |
| after_security / rejected / invalid_patch | Unsupported argument | 11 |
| after_security / rejected / invalid_patch | Unsupported attribute | 2 |
| after_security / rejected / invalid_patch | ansible-lint optional lint failed | 4 |
| after_security / rejected / invalid_patch | helm optional lint failed | 9 |
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
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 1 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 1 |
| before_security / accepted / improved | Unsupported block type | 1 |
| before_security / rejected / invalid_patch | Dashboard requires panels | 2 |
| before_security / rejected / invalid_patch | Missing required argument | 4 |
| before_security / rejected / invalid_patch | Reference to undeclared input variable | 2 |
| before_security / rejected / invalid_patch | Reference to undeclared resource | 3 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 8 |
| before_security / rejected / invalid_patch | Unsupported argument | 16 |
| before_security / rejected / invalid_patch | Unsupported attribute | 3 |
| before_security / rejected / invalid_patch | Unsupported block type | 4 |
| before_security / rejected / invalid_patch | ansible-lint optional lint failed | 4 |
| before_security / rejected / invalid_patch | helm optional lint failed | 10 |
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
| generation / rejected / invalid_patch | Dashboard requires panels | 2 |
| generation / rejected / invalid_patch | Generation syntax check failed | 11 |
| generation / rejected / invalid_patch | Missing required argument | 4 |
| generation / rejected / invalid_patch | Reference to undeclared input variable | 2 |
| generation / rejected / invalid_patch | Reference to undeclared resource | 2 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 9 |
| generation / rejected / invalid_patch | Unsupported argument | 15 |
| generation / rejected / invalid_patch | Unsupported attribute | 3 |
| generation / rejected / invalid_patch | Unsupported block type | 4 |
| generation / rejected / invalid_patch | ansible-lint optional lint failed | 4 |
| generation / rejected / invalid_patch | helm optional lint failed | 10 |
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
| generation / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| generation / rejected / no_improvement | Unsupported argument | 2 |
| generation / rejected / no_improvement | Unsupported block type | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 168 | 0.03846404700016137 | 0.11769139399984851 | 0.5765045850002934 |
| final_security_scan | 36 | 5.405711739499566 | 7.2165928130016255 | 16.105378233998636 |
| final_validation | 36 | 0.14310144699811644 | 1.7159238130006997 | 11.91665338799794 |
| generation_gate | 36 | 22.669258846999583 | 60.353476252999826 | 81.96561143999861 |
| initial_validation | 36 | 0.2543482814999152 | 2.102375608999864 | 3.555138504001661 |
| post_security_validation | 36 | 0.15781453750059882 | 2.2340280070020526 | 3.649152812002285 |
| security_iteration_verification | 138 | 8.770428061005077 | 31.47542768099993 | 50.50675335099913 |
| validation_repair_round | 77 | 8.494878804998734 | 19.911064838997845 | 39.67673861200092 |

Iteration outcomes: {'attempted_fix_iterations': 138, 'deadline_only_rollbacks': 5, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 3, 'validity_regression_rollbacks': 3}.
Initialization: {'init_runs': 61, 'init_reused': 329, 'reinitializations': 3}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 36, 'packages_unknown': 0, 'init_runs': 68, 'init_reused': 451, 'reinitializations': 4, 'init_seconds': 348.5637879520036, 'validate_seconds': 888.8102680289921}
Gate outcomes: {'invalid': 28, 'valid': 8}
Init categories: {'validation_cached': 26, 'unknown': 2, 'initialized': 8}
Schema context sizes (characters): {'generator': {'count': 36, 'median': 4202.0, 'p90': 5503, 'max': 5503}, 'repair': {'count': 78, 'median': 15958.0, 'p90': 15992, 'max': 15998}, 'security': {'count': 182, 'median': 9148.0, 'p90': 12214, 'max': 14994}}
Security context coverage: {'terraform': {'total': 133, 'positive': 133, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 133}}, 'other': {'total': 49, 'positive': 0, 'zero': 49, 'missing': 0, 'reasons': {'not_terraform': 49}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared input variable', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 4}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 8}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 13}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 11}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Missing required argument', 'count': 10}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Reference to undeclared input variable', 'count': 4}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 7}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 24}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 47}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 8}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported block type', 'count': 13}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 24}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 9}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 2 |
| 4+ | 6 |

Phase 9f measured/unknown packages: (36, 0)
Catalogue retained by rule: {'CKV_AWS_103': 7, 'AWS-0177': 1, 'CKV_AWS_293': 1, 'AWS-0028': 3, 'AWS-0131': 3, 'CKV_AWS_8': 3}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 97}, {'template': 'flow_logs', 'status': 'rejected', 'count': 1}, {'template': 'flow_logs', 'status': 'retained', 'count': 17}, {'template': 'flow_logs', 'status': 'skipped', 'count': 46}, {'template': 'kms', 'status': 'rejected', 'count': 22}, {'template': 'kms', 'status': 'retained', 'count': 14}, {'template': 'kms', 'status': 'skipped', 'count': 21}]
Template introduced rules: {'AWS-0090': 95, 'AWS-0132': 113}
Partial groups: {'discarded': 7, 'kept': 9, 'unevaluated': 3}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 29, 'normalization': 2, 'syntax_round_2': 1, 'syntax_round_1': 4}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 36, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 182, 'median': 3.0, 'p90': 12, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 167 | 0.037197780002315994 | 0.11257671400016989 | 0.5765045850002934 |
| final_security_scan | 36 | 5.405711739499566 | 7.2165928130016255 | 16.105378233998636 |
| final_validation | 36 | 0.14310144699811644 | 1.7159238130006997 | 11.91665338799794 |
| generation_gate | 36 | 22.669258846999583 | 60.353476252999826 | 81.96561143999861 |
| initial_validation | 36 | 0.2543482814999152 | 2.102375608999864 | 3.555138504001661 |
| post_security_validation | 36 | 0.15781453750059882 | 2.2340280070020526 | 3.649152812002285 |
| security_iteration_verification | 138 | 8.770428061005077 | 31.47542768099993 | 50.50675335099913 |
| validation_repair_round | 77 | 8.494878804998734 | 19.911064838997845 | 39.67673861200092 |

Iteration outcomes: {'attempted_fix_iterations': 138, 'deadline_only_rollbacks': 5, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 3, 'validity_regression_rollbacks': 3}.
Initialization: {'init_runs': 61, 'init_reused': 329, 'reinitializations': 3}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 121.09235275599985, "p90": 161.1243009990012, "max": 179.96733002999827}; failed/incomplete: 0.

pr01 threshold: PASS.

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
| 1 | 5 | {"none": 5} | performance#1:3474, performance#2:3137, cost#1:3526, security#1:3148, security#2:4006 | {"performance": "incomplete_package"} | {} |
| 2 | 4 | {"none": 4} | security#1:3671, performance#1:3100, cost#1:3791, cost#2:3911 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:1258, security#1:1493, performance#1:1639 | {} | {} |
| 4 | 6 | {"none": 6} | cost#1:3503, cost#2:2613, performance#1:2563, performance#2:3324, security#1:2813, security#2:4550 | {"cost": "incomplete_package"} | {} |
| 5 | 3 | {"none": 3} | performance#1:4400, security#1:3639, cost#1:3713 | {} | {} |
| 6 | 3 | {"none": 3} | performance#1:1608, security#1:1249, cost#1:1582 | {} | {} |
| 7 | 5 | {"none": 5} | security#1:3954, security#2:3552, performance#1:3132, performance#2:3585, cost#1:3379 | {"security": "incomplete_package", "performance": "incomplete_package"} | {} |
| 8 | 5 | {"none": 5} | performance#1:2736, performance#2:2519, cost#1:3869, security#1:3049, security#2:3425 | {"performance": "incomplete_package"} | {} |
| 9 | 3 | {"none": 3} | performance#1:1578, cost#1:1628, security#1:1737 | {} | {} |
| 10 | 4 | {"none": 4} | cost#1:3333, cost#2:3310, performance#1:3364, security#1:4070 | {"cost": "incomplete_package"} | {} |
| 11 | 3 | {"none": 3} | cost#1:3382, performance#1:3652, security#1:4340 | {} | {} |
| 12 | 3 | {"none": 3} | cost#1:3959, performance#1:4782, security#1:4761 | {} | {} |
| 13 | 4 | {"none": 4} | security#1:3368, cost#1:3218, cost#2:3689, performance#1:4484 | {} | {} |
| 14 | 3 | {"none": 3} | performance#1:4735, cost#1:3916, security#1:3980 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.403041; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.3338844, "average_cost_usd": 0.1112948, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["a2ef9d64-d3a9-4153-9375-810e635a4f35", "dc7ec97f-f230-43cb-a9a1-a2976c20ba13", "e0f47a31-f2d3-414d-a1a8-f938300911df"], "before_remaining_usd": 4.650364339999999, "after_remaining_usd": 4.316479940000001}

First-run affordability advisory: {"measured_first_run_cost_usd": 0.1005171, "remaining_credit_usd": 5.603698340000001, "planned_runs_remaining": 13, "run_cap_remaining": null, "projected_further_runs": 13, "assumption": "Projection at first measured cost; fresh guard checks decide."}
