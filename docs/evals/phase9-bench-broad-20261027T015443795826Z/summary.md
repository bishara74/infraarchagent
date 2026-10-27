# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **7/60 (11.67%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 7/60; contextual-v1: 7/60; contextual-v2: 7/60. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 50 |
| checks_passed | 7 |
| scan_error | 3 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 47 |
| plan_conformance_conflict | 40 |
| validation_failed | 29 |
| validation_error | 2 |

| Failed check | Count |
|---|---:|
| terraform.validate: Invalid multi-line string | 76 |
| terraform.validate: Terraform configuration diagnostic | 20 |
| terraform.validate: Unsupported argument | 10 |
| helm.lint: helm optional lint failed (undefined_named_template) | 9 |
| ansible-lint.lint: ansible-lint optional lint failed | 6 |
| terraform.validate: Unsupported block type | 5 |
| grafana.panels: Dashboard requires panels | 4 |
| document.parse: Document could not be parsed | 1 |
| helm.lint: helm optional lint failed | 1 |
| terraform.validate: Missing required argument | 1 |

| Remaining blocking rule | Count |
|---|---:|
| TERRAFORM_SYNTAX | 78 |
| CKV_AWS_130 | 43 |
| AWS-0164 | 42 |
| AWS-0053 | 21 |
| CKV_AWS_91 | 20 |
| AWS-0104 | 17 |
| CKV2_AWS_12 | 17 |
| AWS-0178 | 16 |
| CKV2_AWS_11 | 16 |
| CKV_AWS_260 | 13 |
| CKV_AWS_18 | 11 |
| CKV_AWS_354 | 11 |
| CKV_AWS_378 | 10 |
| AWS-0039 | 10 |
| CKV_AWS_58 | 10 |
| AWS-0090 | 9 |
| CKV_AWS_21 | 9 |
| CKV_AWS_144 | 9 |
| AWS-0040 | 9 |
| AWS-0041 | 9 |

Final failure origins: {'security_fix': 2, 'generated': 129, 'unknown': 2}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Invalid index | 1 |
| after_security / rejected / invalid_patch | Missing required argument | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 1 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 3 |
| after_security / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| after_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 6 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 5 |
| after_security / rejected / no_improvement | Unsupported argument | 2 |
| after_security / rejected / no_improvement | Unsupported block type | 1 |
| after_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| after_security / rejected / no_improvement | helm optional lint failed | 1 |
| after_security / rejected / unknown | Dashboard requires panels | 1 |
| after_security / rejected / unknown | Document could not be parsed | 1 |
| after_security / rejected / unknown | Invalid multi-line string | 1 |
| after_security / rejected / unknown | Terraform configuration diagnostic | 5 |
| after_security / rejected / unknown | Unsupported argument | 6 |
| after_security / rejected / unknown | Unsupported block type | 2 |
| after_security / rejected / unknown | ansible-lint optional lint failed | 1 |
| after_security / rejected / unknown | helm optional lint failed (undefined_named_template) | 2 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Unsupported argument | 2 |
| before_security / rejected / invalid_patch | Dashboard requires panels | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| before_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 2 |
| before_security / rejected / new_blocking_findings | Dashboard requires panels | 2 |
| before_security / rejected / new_blocking_findings | Missing required argument | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| before_security / rejected / new_blocking_findings | Unsupported argument | 1 |
| before_security / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| before_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 6 |
| before_security / rejected / no_improvement | Invalid index | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 6 |
| before_security / rejected / no_improvement | Unsupported argument | 5 |
| before_security / rejected / no_improvement | Unsupported block type | 3 |
| before_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| before_security / rejected / no_improvement | helm optional lint failed | 1 |
| before_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 1 |
| before_security / rejected / unknown | Dashboard requires panels | 1 |
| before_security / rejected / unknown | Document could not be parsed | 1 |
| before_security / rejected / unknown | Invalid multi-line string | 1 |
| before_security / rejected / unknown | Terraform configuration diagnostic | 3 |
| before_security / rejected / unknown | Unsupported argument | 4 |
| before_security / rejected / unknown | Unsupported block type | 1 |
| before_security / rejected / unknown | ansible-lint optional lint failed | 1 |
| generation / accepted / improved | Missing required argument | 3 |
| generation / accepted / improved | Terraform configuration diagnostic | 1 |
| generation / accepted / improved | Unsupported argument | 6 |
| generation / rejected / invalid_patch | Dashboard requires panels | 2 |
| generation / rejected / invalid_patch | Generation syntax check failed | 3 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| generation / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| generation / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 3 |
| generation / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| generation / rejected / new_blocking_findings | Generation syntax check failed | 5 |
| generation / rejected / new_blocking_findings | Missing required argument | 1 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| generation / rejected / new_blocking_findings | Unsupported argument | 1 |
| generation / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 5 |
| generation / rejected / no_improvement | Generation syntax check failed | 1 |
| generation / rejected / no_improvement | Invalid index | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 4 |
| generation / rejected / no_improvement | Unsupported argument | 3 |
| generation / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| generation / rejected / no_improvement | helm optional lint failed | 1 |
| generation / rejected / unknown | Generation syntax check failed | 1 |
| generation / rejected / unknown | Terraform configuration diagnostic | 4 |
| generation / rejected / unknown | Unsupported argument | 7 |
| generation / rejected / unknown | Unsupported block type | 4 |
| generation / rejected / unknown | helm optional lint failed (undefined_named_template) | 1 |
| generation / stopped / round_limit | unknown | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 266 | 0.043688269000995206 | 0.3430919640013599 | 1.4470744840000407 |
| final_security_scan | 57 | 4.807926735000365 | 6.648831122001866 | 7.192321844999242 |
| final_validation | 57 | 0.0024199260005843826 | 0.5682211499988625 | 4.842178891998628 |
| generation_gate | 60 | 23.151915933498458 | 60.86892510100006 | 82.5313030920006 |
| initial_validation | 60 | 0.002615863999380963 | 1.1540499090006051 | 6.795099645998562 |
| post_security_validation | 57 | 0.002004486999794608 | 0.5877043219988991 | 4.482400854998559 |
| security_iteration_verification | 209 | 10.36174103400117 | 30.974273618998268 | 46.11025863699979 |
| validation_repair_round | 94 | 4.461297490501238 | 23.270130093998887 | 29.55127286000061 |

Iteration outcomes: {'attempted_fix_iterations': 209, 'deadline_only_rollbacks': 1, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 1, 'validity_regression_rollbacks': 6}.
Initialization: {'init_runs': 107, 'init_reused': 582, 'reinitializations': 5}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 60, 'packages_unknown': 0, 'init_runs': 121, 'init_reused': 821, 'reinitializations': 5, 'init_seconds': 620.4594235560035, 'validate_seconds': 1644.9474387930277}
Gate outcomes: {'invalid': 31, 'valid': 24, 'error': 5}
Init categories: {'validation_cached': 38, 'initialized': 14, 'mirror_constraint_unavailable': 2, 'syntax': 1, 'reused': 1, 'unknown': 1}
Schema context sizes (characters): {'generator': {'count': 60, 'median': 4484.5, 'p90': 4490, 'max': 4493}, 'repair': {'count': 96, 'median': 15925.0, 'p90': 15988, 'max': 15999}, 'security': {'count': 231, 'median': 7551, 'p90': 11671, 'max': 15974}, 'generator_schema_only': {'count': 60, 'median': 4484.5, 'p90': 4490, 'max': 4493}}
Schema guidance overflow: {'measured_packages': 60, 'overflow_packages': 30, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_cloudfront_distribution': 3, 'aws_dynamodb_table': 6, 'aws_ecs_task_definition': 12, 'aws_lb': 6, 'aws_lb_listener': 6, 'aws_ecs_service': 6, 'aws_instance': 3, 'aws_s3_bucket': 3}}}
Security context coverage: {'terraform': {'total': 206, 'positive': 206, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 202, 'unparseable_document': 4}}, 'other': {'total': 25, 'positive': 0, 'zero': 25, 'missing': 0, 'reasons': {'not_terraform': 25}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 7}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 5}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 25}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 5}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Invalid index', 'count': 4}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Invalid multi-line string', 'count': 4}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Missing required argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 27}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 27}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported block type', 'count': 9}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 74}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 10}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_verification_unavailable', 'error_class': 'unknown', 'count': 8}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 8 |
| 4+ | 11 |

Phase 9f measured/unknown packages: (60, 0)
Catalogue retained by rule: {'CKV2_AWS_12': 3, 'AWS-0177': 3, 'CKV_AWS_293': 3, 'AWS-0164': 7, 'CKV_AWS_130': 7, 'CKV_AWS_103': 3, 'CKV_K8S_23': 8, 'CKV_K8S_40': 8, 'KSV-0012': 8, 'KSV-0118': 8, 'KSV-0104': 8, 'CKV_K8S_10': 4, 'CKV_K8S_11': 4, 'CKV_K8S_12': 4, 'CKV_K8S_13': 4, 'CKV_K8S_20': 4, 'CKV_K8S_22': 4, 'CKV_K8S_31': 4, 'CKV_K8S_37': 4, 'KSV-0001': 4, 'KSV-0003': 4, 'KSV-0004': 4, 'KSV-0014': 4, 'KSV-0106': 4, 'AWS-0028': 3, 'AWS-0131': 3, 'CKV_AWS_8': 3}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 120}, {'template': 'access_logs', 'status': 'retained', 'count': 2}, {'template': 'flow_logs', 'status': 'rejected', 'count': 64}, {'template': 'flow_logs', 'status': 'retained', 'count': 13}, {'template': 'kms', 'status': 'rejected', 'count': 52}, {'template': 'kms', 'status': 'retained', 'count': 8}, {'template': 'kms', 'status': 'skipped', 'count': 13}]
Template introduced rules: {'CKV_AWS_145': 56, 'CKV_AWS_144': 28, 'CKV_AWS_18': 36, 'AWS-0132': 36}
Partial groups: {'unevaluated': 8, 'discarded': 236, 'kept': 90}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 50, 'regeneration': 3, 'unresolved': 1, 'syntax_round_1': 4, 'syntax_round_2': 1, 'normalization': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 60, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 231, 'median': 3, 'p90': 7, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 266 | 0.043688269000995206 | 0.3430919640013599 | 1.4470744840000407 |
| final_security_scan | 57 | 4.807926735000365 | 6.648831122001866 | 7.192321844999242 |
| final_validation | 57 | 0.0024199260005843826 | 0.5682211499988625 | 4.842178891998628 |
| generation_gate | 60 | 23.151915933498458 | 60.86892510100006 | 82.5313030920006 |
| initial_validation | 60 | 0.002615863999380963 | 1.1540499090006051 | 6.795099645998562 |
| post_security_validation | 57 | 0.002004486999794608 | 0.5877043219988991 | 4.482400854998559 |
| security_iteration_verification | 209 | 10.36174103400117 | 30.974273618998268 | 46.11025863699979 |
| validation_repair_round | 94 | 4.461297490501238 | 23.270130093998887 | 29.55127286000061 |

Iteration outcomes: {'attempted_fix_iterations': 209, 'deadline_only_rollbacks': 1, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 1, 'validity_regression_rollbacks': 6}.
Initialization: {'init_runs': 107, 'init_reused': 582, 'reinitializations': 5}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 20, "median": 139.87659622549836, "p90": 218.34925421400112, "max": 255.032373602}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 349, "failures": 0, "missing_measurements": 0, "agents": {"architect": 20, "generator_performance": 20, "generator_cost": 20, "generator_security": 20, "security_iteration": 269}, "durations": {"count": 349, "median": 12.595396, "p90": 41.167767, "max": 84.575045}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | performance#1:810, cost#1:674, security#1:1267 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:1680, security#1:1695, performance#1:1872 | {} | {} |
| 3 | 3 | {"none": 3} | performance#1:980, security#1:1725, cost#1:1730 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:1944, security#1:1448, performance#1:2251 | {} | {} |
| 5 | 3 | {"none": 3} | performance#1:1946, security#1:1568, cost#1:2278 | {} | {} |
| 6 | 3 | {"none": 3} | cost#1:2455, performance#1:3386, security#1:3222 | {} | {} |
| 7 | 4 | {"none": 4} | performance#1:2734, security#1:4987, security#2:3763, cost#1:3295 | {} | {} |
| 8 | 4 | {"none": 4} | performance#1:3835, cost#1:2252, cost#2:2569, security#1:3359 | {} | {} |
| 9 | 7 | {"none": 7} | performance#1:3891, cost#1:3189, cost#2:2672, cost#3:4159, security#1:3793, security#2:3769, security#3:4222 | {} | {} |
| 10 | 6 | {"none": 6} | cost#1:3928, cost#2:3372, performance#1:2629, performance#2:2782, performance#3:4141, security#1:4257 | {} | {} |
| 11 | 4 | {"none": 4} | performance#1:4718, security#1:5142, cost#1:2734, cost#2:4351 | {} | {} |
| 12 | 3 | {"none": 3} | performance#1:3358, security#1:4196, cost#1:3979 | {} | {} |
| 13 | 7 | {"none": 7} | cost#1:2631, performance#1:1860, performance#2:1759, performance#3:1649, security#1:2116, security#2:2196, security#3:2871 | {} | {} |
| 14 | 4 | {"none": 4} | security#1:3169, cost#1:3137, cost#2:2123, performance#1:3428 | {} | {} |
| 15 | 3 | {"none": 3} | security#1:2795, performance#1:2522, cost#1:2085 | {} | {} |
| 16 | 3 | {"none": 3} | performance#1:3048, security#1:2588, cost#1:1576 | {} | {} |
| 17 | 3 | {"none": 3} | security#1:2105, cost#1:2749, performance#1:2041 | {} | {} |
| 18 | 3 | {"none": 3} | cost#1:1623, performance#1:1585, security#1:2013 | {} | {} |
| 19 | 4 | {"none": 4} | cost#1:1269, security#1:1842, performance#1:1407, performance#2:1396 | {} | {} |
| 20 | 3 | {"none": 3} | cost#1:776, performance#1:750, security#1:1146 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.665574; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.0198079, "remaining_credit_usd": 5.661391996, "planned_runs_remaining": 19, "run_cap_remaining": 19, "projected_further_runs": 19, "assumption": "Projection at first measured cost; fresh guard checks decide."}
