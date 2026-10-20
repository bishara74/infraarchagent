# Phase 9 benchmark

Status: **PASS**

Mode: stub rehearsal; system overhead only.

Checks-passed rate among generated packages: **60/60 (100.00%)**.
Legacy labels mapped: 0. Missing variants: 0; runs without quality snapshots: 0.
Strict / contextual-v1 / contextual-v2 assessments: strict: 60/60; contextual-v1: 60/60; contextual-v2: 60/60. Contextual results are experimental and never change package labels.

| Package status | Count |
|---|---:|
| checks_passed | 60 |

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
| deterministic_repairs | 60 | 0.11215944099967601 | 0.38681765100045595 | 0.7440615270024864 |
| final_security_scan | 60 | 7.820012147501984 | 10.032314020005288 | 12.917685282998718 |
| final_validation | 60 | 0.0024257709956145845 | 0.003870097003527917 | 0.009637032999307849 |
| generation_gate | 60 | 0.2402627225019387 | 0.39458838499558624 | 0.8266574590088567 |
| initial_validation | 60 | 0.001936985005158931 | 0.0038442560035036877 | 0.009210511998389848 |
| post_security_validation | 60 | 0.001805603998946026 | 0.003179239996825345 | 0.006242991003091447 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 60, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 60, 'packages_unknown': 0, 'init_runs': 60, 'init_reused': 180, 'reinitializations': 0, 'init_seconds': 5.707425124026486, 'validate_seconds': 5.715358801957336}
Gate outcomes: {'valid': 60}
Init categories: {'initialized': 60}
Schema context sizes (characters): {'generator': {'count': 60, 'median': 4483.0, 'p90': 4483, 'max': 4483}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security context coverage: {'terraform': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: []

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 0 |

Phase 9f measured/unknown packages: (60, 0)
Catalogue retained by rule: {}
Template outcomes: []
Template introduced rules: {}
Partial groups: {}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 60}
Fixer model limits and calls: [{'model': 'stub', 'sessions': 60, 'fix_attempt_timeout_seconds': [90.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 60 | 0.11215944099967601 | 0.38681765100045595 | 0.7440615270024864 |
| final_security_scan | 60 | 7.820012147501984 | 10.032314020005288 | 12.917685282998718 |
| final_validation | 60 | 0.0024257709956145845 | 0.003870097003527917 | 0.009637032999307849 |
| generation_gate | 60 | 0.2402627225019387 | 0.39458838499558624 | 0.8266574590088567 |
| initial_validation | 60 | 0.001936985005158931 | 0.0038442560035036877 | 0.009210511998389848 |
| post_security_validation | 60 | 0.001805603998946026 | 0.003179239996825345 | 0.006242991003091447 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 60, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 20, "median": 17.641757124496507, "p90": 23.769822521993774, "max": 27.204211225005565}; failed/incomplete: 0.

PR-01 descriptive timing only: broad scenario set; no PR-01 threshold verdict.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 140, "failures": 0, "missing_measurements": 0, "agents": {"architect": 20, "generator_cost": 20, "generator_performance": 20, "generator_security": 20, "security_iteration": 60}, "durations": {"count": 140, "median": 0.9611075, "p90": 10.815209, "max": 12.508736}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | performance#1:10, cost#1:10, security#1:10 | {} | {} |
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
| 15 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 16 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 17 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 18 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 19 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 20 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.
