# Phase 9 benchmark

Status: **PASS**

Mode: stub rehearsal; system overhead only.

Production-ready rate among generated packages: **30/30 (100.00%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| production_ready | 30 |

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
| deterministic_repairs | 30 | 0.004182976000265626 | 0.008552256999792007 | 0.267499649000456 |
| final_security_scan | 30 | 7.8768974595000145 | 8.51064742700055 | 9.597963808000713 |
| final_validation | 30 | 0.0030901780000931467 | 0.0036946800000805524 | 0.0057060750004893634 |
| generation_gate | 30 | 0.23986287199977596 | 0.4753410339999391 | 0.541484770000352 |
| initial_validation | 30 | 0.002380090500082588 | 0.003699296000377217 | 0.008803126999737287 |
| post_security_validation | 30 | 0.003264828999817837 | 0.004454356000678672 | 0.005694165000022622 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 30, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 30, 'packages_unknown': 0, 'init_runs': 30, 'init_reused': 90, 'reinitializations': 0, 'init_seconds': 2.442554798999481, 'validate_seconds': 2.98895131900008}
Gate outcomes: {'valid': 30}
Init categories: {'initialized': 30}
Schema context sizes (characters): {'generator': {'count': 30, 'median': 5689.0, 'p90': 5689, 'max': 5689}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security iteration outcomes by class: []

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 30 | 0.004182976000265626 | 0.008552256999792007 | 0.267499649000456 |
| final_security_scan | 30 | 7.8768974595000145 | 8.51064742700055 | 9.597963808000713 |
| final_validation | 30 | 0.0030901780000931467 | 0.0036946800000805524 | 0.0057060750004893634 |
| generation_gate | 30 | 0.23986287199977596 | 0.4753410339999391 | 0.541484770000352 |
| initial_validation | 30 | 0.002380090500082588 | 0.003699296000377217 | 0.008803126999737287 |
| post_security_validation | 30 | 0.003264828999817837 | 0.004454356000678672 | 0.005694165000022622 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 30, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 15.759287522500017, "p90": 19.26267021000058, "max": 19.521889943999668}; failed/incomplete: 0.

pr01 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, security#1:10, performance#1:10 | {} | {} |
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
