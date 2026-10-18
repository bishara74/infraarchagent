# Phase 9 benchmark

Status: **FAIL**

Mode: stub rehearsal; system overhead only.

Production-ready rate among generated packages: **42/42 (100.00%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| production_ready | 42 |

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
| deterministic_repairs | 42 | 0.06061294000028283 | 0.09414275599920074 | 0.5564748809993034 |
| final_security_scan | 42 | 6.333589371999551 | 16.473392500000045 | 18.333430972001224 |
| final_validation | 42 | 0.0015704185007052729 | 0.009680807997938246 | 0.01998734700100613 |
| generation_gate | 42 | 0.16194107350020204 | 0.3977405940022436 | 0.4189184890019533 |
| initial_validation | 42 | 0.0013985880013933638 | 0.0028594600007636473 | 0.003967454998928588 |
| post_security_validation | 42 | 0.0013059395005257102 | 0.002446905000397237 | 0.04730711199954385 |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 42, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

Package initialization totals: {'packages_measured': 42, 'packages_unknown': 0, 'init_runs': 42, 'init_reused': 126, 'reinitializations': 0, 'init_seconds': 2.7729155519882625, 'validate_seconds': 2.9197264770045877}
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
Fixer model limits and calls: [{'model': 'stub', 'sessions': 42, 'fix_attempt_timeout_seconds': [45.0], 'iteration_timeout_seconds': [60.0], 'security_stage_timeout_seconds': [240.0], 'fix_max_resources': [2], 'fix_max_findings': [12], 'partial_max_groups': [6], 'findings_per_call': {'count': 0, 'median': None, 'p90': None, 'max': None}, 'calls_missing_measurements': 0}]

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 42 | 0.06061294000028283 | 0.09414275599920074 | 0.5564748809993034 |
| final_security_scan | 42 | 6.333589371999551 | 16.473392500000045 | 18.333430972001224 |
| final_validation | 42 | 0.0015704185007052729 | 0.009680807997938246 | 0.01998734700100613 |
| generation_gate | 42 | 0.16194107350020204 | 0.3977405940022436 | 0.4189184890019533 |
| initial_validation | 42 | 0.0013985880013933638 | 0.0028594600007636473 | 0.003967454998928588 |
| post_security_validation | 42 | 0.0013059395005257102 | 0.002446905000397237 | 0.04730711199954385 |
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
| security_iteration_verification | 6 | 13.330198018002193 | 27.56207733100382 | 27.56207733100382 |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 6, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 3, 'init_reused': 9, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr01: {"count": 10, "median": 13.778885008499856, "p90": 15.876400752000336, "max": 16.177686514001834}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 38.090459556000496, "p90": 38.40323431199795, "max": 38.40323431199795}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "34883a8b-841f-464c-b68f-e330fbd36b56", "ratio_to_baseline": 2.7980202202907805, "ratio_to_pr01_prompt_median": 2.755320953152742, "pr01_prompt_median_seconds": 13.778885008499856, "pr01_reference_count": 4}

Cohort references: {"run_id": "ee875c49-1b9c-4eae-81fe-edb580de0dd6", "ratio_to_baseline": 2.830299405432799, "ratio_to_pr01_prompt_median": 2.787107540871989, "pr01_prompt_median_seconds": 13.778885008499856, "pr01_reference_count": 4}

Cohort references: {"run_id": "3dc38720-6c6e-4a43-b795-6056d1aab87b", "ratio_to_baseline": 2.816475900434607, "ratio_to_pr01_prompt_median": 2.7734949898649157, "pr01_prompt_median_seconds": 13.778885008499856, "pr01_reference_count": 4}

pr03 threshold: FAIL.

pr04: {"count": 10, "median": 1.1008121654995193, "p90": 1.2312977549991047, "max": 1.2951163299985637}; failed/incomplete: 0.

pr04 threshold: PASS.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

PR-05 workload isolated_pr01 (additional view): {"verdict": "PASS", "observations": 70, "failures": 0, "missing_measurements": 0, "agents": {"architect": 10, "generator_cost": 10, "generator_performance": 10, "generator_security": 10, "security_iteration": 30}, "durations": {"count": 70, "median": 0.3692255, "p90": 6.823371, "max": 7.870998}, "failed_observations": []}

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

Concurrent costs: {"cost_usd": 0.0, "average_cost_usd": 0.0, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["ee875c49-1b9c-4eae-81fe-edb580de0dd6", "3dc38720-6c6e-4a43-b795-6056d1aab87b", "34883a8b-841f-464c-b68f-e330fbd36b56"], "before_remaining_usd": null, "after_remaining_usd": null}
