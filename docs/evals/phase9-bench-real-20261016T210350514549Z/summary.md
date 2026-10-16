# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **1/40 (2.50%)**.
Missing variants: 2; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 39 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 39 |
| validation_failed | 31 |
| validation_error | 1 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 25 |
| terraform.validate: Terraform configuration diagnostic | 10 |
| helm.lint: helm optional lint failed | 7 |
| terraform.validate: Reference to undeclared input variable | 6 |
| document.parse: Document could not be parsed | 3 |
| terraform.validate: Invalid multi-line string | 3 |
| terraform.validate: Invalid index | 3 |
| terraform.validate: Invalid single-argument block definition | 3 |
| terraform.validate: Unsupported block type | 2 |
| terraform.validate: Unsupported attribute | 1 |
| terraform.var_ref: var.nginx_max_capacity is not declared | 1 |
| terraform.var_ref: var.nginx_min_capacity is not declared | 1 |
| terraform.var_ref: var.prometheus_max_capacity is not declared | 1 |
| terraform.var_ref: var.prometheus_min_capacity is not declared | 1 |
| terraform.var_ref: var.grafana_max_capacity is not declared | 1 |
| terraform.var_ref: var.grafana_min_capacity is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 67 |
| CKV_AWS_130 | 43 |
| AWS-0164 | 42 |
| AWS-0038 | 35 |
| AWS-0176 | 28 |
| AWS-0177 | 28 |
| CKV_AWS_129 | 28 |
| CKV_AWS_161 | 28 |
| CKV_AWS_293 | 28 |
| AWS-0053 | 27 |
| CKV_AWS_103 | 26 |
| CKV_AWS_145 | 25 |
| AWS-0028 | 24 |
| AWS-0178 | 24 |
| CKV_AWS_91 | 24 |
| CKV2_AWS_11 | 23 |
| AWS-0132 | 23 |
| CKV_AWS_260 | 22 |
| AWS-0131 | 21 |
| CKV_AWS_378 | 21 |

Final failure origins: {'unknown': 6, 'generated': 51, 'repair': 12}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 1 |
| before_security / accepted / improved | Missing required argument | 1 |
| before_security / accepted / improved | Unsupported argument | 3 |
| before_security / accepted / improved | helm optional lint failed | 2 |
| before_security / rejected / invalid_patch | Document could not be parsed | 1 |
| before_security / rejected / invalid_patch | Reference to undeclared input variable | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| before_security / rejected / invalid_patch | Unsupported argument | 5 |
| before_security / rejected / invalid_patch | Unsupported attribute | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 4 |
| before_security / rejected / invalid_patch | var.grafana_max_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.grafana_min_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.nginx_max_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.nginx_min_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.prometheus_max_capacity is not declared | 1 |
| before_security / rejected / invalid_patch | var.prometheus_min_capacity is not declared | 1 |
| before_security / rejected / new_blocking_findings | Document could not be parsed | 2 |
| before_security / rejected / new_blocking_findings | Invalid multi-line string | 1 |
| before_security / rejected / new_blocking_findings | Invalid single-argument block definition | 2 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 3 |
| before_security / rejected / no_improvement | Invalid index | 1 |
| before_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 5 |
| before_security / rejected / no_improvement | Unsupported argument | 13 |
| before_security / rejected / no_improvement | Unsupported block type | 2 |
| before_security / stopped / round_limit | unknown | 1 |
| generation / accepted / improved | Document could not be parsed | 1 |
| generation / accepted / improved | Invalid single-argument block definition | 1 |
| generation / accepted / improved | Missing required argument | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 5 |
| generation / accepted / improved | Unsupported argument | 2 |
| generation / accepted / improved | Unsupported block type | 3 |
| generation / accepted / improved | var.api_desired_count is not declared | 1 |
| generation / accepted / improved | var.api_image is not declared | 1 |
| generation / accepted / improved | var.api_max_capacity is not declared | 1 |
| generation / accepted / improved | var.api_min_capacity is not declared | 1 |
| generation / accepted / improved | var.aws_region is not declared | 1 |
| generation / accepted / improved | var.db_name is not declared | 1 |
| generation / accepted / improved | var.db_password is not declared | 1 |
| generation / accepted / improved | var.db_username is not declared | 1 |
| generation / accepted / improved | var.grafana_desired_count is not declared | 1 |
| generation / accepted / improved | var.grafana_image is not declared | 1 |
| generation / accepted / improved | var.nginx_desired_count is not declared | 1 |
| generation / accepted / improved | var.nginx_image is not declared | 1 |
| generation / accepted / improved | var.project_name is not declared | 1 |
| generation / accepted / improved | var.prometheus_desired_count is not declared | 1 |
| generation / accepted / improved | var.prometheus_image is not declared | 1 |
| generation / accepted / improved | var.vpc_cidr is not declared | 1 |
| generation / rejected / invalid_patch | Document could not be parsed | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 5 |
| generation / rejected / invalid_patch | Invalid index | 1 |
| generation / rejected / invalid_patch | Missing required argument | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| generation / rejected / invalid_patch | Unsupported argument | 7 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 5 |
| generation / rejected / new_blocking_findings | Document could not be parsed | 1 |
| generation / rejected / new_blocking_findings | Invalid multi-line string | 1 |
| generation / rejected / new_blocking_findings | Invalid single-argument block definition | 1 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| generation / rejected / no_improvement | Document could not be parsed | 1 |
| generation / rejected / no_improvement | Invalid single-argument block definition | 2 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 6 |
| generation / rejected / no_improvement | Unsupported argument | 11 |
| generation / rejected / no_improvement | Unsupported block type | 2 |
| generation / stopped / round_limit | unknown | 2 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 84 | 0.047704692000479554 | 0.17748659000062617 | 0.5786761919998753 |
| final_security_scan | 40 | 4.908768710000004 | 9.83452876499905 | 12.06780247200004 |
| final_validation | 40 | 0.1070776994993139 | 0.43471432800106413 | 4.08563557800062 |
| generation_gate | 40 | 28.143088118000378 | 71.70734923399868 | 119.87594170400007 |
| initial_validation | 40 | 0.13176282650056237 | 0.5245776930005377 | 7.310586949000026 |
| post_security_validation | 40 | 0.1206731020006373 | 0.49826080999991973 | 5.93382687599933 |
| security_iteration_verification | 44 | 4.181310285000109 | 13.72547048999877 | 23.46391187000154 |
| validation_repair_round | 71 | 18.458363826000095 | 49.414774373999535 | 69.6457880550006 |

Iteration outcomes: {'attempted_fix_iterations': 44, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 12}.
Initialization: {'init_runs': 68, 'init_reused': 103, 'reinitializations': 14}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 40, 'packages_unknown': 0, 'init_runs': 86, 'init_reused': 233, 'reinitializations': 17, 'init_seconds': 491.9059447640011, 'validate_seconds': 606.370899480009}
Gate outcomes: {'invalid': 32, 'valid': 7, 'error': 1}
Init categories: {'syntax': 2, 'validation_cached': 27, 'missing_required_providers': 1, 'mirror_constraint_unavailable': 1, 'initialized': 4, 'reused': 5}
Schema context sizes (characters): {'generator': {'count': 40, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 74, 'median': 15971.5, 'p90': 15999, 'max': 23405}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security iteration outcomes by class: []

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 84 | 0.047704692000479554 | 0.17748659000062617 | 0.5786761919998753 |
| final_security_scan | 40 | 4.908768710000004 | 9.83452876499905 | 12.06780247200004 |
| final_validation | 40 | 0.1070776994993139 | 0.43471432800106413 | 4.08563557800062 |
| generation_gate | 40 | 28.143088118000378 | 71.70734923399868 | 119.87594170400007 |
| initial_validation | 40 | 0.13176282650056237 | 0.5245776930005377 | 7.310586949000026 |
| post_security_validation | 40 | 0.1206731020006373 | 0.49826080999991973 | 5.93382687599933 |
| security_iteration_verification | 44 | 4.181310285000109 | 13.72547048999877 | 23.46391187000154 |
| validation_repair_round | 71 | 18.458363826000095 | 49.414774373999535 | 69.6457880550006 |

Iteration outcomes: {'attempted_fix_iterations': 44, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 12}.
Initialization: {'init_runs': 68, 'init_reused': 103, 'reinitializations': 14}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 75.51232989599976, "p90": 96.55747091600006, "max": 123.97397773300054}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 165.01309954050066, "p90": 188.27261903399994, "max": 188.27261903399994}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "81607efb-8a8d-41df-a323-743782131135", "ratio_to_baseline": 2.6079168785016886, "ratio_to_pr01_prompt_median": 2.1488755169848948, "pr01_prompt_median_seconds": 75.51232989599976, "pr01_reference_count": 4}

Cohort references: {"run_id": "9d635e37-59ec-4738-94e8-cda3d1b75842", "ratio_to_baseline": 2.696199379190769, "ratio_to_pr01_prompt_median": 2.221618672977642, "pr01_prompt_median_seconds": 75.51232989599976, "pr01_reference_count": 4}

Cohort references: {"run_id": "80db842f-4889-4cb1-b32f-893d20b05061", "ratio_to_baseline": 3.025880558202221, "ratio_to_pr01_prompt_median": 2.49326989768824, "pr01_prompt_median_seconds": 75.51232989599976, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:2465, cost#1:2499, performance#1:3537 | {} | {} |
| 2 | 4 | {"none": 4} | security#1:2486, security#2:3573, performance#1:4082, cost#1:3013 | {"security": "incomplete_package"} | {} |
| 3 | 3 | {"none": 3} | performance#1:1928, cost#1:1627, security#1:2159 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:3391, performance#1:3233, security#1:4249 | {} | {} |
| 5 | 4 | {"none": 4} | cost#1:3226, security#1:3804, performance#1:2591, performance#2:3473 | {} | {} |
| 6 | 3 | {"none": 3} | cost#1:1031, security#1:1773, performance#1:1095 | {} | {} |
| 7 | 3 | {"none": 3} | cost#1:2632, performance#1:4609, security#1:4088 | {} | {} |
| 8 | 4 | {"none": 4} | cost#1:2060, cost#2:2303, security#1:3418, performance#1:3580 | {"cost": "incomplete_package"} | {} |
| 9 | 3 | {"none": 3} | cost#1:1601, performance#1:1634, security#1:1361 | {} | {} |
| 10 | 3 | {"none": 3} | cost#1:2348, security#1:3279, performance#1:3954 | {} | {} |
| 11 | 3 | {"none": 3} | cost#1:3681, performance#1:3563, security#1:4686 | {} | {} |
| 12 | 3 | {"none": 3} | cost#1:4698, performance#1:3998, security#1:3441 | {} | {} |
| 13 | 3 | {"none": 3} | performance#1:3204, security#1:4212, cost#1:4444 | {} | {} |
| 14 | 3 | {"none": 3} | cost#1:3779, security#1:4404, performance#1:4080 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.124273; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["9d635e37-59ec-4738-94e8-cda3d1b75842", "80db842f-4889-4cb1-b32f-893d20b05061", "81607efb-8a8d-41df-a323-743782131135"], "before_remaining_usd": 9.61043584, "after_remaining_usd": 9.61043584}

First-run affordability advisory: {"measured_first_run_cost_usd": 0.0, "remaining_credit_usd": 9.81838854, "planned_runs_remaining": 13, "run_cap_remaining": null, "projected_further_runs": 13, "assumption": "Projection at first measured cost; fresh guard checks decide."}
