# Phase 10e — final offline verification

Candidate acceptance no longer rejects solely for plan conformance. A shared final
check compares persisted retained files against the immutable Generator original
and plan on initial completion and review retry. Confirmed regressions require
pending_review even with clean scans and valid validation; uncertainty adds
information only. Fixer prompt v8/network context and all other acceptance gates,
file-input refusal/blocker, profiles, scanner rules and thresholds are unchanged.

| Check | Result | Evidence |
|---|---|---|
| make lint | Ruff/format, mypy 192 app sources, ESLint and both TypeScript checks pass | [log](make-lint.txt) |
| make test | 2,861 passed; zero failed/skipped; six perf deselected; 742.44s | [log](make-test.txt) |
| Final focused verification | 118 passed; zero failed/skipped; 23.48s | [log](final-focused.txt) |
| Report-summary tests | Three passed; zero failed/skipped; 1.77s | [log](replay-summary-tests.txt) |
| make frontend-test | 469 passed; zero failed/skipped; 46 files; 90.19s | [log](make-frontend-test.txt) |
| make test-e2e | 36 passed; zero failed/skipped; 9.4m | [log](make-test-e2e.txt) |
| make test-perf | Six passed; zero failed/skipped; 2,863 deselected; 28.09s | [log](make-test-perf.txt), [measurements](performance/results.json) |
| make secret-scan | Zero findings / zero scan errors; working tree and all refs/reflogs | [report](secret-scan/summary.md) |
| Traceability | 59 IDs; zero uncovered/invalid annotations/collection failures | [report](../phase10e-traceability/traceability.md) |
| Evidence index | 45 met / 12 partly met / one not met / one unverified; canonical bytes unchanged | [log](evidence-index.txt), [index](../EVIDENCE.md) |

The unchanged PR-04 two-second bound measured **1.144051566006965 seconds** for a
10 MB package download. Performance ran only after the backend, browser and native
replay workloads ended. Automatic performance output was relocated into
performance/; the console retains its original fresh destination.

## Scope and isolation

Verification used dotenv-disabled Python bootstrap, Vite's existing envDir:false,
synthetic credentials, stub/mocked provider transports and disposable UTF-8
PostgreSQL 16. Backend tests used port 55455; browser tests used a separate cluster
on 55456, with services on 18155/15155. Owner/app/readonly roles and migration
grants retain their existing privileges. No author database, real credentials,
real inference, installs, external services or push were used. OpenAI-labelled
calls in browser logs are mocked transport tests, not real-provider execution.

The full suite includes the final application implementation. Two test-only
additions afterward cover persisted canary redaction and report aggregation; the
focused and summary runs include them. The reporting CLI subsequently gained
complete before/after decision counters, tested separately and regenerated from
identical native observations. No application behavior changed after the full
suite began. Traceability was recollected after those additions.

All **6,661** protected evidence/specification files retain exact original bytes.
Browser verification refreshed 93 historical PNG captures; fresh bytes are in
ui/refreshed/ and the historical files were restored byte-for-byte.
[historical-preservation.json](historical-preservation.json) records every pair.
The [final conflict capture](ui/final-conflict-review.png) was visually reviewed at
1280×800; the service/resource/property explanation and review controls fit.

## Replay and limits

[Two-cohort replay](../phase10e-replay/README.md) verifies all 116 retained packages
and 348 source hashes. It inventories 113 security iterations with conformance
reasons (101 sole-conformance), 120 partial groups, 34 validation Fixer rounds,
16 deterministic validation records and four catalogue records. These are
separate units, not a summed recovered-fix count.

Thirty reconstructable occurrences / 14 distinct pairs have 26 accepted and four
new-blocker decisions both before and after; Phase 10d had already cleared these
available deterministic proposals. Model candidate bodies remain absent. Frozen
retained-file assessment flags zero packages and records information in 73.
The three historical ALB fixtures retain their flips but end in pending_review,
never checks_passed. Unknown bindings alone preserve eligibility for checks_passed.
No replay pass rate or deployment correctness is inferred. See the replay report
for raw-versus-author counting units and missing evidence.

## Preliminary checks and corrections

Initial focused checks: 74 passed / seven old rollback assertions failed; those
assertions were updated for detect-only acceptance and final review. The next
focused run passed 63; expanded unit checks passed 25. Two preliminary backend
runs were interrupted after 302 and 93 passes while edge cases were completed;
neither is a full-suite success claim. Their console logs remain initial-*.

The first complete browser run had 35 passed / one failed: informational binding
paragraphs put a comparison action below the 800px viewport (823.15625px). Final
notes use an accessible disclosure while confirmed conflicts remain visible.
The complete rerun passes all 36 tests without a timeout or layout assertion change.

A report-only aggregation edit initially caused one collection error; it was fixed
before the three passing report tests and final CLI regeneration. Preliminary
report directories stay uncommitted in .cache/phase10e-preliminary; console logs
are retained here. [replay-regeneration.json](replay-regeneration.json) confirms
identical native identity and preexisting counts after the summary-only change.

**The next author-run round is the final reported result regardless of outcome.**
Use the complete fixed [author command](RERUN.md) once, with backend port 8765 and
no Architect override. Codex did not execute a real-provider round.
