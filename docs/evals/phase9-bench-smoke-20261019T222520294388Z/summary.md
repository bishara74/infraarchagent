# Phase 9 benchmark

Status: **INCOMPLETE**

Mode: real

Checks-passed rate among generated packages: **1/9 (11.11%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 1/9; contextual-v1: 1/9. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 8 |
| checks_passed | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 8 |
| validation_failed | 5 |

| Failed check | Count |
|---|---:|
| grafana.panels: Dashboard requires panels | 3 |
| helm.lint: helm optional lint failed | 2 |
| terraform.validate: Cycle | 1 |
| terraform.validate: Unsupported argument | 1 |
| terraform.validate: Terraform configuration diagnostic | 1 |
| terraform.validate: Unsupported block type | 1 |

| Remaining blocking rule | Count |
|---|---:|
| CKV_K8S_40 | 5 |
| KSV-0125 | 5 |
| AWS-0090 | 4 |
| AWS-0164 | 4 |
| CKV_AWS_130 | 4 |
| CKV_AWS_21 | 4 |
| KSV-0117 | 4 |
| CKV_AWS_18 | 4 |
| KSV-0104 | 3 |
| KSV-0118 | 3 |
| KSV-0014 | 3 |
| CKV_AWS_144 | 2 |
| AWS-0104 | 2 |
| AWS-0010 | 2 |
| AWS-0011 | 2 |
| AWS-0052 | 1 |
| AWS-0053 | 1 |
| AWS-0054 | 1 |
| CKV2_AWS_12 | 1 |
| CKV2_AWS_20 | 1 |

Final failure origins: {'unknown': 1, 'generated': 8}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Terraform configuration diagnostic | 1 |
| after_security / accepted / improved | Unsupported block type | 1 |
| after_security / rejected / no_improvement | Cycle | 1 |
| after_security / rejected / no_improvement | Dashboard requires panels | 3 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 1 |
| after_security / rejected / no_improvement | Unsupported block type | 1 |
| after_security / rejected / no_improvement | helm optional lint failed | 2 |
| before_security / accepted / improved | Missing required argument | 1 |
| before_security / rejected / no_improvement | Dashboard requires panels | 3 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| before_security / rejected / no_improvement | Unsupported argument | 1 |
| before_security / rejected / no_improvement | Unsupported block type | 2 |
| before_security / rejected / no_improvement | helm optional lint failed | 2 |
| generation / rejected / invalid_patch | Dashboard requires panels | 2 |
| generation / rejected / invalid_patch | Generation syntax check failed | 2 |
| generation / rejected / invalid_patch | Unsupported argument | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 2 |
| generation / rejected / no_improvement | Dashboard requires panels | 1 |
| generation / rejected / no_improvement | Missing required argument | 1 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 3 |
| generation / rejected / no_improvement | Unsupported block type | 2 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 43 | 0.0814503589999731 | 0.5658742420000635 | 0.976147958999718 |
| final_security_scan | 9 | 7.286719962999996 | 16.330936226000176 | 16.330936226000176 |
| final_validation | 9 | 0.004071122000368632 | 0.47723936700003833 | 0.47723936700003833 |
| generation_gate | 9 | 38.058506684999884 | 58.68745839200028 | 58.68745839200028 |
| initial_validation | 9 | 0.007305973999791604 | 0.6250017659999685 | 0.6250017659999685 |
| post_security_validation | 9 | 0.0037606020000566787 | 0.885831011999926 | 0.885831011999926 |
| security_iteration_verification | 34 | 36.4573735094998 | 50.49218084700078 | 52.30802062800058 |
| validation_repair_round | 20 | 21.657337776000077 | 31.04279663699981 | 37.593845008000244 |

Iteration outcomes: {'attempted_fix_iterations': 34, 'deadline_only_rollbacks': 4, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 6, 'validity_regression_rollbacks': 6}.
Initialization: {'init_runs': 11, 'init_reused': 131, 'reinitializations': 1}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 9, 'packages_unknown': 0, 'init_runs': 11, 'init_reused': 171, 'reinitializations': 1, 'init_seconds': 141.36984017300074, 'validate_seconds': 549.761902188}
Gate outcomes: {'valid': 2, 'invalid': 7}
Init categories: {'initialized': 2, 'validation_cached': 7}
Schema context sizes (characters): {'generator': {'count': 9, 'median': 3434, 'p90': 5503, 'max': 5503}, 'repair': {'count': 20, 'median': 15051.0, 'p90': 15956, 'max': 15999}, 'security': {'count': 49, 'median': 7918, 'p90': 15601, 'max': 15980}}
Security context coverage: {'terraform': {'total': 33, 'positive': 33, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 33}}, 'other': {'total': 16, 'positive': 0, 'zero': 16, 'missing': 0, 'reasons': {'not_terraform': 16}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Cycle', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 4}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 7}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 7}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported block type', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 2 |
| 4+ | 1 |

Phase 9f measured/unknown packages: (9, 0)
Catalogue retained by rule: {'CKV_AWS_103': 1}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 23}, {'template': 'access_logs', 'status': 'retained', 'count': 3}, {'template': 'kms', 'status': 'retained', 'count': 5}, {'template': 'kms', 'status': 'skipped', 'count': 4}]
Template introduced rules: {'CKV_AWS_145': 23, 'CKV_AWS_144': 11}
Partial groups: {'discarded': 18, 'kept': 10, 'unevaluated': 6}
Existing-file proposal recovery: {'normalized': 1, 'retained': 0}
Generation syntax recovery: {'unchanged': 6, 'normalization': 3}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 9, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 49, 'median': 4, 'p90': 12, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 43 | 0.0814503589999731 | 0.5658742420000635 | 0.976147958999718 |
| final_security_scan | 9 | 7.286719962999996 | 16.330936226000176 | 16.330936226000176 |
| final_validation | 9 | 0.004071122000368632 | 0.47723936700003833 | 0.47723936700003833 |
| generation_gate | 9 | 38.058506684999884 | 58.68745839200028 | 58.68745839200028 |
| initial_validation | 9 | 0.007305973999791604 | 0.6250017659999685 | 0.6250017659999685 |
| post_security_validation | 9 | 0.0037606020000566787 | 0.885831011999926 | 0.885831011999926 |
| security_iteration_verification | 34 | 36.4573735094998 | 50.49218084700078 | 52.30802062800058 |
| validation_repair_round | 20 | 21.657337776000077 | 31.04279663699981 | 37.593845008000244 |

Iteration outcomes: {'attempted_fix_iterations': 34, 'deadline_only_rollbacks': 4, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 6, 'validity_regression_rollbacks': 6}.
Initialization: {'init_runs': 11, 'init_reused': 131, 'reinitializations': 1}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 3, "median": 266.48368149099997, "p90": 332.7838196069997, "max": 332.7838196069997}; failed/incomplete: 0.

pr01 threshold: INCOMPLETE.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 53, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_cost": 3, "generator_performance": 3, "generator_security": 3, "security_iteration": 41}, "durations": {"count": 53, "median": 30.087818, "p90": 55.087332, "max": 62.241954}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:4895, performance#1:3910, security#1:3707 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:4057, security#1:4041, performance#1:4444 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:1286, performance#1:1118, security#1:1287 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.322514; unknown costs stay unknown.

First-run affordability advisory: {"measured_first_run_cost_usd": 0.12935845, "remaining_credit_usd": 9.73787809, "planned_runs_remaining": 2, "run_cap_remaining": 2, "projected_further_runs": 2, "assumption": "Projection at first measured cost; fresh guard checks decide."}
