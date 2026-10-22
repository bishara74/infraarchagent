# Codex task — Phase 9j: UI polish (round 1)

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-47 to D-57),
the latest `docs/IMPLEMENTATION_LOG.md` entries, `docs/notes/ui-polish.md`
(**the task list**), the design system notes (`interface-design/system.md` if
present in the repo), the frontend (routes, layout/header, login gate,
settings pages, new-request form, model selection, recent runs, results,
review, diff) and its tests and Playwright flows. Phases 0–9i are complete.

## Goal

Implement every item in `docs/notes/ui-polish.md`. Rule: what is already
built wins unless the thesis wireframe (described in that file) is clearly
better. Behaviour, security properties (session cookie, CSRF, no secrets in
the browser), readiness labels and all backend rules stay unchanged.

## Rules

- No real LLM calls, no `.env` reads, no push.
- The author authorises exactly these new frontend dependencies, if not
  already present: `@fontsource/space-grotesk`, `@fontsource/jetbrains-mono`,
  `@vscode/codicons` (record versions and licences: OFL-1.1 / CC BY 4.0; add
  the Codicons attribution). No other new dependencies, no UI framework, no
  CDN at runtime.
- Plan mode first: report section 0 (including the root cause of both
  **[investigate]** bugs) before changing code.
- One commit per section of the list (0, A–H), prefix `phase9j:`, requirement
  IDs, implementation-log entries with real test counts.

## 0. Investigate (report first)

- Root cause of "Recent runs" hanging on "Loading saved preferences…".
- Why the Architect "Use default" shows google/gemini-3.8-flash:batch (saved
  admin/personal default vs. resolution bug) — read the DB state only through
  the app's own API/test fixtures, report, and propose the fix.
- Current component structure for header/nav, forms, model selects, settings
  tabs, and how styles are organised; where hard-coded colours live.

## Verification

- Vitest for every changed component (searchable combobox: filtering,
  keyboard, disabled invalid options with explanation; account menu; empty and
  error states; default labels).
- Playwright: login (centred card, no nav before login), account-menu logout,
  recent runs empty state and populated state, new request with collapsed
  configuration and model search, settings tabs, users reset-password dialog.
- Screenshots at 1280×800 of every screen saved under
  `docs/evals/phase9j-ui/` (for the author's review and the thesis).
- Run `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
  `make secret-scan` (real counts). D-58 (UI polish decisions, fonts/icons and
  licences). Summary in the `AGENTS.md` §10 format, starting with the two
  investigation results.
