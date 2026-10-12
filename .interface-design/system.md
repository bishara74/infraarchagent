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
--text:            #e6edf3
--text-muted:      #8b949e
--accent:          #ff9900   /* primary action, selected variant, active tab */
--ok:              #3fb950   --ok-bg:      #0d4a2e
--running:         #58a6ff   --running-bg: #1a3a5c
--queued:          #8b949e   --queued-bg:  #21262d
--warn:            #d29922   --warn-bg:    #3d2200   /* MEDIUM, warnings */
--danger:          #f85149   --danger-bg:  #4a0d0d   /* HIGH/CRITICAL, failed */
--diff-add-bg:     #0d2d1a
--diff-del-bg:     #2d0d0d
```
One accent (orange). Status colours are semantic only, never decoration.

### Typography
- UI: system sans stack (`system-ui, -apple-system, "Segoe UI", Roboto,
  sans-serif`). Code, diffs, file paths, run IDs, rule IDs and the live log:
  system mono stack (`ui-monospace, SFMono-Regular, Menlo, Consolas,
  monospace`). **No web fonts**: the app must work offline. This is a
  deliberate project decision, not a default.
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
- The Generators card expands to three variant sub-rows.

### Variant column (screen 3)
- `--surface`, 1px `--border`; selected: 2px `--accent` border.
- Header: variant name, readiness label badge, security summary; body: file
  tree in mono.

### Diff view (screen 4)
- Pane `--bg-code`, mono 13px, line numbers muted.
- Removed lines `--diff-del-bg` with a `-` marker; added lines
  `--diff-add-bg` with a `+` marker; hunk headers muted.
- Right panel: fix list cards with severity badges (HIGH/CRITICAL danger,
  MEDIUM warn); resolved vs unresolved differ in colour **and** label.

### Live log (screen 2)
- `--bg-code`, mono 12px, timestamp muted, level tag coloured, auto-scroll
  that pauses when the user scrolls up.

## Decisions

| Decision | Rationale | Date |
|---|---|---|
| Direction fixed by thesis mockups | The UI must match Chapter 4 figures | 2026-10-12 |
| Borders-only depth | Dense dark engineering tool; shadows add no information | 2026-10-12 |
| System fonts only | Offline local deployment; no font downloads | 2026-10-12 |
| Single orange accent | Mockups use orange for the one primary action and selection | 2026-10-12 |
| Desktop-first (≥1024px) | Single-user local tool; mobile out of scope | 2026-10-12 |
