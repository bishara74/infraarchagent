# Phase 9 benchmark

Status: **PASS**

Mode: stub rehearsal; system overhead only.

Checks-passed rate among generated packages: **30/30 (100.00%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 assessments: strict: 30/30; contextual-v1: 30/30. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| checks_passed | 30 |

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
| deterministic_repairs | 30 | 0.08906417049729498 | 0.21612481999909505 | 1.4447626339970157 |
| final_security_scan | 30 | 9.2236116210006 | 11.879701366000518 | 13.579558744000678 |
| final_validation | 30 | 0.0022494235017802566 | 0.0027539910006453283 | 0.008284232004371006 |
| generation_gate | 30 | 0.2702188245020807 | 0.3775281209964305 | 0.7035817510040943 |
| initial_validation | 30 | 0.0019813670005532913 | 0.003078378998907283 | 0.006003372996929102 |
| post_security_validation | 30 | 0.00175149500137195 | 0.002573486002802383 | 0.007310638000490144 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 30, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 30, 'packages_unknown': 0, 'init_runs': 30, 'init_reused': 90, 'reinitializations': 0, 'init_seconds': 2.837659235985484, 'validate_seconds': 2.798679320017982}
Gate outcomes: {'valid': 30}
Init categories: {'initialized': 30}
Schema context sizes (characters): {'generator': {'count': 30, 'median': 2746.0, 'p90': 2746, 'max': 2746}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security context coverage: {'terraform': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: []

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 0 |

Phase 9f measured/unknown packages: (30, 0)
Catalogue retained by rule: {}
Template outcomes: []
Template introduced rules: {}
Partial groups: {}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 30}
Fixer model limits and calls: [{'model': 'stub', 'sessions': 30, 'fix_attempt_timeout_seconds': [90.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 30 | 0.08906417049729498 | 0.21612481999909505 | 1.4447626339970157 |
| final_security_scan | 30 | 9.2236116210006 | 11.879701366000518 | 13.579558744000678 |
| final_validation | 30 | 0.0022494235017802566 | 0.0027539910006453283 | 0.008284232004371006 |
| generation_gate | 30 | 0.2702188245020807 | 0.3775281209964305 | 0.7035817510040943 |
| initial_validation | 30 | 0.0019813670005532913 | 0.003078378998907283 | 0.006003372996929102 |
| post_security_validation | 30 | 0.00175149500137195 | 0.002573486002802383 | 0.007310638000490144 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 30, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 21.089729495000938, "p90": 25.443249298994488, "max": 25.52553040500061}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 70, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_cost": 10, "generator_performance": 10, "generator_security": 10, "security_iteration": 30}, "durations": {"count": 70, "median": 1.1479755, "p90": 10.564945, "max": 13.443348}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

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

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.
