# Design System — InfraArchAgent

The direction is **decided**. It comes from the thesis (Chapter 4, "UI
design") and the four mockups in `docs/spec/images/screen1_input.pdf` to
`screen4_diff.pdf`. Apply it; do not explore or propose a new direction,
palette, typeface or "signature". If something here is missing, extend it in
the same spirit and record the decision in the table at the end.

## Direction

**Who:** a DevOps or platform engineer at a desk, checking whether generated
Terraform/Kubernetes/Helm packages are safe to use. They read code and logs
all day, in tools like the AWS Console and GitHub.

**Task:** submit a request, watch the pipeline, compare three variants, read
the security fixes and validation report, then approve, retry, reject or
download.

**Feel:** a calm, dense engineering console. Dark, quiet structure; colour
only where it carries meaning (status, diff, the one primary action).

**Personality:** Utility & Function, Data & Analysis.
**Foundation:** cool, blue-tinted dark neutrals.
**Depth:** borders-only. Dark UI, shadows add nothing here.

## Tokens (sampled from the mockups)

### Colours
```
--bg:              #0f1117   /* page */
--bg-code:         #0d1117   /* code and diff panes */
--surface:         #161b22   /* cards, panels */
--surface-raised:  #21262d   /* nested blocks, hover */
--border:          #30363d
--text:            #e6e6e6
--text-muted:      #8b949e
--text-faint:      #484f58   /* nonessential decoration only */
--accent:          #ff9900   /* primary action, selected variant, active tab */
--ok:              #3fb950   --ok-bg:      #0d4a2e
--running:         #58a6ff   --running-bg: #1a3a5c
--queued:          #8b949e   --queued-bg:  #21262d
--warn:            #ff9900   --warn-bg:    #3d2200   /* MEDIUM, warnings */
--danger:          #f85149   --danger-bg:  #4a0d0d   /* HIGH/CRITICAL, failed */
--diff-add-bg:     #0d2d1a
--diff-del-bg:     #2d0d0d
```
One accent (orange). Status colours are semantic only, never decoration.

### Typography
- UI: locally bundled Space Grotesk (400/500/600/700), with system sans fallback.
  Code/logs/paths/run IDs: locally bundled JetBrains Mono (400/500), with system
  mono fallback. Fontsource packages are OFL-1.1; no runtime CDN or network.
- Icons: Codicons (CC BY 4.0), decorative beside text or accessible control names;
  attribution is in frontend/THIRD_PARTY_NOTICES.md.
- Scale (ratio ~1.2, base 14px): 12, 14 (base), 16, 20, 24.
- Weights: 400, 500, 600. Hierarchy through weight and `--text`/`--text-muted`
  first, size second.
- `font-variant-numeric: tabular-nums` on elapsed times, counts and scores.

### Spacing and shape
- Base 4px; scale 4, 8, 12, 16, 24, 32.
- Dense: card padding 12–16px, row height ~32px.
- Radius: 4px (badges, inputs), 6px (buttons), 8px (cards, panels). Nested
  radii stay concentric.

## Patterns

Model controls show the effective model/thinking source in muted 12px text:
“from this run”, “from your defaults”, “from administrator defaults”, or “server
default”. Mixed generator sources are shown per variant, with wrapping instead
of page overflow. Settings previews name the tier being edited. Resolution uses
tier order before per-generator specificity; changing one role never changes
another role's inherited baseline.

### Primary button (Generate, Download ZIP)
- Height 36px, padding 8px 16px, radius 6px, 14px/600.
- Background `--accent`, text `#0f1117`. One per screen.

### Status badge
- Pill, radius 4px, 12px/500, padding 2px 8px.
- Text + background pairs: complete `--ok`/`--ok-bg`, running
  `--running`/`--running-bg`, queued `--queued`/`--queued-bg`, failed
  `--danger`/`--danger-bg`. Always a text label, never colour alone.

### Stage card (screen 2)
- `--surface`, 1px `--border`, radius 8px, padding 12px 16px.
- Left: status icon; then agent name (14/600) and one-line message
  (14/400 muted); right: badge and elapsed time (tabular).
- The Generators card expands to three horizontal variant status blocks on the
  desktop grid, as in the mockup; each keeps a text badge and event sequence.
- Elapsed stage activity is the union of real timestamp intervals across variants
  and retries; concurrent activity counts once and review gaps add no time.

### Variant column (screen 3)
- `--surface`, 1px `--border`; selected: 2px `--accent` border.
- Header: variant name, readiness label badge, security summary; body: readiness, strict/contextual counts, validation and factual planned
  properties. Files live in the selected variant inspection tabs. Secondary check details collapse by default so file/actions fit
  the 1280×800 projector view; all original counts remain available.

### Diff view (screen 4)
- Pane `--bg-code`, mono 13px, line numbers muted.
- Removed lines `--diff-del-bg` with a `-` marker; added lines
  `--diff-add-bg` with a `+` marker; hunk headers muted.
- Right panel: fix list cards with severity badges (HIGH/CRITICAL danger,
  MEDIUM warn); resolved vs unresolved differ in colour **and** label.

### Live log (screen 2)
- `--bg-code`, mono 12px, timestamp muted, level tag coloured, auto-scroll
  that pauses when the user scrolls up. The visible viewport is
  `clamp(144px, 16vh, 240px)` so stages and the log fit at 1440×900.

## Decisions

| Decision | Rationale | Date |
|---|---|---|
| Direction fixed by thesis mockups | The UI must match Chapter 4 figures | 2026-10-12 |
| Borders-only depth | Dense dark engineering tool; shadows add no information | 2026-10-12 |
| Locally bundled fonts and Codicons | Phase 9j author-approved wireframe polish, offline at runtime | 2026-10-22 |
| Single orange accent | Mockups use orange for the one primary action and selection | 2026-10-12 |
| Desktop-first (≥1024px) | Single-user local tool; mobile out of scope | 2026-10-12 |

## Phase 9j shared controls

- Model controls use a two-column grid on wide screens and a single column below
  800px. The searchable list virtualises at most 16 rows of 80px, with total/
  position metadata for assistive technology. Search covers ID and name; invalid
  options have an explanation and cannot be selected. Defaults show model and
  effective thinking; provider-default thinking is distinct from low/off.
- Request configuration starts collapsed; its summary identifies mixed per-role
  settings rather than implying every role uses Architect's model. Use defaults
  stays in the form action row and retains the standard 36px button height.
- Header navigation is available only after authentication or explicit local-mode
  entry. Account is a keyboard-operated menu; user management remains admin-only.
  Account names truncate visually while preserving their full accessible name.
- User/reset/revoke dialogs use native modal behaviour and return focus to their
  trigger after asynchronous actions complete. Credentials/passwords remain
  temporary form state and never enter preference storage.

## Phase 9j round 2 patterns

- Results begin with three compact overview cards; Inspect this variant opens
  URL-addressable Files, Security fixes, Findings and Review tabs. Reviews remain
  per variant. No file trees or diff panels compete with the initial comparison.
- Drafts are explicit recovery hints under an empty new editor; Restore, Discard
  and Dismiss are text controls, preserving account-scoped persistence.
- Model catalogues default to versioned, provider-verified recommendations. A
  shared all-compatible switch never includes unsupported, free or retired models.
  Options show catalogue input/output price and context; a tested badge denotes
  recommendation membership, never inferred capability. Virtual 80px rows use
  internal spacers inside a maximum 280px scroll viewport; short lists fit content.
- Diff presentation defaults to hiding whitespace-only changes, with neutral
  formatting labels and explicit meaningful/formatting line counts. Source and
  archive bytes are unchanged. The setting follows the account.

## Phase 9j round 3 review patterns

- Checks-passed review retains its green readiness badge and download, adds the
  exact no-review-needed message and offers rejection with a required category
  and reason. Approve/retry remain unavailable; focus returns to invalid fields.
- Administrators have a separate Review history Settings tab: a compact table,
  category/decision/UTC-date filters, 25-row pages and an explicit count/filter
  summary beside CSV/JSON exports. Status columns do not split label text.
  Historical missing categories are shown as “not recorded”.
