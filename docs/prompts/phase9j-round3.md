# Codex task — Phase 9j round 3: UI polish, catalogue fixes, review categories

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-47, D-58),
the latest `docs/IMPLEMENTATION_LOG.md` entries, `docs/notes/ui-polish-round3.md`
(**the task list**), rounds 1–2 lists for context, and the frontend (auth
routing, model catalogue/combobox, review tab) plus the related backend
endpoints (catalogue, review decisions, archive) and their tests.

## Goal

Implement every item in `docs/notes/ui-polish-round3.md`. Behaviour, security
properties, readiness labels, archive contents (except the added review
category) and header-authenticated benchmark requests stay unchanged
(existing golden-wire tests must pass).

## Rules

- No real LLM calls, no `.env` reads, no push, no new dependencies.
- Plan mode first: report how the login route is remembered today, how the
  catalogue lookup handles `:nitro`, and whether review decisions need a
  migration for the category, before changing code.
- If a migration is needed: one additive migration; existing decisions get
  category `null` (shown as "not recorded").
- One commit per section (1–3), prefix `phase9j:`, requirement IDs,
  implementation-log entries with real test counts; update D-47/D-58.

## Verification

Vitest and Playwright for every item (login landing vs deep link, suffix
resolution with exact ID sent, effective thinking label, retry message,
alias hiding, compact rows, checks_passed reject flow, mandatory category,
admin export and reviewer denial). Run `make lint`, `make test`,
`make frontend-test`, `make test-e2e`, `make secret-scan` and a frontend
build (real counts). Screenshots at 1280×800 under
`docs/evals/phase9j-ui/round3/`. Summary in the `AGENTS.md` §10 format.
