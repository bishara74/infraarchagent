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
| validation_failed | 11 |
| unresolved_security_findings | 10 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 11 |
| terraform.validate: Terraform configuration diagnostic | 1 |
| terraform.local_ref: local.prefix is not declared | 1 |
| terraform.validate: Unsupported block type | 1 |

| Remaining blocking rule | Count |
|---|---:|
| CKV_AWS_91 | 9 |
| CKV_AWS_130 | 9 |
| AWS-0053 | 8 |
| AWS-0164 | 8 |
| AWS-0077 | 7 |
| AWS-0104 | 7 |
| CKV2_AWS_12 | 7 |
| CKV_AWS_378 | 6 |
| CKV_AWS_260 | 3 |
| CKV_AWS_157 | 3 |
| AWS-0054 | 2 |
| CKV2_AWS_20 | 2 |
| CKV_AWS_103 | 2 |
| CKV_AWS_2 | 2 |
| AWS-0052 | 1 |
| TERRAFORM_SYNTAX | 1 |

Final failure origins: {'generated': 14}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / new_blocking_findings | Unsupported block type | 1 |
| after_security / rejected / new_blocking_findings | local.prefix is not declared | 1 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / rejected / no_improvement | Unsupported argument | 8 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| before_security / rejected / no_improvement | Unsupported argument | 9 |
| before_security / rejected / no_improvement | Unsupported block type | 1 |
| before_security / rejected / no_improvement | local.prefix is not declared | 1 |
| generation / accepted / improved | Reference to undeclared resource | 1 |
| generation / accepted / improved | Terraform configuration diagnostic | 1 |
| generation / rejected / invalid_patch | Unsupported argument | 1 |
| generation / rejected / new_blocking_findings | Unsupported block type | 1 |
| generation / rejected / new_blocking_findings | local.prefix is not declared | 1 |
| generation / rejected / no_improvement | Unsupported argument | 8 |
| generation / stopped / round_limit | unknown | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 42 | 0.1720312000006743 | 0.951430122999227 | 1.091612518999682 |
| final_security_scan | 12 | 7.15925306850022 | 13.347980463999193 | 14.285626754000987 |
| final_validation | 12 | 0.006600960000469058 | 0.009861729999101954 | 0.012338213000475662 |
| generation_gate | 12 | 58.817899419999776 | 64.73987830000078 | 80.68769021200023 |
| initial_validation | 12 | 0.00498488949961029 | 0.012575422999361763 | 0.020206477000101586 |
| post_security_validation | 12 | 0.007138247498915007 | 0.013026066999373143 | 0.02473837499928777 |
| security_iteration_verification | 45 | 43.000212425004065 | 53.91607726099937 | 54.72378266399937 |
| validation_repair_round | 33 | 11.912663037999664 | 28.74986815000011 | 67.97272502799933 |

Iteration outcomes: {'attempted_fix_iterations': 45, 'deadline_only_rollbacks': 25, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 16, 'init_reused': 165, 'reinitializations': 3}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 16, 'init_reused': 222, 'reinitializations': 3, 'init_seconds': 149.5177145460002, 'validate_seconds': 1049.571356814984}
Gate outcomes: {'invalid': 11, 'valid': 1}
Init categories: {'validation_cached': 10, 'initialized': 1, 'reused': 1}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 5503.0, 'p90': 5503, 'max': 5503}, 'repair': {'count': 34, 'median': 15973.0, 'p90': 15994, 'max': 15998}, 'security': {'count': 30, 'median': 11359.5, 'p90': 13318, 'max': 15961}}
Security context coverage: {'terraform': {'total': 30, 'positive': 30, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 30}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 12}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': '', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 25}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'reference_regression', 'error_class': 'unknown', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 1 |

Phase 9f measured/unknown packages: (12, 0)
Catalogue retained by rule: {'AWS-0028': 6, 'AWS-0131': 6, 'CKV_AWS_8': 6, 'CKV_AWS_103': 5}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 37}, {'template': 'access_logs', 'status': 'retained', 'count': 1}, {'template': 'flow_logs', 'status': 'rejected', 'count': 5}, {'template': 'flow_logs', 'status': 'retained', 'count': 8}, {'template': 'kms', 'status': 'rejected', 'count': 5}, {'template': 'kms', 'status': 'retained', 'count': 9}]
Template introduced rules: {'CKV_AWS_18': 32, 'CKV_AWS_145': 25, 'AWS-0132': 32, 'CKV_AWS_144': 10}
Partial groups: {'kept': 6, 'discarded': 4, 'unevaluated': 1}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'syntax_round_1': 2, 'unchanged': 8, 'normalization': 2}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 12, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 30, 'median': 3.0, 'p90': 5, 'max': 5}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 42 | 0.1720312000006743 | 0.951430122999227 | 1.091612518999682 |
| final_security_scan | 12 | 7.15925306850022 | 13.347980463999193 | 14.285626754000987 |
| final_validation | 12 | 0.006600960000469058 | 0.009861729999101954 | 0.012338213000475662 |
| generation_gate | 12 | 58.817899419999776 | 64.73987830000078 | 80.68769021200023 |
| initial_validation | 12 | 0.00498488949961029 | 0.012575422999361763 | 0.020206477000101586 |
| post_security_validation | 12 | 0.007138247498915007 | 0.013026066999373143 | 0.02473837499928777 |
| security_iteration_verification | 43 | 42.83802165199813 | 53.20379395200143 | 54.541567418998966 |
| validation_repair_round | 33 | 11.912663037999664 | 28.74986815000011 | 67.97272502799933 |

Iteration outcomes: {'attempted_fix_iterations': 43, 'deadline_only_rollbacks': 23, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 16, 'init_reused': 158, 'reinitializations': 3}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 321.9223276289995, "p90": 337.6899233080003, "max": 337.6899233080003}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "e007d01c-35b1-4939-ab43-52e1fb086001", "ratio_to_baseline": 2.024947737190979, "ratio_to_pr01_prompt_median": 2.0794701288193576, "pr01_prompt_median_seconds": 162.3922934154998, "pr01_reference_count": 4}

Cohort references: {"run_id": "b0f4701c-ffff-420f-bebd-64df235c1187", "ratio_to_baseline": 1.9599465459073915, "ratio_to_pr01_prompt_median": 2.0127187588312117, "pr01_prompt_median_seconds": 162.3922934154998, "pr01_reference_count": 4}

Cohort references: {"run_id": "83e65ace-224c-4c93-8ea6-7e69d817d2a5", "ratio_to_baseline": 1.9008490768807509, "ratio_to_pr01_prompt_median": 1.9520300707862541, "pr01_prompt_median_seconds": 162.3922934154998, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "PASS", "observations": 16, "failures": 0, "missing_measurements": 0, "agents": {"architect": 1, "generator_performance": 1, "generator_security": 1, "generator_cost": 1, "security_iteration": 12}, "durations": {"count": 16, "median": 12.710432, "p90": 46.728764, "max": 49.636219}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "PASS", "observations": 57, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_performance": 3, "generator_security": 3, "generator_cost": 3, "security_iteration": 45}, "durations": {"count": 57, "median": 55.201475, "p90": 63.430037, "max": 84.195562}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | performance#1:3829, security#1:3871, cost#1:3823 | {} | {} |
| 2 | 3 | {"none": 3} | security#1:3588, cost#1:3816, performance#1:3841 | {} | {} |
| 3 | 3 | {"none": 3} | performance#1:4563, cost#1:3580, security#1:3619 | {} | {} |
| 4 | 3 | {"none": 3} | performance#1:3013, security#1:4104, cost#1:4593 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.498684; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.3678337, "average_cost_usd": 0.12261123333333333, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["b0f4701c-ffff-420f-bebd-64df235c1187", "83e65ace-224c-4c93-8ea6-7e69d817d2a5", "e007d01c-35b1-4939-ab43-52e1fb086001"], "before_remaining_usd": 8.34100404, "after_remaining_usd": 7.97317034}
