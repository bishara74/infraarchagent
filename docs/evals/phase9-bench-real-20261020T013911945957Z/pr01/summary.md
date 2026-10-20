# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **8/29 (27.59%)**.
Legacy labels mapped: 0. Missing variants: 1; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 8/29; contextual-v1: 8/29. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 21 |
| checks_passed | 8 |

| Review reason | Count |
|---|---:|
| validation_failed | 17 |
| unresolved_security_findings | 16 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 14 |
| terraform.validate: Terraform configuration diagnostic | 5 |
| helm.lint: helm optional lint failed | 4 |
| terraform.validate: Unsupported block type | 1 |
| grafana.panels: Dashboard requires panels | 1 |
| terraform.validate: Unsupported attribute | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0053 | 12 |
| CKV_AWS_91 | 10 |
| AWS-0164 | 7 |
| CKV_AWS_130 | 7 |
| CKV_AWS_378 | 6 |
| CKV_AWS_144 | 5 |
| CKV_AWS_157 | 4 |
| KSV-0125 | 4 |
| AWS-0090 | 4 |
| CKV_AWS_21 | 4 |
| CKV_AWS_260 | 3 |
| CKV_AWS_18 | 3 |
| CKV2_AWS_12 | 2 |
| AWS-0104 | 2 |
| AWS-0077 | 2 |
| AWS-0039 | 2 |
| AWS-0040 | 2 |
| AWS-0041 | 2 |
| CKV_AWS_38 | 2 |
| CKV_AWS_39 | 2 |

Final failure origins: {'generated': 23, 'unknown': 3}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / no_improvement | Dashboard requires panels | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 4 |
| after_security / rejected / no_improvement | Unsupported argument | 12 |
| after_security / rejected / no_improvement | Unsupported attribute | 1 |
| after_security / rejected / no_improvement | Unsupported block type | 1 |
| after_security / rejected / no_improvement | helm optional lint failed | 4 |
| before_security / accepted / improved | Unsupported argument | 1 |
| before_security / rejected / no_improvement | Dashboard requires panels | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 4 |
| before_security / rejected / no_improvement | Unsupported argument | 13 |
| before_security / rejected / no_improvement | Unsupported attribute | 1 |
| before_security / rejected / no_improvement | Unsupported block type | 1 |
| before_security / rejected / no_improvement | helm optional lint failed | 4 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 1 |
| generation / accepted / improved | Unsupported argument | 3 |
| generation / accepted / improved | Unsupported block type | 1 |
| generation / rejected / invalid_patch | Dashboard requires panels | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 4 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 2 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 4 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported argument | 10 |
| generation / rejected / no_improvement | Unsupported block type | 1 |
| generation / stopped / round_limit | unknown | 2 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 121 | 0.06932832900020003 | 0.2765271770003892 | 0.834743059000175 |
| final_security_scan | 29 | 5.279237241000374 | 7.383039817999816 | 8.852246371001456 |
| final_validation | 29 | 0.0031392839991895016 | 0.42121422400123265 | 0.6981037999994442 |
| generation_gate | 29 | 13.773086966999472 | 24.10218286700001 | 26.507330099000683 |
| initial_validation | 29 | 0.0029039569999440573 | 0.7756405560012354 | 4.157495392999408 |
| post_security_validation | 29 | 0.0026803640012076357 | 0.5505637030000798 | 3.910164278000593 |
| security_iteration_verification | 92 | 22.306064374500238 | 44.567443938001816 | 52.37685303900071 |
| validation_repair_round | 55 | 5.459819572000924 | 11.0941998720009 | 16.576151481000124 |

Iteration outcomes: {'attempted_fix_iterations': 92, 'deadline_only_rollbacks': 8, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 4, 'validity_regression_rollbacks': 8}.
Initialization: {'init_runs': 52, 'init_reused': 359, 'reinitializations': 9}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 29, 'packages_unknown': 0, 'init_runs': 53, 'init_reused': 479, 'reinitializations': 10, 'init_seconds': 219.7666425460011, 'validate_seconds': 1127.0440557300135}
Gate outcomes: {'invalid': 18, 'valid': 11}
Init categories: {'validation_cached': 18, 'initialized': 10, 'reused': 1}
Schema context sizes (characters): {'generator': {'count': 29, 'median': 4202, 'p90': 5503, 'max': 5503}, 'repair': {'count': 57, 'median': 15958, 'p90': 15994, 'max': 16000}, 'security': {'count': 112, 'median': 11572.0, 'p90': 14170, 'max': 15983}}
Security context coverage: {'terraform': {'total': 92, 'positive': 92, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 92}}, 'other': {'total': 20, 'positive': 0, 'zero': 20, 'missing': 0, 'reasons': {'not_terraform': 20}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 6}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 23}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 19}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 10}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 8}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared resource', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 1 |
| 4+ | 3 |

Phase 9f measured/unknown packages: (29, 0)
Catalogue retained by rule: {'CKV_AWS_103': 9}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 74}, {'template': 'access_logs', 'status': 'retained', 'count': 3}, {'template': 'flow_logs', 'status': 'retained', 'count': 9}, {'template': 'kms', 'status': 'retained', 'count': 14}, {'template': 'kms', 'status': 'skipped', 'count': 5}]
Template introduced rules: {'CKV_AWS_18': 45, 'AWS-0132': 45, 'CKV_AWS_145': 54, 'CKV_AWS_144': 29}
Partial groups: {'kept': 52, 'discarded': 43, 'unevaluated': 9}
Existing-file proposal recovery: {'normalized': 3, 'retained': 1}
Generation syntax recovery: {'unchanged': 26, 'normalization': 1, 'regeneration': 2}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 29, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 112, 'median': 4.0, 'p90': 8, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 121 | 0.06932832900020003 | 0.2765271770003892 | 0.834743059000175 |
| final_security_scan | 29 | 5.279237241000374 | 7.383039817999816 | 8.852246371001456 |
| final_validation | 29 | 0.0031392839991895016 | 0.42121422400123265 | 0.6981037999994442 |
| generation_gate | 29 | 13.773086966999472 | 24.10218286700001 | 26.507330099000683 |
| initial_validation | 29 | 0.0029039569999440573 | 0.7756405560012354 | 4.157495392999408 |
| post_security_validation | 29 | 0.0026803640012076357 | 0.5505637030000798 | 3.910164278000593 |
| security_iteration_verification | 92 | 22.306064374500238 | 44.567443938001816 | 52.37685303900071 |
| validation_repair_round | 55 | 5.459819572000924 | 11.0941998720009 | 16.576151481000124 |

Iteration outcomes: {'attempted_fix_iterations': 92, 'deadline_only_rollbacks': 8, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 4, 'validity_regression_rollbacks': 8}.
Initialization: {'init_runs': 52, 'init_reused': 359, 'reinitializations': 9}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 164.27101094950103, "p90": 212.59432745599952, "max": 243.74560717200075}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 160, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_security": 10, "generator_cost": 10, "generator_performance": 10, "security_iteration": 120}, "durations": {"count": 160, "median": 18.410956, "p90": 52.255427, "max": 55.316444}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:3597, cost#1:4552, performance#1:5365 | {} | {} |
| 2 | 7 | {"none": 7} | performance#1:2470, performance#2:2378, performance#3:3904, security#1:2359, security#2:3193, security#3:4560, cost#1:3997 | {"performance": "incomplete_package"} | {} |
| 3 | 3 | {"none": 3} | performance#1:1567, cost#1:1430, security#1:1633 | {} | {} |
| 4 | 3 | {"none": 3} | performance#1:4455, cost#1:4757, security#1:4811 | {} | {} |
| 5 | 4 | {"none": 4} | cost#1:2843, performance#1:3026, security#1:3173, security#2:3863 | {} | {} |
| 6 | 3 | {"none": 3} | security#1:1570, cost#1:1515, performance#1:1707 | {} | {} |
| 7 | 3 | {"none": 3} | cost#1:3236, security#1:4431, performance#1:4272 | {} | {} |
| 8 | 6 | {"none": 6} | performance#1:4050, security#1:3126, security#2:4514, cost#1:3056, cost#2:4923, cost#3:4075 | {} | {} |
| 9 | 3 | {"none": 3} | cost#1:1308, security#1:1477, performance#1:1072 | {} | {} |
| 10 | 3 | {"none": 3} | security#1:4354, cost#1:2975, performance#1:4512 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.103443; unknown costs stay unknown.
