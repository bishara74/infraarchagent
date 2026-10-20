# Phase 9 benchmark

Status: **FAIL**

Mode: real

Checks-passed rate among generated packages: **0/12 (0.00%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 0/12; contextual-v1: 0/12. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 12 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 12 |
| validation_failed | 10 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 9 |
| helm.lint: helm optional lint failed | 3 |
| terraform.validate: Unsupported attribute | 2 |
| terraform.validate: Terraform configuration diagnostic | 2 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0164 | 19 |
| CKV_AWS_130 | 19 |
| AWS-0104 | 16 |
| AWS-0053 | 11 |
| CKV_AWS_91 | 9 |
| CKV_AWS_378 | 8 |
| CKV2_AWS_12 | 7 |
| CKV_AWS_260 | 7 |
| AWS-0077 | 4 |
| KSV-0118 | 4 |
| KSV-0125 | 4 |
| CKV_K8S_14 | 4 |
| KSV-0013 | 4 |
| KSV-0104 | 4 |
| AWS-0054 | 3 |
| CKV2_AWS_20 | 3 |
| CKV_AWS_103 | 3 |
| CKV_AWS_2 | 3 |
| CKV_AWS_157 | 3 |
| AWS-0090 | 2 |

Final failure origins: {'generated': 16}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 6 |
| after_security / rejected / no_improvement | Unsupported attribute | 1 |
| after_security / rejected / no_improvement | helm optional lint failed | 3 |
| before_security / accepted / improved | ConfigMap reference must resolve in its namespace | 1 |
| before_security / accepted / improved | Dashboard requires panels | 1 |
| before_security / accepted / improved | helm optional lint failed | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 2 |
| before_security / rejected / invalid_patch | helm optional lint failed | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| before_security / rejected / no_improvement | Unsupported argument | 5 |
| before_security / rejected / no_improvement | Unsupported attribute | 1 |
| before_security / rejected / no_improvement | helm optional lint failed | 2 |
| generation / accepted / improved | Unsupported argument | 1 |
| generation / rejected / invalid_patch | ConfigMap reference must resolve in its namespace | 1 |
| generation / rejected / invalid_patch | Dashboard requires panels | 1 |
| generation / rejected / invalid_patch | Generation syntax check failed | 3 |
| generation / rejected / invalid_patch | Unsupported argument | 2 |
| generation / rejected / invalid_patch | helm optional lint failed | 3 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| generation / rejected / no_improvement | Unsupported argument | 5 |
| generation / rejected / no_improvement | Unsupported attribute | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 46 | 0.18414862699955847 | 0.4987824820000242 | 1.5198054170014075 |
| final_security_scan | 12 | 8.464108297499479 | 12.696293040000455 | 15.819555353999021 |
| final_validation | 12 | 0.020959808999577945 | 1.7822610860002897 | 16.636046707000787 |
| generation_gate | 12 | 36.21096338000007 | 49.84745121599917 | 61.46782082199934 |
| initial_validation | 12 | 0.007458605499778059 | 1.1251513189999969 | 1.6121054859995638 |
| post_security_validation | 12 | 0.0100222085002315 | 6.235422110999934 | 6.2998148890001175 |
| security_iteration_verification | 48 | 42.47728218800239 | 52.43434005100062 | 54.822730673997285 |
| validation_repair_round | 32 | 10.183256079499188 | 21.5103544829999 | 66.8678740230007 |

Iteration outcomes: {'attempted_fix_iterations': 48, 'deadline_only_rollbacks': 18, 'deadline_before_candidate': 2, 'multiple_cause_deadline_rollbacks': 1, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 15, 'init_reused': 160, 'reinitializations': 3}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 17, 'init_reused': 212, 'reinitializations': 4, 'init_seconds': 128.75005412799874, 'validate_seconds': 1018.8911669739919}
Gate outcomes: {'invalid': 10, 'valid': 2}
Init categories: {'validation_cached': 11, 'initialized': 1}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 5503.0, 'p90': 5503, 'max': 5503}, 'repair': {'count': 32, 'median': 15968.0, 'p90': 15983, 'max': 15999}, 'security': {'count': 45, 'median': 11172, 'p90': 14632, 'max': 15947}}
Security context coverage: {'terraform': {'total': 34, 'positive': 34, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 34}}, 'other': {'total': 11, 'positive': 0, 'zero': 11, 'missing': 0, 'reasons': {'not_terraform': 11}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 6}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 3}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 20}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 2}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 1 |
| 4+ | 1 |

Phase 9f measured/unknown packages: (12, 0)
Catalogue retained by rule: {'CKV_AWS_103': 7, 'AWS-0028': 6, 'AWS-0131': 3, 'CKV_AWS_8': 3}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 36}, {'template': 'access_logs', 'status': 'retained', 'count': 3}, {'template': 'flow_logs', 'status': 'rejected', 'count': 2}, {'template': 'flow_logs', 'status': 'retained', 'count': 4}, {'template': 'kms', 'status': 'rejected', 'count': 3}, {'template': 'kms', 'status': 'retained', 'count': 7}, {'template': 'kms', 'status': 'skipped', 'count': 10}]
Template introduced rules: {'CKV_AWS_18': 23, 'CKV_AWS_145': 26, 'AWS-0132': 23, 'CKV_AWS_144': 13}
Partial groups: {'discarded': 14, 'kept': 13, 'unevaluated': 9}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 10, 'syntax_round_1': 1, 'normalization': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 12, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 45, 'median': 3, 'p90': 12, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 46 | 0.18414862699955847 | 0.4987824820000242 | 1.5198054170014075 |
| final_security_scan | 12 | 8.464108297499479 | 12.696293040000455 | 15.819555353999021 |
| final_validation | 12 | 0.020959808999577945 | 1.7822610860002897 | 16.636046707000787 |
| generation_gate | 12 | 36.21096338000007 | 49.84745121599917 | 61.46782082199934 |
| initial_validation | 12 | 0.007458605499778059 | 1.1251513189999969 | 1.6121054859995638 |
| post_security_validation | 12 | 0.0100222085002315 | 6.235422110999934 | 6.2998148890001175 |
| security_iteration_verification | 48 | 42.47728218800239 | 52.43434005100062 | 54.822730673997285 |
| validation_repair_round | 32 | 10.183256079499188 | 21.5103544829999 | 66.8678740230007 |

Iteration outcomes: {'attempted_fix_iterations': 48, 'deadline_only_rollbacks': 18, 'deadline_before_candidate': 2, 'multiple_cause_deadline_rollbacks': 1, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 15, 'init_reused': 160, 'reinitializations': 3}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 323.89214541849924, "p90": 374.4273290050005, "max": 374.4273290050005}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "b937844d-9536-4725-8830-ef89af3a3da5", "ratio_to_baseline": 1.6624905968424453, "ratio_to_pr01_prompt_median": 1.7467541419974113, "pr01_prompt_median_seconds": 176.2868271415009, "pr01_reference_count": 4}

Cohort references: {"run_id": "ce347154-cc1a-41d4-89d4-5d79e4e8860d", "ratio_to_baseline": 2.0215062779437973, "ratio_to_pr01_prompt_median": 2.1239665780838934, "pr01_prompt_median_seconds": 176.2868271415009, "pr01_reference_count": 4}

Cohort references: {"run_id": "40c96191-31a0-4f9b-b7bb-b6d19b7d9934", "ratio_to_baseline": 1.8348503001487426, "ratio_to_pr01_prompt_median": 1.9278499185603222, "pr01_prompt_median_seconds": 176.2868271415009, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "PASS", "observations": 19, "failures": 0, "missing_measurements": 0, "agents": {"architect": 1, "generator_security": 1, "generator_cost": 1, "generator_performance": 1, "security_iteration": 15}, "durations": {"count": 19, "median": 19.924321, "p90": 55.053995, "max": 55.106554}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "PASS", "observations": 53, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_security": 3, "generator_performance": 3, "generator_cost": 3, "security_iteration": 41}, "durations": {"count": 53, "median": 55.092615, "p90": 57.670358, "max": 75.575588}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | security#1:5423, cost#1:5118, performance#1:2715 | {} | {} |
| 2 | 3 | {"none": 3} | security#1:4867, performance#1:3553, cost#1:3574 | {} | {} |
| 3 | 6 | {"none": 5, "empty": 1} | cost#1:3020, cost#2:3618, cost#3:4556, security#1:5102, performance#1:unknown, performance#2:5459 | {} | {} |
| 4 | 3 | {"none": 3} | security#1:4454, performance#1:4441, cost#1:4522 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.541340; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.357348, "average_cost_usd": 0.119116, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["ce347154-cc1a-41d4-89d4-5d79e4e8860d", "40c96191-31a0-4f9b-b7bb-b6d19b7d9934", "b937844d-9536-4725-8830-ef89af3a3da5"], "before_remaining_usd": 6.65192049, "after_remaining_usd": 6.29457249}
