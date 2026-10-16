# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **0/12 (0.00%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 12 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 12 |
| validation_failed | 11 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 10 |
| terraform.validate: Terraform configuration diagnostic | 4 |
| terraform.validate: Invalid single-argument block definition | 3 |
| document.parse: Document could not be parsed | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 32 |
| CKV_AWS_130 | 16 |
| AWS-0164 | 15 |
| AWS-0053 | 13 |
| CKV_AWS_103 | 12 |
| CKV_AWS_260 | 12 |
| CKV_AWS_378 | 12 |
| CKV_AWS_91 | 11 |
| AWS-0176 | 10 |
| AWS-0177 | 10 |
| CKV_AWS_129 | 10 |
| CKV_AWS_161 | 10 |
| CKV_AWS_293 | 10 |
| AWS-0054 | 9 |
| CKV_AWS_2 | 9 |
| AWS-0028 | 9 |
| AWS-0131 | 9 |
| CKV2_AWS_20 | 8 |
| AWS-0178 | 7 |
| CKV_AWS_8 | 7 |

Final failure origins: {'generated': 17, 'unknown': 1}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| before_security / rejected / invalid_patch | Unsupported argument | 1 |
| before_security / rejected / new_blocking_findings | Document could not be parsed | 1 |
| before_security / rejected / new_blocking_findings | Invalid single-argument block definition | 2 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 2 |
| before_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 2 |
| before_security / rejected / no_improvement | Unsupported argument | 5 |
| generation / rejected / invalid_patch | Unsupported argument | 2 |
| generation / rejected / new_blocking_findings | Invalid single-argument block definition | 1 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| generation / rejected / no_improvement | Document could not be parsed | 1 |
| generation / rejected / no_improvement | Invalid single-argument block definition | 2 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported argument | 4 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 24 | 0.09027547150071769 | 0.42976448599983996 | 0.5446753889991669 |
| final_security_scan | 12 | 7.518553705999693 | 11.654964377999931 | 12.06780247200004 |
| final_validation | 12 | 0.15821851849977975 | 0.392447797999921 | 0.5115008390002913 |
| generation_gate | 12 | 70.78685723799936 | 82.76637349700104 | 119.87594170400007 |
| initial_validation | 12 | 0.15866703800020332 | 1.1157091170007334 | 1.3634525919987937 |
| post_security_validation | 12 | 0.1731776759997956 | 0.5606533040008799 | 0.9764151370000036 |
| security_iteration_verification | 12 | 2.8103908989996853 | 10.676996472999235 | 23.46391187000154 |
| validation_repair_round | 22 | 39.34236089099977 | 62.00010514399946 | 69.6457880550006 |

Iteration outcomes: {'attempted_fix_iterations': 12, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 3}.
Initialization: {'init_runs': 22, 'init_reused': 28, 'reinitializations': 5}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 28, 'init_reused': 68, 'reinitializations': 5, 'init_seconds': 214.27350700799798, 'validate_seconds': 325.24757700500777}
Gate outcomes: {'valid': 1, 'invalid': 11}
Init categories: {'initialized': 2, 'validation_cached': 5, 'reused': 4, 'syntax': 1}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 22, 'median': 15966.0, 'p90': 15996, 'max': 15998}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security iteration outcomes by class: []

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 24 | 0.09027547150071769 | 0.42976448599983996 | 0.5446753889991669 |
| final_security_scan | 12 | 7.518553705999693 | 11.654964377999931 | 12.06780247200004 |
| final_validation | 12 | 0.15821851849977975 | 0.392447797999921 | 0.5115008390002913 |
| generation_gate | 12 | 70.78685723799936 | 82.76637349700104 | 119.87594170400007 |
| initial_validation | 12 | 0.15866703800020332 | 1.1157091170007334 | 1.3634525919987937 |
| post_security_validation | 12 | 0.1731776759997956 | 0.5606533040008799 | 0.9764151370000036 |
| security_iteration_verification | 12 | 2.8103908989996853 | 10.676996472999235 | 23.46391187000154 |
| validation_repair_round | 22 | 39.34236089099977 | 62.00010514399946 | 69.6457880550006 |

Iteration outcomes: {'attempted_fix_iterations': 12, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 3}.
Initialization: {'init_runs': 22, 'init_reused': 28, 'reinitializations': 5}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

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
| 1 | 3 | {"none": 3} | cost#1:3681, performance#1:3563, security#1:4686 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:4698, performance#1:3998, security#1:3441 | {} | {} |
| 3 | 3 | {"none": 3} | performance#1:3204, security#1:4212, cost#1:4444 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:3779, security#1:4404, performance#1:4080 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.124273; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["9d635e37-59ec-4738-94e8-cda3d1b75842", "80db842f-4889-4cb1-b32f-893d20b05061", "81607efb-8a8d-41df-a323-743782131135"], "before_remaining_usd": 9.61043584, "after_remaining_usd": 9.61043584}
