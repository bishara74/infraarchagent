# Phase 9 benchmark

Status: **INCOMPLETE**

Mode: real

Production-ready rate among generated packages: **1/29 (3.45%)**.
Missing variants: 1; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 28 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 27 |
| validation_failed | 22 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 19 |
| terraform.validate: Terraform configuration diagnostic | 10 |
| helm.lint: helm optional lint failed | 6 |
| terraform.validate: Unsupported block type | 6 |
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
| CKV_AWS_18 | 17 |
| CKV_AWS_91 | 17 |
| CKV_AWS_260 | 13 |
| AWS-0132 | 12 |
| CKV_AWS_145 | 12 |
| KSV-0118 | 12 |
| AWS-0090 | 11 |
| CKV_AWS_21 | 11 |
| CKV_AWS_378 | 10 |
| CKV2_AWS_11 | 9 |
| AWS-0054 | 8 |
| CKV2_AWS_20 | 8 |
| CKV_AWS_103 | 8 |
| CKV_AWS_2 | 8 |
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
Gate outcomes: {'valid': 7, 'invalid': 22}
Init categories: {'initialized': 7, 'validation_cached': 22}
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
Generation syntax recovery: {'unchanged': 21, 'normalization': 3, 'syntax_round_1': 5}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 29, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 140, 'median': 4.0, 'p90': 12, 'max': 12}, 'calls_missing_measurements': 0}]

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

pr01: {"count": 10, "median": 134.6745607595003, "p90": 191.43056716200226, "max": 203.15571544499835}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 184, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_cost": 10, "generator_performance": 10, "generator_security": 10, "security_iteration": 144}, "durations": {"count": 184, "median": 12.2826045, "p90": 37.671314, "max": 55.046981}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:4570, performance#1:5233, security#1:4040 | {} | {} |
| 2 | 6 | {"none": 6} | performance#1:2197, performance#2:2723, performance#3:3045, cost#1:4361, security#1:2971, security#2:4816 | {"performance": "incomplete_package"} | {} |
| 3 | 3 | {"none": 3} | cost#1:1525, security#1:1710, performance#1:2093 | {} | {} |
| 4 | 3 | {"none": 3} | performance#1:3853, security#1:4457, cost#1:4239 | {} | {} |
| 5 | 3 | {"none": 3} | security#1:3670, cost#1:3623, performance#1:3500 | {} | {} |
| 6 | 3 | {"none": 3} | security#1:1873, performance#1:1238, cost#1:1972 | {} | {} |
| 7 | 3 | {"none": 3} | security#1:3917, cost#1:3908, performance#1:3121 | {} | {} |
| 8 | 6 | {"none": 6} | security#1:4854, performance#1:3368, performance#2:4554, cost#1:3426, cost#2:3803, cost#3:4399 | {} | {} |
| 9 | 3 | {"none": 3} | security#1:1586, cost#1:1380, performance#1:1455 | {} | {} |
| 10 | 3 | {"none": 3} | security#1:5469, performance#1:5008, cost#1:4013 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $1.135465; unknown costs stay unknown.

Stopped: PR-03 baseline did not complete successfully.
