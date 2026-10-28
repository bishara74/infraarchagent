# Phase 9 benchmark

Status: **INCOMPLETE**

Mode: real

Checks-passed rate among generated packages: **8/27 (29.63%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 8/27; contextual-v1: 8/27; contextual-v2: 8/27. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 19 |
| checks_passed | 8 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 13 |
| validation_failed | 12 |
| validation_error | 1 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 6 |
| helm.lint: helm optional lint failed (undefined_named_template) | 5 |
| terraform.validate: Unsupported argument | 3 |
| ansible-lint.lint: ansible-lint optional lint failed | 3 |
| terraform.validate: Unsupported block type | 1 |
| grafana.panels: Dashboard requires panels | 1 |
| helm.lint: helm optional lint failed | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0053 | 11 |
| CKV_AWS_91 | 10 |
| CKV_AWS_260 | 4 |
| AWS-0164 | 3 |
| CKV_AWS_130 | 3 |
| AWS-0010 | 2 |
| AWS-0011 | 2 |
| CKV_AWS_18 | 2 |
| CKV2_AWS_12 | 2 |
| AWS-0065 | 1 |
| CKV_AWS_144 | 1 |
| AWS-0052 | 1 |
| AWS-0104 | 1 |
| CKV_AWS_157 | 1 |

Final failure origins: {'generated': 19, 'security_fix': 1}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 1 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| after_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| after_security / rejected / new_blocking_findings | Unsupported argument | 1 |
| after_security / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| after_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 5 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 4 |
| after_security / rejected / no_improvement | Unsupported argument | 2 |
| after_security / rejected / no_improvement | Unsupported block type | 1 |
| before_security / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| before_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 3 |
| before_security / rejected / no_improvement | Dashboard requires panels | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 5 |
| before_security / rejected / no_improvement | Unsupported argument | 3 |
| before_security / rejected / no_improvement | Unsupported block type | 1 |
| before_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| before_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 2 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Unsupported argument | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 1 |
| generation / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| generation / rejected / new_blocking_findings | Generation syntax check failed | 5 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| generation / rejected / new_blocking_findings | Unsupported argument | 1 |
| generation / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| generation / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 5 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported argument | 2 |
| generation / rejected / no_improvement | Unsupported block type | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 96 | 0.04818433299806202 | 0.32929337199311703 | 0.7535321940085851 |
| final_security_scan | 27 | 5.112212241001544 | 6.908193035997101 | 7.439411001992994 |
| final_validation | 27 | 0.0024136400024872273 | 3.6462932430004003 | 6.732214613002725 |
| generation_gate | 27 | 33.804367916993215 | 69.21609928099497 | 88.26856716799375 |
| initial_validation | 27 | 0.0024041629949351773 | 4.662865378995775 | 5.79240371499327 |
| post_security_validation | 27 | 0.0020818670018343255 | 4.020202190004056 | 5.0530421680014115 |
| security_iteration_verification | 75 | 24.13535671203863 | 44.13443184700736 | 50.657150279017515 |
| validation_repair_round | 37 | 6.780244873996708 | 24.370110532996478 | 30.324100017998717 |

Iteration outcomes: {'attempted_fix_iterations': 75, 'deadline_only_rollbacks': 4, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 2, 'validity_regression_rollbacks': 7}.
Initialization: {'init_runs': 36, 'init_reused': 336, 'reinitializations': 5}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 27, 'packages_unknown': 0, 'init_runs': 42, 'init_reused': 449, 'reinitializations': 7, 'init_seconds': 307.98086302498996, 'validate_seconds': 1067.875124668979}
Gate outcomes: {'valid': 14, 'invalid': 12, 'error': 1}
Init categories: {'validation_cached': 19, 'initialized': 7, 'mirror_constraint_unavailable': 1}
Schema context sizes (characters): {'generator': {'count': 27, 'median': 4483, 'p90': 4490, 'max': 4490}, 'repair': {'count': 37, 'median': 15945, 'p90': 16000, 'max': 16000}, 'security': {'count': 72, 'median': 8709.5, 'p90': 12299, 'max': 15959}, 'generator_schema_only': {'count': 27, 'median': 4483, 'p90': 4490, 'max': 4490}}
Schema guidance overflow: {'measured_packages': 27, 'overflow_packages': 15, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_s3_bucket': 3, 'aws_dynamodb_table': 3, 'aws_ecs_task_definition': 6, 'aws_lb': 3, 'aws_lb_listener': 3, 'aws_ecs_service': 3, 'aws_instance': 3}}}
Security context coverage: {'terraform': {'total': 69, 'positive': 69, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 69}}, 'other': {'total': 3, 'positive': 0, 'zero': 3, 'missing': 0, 'reasons': {'not_terraform': 3}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 10}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 21}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 15}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'security_control_removed', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'security_control_removed', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'security_control_removed,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared resource', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 4 |
| 4+ | 2 |

Phase 9f measured/unknown packages: (27, 0)
Catalogue retained by rule: {'AWS-0164': 7, 'CKV_AWS_130': 7, 'CKV2_AWS_12': 2, 'CKV_AWS_103': 3, 'AWS-0028': 6, 'AWS-0131': 6, 'CKV_AWS_8': 6}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 57}, {'template': 'access_logs', 'status': 'retained', 'count': 2}, {'template': 'flow_logs', 'status': 'rejected', 'count': 1}, {'template': 'flow_logs', 'status': 'retained', 'count': 14}, {'template': 'kms', 'status': 'rejected', 'count': 2}, {'template': 'kms', 'status': 'retained', 'count': 9}]
Template introduced rules: {'CKV_AWS_145': 45, 'CKV_AWS_144': 24, 'CKV_AWS_18': 44, 'AWS-0132': 44}
Partial groups: {'discarded': 39, 'kept': 16, 'unevaluated': 2}
Existing-file proposal recovery: {'normalized': 1, 'retained': 1}
Generation syntax recovery: {'unchanged': 26, 'regeneration': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 27, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 72, 'median': 3.0, 'p90': 4, 'max': 9}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 101 | 0.04858866300492082 | 0.32929337199311703 | 0.8348691899882397 |
| final_security_scan | 27 | 5.112212241001544 | 6.908193035997101 | 7.439411001992994 |
| final_validation | 27 | 0.0024136400024872273 | 3.6462932430004003 | 6.732214613002725 |
| generation_gate | 30 | 34.17803151749831 | 75.22445731400512 | 88.26856716799375 |
| initial_validation | 30 | 0.0026607900072121993 | 0.4166512719966704 | 5.79240371499327 |
| post_security_validation | 27 | 0.0020818670018343255 | 4.020202190004056 | 5.0530421680014115 |
| security_iteration_verification | 79 | 24.58856697398005 | 44.32967470699805 | 50.657150279017515 |
| validation_repair_round | 43 | 7.728986249989248 | 24.701556312997127 | 30.324100017998717 |

Iteration outcomes: {'attempted_fix_iterations': 79, 'deadline_only_rollbacks': 6, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 2, 'validity_regression_rollbacks': 7}.
Initialization: {'init_runs': 39, 'init_reused': 368, 'reinitializations': 5}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: not_started=10 (excluded from failures and measurements).

pr01: {"count": 9, "median": 166.635905076997, "p90": 329.9442089189979, "max": 329.9442089189979}; failed/incomplete: 1.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 146, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_security": 10, "generator_performance": 10, "generator_cost": 10, "security_iteration": 106}, "durations": {"count": 146, "median": 23.0947525, "p90": 55.060931, "max": 92.728405}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:874, performance#1:857, cost#1:768 | {} | {} |
| 2 | 3 | {"none": 3} | security#1:1348, performance#1:1342, cost#1:1488 | {} | {} |
| 3 | 3 | {"none": 3} | security#1:2239, performance#1:1617, cost#1:1298 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:1911, security#1:2530, performance#1:2231 | {} | {} |
| 5 | 3 | {"none": 3} | security#1:2017, cost#1:1884, performance#1:2419 | {} | {} |
| 6 | 3 | {"none": 3} | security#1:2091, performance#1:2883, cost#1:2051 | {} | {} |
| 7 | 3 | {"none": 3} | cost#1:1924, performance#1:3372, security#1:2656 | {} | {} |
| 8 | 5 | {"none": 5} | cost#1:2774, security#1:3224, performance#1:2092, performance#2:1677, performance#3:3919 | {} | {} |
| 9 | 5 | {"none": 5} | performance#1:3113, performance#2:4481, performance#3:4748, security#1:4688, cost#1:4055 | {} | {} |
| 10 | 7 | {"none": 7} | security#1:3518, performance#1:3636, performance#2:1733, performance#3:5074, cost#1:2334, cost#2:2343, cost#3:3771 | {"run": "observation_incomplete"} | {} |
| 11 | unknown | null | unknown | {} | {} |
| 12 | unknown | null | unknown | {} | {} |
| 13 | unknown | null | unknown | {} | {} |
| 14 | unknown | null | unknown | {} | {} |
| 15 | unknown | null | unknown | {} | {} |
| 16 | unknown | null | unknown | {} | {} |
| 17 | unknown | null | unknown | {} | {} |
| 18 | unknown | null | unknown | {} | {} |
| 19 | unknown | null | unknown | {} | {} |
| 20 | unknown | null | unknown | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.582346; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.01780255, "remaining_credit_usd": 5.796721276, "planned_runs_remaining": 19, "run_cap_remaining": 19, "projected_further_runs": 19, "assumption": "Projection at first measured cost; fresh guard checks decide."}

Stopped: Run could not be observed to confirmed settlement.
