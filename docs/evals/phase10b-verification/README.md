# Phase 10b verification

The [counter-audit](../phase10b-exposure-audit/README.md) covers **998 packages in
33 folders**, with **3 confirmed public-to-internal regressions**. One affected
baseline package passed all three profiles. Pooled matched baseline passes become
43/120 → 42/120 on confirmed evidence; one unresolved passing package leaves a
corrected range of **41–42/120 (34.2–35.0%)**. There are 703 unknown exposure
outcomes, including 686 packages without source projections. Final-set strict/v1
counts remain 7/40 and 8/41; historical v2 was unavailable. This is static evidence,
not deployment success.

| Verification | Actual result | Evidence |
|---|---|---|
| `make lint` | Passed: Ruff, format checks, mypy (189 app files), ESLint and both TypeScript projects | [final console](make-lint-final.txt) |
| `make test` | 2,739 passed, 0 failed, 0 skipped; 6 performance tests deselected; 605.03 s | [full console](make-test.txt) |
| Final backend checks | 30 passed, 0 failed, 0 skipped; includes the three tests added after the full run for indexed finding identity, supporting-resource attribution and current evidence links | [console](final-focused.txt) |
| `make frontend-test` | 467 passed, 0 failed, 0 skipped across 46 files, with `VITEST_MAX_WORKERS=2` | [final console](make-frontend-test-final.txt) |
| `make test-e2e` | 35 passed, 0 failed; 7.5 minutes | [full console](make-test-e2e.txt) |
| Final browser regression | 1 passed, 0 failed; additionally verifies a rolled-back accepted proposal is unresolved and counts as zero applied fixes | [console](browser-final-focused.txt), [1280×800 screenshot](ui/plan-conflict-review.png) |
| `make test-perf` | 6 passed, 0 failed, 0 skipped; 2,742 deselected; local 10 MiB ASGI transfer 1.055 s, below the unchanged 2 s bound | [console](make-test-perf.txt), [measurements](../phase9-backend-perf-20261027T010755833838Z/results.json) |
| `make secret-scan` | Passed: 0 findings, 0 scan errors; working files and all existing refs/reflogs scanned | [final console](make-secret-scan-final.txt), [verdict](../phase9-secret-scan-20261027T012114354486Z/summary.md) |
| `make traceability` | 59 IDs, 0 uncovered, 0 invalid annotations, 0 collection failures; 2,748 pytest cases collected, not a passing-test claim | [summary](../phase10b-traceability/summary.md), [console](make-traceability-final.txt) |
| Evidence-index generation | 45 met, 12 partly met, 1 not met, 1 unverified across 59 IDs | [index](../EVIDENCE.md) |

The full backend run precedes the final three backend tests and the final UI
presentation correction; focused backend checks and complete frontend checks cover
those final changes. Performance selection collected all 2,748 backend cases.
The final browser check follows the full browser suite. These are separate runs,
not an invented aggregate full-suite count.

Verification used task-owned native PostgreSQL 16 clusters on loopback ports
55442/55443, the normal owner/app roles, synthetic credentials and the existing
`INFRAARCH_TEST_BOOTSTRAP=1` dotenv-disabled bootstrap. Installed binaries replace
the Docker test service without any install or image pull. Providers are mocked;
no real LLM/API request, operator dotenv read, install, external service or push
was performed. Local browser/backend/database HTTP/TCP is confined to loopback.
Performance ran after the full suites stopped; it measures the local ASGI path,
not WAN download time, real-provider performance or deployment readiness.

Initial failures remain visible: the first full backend run had 2,725 passed,
1 failed and 6 deselected because the old whole-run equality assertion omitted
new disabled Fixer provenance ([console](make-test-initial.txt)). The updated
assertion preserves all stable fields and checks that disabled provenance has no
lesson use. The first frontend run had 457 passed and 7 timing failures under
unbounded worker contention ([console](make-frontend-test-initial.txt)); bounded workers
passed 466, then the final added rollback test brought the result to 467. No test
timeout or performance bound was relaxed.

[Protected source checks](protected-sources.json) verify 58 specification,
scanner/policy/threshold, dependency, existing migration and unaffected prompt
files against baseline `6805f79`. The new 0016 role migration is additive.
[Historical checks](historical-evidence-preservation.json) verify unchanged Git
content for 5,672 baseline evidence files, excluding only the explicitly updated
current index/register. Existing CRLF CSV checkout bytes are preserved; 174 CSVs
match LF Git blobs under repository normalization. The browser harness backs up
and restores 94 historical captures byte-for-byte, placing refreshed captures
under `ui/suite/` ([restoration manifest](browser-history-preservation.json)).
Historical evidence directories are not rewritten by this task.

The bounded guard covers supported exposure controls and preserves unresolved
network/dependency projections conservatively. It also protects validation and
provisional syntax-repair Fixer acceptance. It does not certify service purposes,
storage semantics, assumptions, functional completeness, live AWS capacity or
runtime reachability. Unknown changed exposure is rejected; provably unrelated
fixes remain eligible. Private/unknown explanations differ from public intent.
Only relevant still-open findings are annotated, including indexed resources and
supporting resources in other files. Rolled-back fixes are not shown as applied;
legacy reports without retained status keep their earlier display fallback.

[Author analysis](../phase10b-author-lesson-runs/README.md) records a 12-row matrix,
ten scoped lesson-bearing Generator attempts with zero hash/scope mismatches,
and 4 Architect/62 Fixer attempts without recorded injection. Four different
plans and one run per configuration demonstrate the mechanism, not a measured
lesson effect. Run 4's historical self-approved/null-actor provenance was correct;
new direct/reviewed actor snapshots and immutable legacy nulls pass end-to-end
manifest/archive/event tests. D-60/D-63 document the interpretation and remaining
limits; no new open question is introduced.

For reproduction, use the dotenv-disabled synthetic test setup in README, run
the Make targets above, and use an **absolute** fresh `--output-dir` for
`make traceability TRACEABILITY_ARGS=...` because Make executes it in `backend/`.
The collected traceability output was relocated to its canonical folder after
collection. Evidence generation is `cd backend && .venv/bin/python -m
scripts.phase10_evidence`. Apply migration 0016 with `make migrate` using the
owner role and restart before using explicit Fixer lessons. No live migration
of the author's database was attempted. Both task-owned test clusters were stopped
after verification. Console files preserve original whitespace verbatim.
