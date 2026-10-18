# Phase 9 benchmark

Status: **PASS**

Mode: real

Production-ready rate among generated packages: **1/24 (4.17%)**.
Missing variants: 6; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 23 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| unresolved_security_findings | 22 |
| validation_failed | 18 |

| Failed check | Count |
|---|---:|
| terraform.validate: Unsupported argument | 11 |
| helm.lint: helm optional lint failed | 10 |
| terraform.validate: Terraform configuration diagnostic | 9 |
| terraform.validate: Missing required argument | 6 |
| ansible-lint.lint: ansible-lint optional lint failed | 5 |
| terraform.validate: Unsupported block type | 4 |
| terraform.validate: Reference to undeclared resource | 3 |
| terraform.validate: Unsupported attribute | 2 |
| grafana.panels: Dashboard requires panels | 2 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 20 |
| KSV-0118 | 18 |
| CKV2_AWS_12 | 13 |
| CKV2_AWS_11 | 12 |
| AWS-0164 | 12 |
| CKV_AWS_130 | 12 |
| CKV_AWS_18 | 11 |
| CKV_K8S_40 | 10 |
| CKV_K8S_10 | 9 |
| CKV_K8S_11 | 9 |
| CKV_K8S_12 | 9 |
| CKV_K8S_13 | 9 |
| CKV_K8S_20 | 9 |
| CKV_K8S_23 | 9 |
| KSV-0001 | 9 |
| KSV-0012 | 9 |
| KSV-0014 | 9 |
| KSV-0104 | 9 |
| KSV-0125 | 9 |
| CKV_AWS_144 | 9 |

Final failure origins: {'generated': 52}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / accepted / improved | Terraform configuration diagnostic | 1 |
| after_security / accepted / improved | Unsupported argument | 1 |
| after_security / accepted / improved | Unsupported block type | 1 |
| after_security / rejected / invalid_patch | Dashboard requires panels | 2 |
| after_security / rejected / invalid_patch | Missing required argument | 1 |
| after_security / rejected / invalid_patch | Reference to undeclared resource | 2 |
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| after_security / rejected / invalid_patch | Unsupported argument | 8 |
| after_security / rejected / invalid_patch | Unsupported attribute | 1 |
| after_security / rejected / invalid_patch | ansible-lint optional lint failed | 4 |
| after_security / rejected / invalid_patch | helm optional lint failed | 9 |
| after_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| after_security / stopped / round_limit | unknown | 1 |
| before_security / accepted / improved | Terraform configuration diagnostic | 1 |
| before_security / accepted / improved | Unsupported block type | 1 |
| before_security / rejected / invalid_patch | Dashboard requires panels | 2 |
| before_security / rejected / invalid_patch | Missing required argument | 4 |
| before_security / rejected / invalid_patch | Reference to undeclared resource | 2 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 7 |
| before_security / rejected / invalid_patch | Unsupported argument | 12 |
| before_security / rejected / invalid_patch | Unsupported attribute | 2 |
| before_security / rejected / invalid_patch | Unsupported block type | 4 |
| before_security / rejected / invalid_patch | ansible-lint optional lint failed | 4 |
| before_security / rejected / invalid_patch | helm optional lint failed | 10 |
| generation / rejected / invalid_patch | Dashboard requires panels | 2 |
| generation / rejected / invalid_patch | Generation syntax check failed | 11 |
| generation / rejected / invalid_patch | Missing required argument | 4 |
| generation / rejected / invalid_patch | Reference to undeclared resource | 2 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 7 |
| generation / rejected / invalid_patch | Unsupported argument | 11 |
| generation / rejected / invalid_patch | Unsupported attribute | 2 |
| generation / rejected / invalid_patch | Unsupported block type | 4 |
| generation / rejected / invalid_patch | ansible-lint optional lint failed | 4 |
| generation / rejected / invalid_patch | helm optional lint failed | 10 |
| generation / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| generation / rejected / no_improvement | Unsupported argument | 1 |
| generation / rejected / no_improvement | Unsupported block type | 1 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 118 | 0.029335087499930523 | 0.08560382900031982 | 0.5765045850002934 |
| final_security_scan | 24 | 4.938701545998811 | 6.650523837997753 | 7.2165928130016255 |
| final_validation | 24 | 0.1808682909977506 | 1.7159238130006997 | 3.6749039770002128 |
| generation_gate | 24 | 19.788142770999002 | 26.492539271999703 | 27.826753510000344 |
| initial_validation | 24 | 0.2878962884997236 | 2.532389782001701 | 3.555138504001661 |
| post_security_validation | 24 | 0.11972187800165557 | 3.1410089190030703 | 3.649152812002285 |
| security_iteration_verification | 95 | 7.410349476000192 | 28.372477014014294 | 50.50675335099913 |
| validation_repair_round | 51 | 7.820754869000666 | 9.892715854002745 | 17.065897821999897 |

Iteration outcomes: {'attempted_fix_iterations': 95, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 3, 'validity_regression_rollbacks': 3}.
Initialization: {'init_runs': 48, 'init_reused': 222, 'reinitializations': 2}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 24, 'packages_unknown': 0, 'init_runs': 54, 'init_reused': 291, 'reinitializations': 2, 'init_seconds': 165.1201025559967, 'validate_seconds': 395.46787359298105}
Gate outcomes: {'invalid': 19, 'valid': 5}
Init categories: {'validation_cached': 17, 'unknown': 2, 'initialized': 5}
Schema context sizes (characters): {'generator': {'count': 24, 'median': 3434.0, 'p90': 5503, 'max': 5503}, 'repair': {'count': 52, 'median': 15941.5, 'p90': 15986, 'max': 15993}, 'security': {'count': 133, 'median': 8710, 'p90': 12214, 'max': 13566}}
Security context coverage: {'terraform': {'total': 94, 'positive': 94, 'zero': 0, 'missing': 0, 'reasons': {'schema_available': 94}}, 'other': {'total': 39, 'positive': 0, 'zero': 39, 'missing': 0, 'reasons': {'not_terraform': 39}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 7}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 9}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported block type', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 7}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Missing required argument', 'count': 10}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Reference to undeclared resource', 'count': 6}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 20}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 35}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported attribute', 'count': 7}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported block type', 'count': 13}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 17}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'new_blocking_findings,iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Missing required argument', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Terraform configuration diagnostic', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported argument', 'count': 2}, {'outcome': 'rolled_back', 'reason': 'terraform_regression', 'error_class': 'Unsupported block type', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Unsupported argument', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 2 |
| 4+ | 3 |

Phase 9f measured/unknown packages: (24, 0)
Catalogue retained by rule: {'CKV_AWS_103': 3, 'AWS-0177': 1, 'CKV_AWS_293': 1}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 58}, {'template': 'flow_logs', 'status': 'retained', 'count': 12}, {'template': 'flow_logs', 'status': 'skipped', 'count': 36}, {'template': 'kms', 'status': 'rejected', 'count': 16}, {'template': 'kms', 'status': 'retained', 'count': 9}, {'template': 'kms', 'status': 'skipped', 'count': 14}]
Template introduced rules: {'AWS-0090': 58, 'AWS-0132': 74}
Partial groups: {'discarded': 7, 'kept': 9, 'unevaluated': 3}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 21, 'normalization': 1, 'syntax_round_2': 1, 'syntax_round_1': 1}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 24, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 133, 'median': 4, 'p90': 12, 'max': 12}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 118 | 0.029335087499930523 | 0.08560382900031982 | 0.5765045850002934 |
| final_security_scan | 24 | 4.938701545998811 | 6.650523837997753 | 7.2165928130016255 |
| final_validation | 24 | 0.1808682909977506 | 1.7159238130006997 | 3.6749039770002128 |
| generation_gate | 24 | 19.788142770999002 | 26.492539271999703 | 27.826753510000344 |
| initial_validation | 24 | 0.2878962884997236 | 2.532389782001701 | 3.555138504001661 |
| post_security_validation | 24 | 0.11972187800165557 | 3.1410089190030703 | 3.649152812002285 |
| security_iteration_verification | 95 | 7.410349476000192 | 28.372477014014294 | 50.50675335099913 |
| validation_repair_round | 51 | 7.820754869000666 | 9.892715854002745 | 17.065897821999897 |

Iteration outcomes: {'attempted_fix_iterations': 95, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 3, 'validity_regression_rollbacks': 3}.
Initialization: {'init_runs': 48, 'init_reused': 222, 'reinitializations': 2}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 121.09235275599985, "p90": 161.1243009990012, "max": 179.96733002999827}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 5 | {"none": 5} | performance#1:3474, performance#2:3137, cost#1:3526, security#1:3148, security#2:4006 | {"performance": "incomplete_package"} | {} |
| 2 | 4 | {"none": 4} | security#1:3671, performance#1:3100, cost#1:3791, cost#2:3911 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:1258, security#1:1493, performance#1:1639 | {} | {} |
| 4 | 6 | {"none": 6} | cost#1:3503, cost#2:2613, performance#1:2563, performance#2:3324, security#1:2813, security#2:4550 | {"cost": "incomplete_package"} | {} |
| 5 | 3 | {"none": 3} | performance#1:4400, security#1:3639, cost#1:3713 | {} | {} |
| 6 | 3 | {"none": 3} | performance#1:1608, security#1:1249, cost#1:1582 | {} | {} |
| 7 | 5 | {"none": 5} | security#1:3954, security#2:3552, performance#1:3132, performance#2:3585, cost#1:3379 | {"security": "incomplete_package", "performance": "incomplete_package"} | {} |
| 8 | 5 | {"none": 5} | performance#1:2736, performance#2:2519, cost#1:3869, security#1:3049, security#2:3425 | {"performance": "incomplete_package"} | {} |
| 9 | 3 | {"none": 3} | performance#1:1578, cost#1:1628, security#1:1737 | {} | {} |
| 10 | 4 | {"none": 4} | cost#1:3333, cost#2:3310, performance#1:3364, security#1:4070 | {"cost": "incomplete_package"} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.931143; unknown costs stay unknown.
