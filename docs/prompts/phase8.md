# Codex task — Phase 8: Frontend

You are starting a **fresh session**. First read:
- `AGENTS.md`;
- the skills in `.agents/skills/`, starting with `infraarch-frontend`
  (it says which guidance wins), and `.interface-design/system.md`;
- `docs/design-deviations.md` (especially D-33 to D-38) and the latest
  entries of `docs/IMPLEMENTATION_LOG.md`;
- the spec: FR-UI-01 to FR-UI-07, FR-P-04, PR-02, UC-08 and TC-ui-01 in
  `docs/spec/03-requirements.tex`; Chapter 4's "UI design" section and the
  API list in `docs/spec/04-design.tex`; the four mockups
  `docs/spec/images/screen1_input.pdf` … `screen4_diff.pdf`;
- the real backend contract: `backend/app/api/schemas.py`,
  `backend/app/api/pipeline.py`, `backend/app/events/kinds.py` (`to_sse`),
  and the README API examples.

Phases 0–7b are complete. This task is **Phase 8 only**. The empty
`frontend/` folder (with `.gitkeep`) is where the app goes.

## Goal

Build the four-screen React frontend from the thesis, on top of the
existing API, so an engineer can submit a request, watch the pipeline live,
compare the variants, read the diff, fixes and validation report, review
`pending_review` packages, and download labelled packages. FastAPI serves
the built app, so the whole system runs from one origin.

## Decisions already made by the author (do not revisit)

1. **Stack:** Vite + React + TypeScript (strict), plain CSS with the tokens
   from `.interface-design/system.md`. Runtime dependencies: `react`,
   `react-dom`, `react-router`, `diff` (jsdiff). Nothing else at runtime.
2. **Our own SSE client** over `fetch` + `ReadableStream` (no
   `EventSource`, no SSE library), because the API key travels in a header
   (D-36) and PR-02 must be measurable. Rules are in the `infraarch-frontend`
   skill.
3. **Serving:** in development, Vite on port 5173 proxies `/api` to
   `localhost:8000`. Otherwise FastAPI serves `frontend/dist` at `/`, with
   an SPA fallback to `index.html` for non-`/api` paths. No CORS.
4. **Tests:** Vitest + Testing Library for units and components; Playwright
   (`@playwright/test`) end-to-end against the real backend with the stub
   model.
5. **Routes:** `/`, `/runs/:runId`, `/runs/:runId/compare`,
   `/runs/:runId/packages/:variant`, via `react-router`. Reloading any route
   restores the screen from the API.
6. **API key:** an optional field in the config panel, kept only in
   `sessionStorage`, sent as `X-API-Key`, cleared on 401 with a prompt to
   enter it again.
7. **Diff:** computed in the browser from `original_files` → `files` with
   jsdiff (line diff, unified view with context, like the mockup).
8. **No composite "security score".** The mockup's score is shown as real
   counts from the security report (blocking findings at first scan →
   remaining, fixes applied, outcome). Record as D-39.

## Rules

- No real LLM calls. Do not read `.env`. Do not push.
- **Installs:** you may run `npm install --save-exact --ignore-scripts` in
  `frontend/` **once**, for exactly the packages listed in section 1, after
  the author has approved their versions in your plan. Pick the current
  stable version of each that was published **at least 14 days ago**
  (check with `npm view <pkg> time`), and pin exactly. Commit
  `package-lock.json`. If a package needs install scripts to work, stop and
  report; don't work around it. Never use `npx` to fetch tools at run time.
- **Playwright browser:** the author installs Chromium
  (`npx playwright install chromium`) after the install step. Don't
  download browsers yourself.
- **Playwright skill:** use the globally installed `playwright-cli` (0.1.22)
  directly, not the skill's wrapper script (`npx --yes` would download).
- Commit after each numbered section, prefixed `phase8:`, with the
  requirement IDs, and add an implementation-log entry per commit.
- Backend changes are limited to what's listed in sections 0, 3 and 4.

## 0. Follow-ups from the Phase 7b review

1. **Stub always records `stub`.** When the resolved provider is `stub`,
   the resolved model is `"stub"`, even if `.env` sets `LLM_PROVIDER=stub`
   together with a real `LLM_MODEL`. Add the test.
2. **Wall-clock tests out of the default suite.** Mark the tests that
   assert elapsed time (PR-03 parallel runs, PR-04 download time, the
   validator elapsed-time check, and any similar one you find) with a
   `perf` marker. `make test` excludes `perf`; a new `make test-perf` runs
   only them. In the default suite, keep structural versions of these
   tests (for example: the three runs really overlap, the ZIP is complete).
   Real timings are Phase 9 work on a quiet machine.

## 1. Project setup

- `frontend/` with Vite + React + TS; `tsconfig` strict; ESLint
  (flat config with `typescript-eslint` and `eslint-plugin-react-hooks`).
- Allowed packages:
  - runtime: `react`, `react-dom`, `react-router`, `diff`;
  - dev: `vite`, `@vitejs/plugin-react`, `typescript`, `@types/react`,
    `@types/react-dom`, `@types/diff` (only if `diff` ships no types),
    `vitest`, `jsdom`, `@testing-library/react`,
    `@testing-library/user-event`, `@testing-library/jest-dom`, `eslint`,
    `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`,
    `globals`, `@playwright/test`.
- `npm` scripts: `dev`, `build`, `preview`, `lint` (ESLint +
  `tsc --noEmit`), `test` (Vitest), `test:e2e` (Playwright).
- Root `Makefile` targets: `frontend-install` (`npm ci --ignore-scripts`),
  `frontend-dev`, `frontend-build`, `frontend-test`, `test-e2e`. `make lint`
  also runs the frontend lint.
- `index.html`: `<html lang="en" style="color-scheme: dark">`, a
  `theme-color` meta matching `--bg`, title "InfraArchAgent".
- `src/styles/tokens.css` exactly from `.interface-design/system.md`.

**Stop after writing `package.json`** (without installing) and tell me the
exact versions you chose and their publish dates. Continue after I confirm.

## 2. API client, types and the SSE client

- `src/api/types.ts`: TypeScript types that match `schemas.py` exactly
  (results, review request/response, errors, SSE event data from
  `to_sse`). Add a unit test that loads a **recorded** results response
  and a recorded SSE stream (capture them once from a stub run and save
  them under `src/test/fixtures/`), and fails if a field the UI uses is
  missing.
- `src/api/client.ts`: `submitRun`, `getResults`, `review`, `download`;
  adds `X-API-Key` when set; turns `{error, message}` into a typed
  `ApiError(status, code, message)`.
- `src/api/sse.ts`:
  - a pure parser for `id:`/`event:`/`data:` frames, comments
    (`: keepalive`) and blank-line boundaries, robust to chunks split
    anywhere (test: feed a recorded stream byte by byte);
  - a stream function with `Last-Event-ID` resume, backoff reconnect on
    network errors, **no reconnect** after a normal server close, and
    abort on unmount;
  - `useRunStream(runId)` hook returning the ordered events plus a derived
    view model (stages, generator sub-statuses, package statuses, run
    status, log lines). The reducer is a pure function in `src/lib/` with
    its own tests.
- PR-02 support: each stage badge carries `data-testid` and
  `data-seq="<event seq>"`, and the reducer applies events immediately (no
  timers or batching).

## 3. Screens

Follow the mockups and `.interface-design/system.md`. Every screen has
loading, empty and error states.

**Screen 1, Input (`/`, FR-UI-01):**
- text area with character counter (use the backend's real limit from
  `app/domain/input_rules.py`), three example chips from one constants
  file, a collapsible config panel (provider, model, max iterations, API
  key; empty fields mean "server default"), and the orange Generate
  button;
- show the server's 400/422 validation message inline;
- Generate stays enabled until a submission starts; then it is disabled
  until that run reaches a terminal state (track the active run id in
  `sessionStorage` so a reload keeps the rule); on 202, navigate to
  `/runs/:runId`.

**Screen 2, Progress (`/runs/:runId`, FR-UI-02, PR-02):**
- four stage cards (Architect, Generators with cost/performance/security
  sub-rows, Security, Validator), each with status badge, elapsed time and
  latest message; a live log panel (monospace, auto-scroll that pauses when
  the user scrolls up);
- when the run is terminal, a clear "View results" action to the
  comparison screen; a failed run shows its safe error message.

**Screen 3, Comparison (`/runs/:runId/compare`, FR-UI-03):**
- one column per entry in `packages`, labelled by variant, with readiness
  label or status, the security counts (D-39), the validation result, and a
  file tree; a failure note per `missing_variants` entry;
- selecting a column gives it the orange border; "Open" goes to screen 4.

**Screen 4, Diff and review (`/runs/:runId/packages/:variant`, FR-UI-04..07):**
- left: file list (changed files marked); centre: unified diff of the
  selected file, red/green with `-`/`+` markers and line numbers,
  annotated with the rule IDs from the security report where the report
  links a fix to that file; right: tabs "Security fixes" (severity badges;
  resolved vs unresolved distinct in colour **and** label) and "Validation
  report" (passed/failed/warning/skipped, failures with file and line, a
  click selects that file);
- **pending_review** (`review_available` true): a panel explaining why,
  from `review_reasons` in plain language, and three controls in place of
  the download button: Approve, Retry with feedback (opens a text field;
  if `retry_targets` is empty, also a file picker for up to 5
  `target_files`), Reject (asks for confirmation). Only one action at a
  time; buttons disabled while a request is in flight;
- after a 202 retry, reopen the stream from the last seen id and show
  progress inline until the package settles, then refresh results;
- handle `run_in_progress`, `not_pending_review`, `feedback_needs_target`,
  `nothing_to_retry` and `too_many_runs` with clear messages;
- labelled packages (`downloadable` true): the label visible, and
  "Download ZIP" fetching with the key header and saving through a Blob
  URL (revoked afterwards).

Render all generated files, diffs and messages as text only (no
`dangerouslySetInnerHTML`, no HTML/markdown rendering).

## 4. Serving the build from FastAPI

- In `app/main.py`: if `frontend/dist/index.html` exists, mount the static
  assets and add an SPA fallback for `GET` requests outside `/api`; if it
  doesn't exist, the backend behaves exactly as now (tests must not need a
  build).
- Add security headers to the UI responses: a Content-Security-Policy
  allowing only `'self'` (scripts, styles, connect), `X-Content-Type-Options:
  nosniff`, `Referrer-Policy: no-referrer`. Don't change API responses.
- Tests: fallback serves `index.html` for `/runs/x/compare`; `/api/...`
  never falls back; missing `dist` keeps current behaviour.

## 5. Deterministic review scenario for end-to-end tests

The default stub produces clean packages, so nothing reaches review. Add a
test-only scenario:
- setting `PIPELINE_DEMO_SCENARIO` with values `clean` (default) and
  `review`. It only has an effect when the run's provider is `stub`; with
  any other provider it is ignored and a warning is logged at startup;
- in `review`, exactly one variant (say `security`) is generated with a
  deliberate, deterministic **validation** failure that the built-in checks
  catch (no external tool needed), so it ends `invalid → pending_review`;
  the stub fixer, given that failure as a retry target, returns the
  corrected file, so a retry ends `production_ready`;
- the other two variants stay clean;
- unit and integration tests for the scenario; document it in the README
  as a test/demo aid only.

## 6. Tests

| Area | Tests |
|---|---|
| Unit (Vitest) | SSE parser (split chunks, comments, multi-line data), reconnect and no-reconnect rules, reducer for every event kind, diff helper, review-reason text, API error mapping, types against recorded fixtures |
| Components | each screen's loading/empty/error states; submit disabled while active (FR-UI-01); missing-variant note (FR-UI-03); diff colours **and** markers (FR-UI-04); failed vs passed checks and resolved vs unresolved findings distinct (FR-UI-05); review controls replace download, and vice versa (FR-UI-06/07) |
| E2E (Playwright, `review` scenario, stub) | full flow: submit → live progress → compare → open the pending package → reasons shown → retry with feedback → settles `production_ready` → download a ZIP whose entries match the file tree; separate runs for approve and reject (reject keeps download with the label); reload on each route restores the screen; 409 for download of a pending package is never offered by the UI |
| PR-02 | Playwright: for each stage-badge change, the time between the event's server `timestamp` and the DOM mutation (MutationObserver), written to `frontend/test-results/pr02.json`; assert ≤ 1000 ms, tagged `@perf` and excluded from the default e2e run (`npm run test:e2e -- --grep @perf` runs it) |
| Accessibility | keyboard-only pass through the review flow in one e2e test; every control has an accessible name |

The e2e config starts the backend (`make run` with `PIPELINE_DEMO_SCENARIO=review`
and the stub) and the Vite dev server, or reuses running ones. It must not
call a real model even if `.env` configures one: every e2e request sends
`{"provider": "stub"}`.

## 7. Visual check against the mockups

With the backend and dev server running, use `playwright-cli` to open each
screen at 1440×900 in the `review` scenario, save screenshots to
`docs/evals/phase8-ui-<timestamp>/` (screen1 … screen4, plus the
pending-review state), and compare each against its mockup PDF. Fix
mismatches in layout, colours, hierarchy and states. In the summary, list
any deliberate differences from the mockups and why.

## 8. Documentation

- **D-39** (security counts instead of a composite score), **D-40**
  (frontend stack, own SSE client, serving model, `sessionStorage` key),
  **D-41** (the `review` demo scenario). Note in D-36 that the
  fetch-based client is now implemented.
- **"Thesis text to update", add:** the frontend stack and versions
  (Appendix A), the security-counts wording for Figure "Comparison panel",
  the diff annotation source, PR-02 measurement method, and that Screen 4
  shows the validation report as a tab.
- **README:** `make frontend-install`, `make frontend-dev`,
  `make frontend-build`, how `make run` serves the UI after a build,
  `make test-e2e`, `make test-perf`, the `review` scenario, and the
  Chromium install command for the author.
- Implementation log per commit, with real Vitest/Playwright/pytest counts.

## 9. Out of scope

- New backend endpoints or schema changes (except sections 0, 4 and 5).
- Run history list, user accounts, mobile layout, i18n.
- Any UI or component library, CSS framework or web fonts.
- Final performance measurements (Phase 9).

Finish with the summary format from `AGENTS.md` §10, and state explicitly:
- the exact npm package versions installed;
- Vitest, Playwright and pytest counts (default suites and `perf`);
- the PR-02 latencies measured in your run (max and median);
- the screenshot folder and any deliberate differences from the mockups.
