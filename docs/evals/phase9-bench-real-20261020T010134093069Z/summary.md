# Phase 9 benchmark

Status: **FAIL**

Mode: real

Checks-passed rate among generated packages: **7/40 (17.50%)**.
Legacy labels mapped: 0. Missing variants: 2; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 7/40; contextual-v1: 7/40. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 33 |
| checks_passed | 7 |

| Review reason | Count |
|---|---:|
| validation_failed | 31 |
| unresolved_security_findings | 24 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 19 |
| terraform.validate: Terraform configuration diagnostic | 11 |
| helm.lint: helm optional lint failed | 7 |
| grafana.panels: Dashboard requires panels | 5 |
| terraform.validate: Unsupported block type | 3 |
| terraform.validate: Invalid index | 3 |
| terraform.validate: Duplicate required providers configuration | 1 |
| terraform.validate: Invalid single-argument block definition | 1 |
| terraform.validate: Cycle | 1 |
| ansible-lint.lint: ansible-lint optional lint failed | 1 |
| document.parse: Document could not be parsed | 1 |
| k8s.configmap_ref: ConfigMap reference must resolve in its namespace | 1 |
| terraform.local_ref: local.prefix is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| CKV_AWS_91 | 18 |
| AWS-0053 | 13 |
| CKV_AWS_130 | 13 |
| KSV-0125 | 12 |
| AWS-0164 | 10 |
| AWS-0077 | 9 |
| CKV2_AWS_12 | 8 |
| AWS-0104 | 7 |
| CKV_AWS_378 | 6 |
| CKV_AWS_144 | 5 |
| AWS-0090 | 4 |
| CKV_AWS_18 | 4 |
| CKV_AWS_21 | 4 |
| CKV_AWS_157 | 4 |
| CKV_AWS_260 | 3 |
| TERRAFORM_SYNTAX | 2 |
| AWS-0054 | 2 |
| CKV2_AWS_20 | 2 |
| CKV_AWS_103 | 2 |
| CKV_AWS_2 | 2 |

Final failure origins: {'generated': 50, 'unknown': 4, 'security_fix': 1}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Terraform configuration diagnostic | 1 |
| after_security / accepted / improved | ansible-lint optional lint failed | 1 |
| after_security / rejected / invalid_patch | Duplicate required providers configuration | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| after_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| after_security / rejected / new_blocking_findings | Unsupported block type | 1 |
| after_security / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| after_security / rejected / new_blocking_findings | local.prefix is not declared | 1 |
| after_security / rejected / no_improvement | ConfigMap reference must resolve in its namespace | 1 |
| after_security / rejected / no_improvement | Cycle | 1 |
| after_security / rejected / no_improvement | Dashboard requires panels | 4 |
| after_security / rejected / no_improvement | Invalid index | 1 |
| after_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 8 |
| after_security / rejected / no_improvement | Unsupported argument | 15 |
| after_security / rejected / no_improvement | Unsupported block type | 2 |
| after_security / rejected / no_improvement | helm optional lint failed | 7 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Dashboard requires panels | 1 |
| before_security / accepted / improved | Missing required argument | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 2 |
| before_security / accepted / improved | Unsupported argument | 4 |
| before_security / accepted / improved | Unsupported block type | 1 |
| before_security / accepted / improved | helm optional lint failed | 1 |
| before_security / rejected / invalid_patch | Dashboard requires panels | 2 |
| before_security / rejected / invalid_patch | Document could not be parsed | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | ansible-lint optional lint failed | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 1 |
| before_security / rejected / no_improvement | ConfigMap reference must resolve in its namespace | 1 |
| before_security / rejected / no_improvement | Dashboard requires panels | 3 |
| before_security / rejected / no_improvement | Invalid index | 1 |
| before_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 9 |
| before_security / rejected / no_improvement | Unsupported argument | 17 |
| before_security / rejected / no_improvement | Unsupported attribute | 1 |
| before_security / rejected / no_improvement | Unsupported block type | 3 |
| before_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| before_security / rejected / no_improvement | helm optional lint failed | 6 |
| before_security / rejected / no_improvement | local.prefix is not declared | 1 |
| generation / accepted / improved | Missing required argument | 2 |
| generation / accepted / improved | Reference to undeclared resource | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 6 |
| generation / accepted / improved | Unsupported argument | 1 |
| generation / accepted / improved | Unsupported block type | 2 |
| generation / accepted / improved | local.project_name is not declared | 1 |
| generation / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 1 |
| generation / rejected / invalid_patch | Dashboard requires panels | 4 |
| generation / rejected / invalid_patch | Generation syntax check failed | 6 |
| generation / rejected / invalid_patch | Missing required argument | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 5 |
| generation / rejected / invalid_patch | helm optional lint failed | 6 |
| generation / rejected / new_blocking_findings | Unsupported block type | 1 |
| generation / rejected / new_blocking_findings | local.prefix is not declared | 1 |
| generation / rejected / no_improvement | Invalid index | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 7 |
| generation / rejected / no_improvement | Unsupported argument | 14 |
| generation / rejected / no_improvement | Unsupported attribute | 1 |
| generation / rejected / no_improvement | Unsupported block type | 2 |
| generation / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| generation / stopped / round_limit | unknown | 5 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 154 | 0.07884860100057267 | 0.5228520759992534 | 1.091612518999682 |
| final_security_scan | 40 | 5.812661208000463 | 9.549904255000001 | 14.285626754000987 |
| final_validation | 40 | 0.006600960000469058 | 0.4912218329991447 | 9.440075974000138 |
| generation_gate | 40 | 17.49628770399977 | 58.96025863900104 | 80.68769021200023 |
| initial_validation | 40 | 0.004339576499660325 | 0.4339101519999531 | 3.3542337030012277 |
| post_security_validation | 40 | 0.004774545000145736 | 0.5669658659990091 | 3.653664110999671 |
| security_iteration_verification | 129 | 24.46424147900143 | 50.12176873600038 | 54.72378266399937 |
| validation_repair_round | 100 | 7.244098973499604 | 18.78505760400003 | 67.97272502799933 |

Iteration outcomes: {'attempted_fix_iterations': 129, 'deadline_only_rollbacks': 25, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 5, 'validity_regression_rollbacks': 9}.
Initialization: {'init_runs': 56, 'init_reused': 467, 'reinitializations': 6}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 40, 'packages_unknown': 0, 'init_runs': 68, 'init_reused': 637, 'reinitializations': 9, 'init_seconds': 350.25380585899984, 'validate_seconds': 1933.1701102199895}
Gate outcomes: {'valid': 6, 'invalid': 34}
Init categories: {'initialized': 7, 'validation_cached': 30, 'syntax': 1, 'unknown': 1, 'reused': 1}
Schema context sizes (characters): {'generator': {'count': 40, 'median': 5503.0, 'p90': 5503, 'max': 5503}, 'repair': {'count': 106, 'median': 15960.0, 'p90': 15996, 'max': 16000}, 'security': {'count': 147, 'median': 10715, 'p90': 13910, 'max': 15988}}
Security context coverage: {'terraform': {'total': 117, 'positive': 117, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 113, 'no_schema_entries': 4}}, 'other': {'total': 30, 'positive': 0, 'zero': 30, 'missing': 0, 'reasons': {'not_terraform': 30}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Duplicate required providers configuration', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid index', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 23}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 29}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 20}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 25}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid index', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 2}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 1 |
| 2-3 | 0 |
| 4+ | 1 |

Phase 9f measured/unknown packages: (40, 0)
Catalogue retained by rule: {'CKV_AWS_103': 7, 'AWS-0028': 9, 'AWS-0131': 9, 'CKV_AWS_8': 9}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 84}, {'template': 'access_logs', 'status': 'retained', 'count': 4}, {'template': 'access_logs', 'status': 'skipped', 'count': 4}, {'template': 'flow_logs', 'status': 'rejected', 'count': 5}, {'template': 'flow_logs', 'status': 'retained', 'count': 15}, {'template': 'kms', 'status': 'rejected', 'count': 5}, {'template': 'kms', 'status': 'retained', 'count': 25}, {'template': 'kms', 'status': 'skipped', 'count': 1}]
Template introduced rules: {'CKV_AWS_18': 52, 'CKV_AWS_145': 64, 'AWS-0132': 52, 'CKV_AWS_144': 34}
Partial groups: {'discarded': 31, 'kept': 37, 'unevaluated': 28}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 32, 'normalization': 4, 'unresolved': 2, 'syntax_round_1': 2}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 40, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 147, 'median': 3, 'p90': 8, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 154 | 0.07884860100057267 | 0.5228520759992534 | 1.091612518999682 |
| final_security_scan | 40 | 5.812661208000463 | 9.549904255000001 | 14.285626754000987 |
| final_validation | 40 | 0.006600960000469058 | 0.4912218329991447 | 9.440075974000138 |
| generation_gate | 40 | 17.49628770399977 | 58.96025863900104 | 80.68769021200023 |
| initial_validation | 40 | 0.004339576499660325 | 0.4339101519999531 | 3.3542337030012277 |
| post_security_validation | 40 | 0.004774545000145736 | 0.5669658659990091 | 3.653664110999671 |
| security_iteration_verification | 127 | 22.151372548998552 | 49.014465473999735 | 54.541567418998966 |
| validation_repair_round | 100 | 7.244098973499604 | 18.78505760400003 | 67.97272502799933 |

Iteration outcomes: {'attempted_fix_iterations': 127, 'deadline_only_rollbacks': 23, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 5, 'validity_regression_rollbacks': 9}.
Initialization: {'init_runs': 56, 'init_reused': 460, 'reinitializations': 6}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 162.3922934154998, "p90": 182.91267323600005, "max": 198.03473391599982}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 321.9223276289995, "p90": 337.6899233080003, "max": 337.6899233080003}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "e007d01c-35b1-4939-ab43-52e1fb086001", "ratio_to_baseline": 2.024947737190979, "ratio_to_pr01_prompt_median": 2.0794701288193576, "pr01_prompt_median_seconds": 162.3922934154998, "pr01_reference_count": 4}

Cohort references: {"run_id": "b0f4701c-ffff-420f-bebd-64df235c1187", "ratio_to_baseline": 1.9599465459073915, "ratio_to_pr01_prompt_median": 2.0127187588312117, "pr01_prompt_median_seconds": 162.3922934154998, "pr01_reference_count": 4}

Cohort references: {"run_id": "83e65ace-224c-4c93-8ea6-7e69d817d2a5", "ratio_to_baseline": 1.9008490768807509, "ratio_to_pr01_prompt_median": 1.9520300707862541, "pr01_prompt_median_seconds": 162.3922934154998, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 151, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_cost": 10, "generator_security": 10, "generator_performance": 10, "security_iteration": 111}, "durations": {"count": 151, "median": 15.282437, "p90": 40.438627, "max": 55.100577}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "PASS", "observations": 16, "failures": 0, "missing_measurements": 0, "agents": {"architect": 1, "generator_performance": 1, "generator_security": 1, "generator_cost": 1, "security_iteration": 12}, "durations": {"count": 16, "median": 12.710432, "p90": 46.728764, "max": 49.636219}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "PASS", "observations": 57, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_performance": 3, "generator_security": 3, "generator_cost": 3, "security_iteration": 45}, "durations": {"count": 57, "median": 55.201475, "p90": 63.430037, "max": 84.195562}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:3664, security#1:4338, performance#1:5092 | {} | {} |
| 2 | 4 | {"none": 4} | performance#1:3707, cost#1:3136, cost#2:4784, security#1:4675 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:1987, performance#1:1817, security#1:2017 | {} | {} |
| 4 | 3 | {"none": 3} | performance#1:4228, cost#1:4481, security#1:5038 | {} | {} |
| 5 | 6 | {"none": 6} | cost#1:3092, cost#2:2193, cost#3:2939, security#1:4605, security#2:3165, performance#1:3684 | {"cost": "incomplete_package"} | {} |
| 6 | 3 | {"none": 3} | cost#1:1664, performance#1:1671, security#1:1901 | {} | {} |
| 7 | 3 | {"none": 3} | performance#1:3063, cost#1:3329, security#1:3973 | {} | {} |
| 8 | 6 | {"none": 6} | cost#1:3999, security#1:4206, performance#1:2374, performance#2:2839, performance#3:5089, performance#4:2444 | {} | {} |
| 9 | 3 | {"none": 3} | cost#1:1338, security#1:1619, performance#1:1568 | {} | {} |
| 10 | 5 | {"none": 5} | cost#1:3406, cost#2:2367, cost#3:3133, performance#1:3726, security#1:4434 | {"cost": "incomplete_package"} | {} |
| 11 | 3 | {"none": 3} | performance#1:3829, security#1:3871, cost#1:3823 | {} | {} |
| 12 | 3 | {"none": 3} | security#1:3588, cost#1:3816, performance#1:3841 | {} | {} |
| 13 | 3 | {"none": 3} | performance#1:4563, cost#1:3580, security#1:3619 | {} | {} |
| 14 | 3 | {"none": 3} | performance#1:3013, security#1:4104, cost#1:4593 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.566230; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.3678337, "average_cost_usd": 0.12261123333333333, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["b0f4701c-ffff-420f-bebd-64df235c1187", "83e65ace-224c-4c93-8ea6-7e69d817d2a5", "e007d01c-35b1-4939-ab43-52e1fb086001"], "before_remaining_usd": 8.34100404, "after_remaining_usd": 7.97317034}

First-run affordability advisory: {"measured_first_run_cost_usd": 0.1206653, "remaining_credit_usd": 9.41957004, "planned_runs_remaining": 13, "run_cap_remaining": null, "projected_further_runs": 13, "assumption": "Projection at first measured cost; fresh guard checks decide."}
