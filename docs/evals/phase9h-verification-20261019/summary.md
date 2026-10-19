# Phase 9h verification — 19 October 2026

Baseline: `26ef29fa0fbcf07604978b4c31244e1305640b50`.

Verification used disposable PostgreSQL 16 on loopback port 55439, synthetic
accounts/keys, stub LLMs and mocked provider HTTP. Dotenv loading was disabled
before Settings initialization. No author database or real provider was used.
No `.env` file was read or edited. No pushes, unrelated installs or image pulls.

| Check | Result | Evidence |
|---|---|---|
| `make lint` | PASS: Ruff/format, mypy 152 files, ESLint/TypeScript | [log](lint.txt) |
| `make test` | 1,656 passed, 0 failed, 0 skipped; 6 perf tests deselected; 537.76s | [log](backend-tests.txt) |
| Latest account/factory/native/golden regressions | 29 passed; 35.63s | [log](compatibility-tests.txt) |
| `make frontend-test` | 111 passed in 17 files | [log](frontend-tests.txt) |
| `make test-e2e` | 7 passed, 0 failed, 0 skipped; 4.1m | First-run, accessibility, reload and review flows below |
| Frontend production build | PASS: 147 modules | [log](frontend-build.txt) |

The full backend suite preceded the final small factory construction/account
repository refinements; the 29-test focused regression run exercised those
refinements and all four captured wire matrices afterward. Frontend tests/build
and lint ran after the final stale-probe response guard.

## Browser evidence

[Browser result log](browser-tests.txt). All browser flows used a dedicated backend process with synthetic database
reset, HTTP MockTransport provider catalog/probe/completions, and existing local
scanner/validator tools. The onboarding case covers first admin, automatic key
probe/catalog, supported thinking selection, cross-browser server draft
restoration, submission, reload/SSE resume and authenticated review. The other
six cases cover keyboard/accessibility, API failures, reload, and three review
actions. No real provider or network deployment was validated.

[Provider setup](provider-mocked.png) · [Account review](account-review-mocked.png).
Both screenshots were taken at 1280×800 using synthetic fixture data.

## Compatibility and limitations

Golden fixtures were captured before adapter changes from the baseline commit.
Header-authenticated HTTP submissions resolve configuration before the tests
send mocked SDK requests; serialized model/reasoning/complete response_format
and OpenRouter routing projections are byte-identical for every role. The
fixtures include omitted effort, low/off, inherited fixer effort and both
existing output modes. Native legacy omission is preserved; explicit managed
native requests also verify the correct `/v1/messages` path. A separate test
checks all five selections in benchmark environment output.

Migration 0008 revokes old shared-key browser sessions; setup revokes transitional
unbound sessions. Header scripts remain supported. Isolated migrations through
0012 succeeded. Inspection SELECT succeeded and UPDATE was denied; the app/owner
roles received no extra privileges. Compose validation used synthetic values and
`--env-file /dev/null`. The pgAdmin image was not present/pulled, so its browser
runtime remains unverified. No real model, OAuth/Responses or HTTPS verification.

Dependency additions: cryptography 50.0.2 (Apache-2.0 OR BSD-3-Clause), cffi 2.1.1
(MIT-0), pycparser 3.11 (BSD-3-Clause). Only cryptography is direct; versions are
locked. See D-50–D-53 for approved changes and future work; no new unresolved
product question was introduced.

Early verification attempts exposed stale results-contract assertions and a
malformed credit-response case; these were corrected before the passing runs.
An overlapping-database fixture run was stopped and repeated serially. Initial
browser attempts exposed account hydration/label timing, corrected before the
7-pass run. None of those partial attempts is counted as passing evidence.

## Benchmark and secret scan

`make secret-scan` passed: 0 findings, 0 scan errors across working tree and
all refs/reflogs, with dotenv paths excluded before retrieval.
[Final scan report](../phase9-secret-scan-20261019T155553111573Z/summary.md).

The first `make bench-stub` invocation stopped INCOMPLETE before any runs because
its PR-04 seed guard requires the database name `infraarch`, whereas the isolated
test database was named `infraarch_test`. The guard was preserved. A separate
`infraarch` database was created and migrated within the same disposable
container, then the benchmark was repeated there. The author database was
never involved. [Guarded first attempt](../phase9-bench-stub-20261019T154315214134Z/summary.md).

Final `make bench-stub` completed its schedule (command exit 0), with overall
**FAIL** reported by the benchmark, not a passing performance claim:

- PR-01: PASS, 10 runs; median 40.962s, maximum 57.036s.
- PR-03: FAIL, isolated baseline plus 3 concurrent runs; cohort/baseline ratios
  2.395–2.422. No failed or incomplete pipeline observations.
- PR-04: FAIL, 10 successful HTTP-200 downloads of 9,989,906-byte archives;
  median 1.988s, p90 2.497s, maximum 2.653s.
- PR-05: PASS for measured individual-agent thresholds.
- Quality: all 42/42 generated variants reached checks_passed under both recorded
  strict and contextual views. These are stub outputs, not real-provider evidence.
- All 14 pipeline runs record all five resolved agent selections in environment.json.
- Separate offline verification rehearsal: 6 iterations, 2 deadline-only rollbacks,
  3 initializations and 9 reuses. Excluded from quality rates and PR thresholds.

[Complete benchmark report](../phase9-bench-stub-20261019T154457135290Z/summary.md)
contains the raw measurements, quality snapshots and environment metadata.
PR-03/PR-04 remain measured performance gaps; thresholds were not weakened.
The seeded synthetic rejected archive is separately labelled and excluded from
package-quality rates.

The disposable backend was stopped and its PostgreSQL container removed after
verification. Existing author files/services were not modified.
