# Phase 9 benchmark

Status: **FAIL**

Mode: stub rehearsal; system overhead only.

Descriptive durations (seconds; no new thresholds):

| Stage | Count | Median | p90 | Maximum |
|---|---:|---:|---:|---:|
| deterministic_repairs | 0 | unknown | unknown | unknown |
| final_security_scan | 0 | unknown | unknown | unknown |
| final_validation | 0 | unknown | unknown | unknown |
| generation_gate | 0 | unknown | unknown | unknown |
| initial_validation | 0 | unknown | unknown | unknown |
| post_security_validation | 0 | unknown | unknown | unknown |
| security_iteration_verification | 0 | unknown | unknown | unknown |
| validation_repair_round | 0 | unknown | unknown | unknown |

Iteration outcomes: {'attempted_fix_iterations': 0, 'deadline_only_rollbacks': 0, 'deadline_before_candidate': 0, 'multiple_cause_deadline_rollbacks': 0, 'validity_regression_rollbacks': 0}.
Initialization: {'init_runs': 0, 'init_reused': 0, 'reinitializations': 0}.
Repair deadline stops (measured rounds): {}.
Historical 9d stops: four initial / nine post-security (separate historical evidence). A deadline-only rollback does not establish that the candidate would have passed verification.

pr04: {"count": 10, "median": 1.9884766389950528, "p90": 2.497008848004043, "max": 2.6529419849975966}; failed/incomplete: 0.

pr04 threshold: FAIL.

PR-05 workload isolated_pr01 (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload isolated_pr03_baseline (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload concurrent_pr03_cohort (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

PR-05 workload unclassified (additional view): {"verdict": "INCOMPLETE", "observations": 0, "failures": 0, "missing_measurements": 0, "agents": {}, "durations": {"count": 0, "median": null, "p90": null, "max": null}, "failed_observations": []}

Measured known cost: $0.000000; unknown costs stay unknown.
