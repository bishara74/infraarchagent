# Package quality

Checks-passed rate among generated packages: **1/9 (11.11%)**.
Legacy labels mapped: 1. Missing variants: 24; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 1/9; contextual-v1: 1/9. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 8 |
| checks_passed | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 6 |
| validation_failed | 5 |

| Failed check | Count |
|---|---:|
| helm.lint: helm optional lint failed | 3 |
| terraform.validate: Terraform configuration diagnostic | 2 |
| terraform.validate: Cycle | 1 |

| Remaining blocking rule | Count |
|---|---:|
| CKV_AWS_18 | 6 |
| CKV_AWS_144 | 4 |
| AWS-0104 | 4 |
| AWS-0164 | 4 |
| AWS-0053 | 3 |
| AWS-0090 | 3 |
| AWS-0132 | 3 |
| CKV_AWS_130 | 3 |
| CKV_AWS_145 | 3 |
| CKV_AWS_21 | 3 |
| CKV_AWS_378 | 3 |
| CKV2_AWS_11 | 2 |
| CKV2_AWS_20 | 2 |
| CKV_AWS_260 | 2 |
| CKV_AWS_91 | 2 |
| CKV_AWS_354 | 2 |
| AWS-0077 | 1 |
| AWS-0345 | 1 |
| AWS-0054 | 1 |
| CKV2_AWS_12 | 1 |

Final failure origins: {'generated': 5, 'unknown': 1}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Unsupported argument | 2 |
| after_security / accepted / improved | helm optional lint failed | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 1 |
| after_security / rejected / no_improvement | Cycle | 1 |
| after_security / rejected / no_improvement | helm optional lint failed | 1 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Invalid resource type | 1 |
| before_security / accepted / improved | helm optional lint failed | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| before_security / rejected / invalid_patch | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | helm optional lint failed | 1 |
| before_security / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |
| before_security / rejected / no_improvement | Invalid resource type | 1 |
| before_security / rejected / no_improvement | helm optional lint failed | 2 |
| generation / rejected / invalid_patch | Generation syntax check failed | 3 |
| generation / rejected / invalid_patch | Invalid resource type | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 1 |
| generation / rejected / invalid_patch | helm optional lint failed | 3 |
| generation / rejected / new_blocking_findings | Invalid resource type | 1 |
| generation / rejected / new_blocking_findings | Terraform configuration diagnostic | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 39 | 0.060429304001445416 | 0.3100713759995415 | 0.7358206200005952 |
| final_security_scan | 9 | 4.054718937994039 | 6.564914622002107 | 6.564914622002107 |
| final_validation | 9 | 0.003712056997756008 | 0.2813665219946415 | 0.2813665219946415 |
| generation_gate | 9 | 36.38067308999598 | 60.45757596399926 | 60.45757596399926 |
| initial_validation | 9 | 0.005641668998578098 | 0.2793766390022938 | 0.2793766390022938 |
| post_security_validation | 9 | 0.00444896499539027 | 0.46551047800312517 | 0.46551047800312517 |
| security_iteration_verification | 31 | 23.71133067300252 | 32.967640006012516 | 35.42415359199367 |
| validation_repair_round | 19 | 30.109537698997883 | 41.80163588299911 | 56.18776279299345 |

Iteration outcomes: {'attempted_fix_iterations': 31, 'deadline_only_rollbacks': 2, 'deadline_before_candidate': 1, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 1}.
Initialization: {'init_runs': 19, 'init_reused': 108, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 9, 'packages_unknown': 0, 'init_runs': 22, 'init_reused': 141, 'reinitializations': 0, 'init_seconds': 69.08436777399038, 'validate_seconds': 281.7787619689989}
Gate outcomes: {'valid': 3, 'invalid': 6}
Init categories: {'initialized': 3, 'unknown': 1, 'validation_cached': 4, 'reused': 1}
Schema context sizes (characters): {'generator': {'count': 9, 'median': 3434, 'p90': 5503, 'max': 5503}, 'repair': {'count': 20, 'median': 15911.0, 'p90': 15982, 'max': 15992}, 'security': {'count': 32, 'median': 10539.5, 'p90': 13427, 'max': 15978}}
Security context coverage: {'terraform': {'total': 30, 'positive': 30, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 30}}, 'other': {'total': 2, 'positive': 0, 'zero': 2, 'missing': 0, 'reasons': {'not_terraform': 2}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Cycle', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 5}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 10}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 3}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Invalid resource type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Cycle', 'count': 1}, {'outcome': 'stopped', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 3 |

Phase 9f measured/unknown packages: (9, 0)
Catalogue retained by rule: {'CKV_AWS_103': 2}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 28}, {'template': 'flow_logs', 'status': 'retained', 'count': 2}, {'template': 'flow_logs', 'status': 'skipped', 'count': 6}, {'template': 'kms', 'status': 'rejected', 'count': 15}, {'template': 'kms', 'status': 'retained', 'count': 2}]
Template introduced rules: {'AWS-0090': 28, 'AWS-0132': 43}
Partial groups: {'discarded': 5, 'kept': 4}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 9}
Fixer model limits and calls: [{'model': 'anthropic/claude-haiku-5.5', 'sessions': 9, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 32, 'median': 4.0, 'p90': 7, 'max': 12}, 'calls_missing_measurements': 0}]
