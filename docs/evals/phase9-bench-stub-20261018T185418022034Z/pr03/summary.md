# Phase 9 benchmark

Status: **FAIL**

Mode: stub rehearsal; system overhead only.

Production-ready rate among generated packages: **12/12 (100.00%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| production_ready | 12 |

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
| deterministic_repairs | 12 | 0.11421029400116822 | 0.16144159599934937 | 0.24654225099948235 |
| final_security_scan | 12 | 22.613227221499983 | 27.15903509599957 | 27.619207166000706 |
| final_validation | 12 | 0.0019721425014722627 | 0.0025007600015669595 | 0.00467924300028244 |
| generation_gate | 12 | 0.6904971004987601 | 0.8062215280006058 | 0.8432056370002101 |
| initial_validation | 12 | 0.003823151999313268 | 0.007606803999806289 | 0.012296193999645766 |
| post_security_validation | 12 | 0.0021131300018168986 | 0.0037932090017420705 | 0.003815651001787046 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 12, 'init_reused': 36, 'reinitializations': 0, 'init_seconds': 2.333871219001594, 'validate_seconds': 2.6992222360022424}
Gate outcomes: {'valid': 12}
Init categories: {'initialized': 12}
Schema context sizes (characters): {'generator': {'count': 12, 'median': 2746.0, 'p90': 2746, 'max': 2746}, 'repair': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'security': {'count': 0, 'median': None, 'p90': None, 'max': None}}
Security context coverage: {'terraform': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'other': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}, 'unknown': {'total': 0, 'positive': 0, 'zero': 0, 'missing': 0, 'reasons': {}}}
Security iteration outcomes by class: []

| Valid package remaining blockers | Packages |
|---|---:|
| 1 | 0 |
| 2-3 | 0 |
| 4+ | 0 |

Phase 9f measured/unknown packages: (12, 0)
Catalogue retained by rule: {}
Template outcomes: []
Template introduced rules: {}
Partial groups: {}
Existing-file proposal recovery: {'normalized': 0, 'retained': 0}
Generation syntax recovery: {'unchanged': 12}
Fixer model limits and calls: [{'model': 'stub', 'sessions': 12, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 12 | 0.11421029400116822 | 0.16144159599934937 | 0.24654225099948235 |
| final_security_scan | 12 | 22.613227221499983 | 27.15903509599957 | 27.619207166000706 |
| final_validation | 12 | 0.0019721425014722627 | 0.0025007600015669595 | 0.00467924300028244 |
| generation_gate | 12 | 0.6904971004987601 | 0.8062215280006058 | 0.8432056370002101 |
| initial_validation | 12 | 0.003823151999313268 | 0.007606803999806289 | 0.012296193999645766 |
| post_security_validation | 12 | 0.0021131300018168986 | 0.0037932090017420705 | 0.003815651001787046 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 54.000933385997996, "p90": 56.86264880700037, "max": 56.86264880700037}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "9a183521-1feb-4eff-adb4-317fe24d235a", "ratio_to_baseline": 2.873781296757592, "ratio_to_pr01_prompt_median": 2.8672608246172815, "pr01_prompt_median_seconds": 19.83169731849921, "pr01_reference_count": 4}

Cohort references: {"run_id": "f144b58e-02fa-49a2-952e-b899d42fc1ea", "ratio_to_baseline": 2.8256539777540275, "ratio_to_pr01_prompt_median": 2.8192427041957746, "pr01_prompt_median_seconds": 19.83169731849921, "pr01_reference_count": 4}

Cohort references: {"run_id": "d21c1c4c-bc8d-4c95-8a5b-cd4a90140a81", "ratio_to_baseline": 2.632652155639765, "ratio_to_pr01_prompt_median": 2.6266787939732574, "pr01_prompt_median_seconds": 19.83169731849921, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "PASS", "observations": 7, "failures": 0, "missing_measurements": 0, "agents": {"architect": 1, "generator_cost": 1, "generator_security": 1, "generator_performance": 1, "security_iteration": 3}, "durations": {"count": 7, "median": 0.566969, "p90": 9.561274, "max": 9.561274}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "PASS", "observations": 21, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_cost": 3, "generator_performance": 3, "generator_security": 3, "security_iteration": 9}, "durations": {"count": 21, "median": 1.6753, "p90": 29.438542, "max": 30.047985}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, security#1:10, performance#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["f144b58e-02fa-49a2-952e-b899d42fc1ea", "d21c1c4c-bc8d-4c95-8a5b-cd4a90140a81", "9a183521-1feb-4eff-adb4-317fe24d235a"], "before_remaining_usd": null, "after_remaining_usd": null}
