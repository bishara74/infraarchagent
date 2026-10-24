# Phase 9j round 3 browser evidence

Captured at **1280×800**, using isolated UTF-8 PostgreSQL, the real FastAPI
application, stub agents and mocked provider HTTP. All visible run IDs, reports
and decisions belong to these deterministic test fixtures; no real inference or
deployment occurred. The existing dark thesis design and readiness labels remain.

| Screen/state | Capture |
|---|---|
| Login after explicit logout | [Login](login.png) |
| One-use deep link preserves query and fragment | [Deep link](login-deep-link.png) |
| Recommended routing ID, base metadata, 80px rows and effective thinking | [Model catalogue](model-routing.png) |
| Missing details with actionable Retry | [Catalogue retry](model-retry.png) |
| Passed checks with rejection-only review and retained download | [Checks passed](checks-passed-review.png) |
| Categorised rejection confirmation | [Reject dialog](reject-confirmation.png) |
| Automatic findings/report retained after rejection | [Rejected findings](rejected-findings.png) |
| Admin-only filtered history, matching count and both exports | [Review history](review-history.png) |

The browser checks cover root/login landing, explicit logout reset, a consumed
deep link including query/fragment, keyboard model navigation, exact routing ID
submission, inherited effort, aliases, option geometry, catalogue retry, required
category, modal focus and invalid-field focus, preserved reports, actual CSV/JSON
download contents/metadata, reviewer denial, history pagination, UTC date filters,
empty results and retry. Normal-flow console/page errors and horizontal overflow
are checked. Fault-injection scenarios deliberately return catalogue failures,
history 503 responses and authorization denials.

Review-history failure injection stays unavailable until the explicit Retry
interaction, making the check deterministic under React StrictMode. No retry
counts, timeouts or product guards were relaxed. Full UI sweeps also retain the
previous 1920×1080 checks; round 3 captures target the requested projector size.

## Final verification

| Command | Result | Evidence |
|---|---|---|
| `make lint` | PASS; Ruff/format, mypy 172 sources, ESLint/TypeScript | [Log](verification/lint.log) |
| `make test` | 2,029 passed, 0 failed/skipped, 6 performance tests deselected; 336.88s | [Log](verification/backend.log) |
| `make frontend-test` | 213 passed, 0 failed/skipped, 38 files | [Log](verification/frontend.log) |
| `make test-e2e` | 16 passed, 0 failed/skipped; 3.7m | [Log](verification/playwright.log) |
| `make frontend-build` | PASS | [Log](verification/build.log) |
| `make secret-scan` | 0 findings, 0 scan errors | [Summary](verification/secret-scan/summary.md) |

The first full backend pass had 2,027 passed / 1 failed because the exact response
field assertion lacked the new review_actions field. The first full browser pass
had 13 passed / 3 failed: an unscoped Retry selector, invalid username fixture and
an artificial failure consumed by duplicate StrictMode requests. These were fixed
without relaxing assertions, guards or timeouts. Select accessible names and the
retained readiness badge were also corrected before the final fresh browser run.

Header-authenticated golden-wire fixtures remain unchanged and pass. Generated
package bytes and existing readiness document content are retained; category is
the only added archive information. Historical category absence remains null and
is never backfilled by rewriting stored decisions or immutable events.
