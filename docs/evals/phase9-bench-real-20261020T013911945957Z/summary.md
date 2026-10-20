# Phase 9 benchmark

Status: **FAIL**

Mode: real

Checks-passed rate among generated packages: **8/41 (19.51%)**.
Legacy labels mapped: 0. Missing variants: 1; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 8/41; contextual-v1: 8/41. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 33 |
| checks_passed | 8 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 28 |
| validation_failed | 27 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 23 |
| terraform.validate: Terraform configuration diagnostic | 7 |
| helm.lint: helm optional lint failed | 7 |
| terraform.validate: Unsupported attribute | 3 |
| terraform.validate: Unsupported block type | 1 |
| grafana.panels: Dashboard requires panels | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0164 | 26 |
| CKV_AWS_130 | 26 |
| AWS-0053 | 23 |
| CKV_AWS_91 | 19 |
| AWS-0104 | 18 |
| CKV_AWS_378 | 14 |
| CKV_AWS_260 | 10 |
| CKV2_AWS_12 | 9 |
| KSV-0125 | 8 |
| CKV_AWS_157 | 7 |
| CKV_AWS_144 | 7 |
| AWS-0077 | 6 |
| AWS-0090 | 6 |
| CKV_AWS_21 | 6 |
| CKV_AWS_18 | 5 |
| AWS-0054 | 5 |
| CKV2_AWS_20 | 5 |
| CKV_AWS_103 | 5 |
| CKV_AWS_2 | 5 |
| KSV-0118 | 4 |

Final failure origins: {'generated': 39, 'unknown': 3}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Unsupported argument | 2 |
| after_security / rejected / no_improvement | Dashboard requires panels | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 5 |
| after_security / rejected / no_improvement | Unsupported argument | 18 |
| after_security / rejected / no_improvement | Unsupported attribute | 2 |
| after_security / rejected / no_improvement | Unsupported block type | 1 |
| after_security / rejected / no_improvement | helm optional lint failed | 7 |
| before_security / accepted / improved | ConfigMap reference must resolve in its namespace | 1 |
| before_security / accepted / improved | Dashboard requires panels | 1 |
| before_security / accepted / improved | Unsupported argument | 1 |
| before_security / accepted / improved | helm optional lint failed | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 2 |
| before_security / rejected / invalid_patch | helm optional lint failed | 1 |
| before_security / rejected / no_improvement | Dashboard requires panels | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 5 |
| before_security / rejected / no_improvement | Unsupported argument | 18 |
| before_security / rejected / no_improvement | Unsupported attribute | 2 |
| before_security / rejected / no_improvement | Unsupported block type | 1 |
| before_security / rejected / no_improvement | helm optional lint failed | 6 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 1 |
| generation / accepted / improved | Unsupported argument | 4 |
| generation / accepted / improved | Unsupported block type | 1 |
| generation / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 1 |
| generation / rejected / invalid_patch | Dashboard requires panels | 2 |
| generation / rejected / invalid_patch | Generation syntax check failed | 7 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 4 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 7 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported argument | 15 |
| generation / rejected / no_improvement | Unsupported attribute | 1 |
| generation / rejected / no_improvement | Unsupported block type | 1 |
| generation / stopped / round_limit | unknown | 2 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 167 | 0.08602844900087803 | 0.39730979100022523 | 1.5198054170014075 |
| final_security_scan | 41 | 5.6367478009997285 | 11.00884685499841 | 15.819555353999021 |
| final_validation | 41 | 0.003398374001335469 | 0.5232413569992787 | 16.636046707000787 |
| generation_gate | 41 | 16.304251339000984 | 39.74600282500069 | 61.46782082199934 |
| initial_validation | 41 | 0.0033070769986807136 | 0.9509627989991714 | 4.157495392999408 |
| post_security_validation | 41 | 0.004653052001231117 | 0.5505637030000798 | 6.2998148890001175 |
| security_iteration_verification | 140 | 28.489838280002004 | 49.00163347099806 | 54.822730673997285 |
| validation_repair_round | 87 | 6.031977059001292 | 16.110797638000804 | 66.8678740230007 |

Iteration outcomes: {'attempted_fix_iterations': 140, 'deadline_only_rollbacks': 26, 'deadline_before_candidate': 2, 'multiple_cause_deadline_rollbacks': 5, 'validity_regression_rollbacks': 8}.
Initialization: {'init_runs': 67, 'init_reused': 519, 'reinitializations': 12}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 41, 'packages_unknown': 0, 'init_runs': 70, 'init_reused': 691, 'reinitializations': 14, 'init_seconds': 348.51669667399983, 'validate_seconds': 2145.9352227040054}
Gate outcomes: {'invalid': 28, 'valid': 13}
Init categories: {'validation_cached': 29, 'initialized': 11, 'reused': 1}
Schema context sizes (characters): {'generator': {'count': 41, 'median': 4202, 'p90': 5503, 'max': 5503}, 'repair': {'count': 89, 'median': 15964, 'p90': 15994, 'max': 16000}, 'security': {'count': 157, 'median': 11526, 'p90': 14211, 'max': 15983}}
Security context coverage: {'terraform': {'total': 126, 'positive': 126, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 126}}, 'other': {'total': 31, 'positive': 0, 'zero': 31, 'missing': 0, 'reasons': {'not_terraform': 31}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 7}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 29}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 21}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 13}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 8}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 28}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Reference to undeclared resource', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 2}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 2 |
| 4+ | 4 |

Phase 9f measured/unknown packages: (41, 0)
Catalogue retained by rule: {'CKV_AWS_103': 16, 'AWS-0028': 6, 'AWS-0131': 3, 'CKV_AWS_8': 3}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 110}, {'template': 'access_logs', 'status': 'retained', 'count': 6}, {'template': 'flow_logs', 'status': 'rejected', 'count': 2}, {'template': 'flow_logs', 'status': 'retained', 'count': 13}, {'template': 'kms', 'status': 'rejected', 'count': 3}, {'template': 'kms', 'status': 'retained', 'count': 21}, {'template': 'kms', 'status': 'skipped', 'count': 15}]
Template introduced rules: {'CKV_AWS_18': 68, 'AWS-0132': 68, 'CKV_AWS_145': 80, 'CKV_AWS_144': 42}
Partial groups: {'kept': 65, 'discarded': 57, 'unevaluated': 18}
Existing-file proposal recovery: {'normalized': 3, 'retained': 1}
Generation syntax recovery: {'unchanged': 36, 'normalization': 2, 'regeneration': 2, 'syntax_round_1': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 41, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 157, 'median': 3, 'p90': 9, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 167 | 0.08602844900087803 | 0.39730979100022523 | 1.5198054170014075 |
| final_security_scan | 41 | 5.6367478009997285 | 11.00884685499841 | 15.819555353999021 |
| final_validation | 41 | 0.003398374001335469 | 0.5232413569992787 | 16.636046707000787 |
| generation_gate | 41 | 16.304251339000984 | 39.74600282500069 | 61.46782082199934 |
| initial_validation | 41 | 0.0033070769986807136 | 0.9509627989991714 | 4.157495392999408 |
| post_security_validation | 41 | 0.004653052001231117 | 0.5505637030000798 | 6.2998148890001175 |
| security_iteration_verification | 140 | 28.489838280002004 | 49.00163347099806 | 54.822730673997285 |
| validation_repair_round | 87 | 6.031977059001292 | 16.110797638000804 | 66.8678740230007 |

Iteration outcomes: {'attempted_fix_iterations': 140, 'deadline_only_rollbacks': 26, 'deadline_before_candidate': 2, 'multiple_cause_deadline_rollbacks': 5, 'validity_regression_rollbacks': 8}.
Initialization: {'init_runs': 67, 'init_reused': 519, 'reinitializations': 12}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 164.27101094950103, "p90": 212.59432745599952, "max": 243.74560717200075}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 323.89214541849924, "p90": 374.4273290050005, "max": 374.4273290050005}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "b937844d-9536-4725-8830-ef89af3a3da5", "ratio_to_baseline": 1.6624905968424453, "ratio_to_pr01_prompt_median": 1.7467541419974113, "pr01_prompt_median_seconds": 176.2868271415009, "pr01_reference_count": 4}

Cohort references: {"run_id": "ce347154-cc1a-41d4-89d4-5d79e4e8860d", "ratio_to_baseline": 2.0215062779437973, "ratio_to_pr01_prompt_median": 2.1239665780838934, "pr01_prompt_median_seconds": 176.2868271415009, "pr01_reference_count": 4}

Cohort references: {"run_id": "40c96191-31a0-4f9b-b7bb-b6d19b7d9934", "ratio_to_baseline": 1.8348503001487426, "ratio_to_pr01_prompt_median": 1.9278499185603222, "pr01_prompt_median_seconds": 176.2868271415009, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 160, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_security": 10, "generator_cost": 10, "generator_performance": 10, "security_iteration": 120}, "durations": {"count": 160, "median": 18.410956, "p90": 52.255427, "max": 55.316444}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "PASS", "observations": 19, "failures": 0, "missing_measurements": 0, "agents": {"architect": 1, "generator_security": 1, "generator_cost": 1, "generator_performance": 1, "security_iteration": 15}, "durations": {"count": 19, "median": 19.924321, "p90": 55.053995, "max": 55.106554}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "PASS", "observations": 53, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_security": 3, "generator_performance": 3, "generator_cost": 3, "security_iteration": 41}, "durations": {"count": 53, "median": 55.092615, "p90": 57.670358, "max": 75.575588}, "failed_observations": []}

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
| 11 | 3 | {"none": 3} | security#1:5423, cost#1:5118, performance#1:2715 | {} | {} |
| 12 | 3 | {"none": 3} | security#1:4867, performance#1:3553, cost#1:3574 | {} | {} |
| 13 | 6 | {"none": 5, "empty": 1} | cost#1:3020, cost#2:3618, cost#3:4556, security#1:5102, performance#1:unknown, performance#2:5459 | {} | {} |
| 14 | 3 | {"none": 3} | security#1:4454, performance#1:4441, cost#1:4522 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.644783; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.357348, "average_cost_usd": 0.119116, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["ce347154-cc1a-41d4-89d4-5d79e4e8860d", "40c96191-31a0-4f9b-b7bb-b6d19b7d9934", "b937844d-9536-4725-8830-ef89af3a3da5"], "before_remaining_usd": 6.65192049, "after_remaining_usd": 6.29457249}

First-run affordability advisory: {"measured_first_run_cost_usd": 0.14144325, "remaining_credit_usd": 7.80297169, "planned_runs_remaining": 13, "run_cap_remaining": null, "projected_further_runs": 13, "assumption": "Projection at first measured cost; fresh guard checks decide."}
