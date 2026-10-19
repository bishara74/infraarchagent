# Phase 9g verification

All verification used exported isolated PostgreSQL settings and the dotenv-disabled
bootstrap, including Make migration prerequisites. No real model calls, installs,
downloads, new dependencies or pushes. Original A3/B cached results remain
read-only and untracked. Spec documents and historical evaluation folders were
not changed.

| Check | Actual result |
|---|---|
| make lint | PASS; Ruff, 136 application sources in mypy, ESLint and both TypeScript projects |
| make test | 1,632 passed, 0 failed, 0 skipped, 6 deselected (407.76 s) |
| make frontend-test | 105 passed, 15 files |
| make test-e2e | 6 passed, 0 failed (2.4 minutes) |
| make frontend-build | PASS; 143 modules |
| make provider-schema | PASS; all 7 pinned provider versions exported offline |
| make secret-scan | PASS; 0 findings, 0 scan errors (final post-change scan) |
| make bench-stub | Exit 0; 14 pipeline runs + 10 synthetic downloads complete; PR-01/04/05 PASS, PR-03 FAIL |

The initial full backend run was 1,616 passed / 5 failed / 6 deselected. Four
failures were stale compatibility fixtures/contracts (native support filename,
old-schema setup through a new ORM, telemetry field set); one hit a tight existing
deadline under concurrent verification load. All 26 focused corrections passed,
including the unchanged deadline case. A browser run was interrupted after it
exposed cancellation during session renewal; a deterministic PostgreSQL
cancellation test now verifies transaction completion and zero checked-out
connections. The restarted six-test E2E run passed with no connection errors.
Additional focused checks: 13 authentication tests, 41 quota/benchmark tests,
6 migration/provenance tests and 52 strict/profile/quality regressions, all passed.
An intermediate full run passed 1,626 tests / 6 deselected. The final five parity
cases ensure missing/contradictory scan metadata cannot establish assessment
success; strict still requires a clean scan. The combined CLI/parity/contract
regression suite passed 81 cases; zero MAX_RUNS is rejected before submission.
No deadline guard was weakened.

## Migration evidence

- 0004 synthetic historical rehearsal: 1 checks_passed, 1 engineer_approved,
  1 rejected, 1 pending_review; original event rows unchanged.
- 0004 on the newly isolated databases: all four legacy counts 0.
- 0007 synthetic reconciliation: 2 checks_passed (one legacy automatic and one
  current automatic), 1 engineer_approved, 3 pending_review (missing, ambiguous or
  contradictory provenance); original event rows unchanged.
- 0007 on the isolated E2E database: 14 modern automatic outcomes confirmed,
  0 moved to pending; on the isolated benchmark database: both counts 0.
- Author databases were not migrated. 0007 was added because 0004 had already
  been applied; no applied migration was edited. Its downgrade does not restore
  unverifiable success claims.

## Reclassification and baseline limits

A3: strict 1/29, contextual-v1 1/29; 4 missing variants.
B: strict 1/9, contextual-v1 1/9; 24 missing variants.
All 22 saved source JSON SHA-256 hashes match the committed reclassification
manifest. New derived outputs are sanitized; original evidence is unchanged.
The appendix is experimental pending supervisor approval for reported thesis use.
Strict alone controls official labels and template acceptance.

Complete A3/B fixer-attempt format baselines are unknown. The preserved partial
B excerpt contains 14/22 non-quota Haiku invalid_json/prose_before failures,
eight successes and four additional quota failures excluded. This illustrative
partial sample is not a complete B rate; proposal counts are not attempts.
Mocked wire tests establish request behavior, not real-provider reliability.

Existing direct Uvicorn startup was exercised with a synthetic configured key
and no --host argument. The existing VS Code configuration was left untouched;
no GUI debugger session or real credential was used.

## Stub rehearsal (not real-provider evidence)

[Full saved summary](../phase9-bench-stub-20261019T025515537899Z/summary.md).
All 42 generated packages passed static checks under both profiles. The 10
synthetic rejected-fixture downloads are separate and excluded from quality rates.
PR-01 median: 21.0897 seconds. PR-04 median: 1.1444 seconds. PR-03 concurrent
ratios to its isolated baseline: 2.4480–2.5356, failing the unchanged threshold.
All individual PR-05 thresholds passed. The command exited 0 because every
scheduled observation completed; the saved aggregate performance verdict is FAIL.
No real-model reliability, matched-model speed improvement or cloud deployment
claim follows from this stub rehearsal. First isolated observations overlapped
migration/lint verification; timings describe this local run, not a controlled
cross-phase performance comparison.

Final secret-scan evidence: [saved report](../phase9-secret-scan-20261019T120443434782Z/summary.md).
