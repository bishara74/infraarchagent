# Phase 9j round 2 UI evidence

The [bug sweep and root causes](BUG_SWEEP.md) were reported before code changes.
This gallery contains **72 updated captures**: 46 at 1280×800 and 26 at
1920×1080. Two additional pre-change captures are isolated in baseline/.
The [manifest](manifest.json) records image dimensions/SHA-256 and hashes of 281
source files. Captures use local fonts, reduced motion and synthetic data from
real isolated PostgreSQL 16 plus mocked provider HTTP and local scanners.
No inference or deployment was performed. Nitro's catalogue name, prices,
capabilities and context in these screenshots are explicitly mocked test metadata,
not a measurement of the real provider.

| Screen / behavior | 1280×800 capture |
|---|---|
| First administrator setup | [Setup](setup.png) |
| Login | [Login](login.png) |
| Empty editor with dated draft hint | [Draft recovery](empty-prompt-draft.png) |
| Account menu | [Account menu](account-menu.png) |
| Request configuration and Advanced | [Configuration](configuration.png), [Advanced](configuration-advanced.png) |
| Provider-confirmed recommended model | [Recommended search](recommended-search.png) |
| Bounded single-result model search | [Bounded dropdown](bounded-model-search.png) |
| Catalogue failure with Retry | [Retry](catalogue-retry.png) |
| Pipeline progress | [Progress](progress.png) |
| Comparison first, pending review | [Overview](overview.png) |
| Labelled variants and all-three download | [Ready overview](overview-ready.png) |
| Current files | [Files](files.png) |
| Security diff | [Security fixes](security-fixes.png) |
| Findings and validation | [Findings](findings.png) |
| Per-variant review and rejection confirmation | [Review](review.png), [Reject dialog](reject-dialog.png) |
| Formatting-only changes hidden or visible | [Hidden](formatting-hidden.png), [Full diff](formatting-visible.png) |
| Provider and selected credential | [Provider](provider.png), [Selected](provider-selected.png) |
| Credential revoke dialog | [Revoke](revoke-dialog.png) |
| Personal, compatible and administrator models | [Models](models.png), [Compatible](models-compatible.png), [Administrator](models-admin.png) |
| Users and password reset | [Users](users.png), [Reset](reset-dialog.png) |
| Account preferences | [Account](account.png), [Preferences](account-preferences.png) |
| Recent history and empty state | [Recent](recent.png), [Empty](recent-empty.png) |

[1920×1080 captures](1920/) include setup and the same full-screen/dialog sweep.
Long Settings/configuration sections also have explicitly scrolled captures.
Overview inspection/download controls fit inside the initial viewport at both
sizes, verified with browser geometry assertions. File content stays escaped;
large lists and diffs retain bounded virtual rendering.

## Verification

- `make lint`: exit 0; Ruff/format, mypy on 167 app sources, ESLint/TypeScript.
- `make test`: **1,994 passed, 0 failed/skipped; 6 performance tests deselected**, 396.39s.
- `make frontend-test`: **190 passed, 0 failed/skipped**, 35 files.
- `make test-e2e`: **12 passed, 0 failed/skipped**, 3.9 minutes.
- `make frontend-build`: passed with bundled local assets.
- `make secret-scan`: **0 findings, 0 scan errors**, all refs/reflogs and working tree;
  [final secret-scan evidence](verification/secret-scan-final/).
- Additional pre-section-5 versus current ZIP writer checks: **3 identical-byte
  cases**, including readiness filename collisions and mixed file/newline content.
- The focused model/golden-wire suite passed **13 tests**; bundle/download tests
  passed **14 tests**, including a synchronised concurrent-file-change snapshot test
  and the final new-surface secret-canary/redacted-manifest check.

The bundle canary was extended after the full backend run; the focused 14-test
archive suite and complete lint were then repeated successfully. Application code
was unchanged.

Both final sweeps recorded **0 console errors/warnings, failed requests or
unhandled page errors**, no horizontal overflow and no controls protruding
horizontally. Native dialogs preserve background inertness, Escape and trigger
focus; visiting browser chrome during Tab is not treated as a background leak.
[Verification logs and sweep measurements](verification/) include exact results;
only trailing whitespace is normalized in exported command logs.

The browser flow proves login with an empty editor/draft hint, explicit restore
and durable discard, recommended model search, overview-first inspection, all
four tabs, authenticated per-variant approval, and an all-three download whose
manifest/payload hashes match the individual labelled downloads. Separate browser
fixtures prove the 300-model geometry/End/search/chevron regression, catalogue
retry, whitespace counts, server preference reload and identical download bytes
before/after presentation changes.

## Failed attempts and limits

An early simultaneous backend/browser run shared a test database and was discarded.
Final suites use separate clusters and execute serially to avoid resource
contention. A contended full backend run had **1 failed / 1,993 passed**: the
existing 1.1-second cancellation test reached its deadline before its HTTP mock
started. A concurrent frontend run had **10 timeouts / 180 passed**; the browser
run reached a scanner error, had six completed passes and one failure before
interruption (exit 130). Complete quiet reruns above pass without relaxed budgets.
An earlier complete browser run also passed all 12 tests; visual review then
compacted overview spacing and the final 12-pass replay verified control bounds.

The initial temporary database was SQL_ASCII and four Unicode review/archive
checks failed; it was recreated as UTF-8. One auxiliary migration rerun used
relative bootstrap paths across subprocess working directories, so dotenv
suppression for that subprocess could not be established. It is excluded as
trusted isolated evidence; all final verification uses absolute bootstrap paths
that disable dotenv before settings instantiate. No real provider calls were
made, and secret scans found no leaked credentials. These harness issues are
recorded rather than represented as passing evidence.

No real-provider availability, cloud deployment or new performance qualification
is established. The API contains no infrastructure cost estimate or proven
per-variant architecture differences; the UI labels shared planned properties,
optimisation goals and unavailable costs honestly. D-58 records all changes;
no new specification open question is introduced.
