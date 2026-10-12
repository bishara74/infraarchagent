# Phase 8 final scope audit

Audit date: 2026-10-13 (Europe/Budapest). Compare implementation against the
approved revision and base commit 321e1b9. This audit is documentation only;
it follows section 8 commit eb8d170 and makes no runtime/test/configuration change.

## Section coverage and order

| Section | Commit | Delivered and verified |
|---|---|---|
| 0 | 0b91450 | Domain stub-model normalization, provenance/factory tests; perf marker and default/perf structural split in Makefile/backend tests. FR-I-04, PR-03, PR-04. |
| 1 | fa9face | Pinned manifest/lock and strict Vite/React/TS/ESLint scaffold, tokens, test setup, proxy, Makefile, ignores and actual AGENTS.md stack line. Manifest checkpoint honored before the single approved install. NFR-01. |
| 5 | d355c46 | Settings/env example, resolved-stub-only review scenario and trusted fixer adapter; built-in failure/fix, isolation/startup warning and PostgreSQL flow tests. FR-UI-07, FR-S-08. |
| 2 | e21ff7b | Required marker-derived retry boolean, backend schema/results/tests, TS contract, central API/auth/download client, UTF-8 SSE parser/reconnect/EOF rules, reducer/shared store/hooks, real pending/repaired fixtures and explicit recorder. FR-P-04, FR-UI-02, PR-02, NFR-01. |
| 3 | ce839e2 | Four screens, native accessible controls, real report/count views, file tree/contextual diff, review/ZIP/auth/page states, URL selections and component tests. FR-UI-01..07, UC-08. |
| 4 | 13a3aa7 | Optional same-origin FastAPI SPA/assets with API reservation, traversal/missing-file handling, UI-only headers and temporary-dist tests. FR-UI-01, NFR-01. |
| 6 | b638b7a | Real-backend single-worker Playwright review/reload/accessibility/PR-02 tests, tool preflight and dotenv-disabled Python/migration/E2E bootstrap. FR-UI-01..07, FR-P-04, UC-08, PR-02, NFR-01. |
| 7 | 362d8e2 | All mockups inspected with global CLI; real flow, final 1440×900/1024px screenshots, built SPA/CSP check, deterministic cancellation fix, ownership/retry/timing/layout corrections and saved latency evidence. FR-UI-01..07, FR-P-04, UC-08, PR-02, NFR-01. |
| 8 | eb8d170 | README status/setup/results contract, implemented D-39/D-40/D-41 and D-36, D-33 normalization note, collected thesis changes and exact dependency/publish-date record. |
| 9 | This audit | Documentation-only scope verification and final implementation-log entry. No later-phase implementation. |

Every section has one phase8: commit with requirement IDs and an implementation-log
entry, in order 0 → 1 → 5 → 2 → 3 → 4 → 6 → 7 → 8 → 9.

## Backend boundaries and approved exceptions

The normal backend changes match the approved section 0/5/2/4 files: run_config,
settings, demo stub/factory, results/schema, optional frontend serving/main and
related tests/tooling. Existing architecture boundaries, state rules, event-log
writer and ordinary owner/app privileges remain unchanged.

The sole results-schema delta from the base is required
PackageResult.retry_in_progress: bool. Results derive it only from the existing
review_retry_started_at marker, without exposing the timestamp. TS and recorded
fixtures require it. No database model, repository, migration or other response
field changes. AST comparison confirms all pipeline-router endpoint decorators
are identical to the base; the new serving route is only the approved UI fallback.

The author expressly approved the extra SSE cancellation exception in section 7.
Only replay/close-check database reads and their session cleanup are shielded in
api/pipeline.py. The regression first failed on unchanged code (3 failed, 2
cancellation-bound cases passed), then all 10 SSE tests passed. Each canceled-read
case leaves zero checked-out connections and runs a full three-package pipeline
on the same engine/pool. Live/keep-alive cancellation completes within a 0.5-second
watchdog despite a configured 60-second wait. D-40 and the section 7 log record
the cause and narrow exception; there is no new endpoint/schema/migration/dependency.

## Scope and protected files

Read-only git checks show no changes under docs/spec/ or backend/app/db/
(including applied migrations), nor to backend/app/domain/states.py. REVISION.txt
remains untracked and was never opened, edited or staged. No push/rebase/history
rewrite. No .env read, real credential or real LLM call; verification disables
dotenv before settings instantiate, including subprocesses and Vite.

The four runtime packages and 18 dev pins match the approved manifest and lock;
all 22 installed direct versions match the dependency record. The lock is unchanged
since section 1. Only @types/node and @testing-library/dom are approved allowlist
additions; TypeScript 6.0.3 is the approved compatibility exception. One initial
npm install --save-exact --ignore-scripts; no subsequent install, installation
script or agent browser download. The author installed Chromium/system libraries.

No accounts, history list, mobile layout, i18n, UI library, CSS framework, web font,
new pipeline API endpoint or Phase 9 final performance evaluation was added.
Generated code/messages render as text. Authentication remains session-only and
header-based. UI counts and screenshot data come from the actual backend.

D-39/D-40/D-41 and updates to D-33/D-36 capture the deliberate differences:
real counts replace the score; file-linked annotations and validation tabs;
approved stack/Node minimum, external-CSS dark scheme under CSP, EOF marker rule,
and opt-in deterministic demo. Native configuration includes the model/API-key
fields required by the prompt; sparse real demo packages replace invented mockup
files and traits. No new unresolved ambiguity or open question was introduced.

## Actual verification evidence

| Area | Latest executed result |
|---|---|
| make lint | Passed Ruff/format (180 files), mypy (98 sources), ESLint and both strict TypeScript projects |
| Frontend production build | Passed |
| make test | 1057 passed, 0 failed, 0 skipped, 6 deselected (196.01s) |
| make test-perf | 6 passed, 0 failed, 0 skipped, 1057 deselected (30.38s) |
| Frontend unit/components | 82 passed, 0 failed, 0 skipped, 13 files (13.59s) |
| Default E2E | 6 passed, 0 failed, 0 skipped (2.4m) |
| Final PR-02 @perf | 1 passed, 0 failed, 0 skipped (28.6s) |
| SSE cancellation suite | 10 passed (31.13s); original red run 3 failed/2 passed |
| Manual/visual | All four mockups checked; real failure → retry → readiness → verified ZIP; 1440×900 and 1024px evidence; FastAPI build renders under CSP with 0 console errors/warnings |

Saved pr02.json: 32 observed live samples, max 663ms, median 165.5ms, all four stages
covered. Historical replay is excluded; multiple mutations per callback are
reconstructed by sequence. Earlier failures and development runs remain recorded
in the implementation log/evidence notes. No test threshold was relaxed.

These are Phase 8 development checks. Final performance measurements remain
Phase 9. Thesis wording is collected for the author's later source updates.
