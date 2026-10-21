# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **19/60 (31.67%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 19/60; contextual-v1: 19/60; contextual-v2: 19/60. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 41 |
| checks_passed | 19 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 33 |
| validation_failed | 23 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 11 |
| helm.lint: helm optional lint failed (undefined_named_template) | 10 |
| terraform.validate: Unsupported argument | 8 |
| ansible-lint.lint: ansible-lint optional lint failed | 4 |
| terraform.validate: Unsupported block type | 2 |
| grafana.panels: Dashboard requires panels | 2 |
| terraform.validate: Cycle | 1 |
| promtool.lint: promtool optional lint failed | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0053 | 23 |
| CKV_AWS_91 | 20 |
| CKV_AWS_130 | 12 |
| AWS-0164 | 10 |
| CKV_AWS_18 | 8 |
| CKV2_AWS_12 | 8 |
| AWS-0090 | 6 |
| CKV_AWS_21 | 6 |
| AWS-0104 | 6 |
| CKV_AWS_157 | 5 |
| KSV-0125 | 4 |
| AWS-0039 | 3 |
| CKV_AWS_144 | 3 |
| AWS-0010 | 2 |
| AWS-0011 | 2 |
| CKV_AWS_354 | 2 |
| CKV_AWS_260 | 2 |
| CKV_AWS_103 | 2 |
| AWS-0132 | 1 |
| CKV_AWS_145 | 1 |

Final failure origins: {'generated': 36, 'unknown': 3}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Missing required argument | 1 |
| after_security / accepted / improved | Unsupported block type | 1 |
| after_security / rejected / invalid_patch | Cycle | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| after_security / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| after_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| after_security / rejected / new_blocking_findings | Unsupported argument | 1 |
| after_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 6 |
| after_security / rejected / new_blocking_findings | promtool optional lint failed | 1 |
| after_security / rejected / no_improvement | Dashboard requires panels | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 9 |
| after_security / rejected / no_improvement | Unsupported argument | 7 |
| after_security / rejected / no_improvement | Unsupported block type | 1 |
| after_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 4 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Missing required argument | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 2 |
| before_security / accepted / improved | Unsupported argument | 5 |
| before_security / rejected / invalid_patch | Missing required argument | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 2 |
| before_security / rejected / invalid_patch | promtool optional lint failed | 1 |
| before_security / rejected / new_blocking_findings | Dashboard requires panels | 2 |
| before_security / rejected / new_blocking_findings | Missing required argument | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 4 |
| before_security / rejected / new_blocking_findings | Unsupported argument | 2 |
| before_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 7 |
| before_security / rejected / no_improvement | Cycle | 1 |
| before_security / rejected / no_improvement | Missing required argument | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 7 |
| before_security / rejected / no_improvement | Unsupported argument | 6 |
| before_security / rejected / no_improvement | Unsupported block type | 2 |
| before_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| before_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 1 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 4 |
| generation / accepted / improved | Unsupported argument | 4 |
| generation / accepted / improved | Unsupported block type | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| generation / rejected / invalid_patch | Unsupported argument | 1 |
| generation / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| generation / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 1 |
| generation / rejected / invalid_patch | promtool optional lint failed | 1 |
| generation / rejected / new_blocking_findings | Dashboard requires panels | 2 |
| generation / rejected / new_blocking_findings | Generation syntax check failed | 8 |
| generation / rejected / new_blocking_findings | Missing required argument | 2 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 4 |
| generation / rejected / new_blocking_findings | Unsupported argument | 3 |
| generation / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 8 |
| generation / rejected / no_improvement | Cycle | 1 |
| generation / rejected / no_improvement | Generation syntax check failed | 1 |
| generation / rejected / no_improvement | Missing required argument | 2 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 6 |
| generation / rejected / no_improvement | Unsupported argument | 8 |
| generation / rejected / no_improvement | Unsupported block type | 2 |
| generation / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 1 |
| generation / stopped / round_limit | unknown | 3 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 226 | 0.0493132820001847 | 0.26787786799923197 | 0.7242950849999943 |
| final_security_scan | 60 | 4.845256216500047 | 6.460382914000093 | 7.9535131370003 |
| final_validation | 60 | 0.003278434000094421 | 0.42734522599994307 | 3.5723301370003355 |
| generation_gate | 60 | 21.517359385499958 | 56.43385474899969 | 83.48094093600002 |
| initial_validation | 60 | 0.004010033000213298 | 0.39226396100002603 | 3.1894140529998367 |
| post_security_validation | 60 | 0.002415354499817113 | 0.46302942100010114 | 12.733172868999645 |
| security_iteration_verification | 172 | 21.789818460999868 | 44.98007850399972 | 51.148417817999416 |
| validation_repair_round | 88 | 9.238808754000047 | 22.406261600000107 | 24.42078222200007 |

Iteration outcomes: {'attempted_fix_iterations': 172, 'deadline_only_rollbacks': 6, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 10, 'validity_regression_rollbacks': 29}.
Initialization: {'init_runs': 87, 'init_reused': 752, 'reinitializations': 15}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 60, 'packages_unknown': 0, 'init_runs': 92, 'init_reused': 1008, 'reinitializations': 16, 'init_seconds': 527.2740896710009, 'validate_seconds': 2433.3780081390014}
Gate outcomes: {'valid': 29, 'invalid': 31}
Init categories: {'initialized': 19, 'validation_cached': 37, 'reused': 3, 'unknown': 1}
Schema context sizes (characters): {'generator': {'count': 60, 'median': 4487.0, 'p90': 4490, 'max': 4496}, 'repair': {'count': 92, 'median': 15953.0, 'p90': 15990, 'max': 16000}, 'security': {'count': 194, 'median': 9062.5, 'p90': 12855, 'max': 15977}, 'generator_schema_only': {'count': 60, 'median': 4487.0, 'p90': 4490, 'max': 4496}}
Schema guidance overflow: {'measured_packages': 60, 'overflow_packages': 30, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_s3_bucket': 3, 'aws_dynamodb_table': 6, 'aws_ecs_task_definition': 9, 'aws_lb': 6, 'aws_lb_listener': 9, 'aws_ecs_service': 9, 'aws_instance': 3, 'aws_cloudfront_distribution': 3}}}
Security context coverage: {'terraform': {'total': 164, 'positive': 164, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 164}}, 'other': {'total': 30, 'positive': 0, 'zero': 30, 'missing': 0, 'reasons': {'not_terraform': 30}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Cycle', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 17}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 11}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 62}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 3}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 8}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Missing required argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 24}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Cycle', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared resource', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 11}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 9}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported block type', 'count': 2}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 2 |
| 2-3 | 11 |
| 4+ | 5 |

Phase 9f measured/unknown packages: (60, 0)
Catalogue retained by rule: {'AWS-0164': 19, 'CKV_AWS_130': 19, 'CKV2_AWS_12': 9, 'CKV_AWS_103': 4, 'AWS-0077': 5, 'CKV_AWS_129': 1, 'CKV_K8S_23': 10, 'CKV_K8S_40': 10, 'KSV-0012': 10, 'KSV-0118': 10, 'KSV-0104': 10, 'CKV_K8S_10': 5, 'CKV_K8S_11': 5, 'CKV_K8S_12': 5, 'CKV_K8S_13': 5, 'CKV_K8S_20': 5, 'CKV_K8S_22': 5, 'CKV_K8S_31': 5, 'CKV_K8S_37': 5, 'KSV-0001': 5, 'KSV-0003': 5, 'KSV-0004': 5, 'KSV-0014': 5, 'KSV-0106': 5, 'AWS-0176': 1, 'CKV_AWS_161': 1, 'AWS-0131': 3, 'CKV_AWS_8': 3}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 126}, {'template': 'access_logs', 'status': 'retained', 'count': 4}, {'template': 'flow_logs', 'status': 'retained', 'count': 35}, {'template': 'kms', 'status': 'rejected', 'count': 2}, {'template': 'kms', 'status': 'retained', 'count': 22}, {'template': 'kms', 'status': 'skipped', 'count': 12}]
Template introduced rules: {'CKV_AWS_145': 94, 'CKV_AWS_144': 46, 'CKV_AWS_18': 76, 'AWS-0132': 76}
Partial groups: {'discarded': 72, 'kept': 44, 'unevaluated': 14}
Existing-file proposal recovery: {'normalized': 2, 'retained': 1}
Generation syntax recovery: {'unchanged': 57, 'syntax_round_1': 2, 'normalization': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 60, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 194, 'median': 3.0, 'p90': 6, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 226 | 0.0493132820001847 | 0.26787786799923197 | 0.7242950849999943 |
| final_security_scan | 60 | 4.845256216500047 | 6.460382914000093 | 7.9535131370003 |
| final_validation | 60 | 0.003278434000094421 | 0.42734522599994307 | 3.5723301370003355 |
| generation_gate | 60 | 21.517359385499958 | 56.43385474899969 | 83.48094093600002 |
| initial_validation | 60 | 0.004010033000213298 | 0.39226396100002603 | 3.1894140529998367 |
| post_security_validation | 60 | 0.002415354499817113 | 0.46302942100010114 | 12.733172868999645 |
| security_iteration_verification | 172 | 21.789818460999868 | 44.98007850399972 | 51.148417817999416 |
| validation_repair_round | 88 | 9.238808754000047 | 22.406261600000107 | 24.42078222200007 |

Iteration outcomes: {'attempted_fix_iterations': 172, 'deadline_only_rollbacks': 6, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 10, 'validity_regression_rollbacks': 29}.
Initialization: {'init_runs': 87, 'init_reused': 752, 'reinitializations': 15}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 20, "median": 155.82477168800028, "p90": 270.8580784760006, "max": 329.4202319440001}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 311, "failures": 0, "missing_measurements": 0, "agents": {"architect": 20, "generator_performance": 20, "generator_cost": 20, "generator_security": 20, "security_iteration": 231}, "durations": {"count": 311, "median": 17.773361, "p90": 53.319933, "max": 86.301408}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | performance#1:1264, cost#1:1758, security#1:1619 | {} | {} |
| 2 | 3 | {"none": 3} | performance#1:1473, cost#1:1346, security#1:1414 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:1595, security#1:1676, performance#1:1275 | {} | {} |
| 4 | 3 | {"none": 3} | performance#1:1328, security#1:2283, cost#1:1535 | {} | {} |
| 5 | 3 | {"none": 3} | cost#1:2239, security#1:2201, performance#1:1643 | {} | {} |
| 6 | 3 | {"none": 3} | performance#1:2213, cost#1:2244, security#1:2892 | {} | {} |
| 7 | 3 | {"none": 3} | security#1:3303, cost#1:3139, performance#1:3545 | {} | {} |
| 8 | 3 | {"none": 3} | performance#1:3325, security#1:3091, cost#1:3476 | {} | {} |
| 9 | 3 | {"none": 3} | security#1:3589, performance#1:3952, cost#1:2910 | {} | {} |
| 10 | 3 | {"none": 3} | performance#1:4266, cost#1:3029, security#1:3265 | {} | {} |
| 11 | 3 | {"none": 3} | cost#1:4214, performance#1:4683, security#1:4428 | {} | {} |
| 12 | 6 | {"none": 6} | cost#1:2749, cost#2:4156, security#1:3317, security#2:4610, performance#1:4764, performance#2:4816 | {} | {} |
| 13 | 4 | {"none": 4} | security#1:2691, cost#1:2056, cost#2:3028, performance#1:3055 | {} | {} |
| 14 | 4 | {"none": 4} | cost#1:3181, performance#1:3591, security#1:3906, security#2:3259 | {} | {} |
| 15 | 3 | {"none": 3} | cost#1:2009, performance#1:2650, security#1:3289 | {} | {} |
| 16 | 3 | {"none": 3} | cost#1:1677, performance#1:1881, security#1:2554 | {} | {} |
| 17 | 3 | {"none": 3} | security#1:2073, cost#1:1897, performance#1:1749 | {} | {} |
| 18 | 3 | {"none": 3} | performance#1:1174, security#1:1437, cost#1:1377 | {} | {} |
| 19 | 3 | {"none": 3} | cost#1:1652, security#1:1854, performance#1:1675 | {} | {} |
| 20 | 3 | {"none": 3} | cost#1:1087, performance#1:1633, security#1:969 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.417497; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.0202035, "remaining_credit_usd": 4.93350624, "planned_runs_remaining": 19, "run_cap_remaining": 19, "projected_further_runs": 19, "assumption": "Projection at first measured cost; fresh guard checks decide."}
