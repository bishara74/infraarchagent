# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **0/8 (0.00%)**.
Legacy labels mapped: 0. Missing variants: 1; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 0/8; contextual-v1: 0/8; contextual-v2: 1/8. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 8 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 7 |
| validation_failed | 2 |

| Failed check | Count |
|---|---:|
| promtool.lint: promtool optional lint failed | 1 |
| terraform.validate: Unsupported argument | 1 |
| document.parse: Document could not be parsed | 1 |
| terraform.validate: Invalid single-argument block definition | 1 |
| terraform.validate: Terraform configuration diagnostic | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0164 | 8 |
| CKV_AWS_130 | 7 |
| AWS-0053 | 6 |
| CKV_AWS_91 | 4 |
| AWS-0104 | 4 |
| CKV2_AWS_12 | 3 |
| KSV-0125 | 2 |
| TERRAFORM_SYNTAX | 2 |
| AWS-0039 | 1 |
| AWS-0040 | 1 |
| AWS-0041 | 1 |
| AWS-0054 | 1 |
| AWS-0130 | 1 |
| CKV2_AWS_20 | 1 |
| CKV_AWS_103 | 1 |
| CKV_AWS_2 | 1 |
| CKV_AWS_260 | 1 |
| CKV_AWS_378 | 1 |
| CKV_AWS_38 | 1 |
| CKV_AWS_39 | 1 |

Final failure origins: {'generated': 5}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / no_improvement | Document could not be parsed | 1 |
| after_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 1 |
| after_security / rejected / no_improvement | promtool optional lint failed | 1 |
| before_security / rejected / no_improvement | Document could not be parsed | 1 |
| before_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| before_security / rejected / no_improvement | Unsupported argument | 1 |
| before_security / rejected / no_improvement | promtool optional lint failed | 1 |
| generation / accepted / improved | Generation syntax check failed | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 1 |
| generation / accepted / improved | Unresolved bare proxy_pass target in nginx/nginx.conf:19 | 1 |
| generation / accepted / improved | helm optional lint failed | 1 |
| generation / rejected / no_improvement | Unsupported argument | 1 |
| generation / rejected / no_improvement | promtool optional lint failed | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 33 | 0.13408192100177985 | 0.8887384330009809 | 2.5089137940085493 |
| final_security_scan | 8 | 11.858015731995692 | 25.560938716007513 | 25.560938716007513 |
| final_validation | 8 | 0.2197998275005375 | 0.7878654999949504 | 0.7878654999949504 |
| generation_gate | 8 | 78.77236371349863 | 102.71265463600866 | 102.71265463600866 |
| initial_validation | 8 | 0.23886712749663275 | 0.9053429269988555 | 0.9053429269988555 |
| post_security_validation | 8 | 0.6836690674972488 | 6.539911990999826 | 6.539911990999826 |
| security_iteration_verification | 32 | 37.90917786250793 | 51.512120527011575 | 54.39134953900066 |
| validation_repair_round | 7 | 14.242570856993552 | 36.47394438300398 | 36.47394438300398 |

Iteration outcomes: {'attempted_fix_iterations': 32, 'deadline_only_rollbacks': 13, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 2, 'validity_regression_rollbacks': 5}.
Initialization: {'init_runs': 16, 'init_reused': 116, 'reinitializations': 4}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 8, 'packages_unknown': 0, 'init_runs': 23, 'init_reused': 139, 'reinitializations': 6, 'init_seconds': 265.20771374501055, 'validate_seconds': 627.9601166480134}
Gate outcomes: {'valid': 6, 'invalid': 2}
Init categories: {'initialized': 2, 'validation_cached': 5, 'syntax': 1}
Schema context sizes (characters): {'generator': {'count': 8, 'median': 4468.0, 'p90': 4473, 'max': 4473}, 'repair': {'count': 7, 'median': 15924, 'p90': 15989, 'max': 15989}, 'security': {'count': 46, 'median': 2111.0, 'p90': 15940, 'max': 15992}, 'generator_schema_only': {'count': 8, 'median': 4468.0, 'p90': 4473, 'max': 4473}}
Schema guidance overflow: {'measured_packages': 8, 'overflow_packages': 8, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_ecs_service': 5, 'aws_ecs_task_definition': 5, 'aws_lb_listener': 5, 'aws_launch_template': 2, 'aws_db_instance': 2, 'aws_instance': 5, 'aws_s3_bucket': 2, 'aws_lb': 3}}}
Security context coverage: {'terraform': {'total': 25, 'positive': 25, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 21, 'unparseable_document': 4}}, 'other': {'total': 21, 'positive': 0, 'zero': 21, 'missing': 0, 'reasons': {'not_terraform': 21}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 8}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 15}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported attribute', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported attribute', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 1 |
| 2-3 | 1 |
| 4+ | 4 |

Phase 9f measured/unknown packages: (8, 0)
Catalogue retained by rule: {'AWS-0164': 2, 'CKV_AWS_130': 2, 'AWS-0028': 3, 'CKV_AWS_103': 2, 'AWS-0077': 1, 'AWS-0038': 2, 'CKV_AWS_38': 2}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 24}, {'template': 'access_logs', 'status': 'retained', 'count': 1}, {'template': 'flow_logs', 'status': 'rejected', 'count': 3}, {'template': 'flow_logs', 'status': 'retained', 'count': 6}, {'template': 'kms', 'status': 'rejected', 'count': 1}, {'template': 'kms', 'status': 'retained', 'count': 2}]
Template introduced rules: {'CKV_AWS_18': 18, 'AWS-0132': 18, 'CKV_AWS_145': 15, 'CKV_AWS_144': 11}
Partial groups: {'kept': 6, 'unevaluated': 4, 'discarded': 4}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 5, 'syntax_round_1': 1, 'unresolved': 1, 'syntax_round_2': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 8, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 46, 'median': 2.0, 'p90': 3, 'max': 7}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 33 | 0.13408192100177985 | 0.8887384330009809 | 2.5089137940085493 |
| final_security_scan | 8 | 11.858015731995692 | 25.560938716007513 | 25.560938716007513 |
| final_validation | 8 | 0.2197998275005375 | 0.7878654999949504 | 0.7878654999949504 |
| generation_gate | 8 | 78.77236371349863 | 102.71265463600866 | 102.71265463600866 |
| initial_validation | 8 | 0.23886712749663275 | 0.9053429269988555 | 0.9053429269988555 |
| post_security_validation | 8 | 0.6836690674972488 | 6.539911990999826 | 6.539911990999826 |
| security_iteration_verification | 32 | 37.90917786250793 | 51.512120527011575 | 54.39134953900066 |
| validation_repair_round | 7 | 14.242570856993552 | 36.47394438300398 | 36.47394438300398 |

Iteration outcomes: {'attempted_fix_iterations': 32, 'deadline_only_rollbacks': 13, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 2, 'validity_regression_rollbacks': 5}.
Initialization: {'init_runs': 16, 'init_reused': 116, 'reinitializations': 4}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 3, "median": 358.18742774000566, "p90": 359.24406198399083, "max": 359.24406198399083}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 49, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_security": 3, "generator_cost": 3, "generator_performance": 3, "security_iteration": 37}, "durations": {"count": 49, "median": 52.154393, "p90": 78.781619, "max": 108.381238}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:3259, cost#1:2821, performance#1:3605 | {} | {} |
| 2 | 5 | {"none": 5} | performance#1:4953, performance#2:3901, performance#3:4963, security#1:7408, cost#1:5786 | {"performance": "incomplete_package"} | {} |
| 3 | 8 | {"none": 8} | performance#1:5374, performance#2:3962, cost#1:3676, cost#2:3214, cost#3:4162, security#1:2634, security#2:3316, security#3:4314 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.359774; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.08206915, "remaining_credit_usd": 3.347730646, "planned_runs_remaining": 2, "run_cap_remaining": 2, "projected_further_runs": 2, "assumption": "Projection at first measured cost; fresh guard checks decide."}
