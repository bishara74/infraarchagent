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
| validation_failed | 9 |

| Failed check | Count |
|---|---:|
| terraform.validate: Invalid multi-line string | 7 |
| terraform.validate: Terraform configuration diagnostic | 6 |
| terraform.validate: Unsupported argument | 5 |
| terraform.validate: Invalid single-argument block definition | 3 |
| document.parse: Document could not be parsed | 2 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0104 | 18 |
| TERRAFORM_SYNTAX | 12 |
| CKV_AWS_130 | 10 |
| AWS-0164 | 8 |
| AWS-0053 | 6 |
| CKV_AWS_91 | 6 |
| CKV_AWS_260 | 5 |
| CKV2_AWS_12 | 5 |
| AWS-0132 | 4 |
| CKV_AWS_145 | 4 |
| CKV_AWS_18 | 3 |
| AWS-0077 | 3 |
| CKV_AWS_157 | 3 |
| CKV_AWS_354 | 3 |
| AWS-0090 | 2 |
| CKV_AWS_144 | 2 |
| CKV_AWS_21 | 2 |
| AWS-0054 | 1 |
| CKV2_AWS_20 | 1 |
| CKV_AWS_103 | 1 |

Final failure origins: {'generated': 20, 'unknown': 3}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|
| after_security / rejected / invalid_patch | Terraform configuration diagnostic | 2 |
| after_security / rejected / invalid_patch | Unsupported argument | 1 |
| after_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| before_security / accepted / improved | Missing required argument | 1 |
| before_security / accepted / improved | Unsupported argument | 1 |
| before_security / rejected / invalid_patch | Document could not be parsed | 2 |
| before_security / rejected / invalid_patch | Invalid multi-line string | 1 |
| before_security / rejected / invalid_patch | Invalid single-argument block definition | 2 |
| before_security / rejected / invalid_patch | Terraform configuration diagnostic | 5 |
| before_security / rejected / invalid_patch | Unsupported argument | 2 |
| before_security / rejected / no_improvement | Invalid single-argument block definition | 1 |
| before_security / rejected / no_improvement | Terraform configuration diagnostic | 1 |
| before_security / rejected / no_improvement | Unsupported argument | 1 |
| generation / rejected / invalid_patch | Document could not be parsed | 2 |
| generation / rejected / invalid_patch | Invalid multi-line string | 1 |
| generation / rejected / invalid_patch | Invalid single-argument block definition | 3 |
| generation / rejected / invalid_patch | Missing required argument | 1 |
| generation / rejected / invalid_patch | Terraform configuration diagnostic | 5 |
| generation / rejected / invalid_patch | Unsupported argument | 3 |

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 59 | 0.08567651599878445 | 0.3113304500002414 | 1.1343296599952737 |
| final_security_scan | 12 | 6.346410307000042 | 10.303016575999209 | 12.119209108997893 |
| final_validation | 12 | 0.16412445349851623 | 3.032720472998335 | 5.702813989999413 |
| generation_gate | 12 | 27.992309301502246 | 35.82143787200039 | 49.990478615996835 |
| initial_validation | 12 | 0.16572314649965847 | 0.6499939529967378 | 0.7263854170014383 |
| post_security_validation | 12 | 0.14196000199808623 | 1.0032607950051897 | 4.7714139750023605 |
| security_iteration_verification | 48 | 10.456425274991489 | 32.02283800600708 | 46.0864812600048 |
| validation_repair_round | 23 | 11.745637595995504 | 35.12524792199838 | 47.206021455000155 |

Iteration outcomes: {'attempted_fix_iterations': 48, 'deadline_only_rollbacks': 1, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 1, 'validity_regression_rollbacks': 1}.
Initialization: {'init_runs': 42, 'init_reused': 87, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 56, 'init_reused': 113, 'reinitializations': 0, 'init_seconds': 131.3031568740189, 'validate_seconds': 290.7082060139728}
Gate outcomes: {'invalid': 9, 'valid': 3}
Init categories: {'validation_cached': 4, 'unknown': 1, 'initialized': 3, 'syntax': 4}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 5313.0, 'p90': 5313, 'max': 5313}, 'repair': {'count': 23, 'median': 15943, 'p90': 15989, 'max': 15996}, 'security': {'count': 47, 'median': 10847, 'p90': 13582, 'max': 15971}}
Security context coverage: {'terraform': {'total': 47, 'positive': 39, 'zero': 8, 'missing': 0, 'reasons': {'schema_available': 39, 'unparseable_document': 8}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: [{'outcome': 'accepted', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 2}, {'outcome': 'accepted', 'reason': '', 'error_class': 'Unsupported argument', 'count': 1}, {'outcome': 'accepted', 'reason': '', 'error_class': 'unknown', 'count': 6}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Invalid multi-line string', 'count': 4}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Invalid single-argument block definition', 'count': 11}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Terraform configuration diagnostic', 'count': 22}, {'outcome': 'no_change', 'reason': '', 'error_class': 'Unsupported argument', 'count': 10}, {'outcome': 'no_change', 'reason': '', 'error_class': 'unknown', 'count': 6}, {'outcome': 'rolled_back', 'reason': 'iteration_deadline', 'error_class': 'unknown', 'count': 1}, {'outcome': 'rolled_back', 'reason': 'terraform_regression,iteration_deadline', 'error_class': 'Reference to undeclared resource', 'count': 1}]

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 3 |

Phase 9f measured/unknown packages: (12, 0)
Catalogue retained by rule: {'CKV_AWS_103': 4}
Template outcomes: [{'template': 'access_logs', 'status': 'rejected', 'count': 32}, {'template': 'kms', 'status': 'proposed', 'count': 1}, {'template': 'kms', 'status': 'rejected', 'count': 12}, {'template': 'kms', 'status': 'retained', 'count': 3}, {'template': 'kms', 'status': 'skipped', 'count': 4}]
Template introduced rules: {'AWS-0090': 32, 'AWS-0132': 44}
Partial groups: {'discarded': 1, 'kept': 1, 'unevaluated': 1}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Fixer model limits and calls: [{'model': 'openai/gpt-oss-120b:nitro', 'sessions': 12, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 47, 'median': 3, 'p90': 5, 'max': 8}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 59 | 0.08567651599878445 | 0.3113304500002414 | 1.1343296599952737 |
| final_security_scan | 12 | 6.346410307000042 | 10.303016575999209 | 12.119209108997893 |
| final_validation | 12 | 0.16412445349851623 | 3.032720472998335 | 5.702813989999413 |
| generation_gate | 12 | 27.992309301502246 | 35.82143787200039 | 49.990478615996835 |
| initial_validation | 12 | 0.16572314649965847 | 0.6499939529967378 | 0.7263854170014383 |
| post_security_validation | 12 | 0.14196000199808623 | 1.0032607950051897 | 4.7714139750023605 |
| security_iteration_verification | 48 | 10.456425274991489 | 32.02283800600708 | 46.0864812600048 |
| validation_repair_round | 23 | 11.745637595995504 | 35.12524792199838 | 47.206021455000155 |

Iteration outcomes: {'attempted_fix_iterations': 48, 'deadline_only_rollbacks': 1, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 1, 'validity_regression_rollbacks': 1}.
Initialization: {'init_runs': 42, 'init_reused': 87, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

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
| 1 | 3 | {"none": 3} | security#1:5418, cost#1:3953, performance#1:4739 | {} | {} |
| 2 | 3 | {"none": 3} | security#1:4524, performance#1:4592, cost#1:4692 | {} | {} |
| 3 | 3 | {"none": 3} | security#1:3355, cost#1:4679, performance#1:4931 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:4358, performance#1:4212, security#1:4035 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.569316; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.4257765, "average_cost_usd": 0.1419255, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["e986acdc-148a-4c6e-a26f-c818304637a6", "2feb779a-4321-49f3-ad25-15e1813db8e4", "6f80d5cb-e971-4022-a83e-0e135402a960"], "before_remaining_usd": 6.14330704, "after_remaining_usd": 5.7175305399999985}
