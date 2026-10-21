# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **24/60 (40.00%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 24/60; contextual-v1: 24/60; contextual-v2: 24/60. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 36 |
| checks_passed | 24 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 26 |
| validation_failed | 23 |
| validation_error | 2 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 10 |
| helm.lint: helm optional lint failed (undefined_named_template) | 8 |
| terraform.validate: Missing required argument | 8 |
| terraform.validate: Unsupported argument | 6 |
| grafana.panels: Dashboard requires panels | 4 |
| helm.lint: helm optional lint failed | 4 |
| ansible-lint.lint: ansible-lint optional lint failed | 2 |
| terraform.validate: Duplicate required providers configuration | 1 |
| helm.templates: Chart requires templates | 1 |
| terraform.validate: Unsupported attribute | 1 |
| terraform.validate: Invalid resource type | 1 |
| terraform.validate: Unsupported block type | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0053 | 18 |
| CKV_AWS_91 | 17 |
| CKV_AWS_130 | 9 |
| AWS-0164 | 6 |
| AWS-0104 | 6 |
| CKV_AWS_157 | 5 |
| CKV_AWS_260 | 4 |
| AWS-0090 | 4 |
| CKV_AWS_21 | 4 |
| CKV2_AWS_12 | 4 |
| CKV_AWS_18 | 3 |
| KSV-0125 | 3 |
| AWS-0024 | 2 |
| AWS-0039 | 2 |
| CKV_AWS_144 | 2 |
| AWS-0054 | 2 |
| CKV2_AWS_20 | 2 |
| CKV_AWS_103 | 2 |
| CKV_AWS_2 | 2 |
| CKV_AWS_378 | 2 |

Final failure origins: {'unknown': 3, 'generated': 44}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Chart requires templates | 1 |
| after_security / rejected / invalid_patch | Dashboard requires panels | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| after_security / rejected / invalid_patch | helm optional lint failed | 4 |
| after_security / rejected / invalid_patch | helm optional lint failed (undefined_named_template) | 1 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 2 |
| after_security / rejected / new_blocking_findings | Missing required argument | 1 |
| after_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| after_security / rejected / new_blocking_findings | Unsupported argument | 3 |
| after_security / rejected / new_blocking_findings | Unsupported attribute | 1 |
| after_security / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| after_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 6 |
| after_security / rejected / no_improvement | Dashboard requires panels | 1 |
| after_security / rejected / no_improvement | Duplicate required providers configuration | 1 |
| after_security / rejected / no_improvement | Invalid resource type | 1 |
| after_security / rejected / no_improvement | Missing required argument | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 6 |
| after_security / rejected / no_improvement | Unsupported argument | 3 |
| after_security / rejected / no_improvement | Unsupported block type | 1 |
| after_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 1 |
| before_security / accepted / improved | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| before_security / rejected / invalid_patch | helm optional lint failed | 4 |
| before_security / rejected / new_blocking_findings | Chart requires templates | 1 |
| before_security / rejected / new_blocking_findings | Dashboard requires panels | 3 |
| before_security / rejected / new_blocking_findings | Missing required argument | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| before_security / rejected / new_blocking_findings | Unsupported argument | 2 |
| before_security / rejected / new_blocking_findings | Unsupported attribute | 1 |
| before_security / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| before_security / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 7 |
| before_security / rejected / no_improvement | Dashboard requires panels | 1 |
| before_security / rejected / no_improvement | Duplicate required providers configuration | 1 |
| before_security / rejected / no_improvement | Missing required argument | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 7 |
| before_security / rejected / no_improvement | Unsupported argument | 3 |
| before_security / rejected / no_improvement | Unsupported block type | 1 |
| before_security / rejected / no_improvement | helm optional lint failed (undefined_named_template) | 1 |
| generation / accepted / improved | Invalid resource type | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 3 |
| generation / accepted / improved | Unsupported argument | 2 |
| generation / rejected / invalid_patch | Chart requires templates | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 4 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| generation / rejected / invalid_patch | helm optional lint failed | 4 |
| generation / rejected / new_blocking_findings | Dashboard requires panels | 4 |
| generation / rejected / new_blocking_findings | Generation syntax check failed | 8 |
| generation / rejected / new_blocking_findings | Missing required argument | 1 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| generation / rejected / new_blocking_findings | Unsupported argument | 3 |
| generation / rejected / new_blocking_findings | Unsupported attribute | 1 |
| generation / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| generation / rejected / new_blocking_findings | helm optional lint failed (undefined_named_template) | 8 |
| generation / rejected / no_improvement | Missing required argument | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 8 |
| generation / rejected / no_improvement | Unsupported argument | 3 |
| generation / rejected / no_improvement | Unsupported block type | 1 |
| generation / stopped / round_limit | unknown | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 213 | 0.055444939993321896 | 0.25925827299943194 | 0.95329993100313 |
| final_security_scan | 60 | 5.235125564002374 | 7.015988009996363 | 8.677162752006552 |
| final_validation | 60 | 0.003013780507899355 | 0.565546952013392 | 9.52537368099729 |
| generation_gate | 60 | 19.742395093002415 | 60.58029559199349 | 75.0915248359961 |
| initial_validation | 60 | 0.0031275700021069497 | 0.5475737880042288 | 7.9831223170040175 |
| post_security_validation | 60 | 0.0023459424992324784 | 0.5309913560049608 | 5.081832790005137 |
| security_iteration_verification | 163 | 23.060674916981952 | 44.75295797796571 | 53.02460237505147 |
| validation_repair_round | 78 | 7.222632120006892 | 23.631336318008834 | 43.8961570669926 |

Iteration outcomes: {'attempted_fix_iterations': 163, 'deadline_only_rollbacks': 13, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 8, 'validity_regression_rollbacks': 20}.
Initialization: {'init_runs': 123, 'init_reused': 634, 'reinitializations': 10}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 60, 'packages_unknown': 0, 'init_runs': 148, 'init_reused': 856, 'reinitializations': 12, 'init_seconds': 751.598967184007, 'validate_seconds': 2223.8567941231304}
Gate outcomes: {'valid': 33, 'invalid': 25, 'error': 2}
Init categories: {'initialized': 21, 'validation_cached': 32, 'invalid_required_providers': 1, 'mirror_constraint_unavailable': 2, 'reused': 3, 'unknown': 1}
Schema context sizes (characters): {'generator': {'count': 60, 'median': 4484.0, 'p90': 4489, 'max': 4490}, 'repair': {'count': 79, 'median': 15908, 'p90': 15996, 'max': 23253}, 'security': {'count': 178, 'median': 7727.0, 'p90': 13411, 'max': 15940}}
Security context coverage: {'terraform': {'total': 153, 'positive': 153, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 153}}, 'other': {'total': 25, 'positive': 0, 'zero': 25, 'missing': 0, 'reasons': {'not_terraform': 25}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Duplicate required providers configuration', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid resource type', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 14}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 6}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 56}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 13}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Duplicate required providers configuration', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Missing required argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 16}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Cycle', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid resource type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 7}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Reference to undeclared resource', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_verification_unavailable', 'error_class': 'unknown', 'count': 8}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 8 |
| 4+ | 3 |

Phase 9f measured/unknown packages: (60, 0)
Catalogue retained by rule: {'AWS-0164': 15, 'CKV_AWS_130': 15, 'CKV2_AWS_12': 8, 'CKV_AWS_103': 14, 'AWS-0077': 1, 'CKV_K8S_23': 16, 'CKV_K8S_40': 16, 'KSV-0012': 16, 'KSV-0118': 16, 'KSV-0104': 16, 'CKV_K8S_10': 8, 'CKV_K8S_11': 8, 'CKV_K8S_12': 8, 'CKV_K8S_13': 8, 'CKV_K8S_20': 8, 'CKV_K8S_22': 8, 'CKV_K8S_31': 8, 'CKV_K8S_37': 8, 'KSV-0001': 8, 'KSV-0003': 8, 'KSV-0004': 8, 'KSV-0014': 8, 'KSV-0106': 8, 'AWS-0028': 3, 'AWS-0131': 3, 'CKV_AWS_8': 3}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 92}, {'template': 'access_logs', 'status': 'retained', 'count': 7}, {'template': 'flow_logs', 'status': 'retained', 'count': 28}, {'template': 'kms', 'status': 'rejected', 'count': 6}, {'template': 'kms', 'status': 'retained', 'count': 20}, {'template': 'kms', 'status': 'skipped', 'count': 1}]
Template introduced rules: {'CKV_AWS_145': 72, 'CKV_AWS_144': 35, 'CKV_AWS_18': 64, 'AWS-0132': 64}
Partial groups: {'kept': 51, 'discarded': 74, 'unevaluated': 8}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 54, 'regeneration': 2, 'syntax_round_1': 3, 'normalization': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 60, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 178, 'median': 2.5, 'p90': 7, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 213 | 0.055444939993321896 | 0.25925827299943194 | 0.95329993100313 |
| final_security_scan | 60 | 5.235125564002374 | 7.015988009996363 | 8.677162752006552 |
| final_validation | 60 | 0.003013780507899355 | 0.565546952013392 | 9.52537368099729 |
| generation_gate | 60 | 19.742395093002415 | 60.58029559199349 | 75.0915248359961 |
| initial_validation | 60 | 0.0031275700021069497 | 0.5475737880042288 | 7.9831223170040175 |
| post_security_validation | 60 | 0.0023459424992324784 | 0.5309913560049608 | 5.081832790005137 |
| security_iteration_verification | 163 | 23.060674916981952 | 44.75295797796571 | 53.02460237505147 |
| validation_repair_round | 78 | 7.222632120006892 | 23.631336318008834 | 43.8961570669926 |

Iteration outcomes: {'attempted_fix_iterations': 163, 'deadline_only_rollbacks': 13, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 8, 'validity_regression_rollbacks': 20}.
Initialization: {'init_runs': 123, 'init_reused': 634, 'reinitializations': 10}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 20, "median": 159.28758261199982, "p90": 228.08679650099657, "max": 343.8536134099995}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 302, "failures": 0, "missing_measurements": 0, "agents": {"architect": 20, "generator_cost": 20, "generator_performance": 20, "generator_security": 20, "security_iteration": 222}, "durations": {"count": 302, "median": 19.701883000000002, "p90": 53.398163, "max": 81.305051}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:1121, performance#1:1098, security#1:1344 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:1441, performance#1:1596, security#1:1470 | {} | {} |
| 3 | 4 | {"none": 4} | cost#1:1582, performance#1:1498, security#1:1915, security#2:1863 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:1818, performance#1:2268, security#1:2031 | {} | {} |
| 5 | 4 | {"none": 4} | cost#1:1413, security#1:2033, security#2:1759, performance#1:1700 | {} | {} |
| 6 | 6 | {"none": 6} | security#1:2790, cost#1:1894, cost#2:1822, cost#3:2360, performance#1:2340, performance#2:2188 | {} | {} |
| 7 | 3 | {"none": 3} | security#1:3079, cost#1:3660, performance#1:4227 | {} | {} |
| 8 | 5 | {"none": 5} | security#1:2042, security#2:2372, performance#1:2574, cost#1:1819, cost#2:2085 | {} | {} |
| 9 | 3 | {"none": 3} | cost#1:4424, security#1:4175, performance#1:4737 | {} | {} |
| 10 | 5 | {"none": 5} | security#1:5016, cost#1:2139, cost#2:4342, performance#1:3228, performance#2:3875 | {} | {} |
| 11 | 7 | {"none": 7} | performance#1:3774, security#1:2704, security#2:2665, security#3:3946, cost#1:1763, cost#2:3861, cost#3:3825 | {} | {} |
| 12 | 3 | {"none": 3} | performance#1:3758, security#1:2849, cost#1:2911 | {} | {} |
| 13 | 4 | {"none": 4} | performance#1:2660, security#1:2651, cost#1:1548, cost#2:2335 | {} | {} |
| 14 | 3 | {"none": 3} | security#1:3194, performance#1:4099, cost#1:3611 | {} | {} |
| 15 | 3 | {"none": 3} | performance#1:2208, security#1:3241, cost#1:2860 | {} | {} |
| 16 | 3 | {"none": 3} | performance#1:1384, cost#1:1614, security#1:2159 | {} | {} |
| 17 | 3 | {"none": 3} | security#1:1625, cost#1:2369, performance#1:2267 | {} | {} |
| 18 | 3 | {"none": 3} | security#1:1551, performance#1:1296, cost#1:1414 | {} | {} |
| 19 | 3 | {"none": 3} | cost#1:1349, security#1:1491, performance#1:1650 | {} | {} |
| 20 | 3 | {"none": 3} | security#1:795, cost#1:1030, performance#1:1530 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.275615; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.02332895, "remaining_credit_usd": 6.26321544, "planned_runs_remaining": 19, "run_cap_remaining": 19, "projected_further_runs": 19, "assumption": "Projection at first measured cost; fresh guard checks decide."}
