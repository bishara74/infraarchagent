# Phase 9d verification

Functional acceptance passed; stub PR-03 performance criterion failed.

- make lint: PASS; Ruff, formatting, strict mypy (105 files), ESLint and TypeScript.
- make test: 1244 passed, 0 failed, 0 skipped, 6 performance tests deselected.
- make frontend-test: 100 passed, 0 failed (15 files).
- make test-e2e: 6 passed, 0 failed.
- make secret-scan: 0 findings / 0 scan errors (all refs/reflogs and working tree).
  [Final scan evidence](../phase9-secret-scan-20261015T154529168973Z/summary.md).
- make bench-stub: 14 successful pipeline runs, 10 successful downloads,
  42/42 stub packages ready, zero missing variants. These are rehearsal outcomes,
  not evidence of real-model quality improvement.

Stub PR-01 median 14.229337 s: PASS. PR-03 concurrent/baseline ratios
2.571282–2.616546: FAIL against 1.5. PR-04 maximum 1.321749 s: PASS.
Recorded PR-05 thresholds: PASS. The benchmark summary therefore remains FAIL.
Evidence: ../phase9-bench-stub-20261015T135741234853Z/summary.md.

Tests used a separate PostgreSQL 16 instance with synthetic credentials and
explicit dotenv-disabled verification settings. No existing developer database,
real credentials, real provider calls, new dependencies or downloads were used.
Backend/browser suites were rerun serially after interrupting an overlapping
attempt. Recorded scanner fixtures now include mandatory final verification.

The final scope guard is covered for both stub and fake real-provider contexts;
review-demo bypass never disables repair for real runs. Retry retains its
acceptance and recovery policy and preserves automatic repair history.

The original benchmark and docs/spec remain unchanged. The offline baseline
quality projection reproduces 1/36 ready (2.78%), 35 validation failures,
30 unresolved-security packages and six missing variants. Only status, reasons,
failed-check IDs/messages/locations, rule IDs and counts are saved in quality inputs.

D-44 records the feedback loop and unchanged readiness/blocking/validation rules.
No new open question. Grafana row panels pass; API-wrapped dashboards remain
unsupported (48ce2227/security is a real example), without a check change.

New setting: VALIDATION_REPAIR_MAX_ROUNDS=2. Changed default:
MAX_REMEDIATION_ITERATIONS=4 (was 3). FIX_ATTEMPT_TIMEOUT_SECONDS retains its
90-second default; automated security iterations clip execution to 60 seconds.
Post-security repair is fixed at one round and the security deadline stays 240 s.
Generator defaults remain 8000 tokens / 120 s; preserve baseline overrides for
an author comparison, keeping the same model/provider selection:

```dotenv
VALIDATION_REPAIR_MAX_ROUNDS=2
MAX_REMEDIATION_ITERATIONS=4
FIX_ATTEMPT_TIMEOUT_SECONDS=45
SECURITY_DEADLINE_SECONDS=240
GENERATOR_MAX_OUTPUT_TOKENS=16000
GENERATOR_ATTEMPT_TIMEOUT_SECONDS=140
GENERATOR_DEADLINE_SECONDS=150
LLM_DEADLINE_SECONDS=150
LLM_STRUCTURED_OUTPUT=json_schema
```

Next: the author runs the real benchmark with these overrides and measures the
production-ready rate and total time. No after-change real outcome is estimated.
