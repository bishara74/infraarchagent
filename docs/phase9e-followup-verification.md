# Phase 9e follow-up verification — 2026-10-17

The [sanitized historical audit](evals/phase9e-security-loop-audit-20261017/audit.md)
records the confirmed diagnosis. Phase 5 commit `91633dc` (1 October 2026)
introduced `elif fingerprints in seen: reason = "no progress"`. Phase 9e's
rollback/baseline reuse (`5584316`) exposed the shortcut after rejected changes.
It ended 38 saved sessions early. Grounding was already sent: 52 saved proposal
measurements, 44 positive; sample lengths 11,689 and 15,452 exactly match
regenerated version-correct context. The zero summary read the wrong report
level. All 14 cached input SHA-256 hashes were unchanged after the audit.

The implementation continues bounded attempts after unchanged findings,
rejection or rollback; preserves validity/security safeguards and retained-file
baselines; and passes separate redacted rejection feedback capped at 4,000
characters. Canonical nested-session reporting has legacy fallback without
double counting and distinguishes positive, zero and missing measurements.
Readiness rules, thresholds, models, provider versions and output limits are
unchanged. D-45 and CL-01 document the approved behavior; no new open question
was introduced.

## Commands and actual results

Verification used isolated PostgreSQL 16 with owner/app roles and synthetic
credentials, dotenv-disabled settings, stub models, installed tools and the
offline mirror. No installs, downloads, dependencies, real LLM calls, real
benchmarks, database-interface changes, thesis edits or pushes were made.

| Command | Result |
|---|---|
| `make lint` | Passed Ruff/format, mypy (114 source files), frontend ESLint/TypeScript |
| `make test` | 1322 passed, 0 failed, 0 skipped, 6 perf deselected; 435.31 s |
| `make frontend-test` | 100 passed across 15 files; 19.18 s |
| `make test-e2e` | 6 passed; 3.9 min |
| `make secret-scan` | 0 findings, 0 errors; [evidence](evals/phase9-secret-scan-20261017T114149636340Z/summary.md) |
| `make provider-schema` | All seven pinned provider-version indexes exported offline |
| `make bench-stub` | Completed 14 pipeline runs / 42 ready packages and ten ZIP measurements; PR-01/05 pass, PR-03/04 fail |

The independent unit run passed 1121 tests in 177.72 s. Four legacy fixture/
assertion failures in an earlier focused run were corrected for the approved
continuation policy. A 12-case run encountered setup errors while Docker's WSL
integration was unavailable; after restoration, all cases passed in the final
full suite. Backend and E2E verification overlapped the benchmark on separate
application/test databases; E2E began after backend database tests completed.

## Measured stub evidence

[Summary](evals/phase9-bench-stub-20261017T113847606154Z/summary.md),
[quality](evals/phase9-bench-stub-20261017T113847606154Z/quality.json),
[agents.csv](evals/phase9-bench-stub-20261017T113847606154Z/agents.csv), and
[scripted verification rehearsal](evals/phase9-bench-stub-20261017T113847606154Z/verification-rehearsal.json)
are separate from historical real-run evidence.

| Measurement | Count | Median s | p90 s | Maximum s |
|---|---:|---:|---:|---:|
| PR-01 | 10 | 26.0000 | 35.0963 | 41.6738 |
| PR-03, including isolated baseline | 4 | 51.2740 | 51.8694 | 51.8694 |
| PR-04 ZIP download | 10 | 2.1627 | 3.3297 | 3.4380 |
| Separate scripted iteration verification | 6 | 14.8905 | 31.4790 | 31.4790 |

All 42 generated packages had valid gates and final readiness. Normal clean
stub packages attempted **zero security fixes** and required no repair rounds:
initial/post-security deadline stops are **0/0**. Their zero security-context
count reflects no calls. Package initialization totals are 42 runs, 126 reuse
events and zero reinitializations; generator context is 5,689 characters.

The separately labelled rehearsal used real offline Terraform, both AWS
versions and three concurrent private workspaces. Verification durations include
initialization, validation and concurrency waiting. It recorded three init runs,
nine reuse events, zero reinitializations, zero validity-regression rollbacks,
zero pre-candidate deadline stops and zero multiple-cause deadline rollbacks:
**0 deadline-only rollbacks / 6 attempted fix iterations**. These six attempts
are excluded from quality rates and PR thresholds. A deadline-only rollback
would not imply a candidate would have passed verification.

PR-03 cohort/baseline ratios were 1.6849–1.7190 and failed the existing threshold.
PR-04 also failed its unchanged latency threshold. These measured failures remain
visible; no thresholds, labels or benchmark settings were adjusted.

## Injected clocks and historical deadline stops

These are separate evidence, not estimates of real-run improvements:

- The three existing boundary cases assert one pre-candidate deadline stop,
  one deadline-only rollback and one rollback with both regression and deadline
  causes.
- The new complete-loop matrix asserts a timed-out first candidate is discarded,
  followed by a successful second attempt. The Retry variant does the same and
  preserves engineer feedback and prior session history.
- The injected short-stage case stops after two started attempts. Four injected
  baseline-only expirations exhaust the stage with zero fix attempts. Repeated
  findings, rejection and validity rollback each reach the configured allowance
  when findings remain; mixed-file cases retain verified non-Terraform edits.
- Existing long-security-stage tests still give post-security repair its fresh
  budget. The historical **four initial / nine post-security** deadline stops
  are unchanged historical observations. The new clean stub counts are 0/0.

The next step is an author-run real comparison using the existing 9d model and
benchmark settings and the documented Phase 9e budgets. This verification does
not predict real security quality, validity or deadline-stop improvements.
