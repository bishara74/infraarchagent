# Phase 9 benchmark

Status: **FAIL**

Mode: stub rehearsal; system overhead only.

Checks-passed rate among generated packages: **42/42 (100.00%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 42/42; contextual-v1: 42/42. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| checks_passed | 42 |

| Review reason | Count |
|---|---:|

| Failed check | Count |
|---|---:|

| Remaining blocking rule | Count |
|---|---:|

Final failure origins: {}

| Repair phase / outcome / reason | Error class | Count |
|---|---|---:|

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 42 | 0.0850113854976371 | 0.2074817019965849 | 1.4447626339970157 |
| final_security_scan | 42 | 10.099610997996933 | 18.712185905002116 | 20.081666870995832 |
| final_validation | 42 | 0.0023600794993399177 | 0.008284232004371006 | 0.01686004600196611 |
| generation_gate | 42 | 0.27974229349638335 | 0.4908281329990132 | 0.7035817510040943 |
| initial_validation | 42 | 0.0020892005013593007 | 0.0034676989962463267 | 0.006003372996929102 |
| post_security_validation | 42 | 0.0018084675029967912 | 0.007310638000490144 | 0.028471944002376404 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 42, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 42, 'packages_unknown': 0, 'init_runs': 42, 'init_reused': 126, 'reinitializations': 0, 'init_seconds': 4.259888628992485, 'validate_seconds': 4.389970888012613}
Gate outcomes: {'valid': 42}
Init categories: {'initialized': 42}
Schema context sizes (characters): {'generator': {'count': 42, 'median': 2746.0, 'p90': 2746, 'max': 2746}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security context coverage: {'terraform': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: []

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 0 |

Phase 9f measured/unknown packages: (42, 0)
Catalogue retained by rule: {}
Template outcomes: []
Template introduced rules: {}
Partial groups: {}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 42}
Fixer model limits and calls: [{'model': 'stub', 'sessions': 42, 'fix_attempt_timeout_seconds': [90.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 42 | 0.0850113854976371 | 0.2074817019965849 | 1.4447626339970157 |
| final_security_scan | 42 | 10.099610997996933 | 18.712185905002116 | 20.081666870995832 |
| final_validation | 42 | 0.0023600794993399177 | 0.008284232004371006 | 0.01686004600196611 |
| generation_gate | 42 | 0.27974229349638335 | 0.4908281329990132 | 0.7035817510040943 |
| initial_validation | 42 | 0.0020892005013593007 | 0.0034676989962463267 | 0.006003372996929102 |
| post_security_validation | 42 | 0.0018084675029967912 | 0.007310638000490144 | 0.028471944002376404 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 42, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Separate scripted-fix offline verification rehearsal (excluded from quality rates and PR thresholds).

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 0 | unknown | unknown | unknown |
| final_security_scan | 0 | unknown | unknown | unknown |
| final_validation | 0 | unknown | unknown | unknown |
| generation_gate | 0 | unknown | unknown | unknown |
| initial_validation | 0 | unknown | unknown | unknown |
| post_security_validation | 0 | unknown | unknown | unknown |
| security_iteration_verification | 6 | 15.763849595507054 | 32.6452550660033 | 32.6452550660033 |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 6, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 3, 'init_reused': 9, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 21.089729495000938, "p90": 25.443249298994488, "max": 25.52553040500061}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 40.30773211850101, "p90": 41.091245670002536, "max": 41.091245670002536}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "81470a4c-d898-4dd7-a7b6-5631b9f761f9", "ratio_to_baseline": 2.5265250866650377, "ratio_to_pr01_prompt_median": 2.1331445976598578, "pr01_prompt_median_seconds": 19.194360739500553, "pr01_reference_count": 4}

Cohort references: {"run_id": "b3e9359c-f76a-42c2-b082-50125f6dd954", "ratio_to_baseline": 2.4479587701862036, "ratio_to_pr01_prompt_median": 2.0668110732316163, "pr01_prompt_median_seconds": 19.194360739500553, "pr01_reference_count": 4}

Cohort references: {"run_id": "9ce48736-7e7a-4827-9e9c-3a0c76efc505", "ratio_to_baseline": 2.5355896685330275, "ratio_to_pr01_prompt_median": 2.140797822218681, "pr01_prompt_median_seconds": 19.194360739500553, "pr01_reference_count": 4}

pr03 threshold: FAIL.

pr04: {"count": 10, "median": 1.144391601505049, "p90": 1.322912900999654, "max": 1.3520298820003518}; failed/incomplete: 0.

pr04 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 70, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_cost": 10, "generator_performance": 10, "generator_security": 10, "security_iteration": 30}, "durations": {"count": 70, "median": 1.1479755, "p90": 10.564945, "max": 13.443348}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "PASS", "observations": 7, "failures": 0, "missing_measurements": 0, "agents": {"architect": 1, "generator_cost": 1, "generator_performance": 1, "generator_security": 1, "security_iteration": 3}, "durations": {"count": 7, "median": 0.396516, "p90": 7.115743, "max": 7.115743}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "PASS", "observations": 21, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_cost": 3, "generator_performance": 3, "generator_security": 3, "security_iteration": 9}, "durations": {"count": 21, "median": 1.059409, "p90": 19.812252, "max": 23.384443}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 5 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 6 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 7 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 8 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 9 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 10 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 11 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 12 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 13 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 14 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["b3e9359c-f76a-42c2-b082-50125f6dd954", "9ce48736-7e7a-4827-9e9c-3a0c76efc505", "81470a4c-d898-4dd7-a7b6-5631b9f761f9"], "before_remaining_usd": null, "after_remaining_usd": null}
