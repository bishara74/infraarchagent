# Phase 8 UI evidence

Captured with global playwright-cli 0.1.22 and author-installed Chromium
153.0.8010.12 (Playwright 1.63.0), using the real local PostgreSQL test database,
installed offline scanners/Terraform and the stub review scenario. No generated
file, count, duration, run ID or message was invented for these screenshots.

## Mockup comparison

| Screen | Verification and intentional differences |
|---|---|
| Input | Dark tokens, system type, broad textarea, native config and primary action. Model/API-key fields extend the mockup as explicitly required. Empty values mean server default; the counter uses actual trimmed Unicode code points. Copy asks for checks/review rather than promising deployability. |
| Progress | Four real stages with immediate badges, elapsed UTC timestamps and ordered log. Generator states are horizontal as in the PDF; a compact log viewport keeps the screen visible at 1440×900. Sub-second stub stages correctly show 0s. Stage durations use the union of real active intervals, excluding review gaps and double-counted concurrent variants. Full run ID remains real; long request text is ellipsized with its full title. |
| Comparison | Three returned columns, URL-selected orange border, real blocking/fix/outcome/validation counts and derived file directories. Deployment traits and composite scores absent from the API are omitted. Demo files are sparse rather than filling the screen with invented files. |
| Package | File sidebar, contextual line diff and right report tabs. Pending review controls replace download; readiness controls stay in a consistent separate panel. Validation-only fixes have no security rule IDs or invented severity. Both current validation and retained fix history remain visible. |

Each mockup PDF was rendered locally in Chromium and compared visually. PDFs in
docs/spec were read only. System colours, 4px spacing rhythm, borders-only depth,
semantic text badges and keyboard focus remain the fixed design direction.

## Real flow

Final manual run 18f1ab93-15a9-49c6-97c2-4d30c626dd61 reached pending review on
terraform.local_ref at terraform/main.tf:4. Terraform also reported the same
undeclared local. Retry declared review_demo, reached production ready and
retained the original output block. The ZIP was opened and verified to contain
terraform/main.tf with the actual locals repair plus INFRAARCHAGENT_READINESS.md
headed PRODUCTION READY. The run remains historically partial_success.

All four screen layouts were checked at 1024px. Package and progress page widths
were measured as exactly 1024px, with no page overflow; final progress page height
was 900px. A second actual run, a0deaf7b-92f1-450f-9e39-5fa8fd48f9d0, supplies the
final live progress screenshots. Earlier manual run 5bbd233d-c41a-41a8-bc78-cb601fdbb2a3
also completed the review/repair/download flow before regression cleanup. The built SPA
was also loaded through FastAPI at port 8000 under self-only CSP; computed page
background was rgb(15, 17, 23), and CSS/JS/virtualized rows rendered correctly.
Initial favicon 404 was resolved with the local brand SVG. The final built SPA console reported 0 errors and 0 warnings. Recorded routes/run
IDs are test fixtures and can be removed by the regression database cleanup.

## PR-02 development measurement

pr02.json contains 32 real server-event-to-DOM-mutation samples: max
663ms, median 165.5ms. All four stage badges had multiple observed live
transitions. Earlier development measurements were: 1134ms/275.5ms (failed),
949ms/305ms (passed), and 726ms/242.5ms (passed). The live log now reuses
Intl.DateTimeFormat instead of allocating a formatter during every event commit.
The limit remains 1000ms. These observations are not controlled comparisons,
Phase 9 final measurements or guarantees under arbitrary machine load.

## Verification

- make lint: Ruff/format (180 files), mypy (98 sources), ESLint and both strict
  TypeScript projects passed; frontend production build passed.
- make test: 1057 passed, 0 failed, 0 skipped, 6 deselected (196.01s).
- make test-perf: 6 passed, 0 failed, 0 skipped, 1057 deselected (30.38s).
- Frontend Vitest: 82 passed, 0 failed, 0 skipped in 13 files (13.59s).
- Default Playwright: 6 passed, 0 failed, 0 skipped (2.4m), including active-run
  reload, keyboard-only review, key reentry, retry/ZIP, approval and rejection.
- Final @perf Playwright: 1 passed, 0 failed, 0 skipped (28.6s).
- Final SSE regression: 10 passed (31.13s), including cancellation watchdogs
  with a 60-second configured keep-alive wait and three same-pool full pipelines.

## Backend bug found during Phase 8

Full reload while an SSE database read owns a connection reproducibly exposes
a pre-existing backend cancellation-cleanup race. A closed pooled connection
then causes an unrelated pipeline transaction to fail. Frontend ownership
transfer now avoids navigation/StrictMode cancellation and aborts on final
unmount, but cannot prevent real browser disconnects. The author approved a narrow backend scope exception recorded in D-40.
Only replay/close-check database reads and their session cleanup are shielded;
yields and live/keep-alive waits stay cancellable. On the unchanged code, the
synchronized regression failed at all three read points (3 failed, 2 passed).
After the fix, the SSE suite passed all 10 tests, including complete successful
stub pipelines on the same engine/pool after cancellation, no checked-out
connection left behind, and cancellation within a 0.5-second watchdog while the
configured keep-alive wait is 60 seconds. No endpoint, schema, migration or
dependency was added. Full default backend regression: 1057 passed, 6 deselected.
