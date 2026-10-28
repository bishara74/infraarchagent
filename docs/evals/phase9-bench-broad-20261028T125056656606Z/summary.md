# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **15/58 (25.86%)**.
Legacy labels mapped: 0. Missing variants: 2; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 15/58; contextual-v1: 15/58; contextual-v2: 15/58. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 43 |
| checks_passed | 15 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 33 |
| validation_failed | 21 |
| validation_error | 6 |
| plan_conformance_conflict | 6 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 14 |
| helm.lint: helm optional lint failed (undefined_named_template) | 9 |
| terraform.validate: Invalid index | 3 |
| grafana.panels: Dashboard requires panels | 3 |
| terraform.validate: Unsupported argument | 2 |
| terraform.validate: Unsupported attribute | 1 |
| terraform.local_module: Local module unavailable: local_module_missing | 1 |
| terraform.local_module: Local module source must exist inside the package | 1 |
| helm.lint: helm optional lint failed | 1 |
| promtool.lint: promtool optional lint failed | 1 |
| terraform.validate: Missing required argument | 1 |
| terraform.validate: Cycle | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0053 | 17 |
| AWS-0090 | 12 |
| CKV_AWS_21 | 12 |
| CKV_AWS_91 | 11 |
| CKV_AWS_18 | 9 |
| CKV_AWS_144 | 6 |
| TERRAFORM_FILE_INPUT | 5 |
| AWS-0104 | 5 |
| CKV2_AWS_12 | 5 |
| AWS-0132 | 5 |
| AWS-0164 | 5 |
| CKV_AWS_130 | 5 |
| CKV_AWS_145 | 5 |
| CKV_AWS_260 | 4 |
| AWS-0011 | 3 |
| AWS-0039 | 3 |
| CKV_AWS_354 | 3 |
| KSV-0125 | 3 |
| CKV_AWS_157 | 3 |
| AWS-0010 | 2 |

Final failure origins: {'generated': 35, 'security_fix': 1, 'unknown': 2}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Unsupported argument | 1 |
| after_security / rejected / invalid_patch | Missing required argument | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 3 |
| after_security / rejected / invalid_patch | promtool optional lint failed | 1 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| after_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| after_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 3 |
| after_security / rejected / no_improvement | Cycle | 1 |
| after_security / rejected / no_improvement | Invalid index | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 6 |
| after_security / rejected / no_improvement | Unsupported argument | 1 |
| after_security / rejected / no_improvement | Unsupported attribute | 1 |
| after_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 1 |
| after_security / stopped / deadline | Dashboard requires panels | 2 |
| after_security / stopped / deadline | Local module source must exist inside the package | 1 |
| after_security / stopped / deadline | Local module unavailable: local_module_missing | 1 |
| after_security / stopped / deadline | helm optional lint failed (undefined_named_template) | 2 |
| before_security / accepted / improved | Invalid index | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 2 |
| before_security / accepted / improved | Unsupported argument | 2 |
| before_security / accepted / improved | Unsupported block type | 1 |
| before_security / rejected / invalid_patch | Dashboard requires panels | 3 |
| before_security / rejected / invalid_patch | Local module source must exist inside the package | 1 |
| before_security / rejected / invalid_patch | Local module unavailable: local_module_missing | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 3 |
| before_security / rejected / invalid_patch | promtool optional lint failed | 1 |
| before_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| before_security / rejected / new_blocking_findings | Invalid multi-line string | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 3 |
| before_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 5 |
| before_security / rejected / new_blocking_findings | var.aws_region is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.backup_bucket_name is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.lambda_name is not declared | 1 |
| before_security / rejected / new_blocking_findings | var.lambda_zip_path is not declared | 1 |
| before_security / rejected / no_improvement | Invalid index | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 6 |
| before_security / rejected / no_improvement | Unsupported argument | 3 |
| before_security / rejected / no_improvement | Unsupported attribute | 1 |
| before_security / stopped / deadline | Missing required argument | 1 |
| before_security / stopped / deadline | Unsupported argument | 1 |
| before_security / stopped / deadline | helm optional lint failed (undefined_named_template) | 1 |
| generation / accepted / improved | Invalid index | 1 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Reference to undeclared local value | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 3 |
| generation / accepted / improved | Unresolved bare proxy_pass target in nginx/nginx.conf:8 | 1 |
| generation / accepted / improved | Unsupported argument | 1 |
| generation / accepted / improved | local.project_name is not declared | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 3 |
| generation / rejected / invalid_patch | Missing required argument | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 1 |
| generation / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 2 |
| generation / rejected / invalid_patch | promtool optional lint failed | 1 |
| generation / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| generation / rejected / new_blocking_findings | Generation syntax check failed | 5 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| generation / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 5 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 4 |
| generation / rejected / no_improvement | Unsupported argument | 3 |
| generation / rejected / no_improvement | Unsupported attribute | 1 |
| generation / rejected / no_improvement | Unsupported block type | 1 |
| generation / stopped / round_limit | unknown | 2 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 203 | 0.04131360800238326 | 0.2905389610095881 | 2.1331838680198416 |
| final_security_scan | 58 | 5.169356347993016 | 6.736842645012075 | 7.0888290549919475 |
| final_validation | 58 | 0.003245805506594479 | 0.4857227070024237 | 4.579230984003516 |
| generation_gate | 58 | 28.97202659600589 | 81.33779611097998 | 135.66511810800876 |
| initial_validation | 58 | 0.0029285710043041036 | 0.5015194090083241 | 7.783282149990555 |
| post_security_validation | 58 | 0.0027053505036747083 | 0.5049400610150769 | 10.327813906013034 |
| security_iteration_verification | 178 | 13.584405852554482 | 39.876424685964594 | 53.0410041489813 |
| validation_repair_round | 69 | 14.519213959982153 | 43.3958706179983 | 101.1059277089953 |

Iteration outcomes: {'attempted_fix_iterations': 178, 'deadline_only_rollbacks': 12, 'deadline_before_candidate': 26, 'multiple_cause_deadline_rollbacks': 4, 'validity_regression_rollbacks': 24}.
Initialization: {'init_runs': 143, 'init_reused': 522, 'reinitializations': 13}.
Repair deadline stops (measured rounds): {'after_security': 2, 'before_security': 1}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 58, 'packages_unknown': 0, 'init_runs': 198, 'init_reused': 706, 'reinitializations': 15, 'init_seconds': 550.5789096869121, 'validate_seconds': 1711.6312187131261}
Gate outcomes: {'valid': 28, 'invalid': 18, 'error': 6, 'deadline': 6}
Init categories: {'initialized': 15, 'validation_cached': 28, 'unknown': 6, 'mirror_constraint_unavailable': 1}
Schema context sizes (characters): {'generator': {'count': 58, 'median': 4483.0, 'p90': 4493, 'max': 4496}, 'repair': {'count': 71, 'median': 12140, 'p90': 15988, 'max': 15997}, 'security': {'count': 160, 'median': 8782.0, 'p90': 13895, 'max': 16000}, 'generator_schema_only': {'count': 58, 'median': 4483.0, 'p90': 4493, 'max': 4496}}
Schema guidance overflow: {'measured_packages': 58, 'overflow_packages': 31, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_cloudfront_distribution': 3, 'aws_dynamodb_table': 6, 'aws_ecs_service': 17, 'aws_lb_listener': 8, 'aws_launch_template': 3, 'aws_db_instance': 2, 'aws_s3_bucket': 3}}}
Security context coverage: {'terraform': {'total': 145, 'positive': 145, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 144, 'no_schema_entries': 1}}, 'other': {'total': 15, 'positive': 0, 'zero': 15, 'missing': 0, 'reasons': {'not_terraform': 15}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Cycle', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid index', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Local module unavailable: local_module_missing', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 16}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 7}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 55}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Local module unavailable: local_module_missing', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 8}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 12}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Invalid index', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 15}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Cycle', 'count': 9}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Duplicate required providers configuration', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid index', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_verification_unavailable', 'error_class': 'unknown', 'count': 2}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 26}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 7 |
| 4+ | 9 |

Phase 9f measured/unknown packages: (58, 0)
Catalogue retained by rule: {'AWS-0164': 21, 'CKV_AWS_130': 21, 'CKV2_AWS_12': 6, 'CKV_AWS_103': 4, 'AWS-0028': 1, 'AWS-0131': 1, 'CKV_AWS_8': 1, 'CKV_K8S_23': 8, 'CKV_K8S_40': 8, 'KSV-0012': 8, 'KSV-0118': 8, 'KSV-0104': 8, 'CKV_K8S_10': 4, 'CKV_K8S_11': 4, 'CKV_K8S_12': 4, 'CKV_K8S_13': 4, 'CKV_K8S_20': 4, 'CKV_K8S_22': 4, 'CKV_K8S_31': 4, 'CKV_K8S_37': 4, 'KSV-0001': 4, 'KSV-0003': 4, 'KSV-0004': 4, 'KSV-0014': 4, 'KSV-0106': 4}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 84}, {'template': 'access_logs', 'status': 'retained', 'count': 7}, {'template': 'flow_logs', 'status': 'retained', 'count': 26}, {'template': 'kms', 'status': 'rejected', 'count': 2}, {'template': 'kms', 'status': 'retained', 'count': 20}, {'template': 'kms', 'status': 'skipped', 'count': 20}]
Template introduced rules: {'CKV_AWS_145': 68, 'CKV_AWS_144': 34, 'CKV_AWS_18': 40, 'AWS-0132': 40}
Partial groups: {'kept': 24, 'unevaluated': 4, 'discarded': 63}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 49, 'regeneration': 1, 'syntax_round_1': 5, 'normalization': 2, 'unknown': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 58, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 160, 'median': 2.0, 'p90': 7, 'max': 9}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 203 | 0.04131360800238326 | 0.2905389610095881 | 2.1331838680198416 |
| final_security_scan | 58 | 5.169356347993016 | 6.736842645012075 | 7.0888290549919475 |
| final_validation | 58 | 0.003245805506594479 | 0.4857227070024237 | 4.579230984003516 |
| generation_gate | 58 | 28.97202659600589 | 81.33779611097998 | 135.66511810800876 |
| initial_validation | 58 | 0.0029285710043041036 | 0.5015194090083241 | 7.783282149990555 |
| post_security_validation | 58 | 0.0027053505036747083 | 0.5049400610150769 | 10.327813906013034 |
| security_iteration_verification | 178 | 13.584405852554482 | 39.876424685964594 | 53.0410041489813 |
| validation_repair_round | 69 | 14.519213959982153 | 43.3958706179983 | 101.1059277089953 |

Iteration outcomes: {'attempted_fix_iterations': 178, 'deadline_only_rollbacks': 12, 'deadline_before_candidate': 26, 'multiple_cause_deadline_rollbacks': 4, 'validity_regression_rollbacks': 24}.
Initialization: {'init_runs': 143, 'init_reused': 522, 'reinitializations': 13}.
Repair deadline stops (measured rounds): {'after_security': 2, 'before_security': 1}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 20, "median": 207.61536276699917, "p90": 406.40972391999094, "max": 444.8063853739877}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 309, "failures": 0, "missing_measurements": 0, "agents": {"architect": 20, "generator_cost": 20, "generator_performance": 20, "generator_security": 20, "security_iteration": 229}, "durations": {"count": 309, "median": 20.916285, "p90": 55.048274, "max": 145.043351}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:954, performance#1:819, security#1:712 | {} | {} |
| 2 | 3 | {"none": 3} | security#1:1531, cost#1:1587, performance#1:1721 | {} | {} |
| 3 | 4 | {"none": 4} | performance#1:1600, security#1:2165, cost#1:1645, cost#2:1682 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:1592, security#1:1929, performance#1:2227 | {} | {} |
| 5 | 3 | {"none": 3} | security#1:2000, performance#1:2283, cost#1:1776 | {} | {} |
| 6 | 3 | {"none": 3} | performance#1:2502, security#1:2050, cost#1:2135 | {} | {} |
| 7 | 3 | {"none": 3} | performance#1:3495, security#1:3787, cost#1:3496 | {} | {} |
| 8 | 5 | {"none": 5} | performance#1:1875, performance#2:2699, cost#1:2539, security#1:1805, security#2:2291 | {} | {} |
| 9 | 5 | {"none": 5} | security#1:3586, cost#1:3573, cost#2:3999, performance#1:4041, performance#2:3398 | {} | {} |
| 10 | 5 | {"none": 5} | cost#1:1045, cost#2:3189, security#1:3327, security#2:unknown, performance#1:4105 | {"security": "deadline"} | {} |
| 11 | 4 | {"none": 4} | security#1:3711, cost#1:2609, cost#2:4487, performance#1:4467 | {} | {} |
| 12 | 5 | {"none": 5} | security#1:1254, security#2:4593, performance#1:499, performance#2:unknown, cost#1:4437 | {"performance": "deadline"} | {} |
| 13 | 4 | {"none": 4} | performance#1:2787, cost#1:2142, security#1:1764, security#2:2717 | {} | {} |
| 14 | 3 | {"none": 3} | performance#1:324, security#1:3449, cost#1:4350 | {} | {} |
| 15 | 3 | {"none": 3} | cost#1:1925, security#1:2806, performance#1:2755 | {} | {} |
| 16 | 3 | {"none": 3} | security#1:2424, performance#1:2509, cost#1:2461 | {} | {} |
| 17 | 3 | {"none": 3} | cost#1:1908, security#1:2332, performance#1:1594 | {} | {} |
| 18 | 3 | {"none": 3} | performance#1:1110, security#1:1632, cost#1:1351 | {} | {} |
| 19 | 3 | {"none": 3} | cost#1:1361, security#1:1416, performance#1:1569 | {} | {} |
| 20 | 4 | {"none": 4} | security#1:742, performance#1:1210, cost#1:804, cost#2:unknown | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.049170; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.0096978, "remaining_credit_usd": 5.137647376, "planned_runs_remaining": 19, "run_cap_remaining": 19, "projected_further_runs": 19, "assumption": "Projection at first measured cost; fresh guard checks decide."}
