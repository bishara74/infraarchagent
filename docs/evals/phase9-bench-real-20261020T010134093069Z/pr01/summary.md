# Phase 9 benchmark

Status: **PASS**

Mode: real

Checks-passed rate among generated packages: **7/28 (25.00%)**.
Legacy labels mapped: 0. Missing variants: 2; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 7/28; contextual-v1: 7/28. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 21 |
| checks_passed | 7 |

| Review reason | Count |
|---|---:|
| validation_failed | 20 |
| unresolved_security_findings | 14 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 10 |
| terraform.validate: Unsupported argument | 8 |
| helm.lint: helm optional lint failed | 7 |
| grafana.panels: Dashboard requires panels | 5 |
| terraform.validate: Invalid index | 3 |
| terraform.validate: Unsupported block type | 2 |
| terraform.validate: Duplicate required providers configuration | 1 |
| terraform.validate: Invalid single-argument block definition | 1 |
| terraform.validate: Cycle | 1 |
| ansible-lint.lint: ansible-lint optional lint failed | 1 |
| document.parse: Document could not be parsed | 1 |
| k8s.configmap_ref: ConfigMap reference must resolve in its namespace | 1 |

| Remaining blocking rule | Count |
|---|---:|
| KSV-0125 | 12 |
| CKV_AWS_91 | 9 |
| AWS-0053 | 5 |
| CKV_AWS_144 | 5 |
| AWS-0090 | 4 |
| CKV_AWS_18 | 4 |
| CKV_AWS_21 | 4 |
| CKV_AWS_130 | 4 |
| AWS-0077 | 2 |
| AWS-0164 | 2 |
| CKV2_AWS_12 | 1 |
| CKV_K8S_40 | 1 |
| AWS-0039 | 1 |
| TERRAFORM_SYNTAX | 1 |
| CKV_AWS_157 | 1 |
| KSV-0117 | 1 |
| CKV_K8S_14 | 1 |
| KSV-0013 | 1 |
| AWS-0079 | 1 |

Final failure origins: {'generated': 36, 'unknown': 4, 'security_fix': 1}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Terraform configuration diagnostic | 1 |
| after_security / accepted / improved | ansible-lint optional lint failed | 1 |
| after_security / rejected / invalid_patch | Duplicate required providers configuration | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| after_security / rejected / new_blocking_findings | Dashboard requires panels | 1 |
| after_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| after_security / rejected / new_blocking_findings | ansible-lint optional lint failed | 1 |
| after_security / rejected / no_improvement | ConfigMap reference must resolve in its namespace | 1 |
| after_security / rejected / no_improvement | Cycle | 1 |
| after_security / rejected / no_improvement | Dashboard requires panels | 4 |
| after_security / rejected / no_improvement | Invalid index | 1 |
| after_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 7 |
| after_security / rejected / no_improvement | Unsupported argument | 7 |
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
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 8 |
| before_security / rejected / no_improvement | Unsupported argument | 8 |
| before_security / rejected / no_improvement | Unsupported attribute | 1 |
| before_security / rejected / no_improvement | Unsupported block type | 2 |
| before_security / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| before_security / rejected / no_improvement | helm optional lint failed | 6 |
| generation / accepted / improved | Missing required argument | 2 |
| generation / accepted / improved | Terraform configuration diagnostic | 5 |
| generation / accepted / improved | Unsupported argument | 1 |
| generation / accepted / improved | Unsupported block type | 2 |
| generation / accepted / improved | local.project_name is not declared | 1 |
| generation / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 1 |
| generation / rejected / invalid_patch | Dashboard requires panels | 4 |
| generation / rejected / invalid_patch | Generation syntax check failed | 6 |
| generation / rejected / invalid_patch | Missing required argument | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 4 |
| generation / rejected / invalid_patch | helm optional lint failed | 6 |
| generation / rejected / no_improvement | Invalid index | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 7 |
| generation / rejected / no_improvement | Unsupported argument | 6 |
| generation / rejected / no_improvement | Unsupported attribute | 1 |
| generation / rejected / no_improvement | Unsupported block type | 2 |
| generation / rejected / no_improvement | ansible-lint optional lint failed | 1 |
| generation / stopped / round_limit | unknown | 4 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 112 | 0.06382977100020071 | 0.2439380939995317 | 0.7947341079998296 |
| final_security_scan | 28 | 5.074097327499658 | 6.552538902000379 | 8.403643913999986 |
| final_validation | 28 | 0.006336639499750163 | 2.4254966739990778 | 9.440075974000138 |
| generation_gate | 28 | 16.21734298950105 | 24.12818258600055 | 27.7743718110014 |
| initial_validation | 28 | 0.00314511849956034 | 0.4714444420005748 | 3.3542337030012277 |
| post_security_validation | 28 | 0.00301793499966152 | 0.7478326069995092 | 3.653664110999671 |
| security_iteration_verification | 84 | 16.612801535499784 | 39.81689885900414 | 52.77888590400471 |
| validation_repair_round | 67 | 5.487379219999639 | 16.68453835999935 | 28.03309004000039 |

Iteration outcomes: {'attempted_fix_iterations': 84, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 5, 'validity_regression_rollbacks': 9}.
Initialization: {'init_runs': 40, 'init_reused': 302, 'reinitializations': 3}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 28, 'packages_unknown': 0, 'init_runs': 52, 'init_reused': 415, 'reinitializations': 6, 'init_seconds': 200.73609131299963, 'validate_seconds': 883.5987534050055}
Gate outcomes: {'valid': 5, 'invalid': 23}
Init categories: {'initialized': 6, 'validation_cached': 20, 'syntax': 1, 'unknown': 1}
Schema context sizes (characters): {'generator': {'count': 28, 'median': 3434.0, 'p90': 5503, 'max': 5503}, 'repair': {'count': 72, 'median': 15945.5, 'p90': 15996, 'max': 16000}, 'security': {'count': 117, 'median': 10258, 'p90': 14243, 'max': 15988}}
Security context coverage: {'terraform': {'total': 87, 'positive': 87, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 83, 'no_schema_entries': 4}}, 'other': {'total': 30, 'positive': 0, 'zero': 30, 'missing': 0, 'reasons': {'not_terraform': 30}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Duplicate required providers configuration', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid index', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 21}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 17}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 20}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Invalid index', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 5}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 2}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 1 |
| 2-3 | 0 |
| 4+ | 0 |

Phase 9f measured/unknown packages: (28, 0)
Catalogue retained by rule: {'CKV_AWS_103': 2, 'AWS-0028': 3, 'AWS-0131': 3, 'CKV_AWS_8': 3}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 47}, {'template': 'access_logs', 'status': 'retained', 'count': 3}, {'template': 'access_logs', 'status': 'skipped', 'count': 4}, {'template': 'flow_logs', 'status': 'retained', 'count': 7}, {'template': 'kms', 'status': 'retained', 'count': 16}, {'template': 'kms', 'status': 'skipped', 'count': 1}]
Template introduced rules: {'CKV_AWS_18': 20, 'CKV_AWS_145': 39, 'AWS-0132': 20, 'CKV_AWS_144': 24}
Partial groups: {'discarded': 27, 'kept': 31, 'unevaluated': 27}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 24, 'normalization': 2, 'unresolved': 2}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 28, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 117, 'median': 3, 'p90': 9, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 112 | 0.06382977100020071 | 0.2439380939995317 | 0.7947341079998296 |
| final_security_scan | 28 | 5.074097327499658 | 6.552538902000379 | 8.403643913999986 |
| final_validation | 28 | 0.006336639499750163 | 2.4254966739990778 | 9.440075974000138 |
| generation_gate | 28 | 16.21734298950105 | 24.12818258600055 | 27.7743718110014 |
| initial_validation | 28 | 0.00314511849956034 | 0.4714444420005748 | 3.3542337030012277 |
| post_security_validation | 28 | 0.00301793499966152 | 0.7478326069995092 | 3.653664110999671 |
| security_iteration_verification | 84 | 16.612801535499784 | 39.81689885900414 | 52.77888590400471 |
| validation_repair_round | 67 | 5.487379219999639 | 16.68453835999935 | 28.03309004000039 |

Iteration outcomes: {'attempted_fix_iterations': 84, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 5, 'validity_regression_rollbacks': 9}.
Initialization: {'init_runs': 40, 'init_reused': 302, 'reinitializations': 3}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 162.3922934154998, "p90": 182.91267323600005, "max": 198.03473391599982}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 151, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_cost": 10, "generator_security": 10, "generator_performance": 10, "security_iteration": 111}, "durations": {"count": 151, "median": 15.282437, "p90": 40.438627, "max": 55.100577}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

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

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.067546; unknown costs stay unknown.
