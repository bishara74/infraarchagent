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
| deterministic_repairs | 12 | 0.070576568999968 | 0.09414275599920074 | 0.09801740499824518 |
| final_security_scan | 12 | 16.12054059750153 | 17.302227313000913 | 18.333430972001224 |
| final_validation | 12 | 0.003465276000497397 | 0.016266700000414858 | 0.01998734700100613 |
| generation_gate | 12 | 0.3619789855001727 | 0.41050771300069755 | 0.4189184890019533 |
| initial_validation | 12 | 0.0024597105002612807 | 0.0035092719990643673 | 0.003967454998928588 |
| post_security_validation | 12 | 0.0015839865009183995 | 0.004788688998814905 | 0.04730711199954385 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 12, 'packages_unknown': 0, 'init_runs': 12, 'init_reused': 36, 'reinitializations': 0, 'init_seconds': 1.2332741909995093, 'validate_seconds': 1.311297940013901}
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
| deterministic_repairs | 12 | 0.070576568999968 | 0.09414275599920074 | 0.09801740499824518 |
| final_security_scan | 12 | 16.12054059750153 | 17.302227313000913 | 18.333430972001224 |
| final_validation | 12 | 0.003465276000497397 | 0.016266700000414858 | 0.01998734700100613 |
| generation_gate | 12 | 0.3619789855001727 | 0.41050771300069755 | 0.4189184890019533 |
| initial_validation | 12 | 0.0024597105002612807 | 0.0035092719990643673 | 0.003967454998928588 |
| post_security_validation | 12 | 0.0015839865009183995 | 0.004788688998814905 | 0.04730711199954385 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 12, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr03: {"count": 4, "median": 38.090459556000496, "p90": 38.40323431199795, "max": 38.40323431199795}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "34883a8b-841f-464c-b68f-e330fbd36b56", "ratio_to_baseline": 2.7980202202907805, "ratio_to_pr01_prompt_median": 2.755320953152742, "pr01_prompt_median_seconds": 13.778885008499856, "pr01_reference_count": 4}

Cohort references: {"run_id": "ee875c49-1b9c-4eae-81fe-edb580de0dd6", "ratio_to_baseline": 2.830299405432799, "ratio_to_pr01_prompt_median": 2.787107540871989, "pr01_prompt_median_seconds": 13.778885008499856, "pr01_reference_count": 4}

Cohort references: {"run_id": "3dc38720-6c6e-4a43-b795-6056d1aab87b", "ratio_to_baseline": 2.816475900434607, "ratio_to_pr01_prompt_median": 2.7734949898649157, "pr01_prompt_median_seconds": 13.778885008499856, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "PASS", "observations": 7, "failures": 0, "missing_measurements": 0, "agents": {"architect": 1, "generator_cost": 1, "generator_performance": 1, "generator_security": 1, "security_iteration": 3}, "durations": {"count": 7, "median": 0.389833, "p90": 6.49131, "max": 6.49131}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "PASS", "observations": 21, "failures": 0, "missing_measurements": 0, "agents": {"architect": 3, "generator_cost": 3, "generator_performance": 3, "generator_security": 3, "security_iteration": 9}, "durations": {"count": 21, "median": 0.954628, "p90": 18.448658, "max": 19.245344}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |
| 4 | 3 | {"none": 3} | cost#1:10, performance#1:10, security#1:10 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.000000; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["ee875c49-1b9c-4eae-81fe-edb580de0dd6", "3dc38720-6c6e-4a43-b795-6056d1aab87b", "34883a8b-841f-464c-b68f-e330fbd36b56"], "before_remaining_usd": null, "after_remaining_usd": null}
