# Codex task — Phase 9j round 2: UI polish and bug sweep

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-58),
the latest `docs/IMPLEMENTATION_LOG.md` entries, `docs/notes/ui-polish-round2.md`
(**the task list**), `docs/notes/ui-polish.md` (round 1, for context),
`docs/evals/phase9j-ui/`, and the frontend (new-request form, draft
persistence, ModelControls/combobox, model catalogue loading, results,
diff, review, downloads) plus the related backend endpoints and tests.
Phases 0–9j round 1 are complete.

## Goal

Implement every item in `docs/notes/ui-polish-round2.md`, starting with the
bug sweep (section 0) and the **[bug]** items. Behaviour, security properties
(session cookie, CSRF, no secrets in the browser), readiness labels,
benchmark/header request behaviour and archive contents stay unchanged.

## Rules

- No real LLM calls, no `.env` reads, no push, no new dependencies.
- Plan mode first: report the bug-sweep findings and the root causes of the
  four model-dropdown bugs before changing code.
- Model filtering applies to the interactive UI only. Header-authenticated
  benchmark runs and environment defaults must keep sending exactly the same
  requests as today (existing golden wire tests must still pass).
- The recommended-model allowlist is a versioned config file, documented in
  D-58; never invent capability data — use the provider catalogue.
- One commit per section of the list (0–5), prefix `phase9j:`, requirement
  IDs, implementation-log entries with real test counts.

## Verification

- Vitest for every changed component (empty prompt + draft restore/discard,
  catalogue states and retry, unknown vs incompatible capabilities, dropdown
  panel sizing, recommended/all-compatible toggle, `:free` hiding, whitespace
  toggle and counts, results overview and tabs, download-all).
- Playwright: login → empty prompt with draft hint; model search with the
  recommended list; results overview → inspect variant → files/fixes tabs →
  approve; download all three; diff with formatting-only hunks hidden.
- Updated screenshots at 1280×800 under `docs/evals/phase9j-ui/round2/`.
- Run `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
  `make secret-scan` and a frontend build (real counts). Update D-58.
  Summary in the `AGENTS.md` §10 format, starting with the bug-sweep findings.
