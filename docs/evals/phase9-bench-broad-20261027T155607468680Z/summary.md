# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **11/59 (18.64%)**.
Legacy labels mapped: 0. Missing variants: 1; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 11/59; contextual-v1: 11/59; contextual-v2: 12/59. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 48 |
| checks_passed | 11 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 38 |
| validation_failed | 29 |
| plan_conformance_conflict | 16 |
| validation_error | 5 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 18 |
| terraform.validate: Unsupported argument | 11 |
| helm.lint: helm optional lint failed (undefined_named_template) | 8 |
| terraform.validate: Missing required argument | 7 |
| terraform.validate: Unsupported block type | 3 |
| terraform.validate: Unsupported attribute | 2 |
| grafana.panels: Dashboard requires panels | 2 |
| document.parse: Document could not be parsed | 2 |
| terraform.validate: Cycle | 1 |
| terraform.local_module: Local module unavailable: local_module_missing | 1 |
| terraform.local_module: Local module source must exist inside the package | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0053 | 19 |
| CKV_AWS_91 | 18 |
| AWS-0164 | 14 |
| CKV_AWS_130 | 14 |
| CKV_AWS_260 | 13 |
| AWS-0104 | 9 |
| CKV_AWS_18 | 8 |
| AWS-0039 | 8 |
| CKV_AWS_58 | 8 |
| KSV-0125 | 8 |
| CKV_AWS_378 | 7 |
| CKV_AWS_144 | 6 |
| CKV2_AWS_20 | 6 |
| TERRAFORM_FILE_INPUT | 5 |
| AWS-0054 | 5 |
| CKV_AWS_103 | 5 |
| CKV_AWS_2 | 5 |
| AWS-0040 | 5 |
| AWS-0041 | 5 |
| CKV_AWS_38 | 5 |

Final failure origins: {'generated': 53, 'unknown': 1, 'security_fix': 1, 'repair': 1}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Missing required argument | 1 |
| after_security / accepted / improved | Terraform configuration diagnostic | 1 |
| after_security / rejected / invalid_patch | Document could not be parsed | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / invalid_patch | Unsupported attribute | 1 |
| after_security / rejected / invalid_patch | Unsupported block type | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 2 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| after_security / rejected / new_blocking_findings | Missing required argument | 2 |
| after_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| after_security / rejected / new_blocking_findings | Unsupported argument | 2 |
| after_security / rejected / new_blocking_findings | Unsupported attribute | 1 |
| after_security / rejected / new_blocking_findings | Unsupported block type | 1 |
| after_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 3 |
| after_security / rejected / no_improvement | Cycle | 1 |
| after_security / rejected / no_improvement | Document could not be parsed | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 8 |
| after_security / rejected / no_improvement | Unsupported argument | 6 |
| after_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 2 |
| after_security / rejected / unknown | Dashboard requires panels | 1 |
| after_security / rejected / unknown | Local module source must exist inside the package | 1 |
| after_security / rejected / unknown | Local module unavailable: local_module_missing | 1 |
| after_security / rejected / unknown | Missing required argument | 1 |
| after_security / rejected / unknown | Terraform configuration diagnostic | 2 |
| after_security / rejected / unknown | Unsupported argument | 2 |
| after_security / rejected / unknown | Unsupported block type | 1 |
| after_security / rejected / unknown | helm optional lint failed (undefined_named_template) | 1 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | Missing required argument | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | Unsupported attribute | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 1 |
| before_security / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| before_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| before_security / rejected / new_blocking_findings | Missing required argument | 2 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 3 |
| before_security / rejected / new_blocking_findings | Unsupported argument | 2 |
| before_security / rejected / new_blocking_findings | Unsupported attribute | 1 |
| before_security / rejected / new_blocking_findings | Unsupported block type | 1 |
| before_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 6 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 8 |
| before_security / rejected / no_improvement | Unsupported argument | 7 |
| before_security / rejected / unknown | Dashboard requires panels | 1 |
| before_security / rejected / unknown | Document could not be parsed | 1 |
| before_security / rejected / unknown | Local module source must exist inside the package | 1 |
| before_security / rejected / unknown | Local module unavailable: local_module_missing | 1 |
| before_security / rejected / unknown | Missing required argument | 1 |
| before_security / rejected / unknown | Terraform configuration diagnostic | 3 |
| before_security / rejected / unknown | Unsupported argument | 1 |
| before_security / rejected / unknown | Unsupported block type | 2 |
| before_security / rejected / unknown | helm optional lint failed (undefined_named_template) | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 1 |
| generation / accepted / improved | Unsupported argument | 8 |
| generation / rejected / invalid_patch | Generation syntax check failed | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 1 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 1 |
| generation / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| generation / rejected / new_blocking_findings | Generation syntax check failed | 5 |
| generation / rejected / new_blocking_findings | Missing required argument | 2 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| generation / rejected / new_blocking_findings | Unsupported argument | 2 |
| generation / rejected / new_blocking_findings | Unsupported attribute | 1 |
| generation / rejected / new_blocking_findings | Unsupported block type | 1 |
| generation / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 5 |
| generation / rejected / no_improvement | Missing required argument | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 10 |
| generation / rejected / no_improvement | Unsupported argument | 4 |
| generation / rejected / no_improvement | Unsupported block type | 1 |
| generation / rejected / unknown | Dashboard requires panels | 1 |
| generation / rejected / unknown | Generation syntax check failed | 1 |
| generation / rejected / unknown | Local module source must exist inside the package | 1 |
| generation / rejected / unknown | Local module unavailable: local_module_missing | 1 |
| generation / rejected / unknown | Missing required argument | 1 |
| generation / rejected / unknown | Terraform configuration diagnostic | 1 |
| generation / rejected / unknown | Unsupported argument | 3 |
| generation / rejected / unknown | Unsupported block type | 1 |
| generation / rejected / unknown | helm optional lint failed (undefined_named_template) | 1 |
| generation / stopped / round_limit | unknown | 2 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 241 | 0.05343327899754513 | 0.302122724999208 | 1.0090924219985027 |
| final_security_scan | 59 | 5.418493817000126 | 7.358987217005051 | 8.329802018997725 |
| final_validation | 59 | 0.002879302999645006 | 0.4343068200032576 | 8.07461249899643 |
| generation_gate | 59 | 23.304578514005698 | 54.17191894300049 | 82.78743930099881 |
| initial_validation | 59 | 0.002738318005867768 | 0.46959008700650884 | 0.694833389003179 |
| post_security_validation | 59 | 0.002539144996262621 | 0.4997894729967811 | 5.261409177001042 |
| security_iteration_verification | 188 | 16.819059643497894 | 44.000427805985964 | 52.30111891200795 |
| validation_repair_round | 93 | 6.054859276999196 | 19.47405761599657 | 38.755549205001444 |

Iteration outcomes: {'attempted_fix_iterations': 188, 'deadline_only_rollbacks': 3, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 9, 'validity_regression_rollbacks': 14}.
Initialization: {'init_runs': 91, 'init_reused': 595, 'reinitializations': 13}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 59, 'packages_unknown': 0, 'init_runs': 111, 'init_reused': 813, 'reinitializations': 14, 'init_seconds': 491.3028471570142, 'validate_seconds': 1955.4691062200945}
Gate outcomes: {'error': 5, 'invalid': 30, 'valid': 24}
Init categories: {'reused': 1, 'validation_cached': 37, 'initialized': 12, 'unknown': 2, 'syntax': 1}
Schema context sizes (characters): {'generator': {'count': 59, 'median': 4485, 'p90': 4496, 'max': 4496}, 'repair': {'count': 96, 'median': 15956.0, 'p90': 15992, 'max': 15999}, 'security': {'count': 217, 'median': 7800, 'p90': 12358, 'max': 15945}, 'generator_schema_only': {'count': 59, 'median': 4485, 'p90': 4496, 'max': 4496}}
Schema guidance overflow: {'measured_packages': 59, 'overflow_packages': 29, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_cloudfront_distribution': 6, 'aws_dynamodb_table': 6, 'aws_ecs_task_definition': 11, 'aws_lb': 6, 'aws_lb_listener': 6, 'aws_ecs_service': 6, 'aws_instance': 3}}}
Security context coverage: {'terraform': {'total': 178, 'positive': 177, 'zero': 1, 'missing': 0, 'reasons': {'schema_available': 177, 'not_attempted': 1}}, 'other': {'total': 39, 'positive': 0, 'zero': 39, 'missing': 0, 'reasons': {'not_terraform': 39}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 5}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 15}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 13}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 35}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Cycle', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Local module unavailable: local_module_missing', 'count': 3}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Missing required argument', 'count': 6}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 15}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 13}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 5}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported block type', 'count': 4}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 19}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 13}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Local module unavailable: local_module_missing', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'reference_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Cycle', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid resource type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_verification_unavailable', 'error_class': 'unknown', 'count': 17}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 1 |
| 2-3 | 7 |
| 4+ | 6 |

Phase 9f measured/unknown packages: (59, 0)
Catalogue retained by rule: {'AWS-0164': 16, 'CKV_AWS_130': 16, 'CKV2_AWS_12': 4, 'CKV_K8S_23': 12, 'CKV_K8S_40': 12, 'KSV-0012': 12, 'KSV-0118': 12, 'KSV-0104': 12, 'CKV_K8S_10': 6, 'CKV_K8S_11': 6, 'CKV_K8S_12': 6, 'CKV_K8S_13': 6, 'CKV_K8S_20': 6, 'CKV_K8S_22': 6, 'CKV_K8S_31': 6, 'CKV_K8S_37': 6, 'KSV-0001': 6, 'KSV-0003': 6, 'KSV-0004': 6, 'KSV-0014': 6, 'KSV-0106': 6, 'AWS-0131': 1, 'CKV_AWS_8': 2, 'CKV_AWS_103': 4, 'AWS-0176': 1, 'CKV_AWS_161': 1}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 97}, {'template': 'access_logs', 'status': 'retained', 'count': 5}, {'template': 'access_logs', 'status': 'skipped', 'count': 4}, {'template': 'flow_logs', 'status': 'rejected', 'count': 2}, {'template': 'flow_logs', 'status': 'retained', 'count': 30}, {'template': 'kms', 'status': 'rejected', 'count': 4}, {'template': 'kms', 'status': 'retained', 'count': 17}, {'template': 'kms', 'status': 'skipped', 'count': 7}]
Template introduced rules: {'CKV_AWS_145': 69, 'CKV_AWS_144': 36, 'CKV_AWS_18': 64, 'AWS-0132': 64}
Partial groups: {'discarded': 138, 'unevaluated': 23, 'kept': 52}
Existing-file proposal recovery: {'normalized': 1, 'retained': 0}
Generation syntax recovery: {'unchanged': 46, 'syntax_round_1': 3, 'regeneration': 4, 'normalization': 3, 'unresolved': 2, 'syntax_round_2': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 59, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 216, 'median': 2.0, 'p90': 5, 'max': 9}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 241 | 0.05343327899754513 | 0.302122724999208 | 1.0090924219985027 |
| final_security_scan | 59 | 5.418493817000126 | 7.358987217005051 | 8.329802018997725 |
| final_validation | 59 | 0.002879302999645006 | 0.4343068200032576 | 8.07461249899643 |
| generation_gate | 59 | 23.304578514005698 | 54.17191894300049 | 82.78743930099881 |
| initial_validation | 59 | 0.002738318005867768 | 0.46959008700650884 | 0.694833389003179 |
| post_security_validation | 59 | 0.002539144996262621 | 0.4997894729967811 | 5.261409177001042 |
| security_iteration_verification | 188 | 16.819059643497894 | 44.000427805985964 | 52.30111891200795 |
| validation_repair_round | 93 | 6.054859276999196 | 19.47405761599657 | 38.755549205001444 |

Iteration outcomes: {'attempted_fix_iterations': 188, 'deadline_only_rollbacks': 3, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 9, 'validity_regression_rollbacks': 14}.
Initialization: {'init_runs': 91, 'init_reused': 595, 'reinitializations': 13}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 20, "median": 167.30264254600115, "p90": 288.3524375180059, "max": 295.9410424950038}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 326, "failures": 0, "missing_measurements": 0, "agents": {"architect": 20, "generator_security": 20, "generator_cost": 20, "generator_performance": 20, "security_iteration": 246}, "durations": {"count": 326, "median": 13.9398265, "p90": 50.91756, "max": 86.830309}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:1584, cost#1:1438, performance#1:1218 | {} | {} |
| 2 | 3 | {"none": 3} | security#1:1474, cost#1:1559, performance#1:1903 | {} | {} |
| 3 | 3 | {"none": 3} | performance#1:1220, cost#1:1617, security#1:1914 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:1539, security#1:2317, performance#1:2297 | {} | {} |
| 5 | 3 | {"none": 3} | performance#1:2137, security#1:2200, cost#1:2270 | {} | {} |
| 6 | 3 | {"none": 3} | cost#1:2229, security#1:2393, performance#1:2574 | {} | {} |
| 7 | 3 | {"none": 3} | performance#1:3139, security#1:2081, cost#1:2769 | {} | {} |
| 8 | 6 | {"none": 6} | cost#1:2284, cost#2:2891, performance#1:2675, security#1:2490, security#2:3348, security#3:3615 | {} | {} |
| 9 | 5 | {"none": 5} | cost#1:4143, performance#1:4369, security#1:3623, security#2:3770, security#3:4154 | {} | {} |
| 10 | 7 | {"none": 7} | performance#1:2942, performance#2:3206, performance#3:3096, cost#1:3961, cost#2:4292, security#1:2794, security#2:3857 | {} | {} |
| 11 | 5 | {"none": 5} | cost#1:4844, cost#2:3406, security#1:4864, security#2:2828, performance#1:3658 | {} | {} |
| 12 | 5 | {"none": 5} | performance#1:4580, performance#2:4226, performance#3:3930, cost#1:4894, security#1:3986 | {"performance": "incomplete_package"} | {} |
| 13 | 4 | {"none": 4} | cost#1:3351, security#1:2626, security#2:3375, performance#1:3545 | {} | {} |
| 14 | 3 | {"none": 3} | cost#1:3578, performance#1:3045, security#1:3253 | {} | {} |
| 15 | 3 | {"none": 3} | performance#1:2789, security#1:2123, cost#1:2378 | {} | {} |
| 16 | 4 | {"none": 4} | security#1:2596, cost#1:2377, performance#1:2082, performance#2:2386 | {} | {} |
| 17 | 4 | {"none": 4} | performance#1:1855, cost#1:1739, security#1:1856, security#2:2121 | {} | {} |
| 18 | 3 | {"none": 3} | cost#1:1493, performance#1:2053, security#1:1824 | {} | {} |
| 19 | 3 | {"none": 3} | performance#1:1259, cost#1:1625, security#1:1387 | {} | {} |
| 20 | 3 | {"none": 3} | performance#1:1425, cost#1:1791, security#1:2269 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.554777; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.02360736, "remaining_credit_usd": 3.933199486, "planned_runs_remaining": 19, "run_cap_remaining": 19, "projected_further_runs": 19, "assumption": "Projection at first measured cost; fresh guard checks decide."}
