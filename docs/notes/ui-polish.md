# UI polish list (Phase 9j, round 1)

Rule: what is already built wins, unless the wireframe (thesis mockups
screen1–4) is clearly better. Every change keeps working behaviour,
accessibility (keyboard, visible focus, colour **and** text label) and the
existing tests. Items marked **[investigate]** need a root cause first.

## 0. Bugs to investigate first

- **[investigate] Recent runs hangs forever on "Loading saved preferences…".**
  Find the cause (no runs for this user? preferences request never resolves?
  error swallowed?). Fix it. If the list is genuinely empty, show a clear
  empty state: "No runs yet — start one from New request" with a button.
  Any load error must show a message with a Retry button, never an endless
  spinner.
- **[investigate] Architect "Use default" shows google/gemini-3.8-flash:batch**
  although the configured default is openai/gpt-oss-120b:nitro. Determine
  whether an administrator or personal default was saved during testing, or
  whether default resolution picks the wrong entry (e.g. first catalogue
  item). Report which. If it is a bug, fix it; the label must always show the
  model that would really be used.

## A. Visual foundation (from the wireframe)

- Colour tokens on `:root`, matching the wireframe: page `#0f1117`,
  panel/nav `#161b22`, code/diff bg `#0d1117`, border `#30363d`, text
  `#e6e6e6`, muted `#8b949e`, faint `#484f58`, accent orange `#ff9900`, blue
  `#58a6ff`, green `#3fb950`, red `#f85149`; state fills green `#0d4a2e`, blue
  `#1a3a5c`, gray `#21262d`, orange `#3d2200`, red `#4a0d0d`; diff removed
  `#2d0d0d`, added `#0d2d1a`. Replace hard-coded colours.
- Fonts: Space Grotesk (UI 400/500/600/700) and JetBrains Mono (code, logs,
  file trees, run IDs), self-hosted via `@fontsource/space-grotesk` and
  `@fontsource/jetbrains-mono` (author-authorised), no CDN at runtime.
- Icons: Codicons (CC BY 4.0) via `@vscode/codicons` (author-authorised) or
  inline SVG components generated from it, attribution in the repo. Used:
  circuit-board, gear, account, chevron-down, chevron-up, zap, check, loading,
  history, terminal, watch, credit-card, dashboard, shield, folder, file,
  cloud-download, arrow-left, search, sign-out, key, person-add, trash/lock as
  needed. No icon without a working feature (no bell).
- Logo: replace the current square mark with the orange circuit-board icon +
  "InfraArch" (orange) "Agent" (text colour).
- One spacing scale (4/8/12/16/24/32) and one form-field style everywhere;
  consistent card style (surface, 1px border, radius 8px).

## B. Header, navigation, login, logout

- Before login: header shows the logo only (no nav links, no pop-up).
- After login: nav items New request (zap), Recent runs (history), Settings
  (gear) as real nav entries — no underline, hover state, active page
  highlighted with the accent. Right side: account menu (account icon +
  username + chevron-down) containing Account and **Log out** (sign-out icon).
- Remove the standalone "Log out" button from page bodies on every page; Log
  out lives only in the account menu.
- Login card centred horizontally and vertically, ~400px wide, title + one
  subtitle: "Sign in to generate and review secure infrastructure packages."
- Primary full-width accent "Log in" button; show-password toggle; Caps Lock
  warning; generic error "Username or password is incorrect"; footer hint
  "Forgot your password? Ask an administrator to reset it." No example
  credentials. First-run admin setup uses the same layout.

## C. New request (screen 1)

- Wireframe layout: large prompt area with example placeholder, clear primary
  "Generate" button, short explanation of the three variants with icons
  (credit-card cost, dashboard performance, shield security).
- "Configuration options" collapsed by default, with a one-line summary
  ("Defaults: openai/gpt-oss-120b:nitro · thinking low · strict").
- Inside it: remove the large vertical gaps between fields; use a compact
  two-column grid on wide screens, one column on narrow screens.
- "Use defaults" is a normal-size secondary button aligned with the form
  actions — never stretched to the height of the Advanced section (current
  layout bug when Advanced is open).
- Model fields are **searchable comboboxes**: typing filters the list (by id
  and name, case-insensitive), keyboard navigation (↑/↓/Enter/Esc), shows
  each option's capabilities (structured output, reasoning) and price.
- Every "Use default" shows the resolved model **and** thinking mode
  ("Use default — openai/gpt-oss-120b:nitro · low"), including the Generators
  group; compact text, not oversized.
- Thinking-mode control always visible (also for defaults); hidden only for
  models without reasoning support, with a short note why.
- Replace the error "Choose a structured-output model for Generators and
  Fixer." with an actionable message next to the affected field:
  "This model can't return the structured JSON the Generators and Fixer need.
  Pick a model marked 'structured output', or select Use default."
  Invalid choices are filtered or disabled with that explanation.
- "Secondary assessment" select: label as "Additional assessment
  (experimental)" with a one-line help text that strict always decides the
  label.
- "Max remediation iterations": show the actual server default as the
  placeholder ("Server default: 4").

## D. Progress and live log (screen 2)

- Stage cards per wireframe: status icon (check / loading spinner / watch),
  agent name 14/600, one-line muted message, badge + elapsed time (tabular
  numbers) on the right; Generators card expands to three variant rows.
- Live log: code background, mono 12px, muted timestamps, coloured level
  tag, auto-scroll that pauses when the user scrolls up, blinking cursor as a
  U+2588 glyph in the text flow (not a positioned rect).

## E. Variant comparison (screen 3)

- Three equal columns; selected column 2px accent border. Header: variant
  icon + name, readiness badge (checks_passed / engineer_approved /
  pending_review / rejected; colour + text), security summary (strict count;
  contextual counts secondary, labelled experimental).
- Subtitle = architectural properties derived from the plan/package (e.g.
  "Single-AZ · on-demand", "Multi-AZ · autoscaling", "Private subnets ·
  encryption"); never product names or "Free Tier"; never hard-coded.
- File tree in mono with folder/file icons; download button (cloud-download).
- One line at the top: labels reflect static checks only, not a deployment.

## F. Security-fix diff (screen 4)

- Diff pane on code background, mono 13px, muted line numbers, removed/added
  rows with `-`/`+` markers, `@@` hunk headers between hunks.
- Right panel: fix cards with severity badges (HIGH/CRITICAL red, MEDIUM
  orange); resolved vs unresolved differ in colour and label; back link with
  arrow-left.

## G. Settings

- Settings sub-navigation (Provider, Models, Users, Account) as proper tabs
  with icons (key, gear, person, account), active tab highlighted; no
  underlined text links.
- **Provider:** tidy two-part layout — "Add provider" card (provider select,
  label, key with show/hide, live test status as a coloured status line:
  valid / invalid / no credit, with what to do next) and "Saved credentials"
  as a list of cards (label, provider, •••• last4, "selected" badge, actions
  Test / Use / Revoke with a confirmation for Revoke). Allow saving a key
  without credit, with a clear warning.
- **Models:** same searchable comboboxes and default labels as in C; show
  "Declare model capabilities" only for the custom OpenAI-compatible
  provider; collapse "Advanced" and "Declare capabilities" by default;
  personal vs administrator defaults clearly separated with a short
  explanation of precedence.
- **Users:** a table (username, role badge, status badge, created, last
  login) with row actions (Reset password, Disable/Enable) — reset opens a
  small dialog with password + confirm and the 12-character rule; "Create
  reviewer" as a compact card or dialog with the same password rules and a
  role hint. No bullet-list layout.
- **Account:** tidy card with username, role, last login; "Change password"
  form (current, new, confirm, strength/length hint); UI preferences grouped.

## H. Committee demo details

- Readable at 1280×800 (projector); consistent spacing; empty states and
  errors that say what to do next; no endless spinners anywhere.
- Screenshots of every screen for the README and the thesis (replace the
  placeholders).

## Round 2

After this round the author tests again and adds a second list.
