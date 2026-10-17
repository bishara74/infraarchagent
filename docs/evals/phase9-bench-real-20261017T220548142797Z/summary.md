# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **3/41 (7.32%)**.
Missing variants: 1; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 37 |
| production_ready | 3 |
| scan_error | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 34 |
| validation_failed | 32 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 22 |
| terraform.validate: Terraform configuration diagnostic | 20 |
| terraform.validate: Invalid multi-line string | 10 |
| terraform.validate: Missing required argument | 7 |
| document.parse: Document could not be parsed | 7 |
| terraform.validate: Invalid single-argument block definition | 6 |
| terraform.validate: Reference to undeclared resource | 2 |
| helm.lint: helm optional lint failed | 2 |
| k8s.configmap_ref: ConfigMap reference must resolve in its namespace | 2 |
| terraform.validate: Unsupported block type | 2 |
| terraform.var_ref: var.eks_name is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 37 |
| CKV_AWS_130 | 24 |
| AWS-0164 | 20 |
| TERRAFORM_SYNTAX | 20 |
| CKV_AWS_91 | 19 |
| KSV-0118 | 18 |
| AWS-0053 | 17 |
| CKV_AWS_145 | 16 |
| CKV_AWS_18 | 14 |
| AWS-0132 | 14 |
| CKV_AWS_21 | 13 |
| CKV_AWS_378 | 12 |
| AWS-0090 | 11 |
| CKV2_AWS_12 | 11 |
| CKV_AWS_260 | 10 |
| CKV_K8S_10 | 9 |
| CKV_K8S_11 | 9 |
| CKV_K8S_12 | 9 |
| CKV_K8S_13 | 9 |
| CKV_K8S_20 | 9 |

Final failure origins: {'generated': 62, 'unknown': 19}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 2 |
| after_security / rejected / invalid_patch | Document could not be parsed | 3 |
| after_security / rejected / invalid_patch | Invalid single-argument block definition | 2 |
| after_security / rejected / invalid_patch | Missing required argument | 4 |
| after_security / rejected / invalid_patch | Reference to undeclared resource | 2 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 10 |
| after_security / rejected / invalid_patch | Unsupported argument | 9 |
| after_security / rejected / invalid_patch | Unsupported block type | 2 |
| after_security / rejected / invalid_patch | helm optional lint failed | 2 |
| after_security / rejected / invalid_patch | var.eks_name is not declared | 1 |
| after_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| before_security / accepted / improved | Missing required argument | 1 |
| before_security / accepted / improved | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 2 |
| before_security / rejected / invalid_patch | Document could not be parsed | 7 |
| before_security / rejected / invalid_patch | Invalid multi-line string | 2 |
| before_security / rejected / invalid_patch | Invalid single-argument block definition | 5 |
| before_security / rejected / invalid_patch | Missing required argument | 5 |
| before_security / rejected / invalid_patch | Reference to undeclared resource | 2 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 14 |
| before_security / rejected / invalid_patch | Unsupported argument | 10 |
| before_security / rejected / invalid_patch | Unsupported block type | 2 |
| before_security / rejected / invalid_patch | helm optional lint failed | 2 |
| before_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 5 |
| before_security / rejected / no_improvement | Unsupported argument | 2 |
| before_security / rejected / verification_unavailable | Missing required argument | 1 |
| before_security / rejected / verification_unavailable | Unsupported argument | 1 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 2 |
| generation / accepted / improved | Unsupported argument | 2 |
| generation / accepted / improved | Unsupported block type | 1 |
| generation / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 2 |
| generation / rejected / invalid_patch | Document could not be parsed | 6 |
| generation / rejected / invalid_patch | Generation syntax check failed | 2 |
| generation / rejected / invalid_patch | Invalid multi-line string | 1 |
| generation / rejected / invalid_patch | Invalid single-argument block definition | 6 |
| generation / rejected / invalid_patch | Missing required argument | 4 |
| generation / rejected / invalid_patch | Reference to undeclared resource | 2 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 13 |
| generation / rejected / invalid_patch | Unsupported argument | 9 |
| generation / rejected / invalid_patch | Unsupported block type | 2 |
| generation / rejected / invalid_patch | helm optional lint failed | 2 |
| generation / rejected / no_improvement | Document could not be parsed | 1 |
| generation / rejected / no_improvement | Invalid multi-line string | 1 |
| generation / rejected / no_improvement | Missing required argument | 2 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported argument | 2 |
| generation / rejected / verification_unavailable | Missing required argument | 1 |
| generation / rejected / verification_unavailable | Unsupported argument | 1 |
| generation / stopped / round_limit | unknown | 3 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 186 | 0.058249506502761506 | 0.11538731699693017 | 1.1343296599952737 |
| final_security_scan | 40 | 4.742411507500947 | 7.439006710003014 | 12.119209108997893 |
| final_validation | 40 | 0.0797336739997263 | 0.3885050489989226 | 5.702813989999413 |
| generation_gate | 41 | 20.539721125998767 | 29.866456750001817 | 49.990478615996835 |
| initial_validation | 41 | 0.08000004600035027 | 0.4617155450032442 | 0.7263854170014383 |
| post_security_validation | 40 | 0.09868282550087315 | 0.5221798589991522 | 4.7714139750023605 |
| security_iteration_verification | 146 | 9.325800148501003 | 28.755359884991776 | 46.0864812600048 |
| validation_repair_round | 91 | 8.39982121900539 | 19.138607731001684 | 47.206021455000155 |

Iteration outcomes: {'attempted_fix_iterations': 146, 'deadline_only_rollbacks': 1, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 1, 'validity_regression_rollbacks': 4}.
Initialization: {'init_runs': 105, 'init_reused': 330, 'reinitializations': 2}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 41, 'packages_unknown': 0, 'init_runs': 133, 'init_reused': 434, 'reinitializations': 2, 'init_seconds': 298.54127463502664, 'validate_seconds': 706.2711341519534}
Gate outcomes: {'invalid': 33, 'valid': 8}
Init categories: {'validation_cached': 23, 'syntax': 8, 'unknown': 2, 'initialized': 8}
Schema context sizes (characters): {'generator': {'count': 41, 'median': 5313, 'p90': 5313, 'max': 5313}, 'repair': {'count': 94, 'median': 15956.0, 'p90': 15990, 'max': 24536}, 'security': {'count': 165, 'median': 10343, 'p90': 13544, 'max': 15974}}
Security context coverage: {'terraform': {'total': 145, 'positive': 129, 'zero': 16, 'missing': 0, 'reasons': {'schema_available': 129, 'unparseable_document': 16}}, 'other': {'total': 20, 'positive': 0, 'zero': 20, 'missing': 0, 'reasons': {'not_terraform': 20}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 5}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 11}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 11}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 11}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Invalid multi-line string', 'count': 7}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 21}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Missing required argument', 'count': 10}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 6}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 55}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 29}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 16}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 5}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 4}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Reference to undeclared input variable', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Reference to undeclared resource', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 5 |

Phase 9f measured/unknown packages: (41, 0)
Catalogue retained by rule: {'CKV_AWS_8': 3, 'CKV_AWS_103': 10}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 94}, {'template': 'access_logs', 'status': 'skipped', 'count': 4}, {'template': 'flow_logs', 'status': 'retained', 'count': 1}, {'template': 'kms', 'status': 'proposed', 'count': 1}, {'template': 'kms', 'status': 'rejected', 'count': 33}, {'template': 'kms', 'status': 'retained', 'count': 8}, {'template': 'kms', 'status': 'skipped', 'count': 43}]
Template introduced rules: {'AWS-0090': 94, 'AWS-0132': 127}
Partial groups: {'discarded': 15, 'kept': 28, 'unevaluated': 9}
Existing-file proposal recovery: {'normalized': 1, 'retained': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 41, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 165, 'median': 3, 'p90': 12, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 186 | 0.058249506502761506 | 0.11538731699693017 | 1.1343296599952737 |
| final_security_scan | 40 | 4.742411507500947 | 7.439006710003014 | 12.119209108997893 |
| final_validation | 40 | 0.0797336739997263 | 0.3885050489989226 | 5.702813989999413 |
| generation_gate | 41 | 20.539721125998767 | 29.866456750001817 | 49.990478615996835 |
| initial_validation | 41 | 0.08000004600035027 | 0.4617155450032442 | 0.7263854170014383 |
| post_security_validation | 40 | 0.09868282550087315 | 0.5221798589991522 | 4.7714139750023605 |
| security_iteration_verification | 146 | 9.325800148501003 | 28.755359884991776 | 46.0864812600048 |
| validation_repair_round | 91 | 8.39982121900539 | 19.138607731001684 | 47.206021455000155 |

Iteration outcomes: {'attempted_fix_iterations': 146, 'deadline_only_rollbacks': 1, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 1, 'validity_regression_rollbacks': 4}.
Initialization: {'init_runs': 105, 'init_reused': 330, 'reinitializations': 2}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 133.92153543949826, "p90": 153.54062278699712, "max": 157.25570357299875}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 200.1924743519994, "p90": 227.92902846599463, "max": 227.92902846599463}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "6f80d5cb-e971-4022-a83e-0e135402a960", "ratio_to_baseline": 1.6959675814611759, "ratio_to_pr01_prompt_median": 1.3817765886391238, "pr01_prompt_median_seconds": 150.00023320349646, "pr01_reference_count": 4}

Cohort references: {"run_id": "e986acdc-148a-4c6e-a26f-c818304637a6", "ratio_to_baseline": 1.8650368679960538, "ratio_to_pr01_prompt_median": 1.5195244940504644, "pr01_prompt_median_seconds": 150.00023320349646, "pr01_reference_count": 4}

Cohort references: {"run_id": "2feb779a-4321-49f3-ad25-15e1813db8e4", "ratio_to_baseline": 1.5801955985835885, "ratio_to_pr01_prompt_median": 1.2874522528975436, "pr01_prompt_median_seconds": 150.00023320349646, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: FAIL. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:4301, performance#1:4741, cost#1:3581 | {} | {} |
| 2 | 3 | {"none": 3} | performance#1:3946, security#1:4029, cost#1:3222 | {} | {} |
| 3 | 3 | {"none": 3} | security#1:604, cost#1:1360, performance#1:1625 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:3916, security#1:4557, performance#1:3487 | {} | {} |
| 5 | 4 | {"none": 4} | security#1:2856, security#2:3016, cost#1:3750, performance#1:4339 | {"security": "incomplete_package"} | {} |
| 6 | 3 | {"none": 3} | cost#1:1152, security#1:1390, performance#1:1385 | {} | {} |
| 7 | 3 | {"none": 3} | security#1:4647, cost#1:4217, performance#1:5230 | {} | {} |
| 8 | 4 | {"none": 4} | cost#1:4263, security#1:5351, performance#1:3868, performance#2:5034 | {} | {} |
| 9 | 3 | {"none": 3} | performance#1:1634, security#1:1870, cost#1:1840 | {} | {} |
| 10 | 3 | {"none": 3} | cost#1:3945, performance#1:3613, security#1:4080 | {} | {} |
| 11 | 3 | {"none": 3} | security#1:5418, cost#1:3953, performance#1:4739 | {} | {} |
| 12 | 3 | {"none": 3} | security#1:4524, performance#1:4592, cost#1:4692 | {} | {} |
| 13 | 3 | {"none": 3} | security#1:3355, cost#1:4679, performance#1:4931 | {} | {} |
| 14 | 3 | {"none": 3} | cost#1:4358, performance#1:4212, security#1:4035 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.719576; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.4257765, "average_cost_usd": 0.1419255, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["e986acdc-148a-4c6e-a26f-c818304637a6", "2feb779a-4321-49f3-ad25-15e1813db8e4", "6f80d5cb-e971-4022-a83e-0e135402a960"], "before_remaining_usd": 6.14330704, "after_remaining_usd": 5.7175305399999985}

First-run affordability advisory: {"measured_first_run_cost_usd": 0.1661572, "remaining_credit_usd": 7.255221389999999, "planned_runs_remaining": 13, "run_cap_remaining": null, "projected_further_runs": 13, "assumption": "Projection at first measured cost; fresh guard checks decide."}
