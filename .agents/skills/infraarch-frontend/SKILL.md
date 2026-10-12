---
name: infraarch-frontend
description: Use for any work in frontend/ of InfraArchAgent - building or changing screens, components, the API client, the SSE stream client, styles, or frontend tests. Encodes the thesis mockups, the backend API contract and the project's UI rules.
---

# InfraArchAgent frontend

This UI is part of an ELTE BSc thesis. It must match the thesis design
(Chapter 4, "UI design", and the screen mockups in `docs/spec/images/screen1_input.pdf` to
`screen4_diff.pdf`) and the requirements FR-UI-01 to FR-UI-07, FR-P-04 and
PR-02 in `docs/spec/03-requirements.tex`. When this skill and the phase
prompt disagree, the phase prompt wins. When a general design skill and the
mockups disagree, **the mockups win**: this is a working tool for DevOps
engineers, not a landing page.

## Which guidance wins

1. The phase prompt.
2. This skill.
3. `.interface-design/system.md` (tokens and component patterns from the
   mockups; the direction there is already decided).
4. The `interface-design` skill, for craft only: hierarchy, spacing rhythm,
   states and polish. Do **not** run its domain exploration or propose a
   new direction, palette, typeface or signature. Prefer native HTML
   controls; add no headless-UI library without the author's approval.
5. The review checklist in `references/web-interface-guidelines.md`.

## Stack (fixed)

- Vite + React + TypeScript (strict mode), plain CSS with CSS custom
  properties. No UI framework, no CSS-in-JS, no Tailwind.
- Runtime dependencies are limited to: `react`, `react-dom`, `react-router`
  and `diff` (jsdiff). Anything else needs the author's approval first.
- Tests: Vitest + Testing Library for units/components; Playwright
  (`@playwright/test`) for end-to-end tests against the real backend with
  the stub model.
- Exact versions in `package.json` (no `^` or `~`), and a committed
  `package-lock.json`. Never run `npm install <new package>` yourself; ask.

## Visual language (from the mockups)

- Dark navy backgrounds, orange accent for the primary action and the
  selected variant, monospace for code, diffs and the live log.
- Define everything as tokens in `src/styles/tokens.css` and use only
  tokens in components: `--bg`, `--surface`, `--surface-raised`,
  `--border`, `--text`, `--text-muted`, `--accent` (orange),
  `--ok` (green), `--running` (blue), `--queued` (gray), `--warn`,
  `--danger`, `--diff-add-bg`, `--diff-del-bg`, `--font-ui`, `--font-mono`.
- Status badges: green = complete/passed, blue = running, gray = queued,
  red = failed. Never rely on colour alone: every badge also has text, and
  diff lines also have a `+`/`-` marker (accessibility, and FR-UI-04/05
  "distinct colour" must also be distinguishable without colour).
- Unresolved security findings use a different colour **and** label from
  resolved ones (FR-UI-05).
- Use the system font stack plus a system monospace stack. Don't load web
  fonts from the internet (the app must work offline).
- Layout targets a desktop browser (1280px and up). It should not break at
  1024px; mobile is out of scope.

## Content discipline

Every string, number and label on screen is either real data from the API
or plain, honest UI copy. Screenshots of this UI go into the thesis, so:

- **No invented data.** No fake run IDs, timings, scores, counts, model
  names or log lines to make a screen look busy. If there is no data, show
  an explicit empty or loading state.
- **No filler labels**: no decorative all-caps subtitles, `//`-style
  kickers or slogans. If removing a label loses no information, remove it.
- **Standard words for standard actions**: "Generate", "Download ZIP",
  "Approve", "Retry with feedback", "Reject", "Back to comparison". No
  themed renamings.
- **No unicode symbols as icons** (▣, ◊, ➜ and the like). Use a tiny set of
  inline SVG icons written in the project, or text only.
- Terms match the thesis: package, variant (cost, performance, security),
  readiness label, pending review, production ready, not production ready.
- Examples on screen 1 use the three real example prompts defined in one
  constants file, not lorem ipsum.

## Screens and routes

| Route | Screen | Key requirements |
|---|---|---|
| `/` | 1 Input | FR-UI-01: text area, character counter, 3 example chips, collapsible config panel (provider, model, max iterations, API key), submit disabled while a run is active |
| `/runs/:runId` | 2 Progress | FR-UI-02, PR-02: four stage cards (Architect, Generators with per-variant sub-status, Security, Validator), elapsed time, one-line message, live log panel |
| `/runs/:runId/compare` | 3 Comparison | FR-UI-03: up to 3 columns from `packages`, a failure note per `missing_variants` entry, file tree, selected variant has an orange border |
| `/runs/:runId/packages/:variant` | 4 Diff and review | FR-UI-04..07: file sidebar, diff, fix list and validation report, readiness label, review controls or download |

Reloading any route must restore the screen from the API (results endpoint
plus stream replay); never depend on state that only lived in memory.

## Backend contract (do not invent fields)

- Read the actual response models in `backend/app/api/schemas.py` and the
  README examples. Generate or hand-write `src/api/types.ts` to match them
  exactly, and keep a test that fails if a field used by the UI is missing
  from a recorded results fixture.
- Use the derived fields from the results endpoint (`readiness_label`,
  `downloadable`, `review_available`, `review_reasons`, `retry_targets`).
  **Never recompute these rules in the UI.**
- Errors come as `{error, message}`. Show `message`; branch on `error`
  codes (`run_in_progress`, `not_pending_review`, `feedback_needs_target`,
  `nothing_to_retry`, `too_many_runs`, `unauthorized`, `not_downloadable`).
- All requests go through one API client module that adds `X-API-Key` when
  a key is set.

## SSE stream client (our own, no library)

- Implemented over `fetch` + `ReadableStream` in `src/api/sse.ts`, with a
  pure parser function for `id:`/`event:`/`data:` lines that is unit-tested
  with recorded server output, including chunks split mid-line.
- Sends `X-API-Key` and `Last-Event-ID`. Reconnects with backoff after a
  network error, resuming from the last seen id. **Does not reconnect** when
  the server ends the stream normally (run settled, no active package).
- After a retry review (202), reopen the stream from the last seen id.
- Expose it to React through one hook, `useRunStream(runId)`. Components
  never touch `fetch` or the parser directly.
- PR-02: apply each event to state immediately (no batching timers, no
  polling). Put a `data-testid` and the event `seq` on each stage badge so
  Playwright can measure event-to-DOM latency.

## Security rules (NFR-01 and untrusted content)

- Generated files, diffs, LLM-produced messages and tool messages are
  **untrusted text**. Render them only as React text children. Never use
  `dangerouslySetInnerHTML`, `innerHTML`, `eval` or markdown-to-HTML
  rendering for them.
- The API key is kept in `sessionStorage` only (never `localStorage`,
  cookies or the URL), is never logged, and is cleared on a 401.
- Downloads: fetch the ZIP with the API-key header and save it via a Blob
  URL; revoke the URL afterwards. Don't put the key in a link.

## Code rules

- Function components and hooks only. Keep components small; business logic
  lives in `src/lib/` as pure, unit-tested functions.
- Every interactive element is reachable by keyboard and has an accessible
  name; use real `<button>`, `<label>` and `<textarea>` elements.
- Loading, empty and error states exist for every screen.
- `npm run lint` (ESLint + TypeScript `--noEmit`) and `npm test` must pass
  before every commit; Playwright runs with `npm run test:e2e`.

## Review checklist

Before each commit that touches UI, check the changed components against
`references/web-interface-guidelines.md` (a pinned copy of Vercel's Web
Interface Guidelines) and fix any MUST violation. Project exceptions:

- Mobile layouts, safe areas, touch and iOS rules: out of scope (desktop
  tool), except "never disable zoom".
- Font preloading and CDN preconnect: not applicable (system fonts,
  offline).
- Hydration rules: not applicable (client-rendered SPA).
- Submit button: FR-UI-01 wins. It stays enabled until a run is submitted,
  then stays disabled until the run is terminal.
- "URL reflects state": applies to routes, the selected variant and the
  selected file; not to transient UI such as an open feedback field.
- Don't load anything from the internet at run time, including the
  guidelines themselves.

## Verifying your own work

When the dev server and backend are running, open each screen in a real
browser (the `playwright` skill, if installed) and compare it against the
matching mockup PDF in `docs/spec/images/`. Check the run-to-review flow at
least once by hand with the stub scenario. Report what you checked, and
attach screenshots if the phase prompt asks for them.
