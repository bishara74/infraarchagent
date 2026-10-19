# Package quality

Checks-passed rate among generated packages: **1/29 (3.45%)**.
Legacy labels mapped: 1. Missing variants: 4; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 1/29; contextual-v1: 1/29. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| pending_review | 28 |
| checks_passed | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 27 |
| validation_failed | 22 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 19 |
| terraform.validate: Terraform configuration diagnostic | 10 |
| terraform.validate: Unsupported block type | 6 |
| helm.lint: helm optional lint failed | 6 |
| grafana.panels: Dashboard requires panels | 3 |
| terraform.validate: Missing required argument | 2 |
| terraform.validate: Unsupported attribute | 1 |
| promtool.lint: promtool optional lint failed | 1 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 43 |
| CKV_AWS_130 | 21 |
| AWS-0164 | 20 |
| AWS-0053 | 18 |
| CKV2_AWS_12 | 18 |
| CKV_AWS_91 | 17 |
| CKV_AWS_18 | 17 |
| CKV_AWS_260 | 13 |
| AWS-0132 | 12 |
| CKV_AWS_145 | 12 |
| KSV-0118 | 12 |
| AWS-0090 | 11 |
| CKV_AWS_21 | 11 |
| CKV_AWS_378 | 10 |
| CKV2_AWS_11 | 9 |
| CKV_AWS_144 | 8 |
| AWS-0039 | 8 |
| AWS-0040 | 8 |
| AWS-0041 | 8 |
| AWS-0077 | 8 |

Final failure origins: {'generated': 48}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Dashboard requires panels | 3 |
| after_security / rejected / invalid_patch | Missing required argument | 1 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 3 |
| after_security / rejected / invalid_patch | Unsupported argument | 8 |
| after_security / rejected / invalid_patch | Unsupported attribute | 1 |
| after_security / rejected / invalid_patch | Unsupported block type | 1 |
| after_security / rejected / invalid_patch | helm optional lint failed | 4 |
| after_security / rejected / invalid_patch | promtool optional lint failed | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 2 |
| after_security / rejected / no_improvement | helm optional lint failed | 1 |
| before_security / rejected / invalid_patch | Dashboard requires panels | 3 |
| before_security / rejected / invalid_patch | Missing required argument | 1 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 9 |
| before_security / rejected / invalid_patch | Unsupported argument | 12 |
| before_security / rejected / invalid_patch | Unsupported attribute | 1 |
| before_security / rejected / invalid_patch | Unsupported block type | 6 |
| before_security / rejected / invalid_patch | helm optional lint failed | 6 |
| before_security / rejected / invalid_patch | promtool optional lint failed | 1 |
| before_security / rejected / no_improvement | Unsupported argument | 2 |
| generation / rejected / invalid_patch | Dashboard requires panels | 3 |
| generation / rejected / invalid_patch | Generation syntax check failed | 6 |
| generation / rejected / invalid_patch | Missing required argument | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 9 |
| generation / rejected / invalid_patch | Unsupported argument | 11 |
| generation / rejected / invalid_patch | Unsupported attribute | 1 |
| generation / rejected / invalid_patch | Unsupported block type | 6 |
| generation / rejected / invalid_patch | helm optional lint failed | 6 |
| generation / rejected / invalid_patch | promtool optional lint failed | 1 |
| generation / rejected / no_improvement | Unsupported argument | 3 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 142 | 0.05228676100159646 | 0.19634289300302044 | 0.8405360809992999 |
| final_security_scan | 29 | 5.301197323999077 | 7.185033050998754 | 8.367508132003422 |
| final_validation | 29 | 0.003442614004597999 | 0.3052309679987957 | 0.5723178109983564 |
| generation_gate | 29 | 23.3953002690032 | 36.64279895499931 | 44.02472685599787 |
| initial_validation | 29 | 0.0030640229961136356 | 0.27913053200609284 | 0.3542267640004866 |
| post_security_validation | 29 | 0.002587781003967393 | 0.44193036400247365 | 4.7335922089987434 |
| security_iteration_verification | 115 | 10.368643825007894 | 32.38426261199493 | 50.84316083401063 |
| validation_repair_round | 59 | 8.388891604998207 | 15.274054682005954 | 22.440721694001695 |

Iteration outcomes: {'attempted_fix_iterations': 115, 'deadline_only_rollbacks': 3, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 2}.
Initialization: {'init_runs': 31, 'init_reused': 323, 'reinitializations': 2}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 29, 'packages_unknown': 0, 'init_runs': 31, 'init_reused': 415, 'reinitializations': 2, 'init_seconds': 315.6553304400004, 'validate_seconds': 601.8245731369752}
Gate outcomes: {'invalid': 22, 'valid': 7}
Init categories: {'validation_cached': 22, 'initialized': 7}
Schema context sizes (characters): {'generator': {'count': 29, 'median': 4202, 'p90': 5503, 'max': 5503}, 'repair': {'count': 59, 'median': 15953, 'p90': 15994, 'max': 15999}, 'security': {'count': 140, 'median': 9527.0, 'p90': 12934, 'max': 15896}}
Security context coverage: {'terraform': {'total': 113, 'positive': 113, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 113}}, 'other': {'total': 27, 'positive': 0, 'zero': 27, 'missing': 0, 'reasons': {'not_terraform': 27}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 4}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 8}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 8}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Missing required argument', 'count': 2}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 30}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 45}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 3}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported block type', 'count': 23}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 21}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 3}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 2}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 6 |

Phase 9f measured/unknown packages: (29, 0)
Catalogue retained by rule: {'CKV_AWS_103': 10}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 103}, {'template': 'flow_logs', 'status': 'retained', 'count': 9}, {'template': 'flow_logs', 'status': 'skipped', 'count': 27}, {'template': 'kms', 'status': 'rejected', 'count': 37}, {'template': 'kms', 'status': 'retained', 'count': 8}, {'template': 'kms', 'status': 'skipped', 'count': 12}]
Template introduced rules: {'AWS-0090': 103, 'AWS-0132': 138}
Partial groups: {'discarded': 6, 'kept': 5, 'unevaluated': 13}
Existing-file proposal recovery: {'normalized': 1, 'retained': 1}
Generation syntax recovery: {'unchanged': 21, 'syntax_round_1': 5, 'normalization': 3}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 29, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 140, 'median': 4.0, 'p90': 12, 'max': 12}, 'calls_missing_measurements': 0}]
