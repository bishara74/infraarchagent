# UI polish list (Phase 9j, round 2)

Same rules as round 1: built behaviour wins unless clearly worse; keep
accessibility (keyboard, focus, colour + text), security properties and tests.

## 0. Bug sweep first (Codex)

- Walk every screen and dialog with Playwright against the stub provider
  (login, setup, new request, configuration options, live view, results,
  diff, review, recent runs, all settings tabs, account menu) at 1280×800 and
  1920×1080. Collect browser console errors/warnings, failed network
  requests, unhandled promise rejections, layout overflow/clipping, elements
  outside the viewport, focus traps, and endless loading states. Report every
  finding with screen, cause and fix; fix them in this phase.

## 1. New request — no prefilled prompt

- After login the prompt box starts **empty**. Do not auto-restore the saved
  draft into the textarea.
- If a saved draft exists, show a small, dismissible line under the box:
  "You have an unsent draft from <time> — Restore · Discard". Restore fills
  the box; Discard deletes the server draft. Example prompts stay as clickable
  suggestions only, never inserted automatically.

## 2. Model dropdowns — bugs

- **[bug]** Comboboxes sometimes list only "Use default" and show
  "Model capabilities unavailable. Refresh the catalogue" although a provider
  credential is selected. Find why the catalogue is missing (not loaded, load
  error swallowed, race with preferences hydration, cache key) and fix it.
  If it genuinely cannot load, show why (no provider selected / no credit /
  network error) with a Retry button.
- **[bug]** False error "This model can't return the structured JSON…" is
  shown under "Use default — openai/gpt-oss-120b:nitro" when capabilities are
  unknown. Unknown capability must never be shown as incompatible; the
  environment default is the known-good benchmark configuration.
- **[bug]** "This saved model is unavailable" appears under a "Use default"
  selection. Only show it when an explicitly saved model is missing from the
  catalogue, and say which model and what to do.
- **[bug]** The open dropdown panel is a huge empty area with one item at
  the top. The panel height must fit its content (max height with scroll),
  never fill the screen.

## 3. Model dropdowns — only relevant, usable models

- Every role (Architect, Generators, Fixer) requires structured JSON output,
  so the lists show **only models with structured-output support** for the
  selected provider. Incompatible models never appear.
- Default view "Recommended": a short, documented allowlist of models tested
  with this system (at least openai/gpt-oss-120b:nitro; others only if they
  support structured output and are in the catalogue), each with price and
  "tested" badge.
- A toggle "Show all compatible models" reveals the remaining
  structured-output models, still searchable, sorted by provider and name.
- Hide `:free` variants by default (rate-limited, unreliable for the
  pipeline); hide deprecated/expired models; show the price per million
  tokens and context length on each option.
- The allowlist lives in a versioned config file (not hard-coded in
  components) and is documented in D-58.

## 4. Diff view — formatting-only changes

- Add a "Hide whitespace-only changes" toggle (default on), like GitHub's
  `?w=1`: lines whose only difference is whitespace/alignment (e.g. from
  `terraform fmt`) are shown as unchanged context. The toggle is remembered
  per user (server-side preferences, localStorage cache).
- When a hunk contains only whitespace changes, label it
  "Formatting only (terraform fmt)" instead of showing red/green rows.
- Show a small count above the diff: "N changed lines · M formatting-only
  lines hidden", so reviewers see that nothing was silently dropped.
- The underlying diff, downloads and archive stay byte-exact; only the
  presentation changes.

## 5. Results — overview first, details on demand

- Keep variant selection (review and approval are per variant), but make the
  results page start with a **comparison overview**: three cards side by side
  with readiness label, blocking-finding count (strict; contextual secondary),
  validation status, architectural properties, key trade-offs and estimated
  cost where available. Selecting a card means "inspect this one", with a
  short hint explaining that review/approval apply to the selected variant.
- Files and security-fix diff move into tabs/expandable sections of the
  selected variant ("Files", "Security fixes", "Findings", "Review"), not
  shown by default.
- Downloads available from the overview: "Download all three" (one ZIP with
  the three packages and their readiness documents) and "Download this
  variant" on each card; existing download rules and archive contents
  unchanged.
- Approve/Reject (with the existing name/reason rules) on the selected
  variant's card or Review tab.
