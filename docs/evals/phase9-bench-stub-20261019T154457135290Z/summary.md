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
| deterministic_repairs | 42 | 0.24029307000455447 | 0.37013449901132844 | 1.420343784004217 |
| final_security_scan | 42 | 18.33436716649885 | 30.573302926000906 | 35.51425796400872 |
| final_validation | 42 | 0.0018089524965034798 | 0.00881813300657086 | 0.014795107010286301 |
| generation_gate | 42 | 0.611815429496346 | 1.5222910070006037 | 1.7563591950020054 |
| initial_validation | 42 | 0.0027815685025416315 | 0.007516471989220008 | 0.013846287998603657 |
| post_security_validation | 42 | 0.0020519605022855103 | 0.014106094007729553 | 0.02225367000210099 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 42, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 42, 'packages_unknown': 0, 'init_runs': 42, 'init_reused': 126, 'reinitializations': 0, 'init_seconds': 10.02559782503522, 'validate_seconds': 10.483736517955549}
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
| deterministic_repairs | 42 | 0.24029307000455447 | 0.37013449901132844 | 1.420343784004217 |
| final_security_scan | 42 | 18.33436716649885 | 30.573302926000906 | 35.51425796400872 |
| final_validation | 42 | 0.0018089524965034798 | 0.00881813300657086 | 0.014795107010286301 |
| generation_gate | 42 | 0.611815429496346 | 1.5222910070006037 | 1.7563591950020054 |
| initial_validation | 42 | 0.0027815685025416315 | 0.007516471989220008 | 0.013846287998603657 |
| post_security_validation | 42 | 0.0020519605022855103 | 0.014106094007729553 | 0.02225367000210099 |
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
| security_iteration_verification | 6 | 34.70341389100213 | 59.89580366300652 | 59.89580366300652 |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 6, 'deadline_only_rollbacks': 2, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 3, 'init_reused': 9, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 40.9621788259974, "p90": 54.10937141701288, "max": 57.0364116540004}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 79.51988864650048, "p90": 80.08109538198914, "max": 80.08109538198914}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "88cc8790-125b-4d32-99cd-6b2021c1a7ed", "ratio_to_baseline": 2.3951004589493983, "ratio_to_pr01_prompt_median": 1.848906131787436, "pr01_prompt_median_seconds": 42.83975654049573, "pr01_reference_count": 4}

Cohort references: {"run_id": "9e7a058a-ffed-49c2-9827-061904103621", "ratio_to_baseline": 2.4215413093130915, "ratio_to_pr01_prompt_median": 1.8693172382128218, "pr01_prompt_median_seconds": 42.83975654049573, "pr01_reference_count": 4}

Cohort references: {"run_id": "b66f378a-8e96-4e71-874a-3c34774c3e3b", "ratio_to_baseline": 2.4140419322968234, "ratio_to_pr01_prompt_median": 1.8635280680349469, "pr01_prompt_median_seconds": 42.83975654049573, "pr01_reference_count": 4}

pr03 threshold: FAIL.

pr04: {"count": 10, "median": 1.9884766389950528, "p90": 2.497008848004043, "max": 2.6529419849975966}; failed/incomplete: 0.

pr04 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 70, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_cost": 10, "generator_performance": 10, "generator_security": 10, "security_iteration": 30}, "durations": {"count": 70, "median": 1.421113, "p90": 21.840415, "max": 38.012688}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "PASS", "observations": 7, "failures": 0, "missing_measurements": 0, "agents": {"architect": 1, "generator_cost": 1, "generator_performance": 1, "generator_security": 1, "security_iteration": 3}, "durations": {"count": 7, "median": 0.950422, "p90": 17.063464, "max": 17.063464}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "PASS", "observations": 21, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_cost": 3, "generator_performance": 3, "generator_security": 3, "security_iteration": 9}, "durations": {"count": 21, "median": 3.526587, "p90": 45.935893, "max": 47.479356}, "failed_observations": []}

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

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["9e7a058a-ffed-49c2-9827-061904103621", "b66f378a-8e96-4e71-874a-3c34774c3e3b", "88cc8790-125b-4d32-99cd-6b2021c1a7ed"], "before_remaining_usd": null, "after_remaining_usd": null}
