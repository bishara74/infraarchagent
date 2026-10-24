# UI polish list (Phase 9j, round 3)

Same rules as rounds 1–2: built behaviour wins unless clearly worse; keep
accessibility (keyboard, focus, colour + text), security properties,
readiness labels, header/benchmark requests and tests unchanged.

## 1. Login redirect

- After a normal login (app opened at `/` or `/login`, or after an explicit
  Log out) always land on **New request**.
- Return to a previous route only when the user opened a specific deep link
  while signed out (e.g. a run URL), and only for that one navigation.
- Log out clears any remembered route; never restore the "last visited page"
  from saved preferences or localStorage.

## 2. Model catalogue and dropdowns

- Resolve OpenRouter routing suffixes (`:nitro`, `:floor` and other
  documented routing suffixes; **not** `:free`, which stays hidden) to the base
  model's catalogue entry for capabilities, price and context, while still
  sending the exact configured ID (e.g. `openai/gpt-oss-120b:nitro`). The
  Recommended entry, "tested" badge and thinking modes then work for the
  default model.
- Thinking field for inherited defaults shows the real effective value,
  e.g. "low (server default)", never "Provider default" when the server
  configures an effort.
- Replace "Capabilities for this inherited or saved model are unknown. Retry
  the catalogue to verify them." with: "We couldn't load details for this
  model. It will still run with the server's settings." plus a **Retry**
  button. Show it only when details genuinely cannot be loaded.
- Hide moving aliases (IDs starting with `~` or ending in `-latest`) by
  default in both views; if shown via "all compatible", label them
  "alias — changes over time" and prefer pinned IDs.
- Compact option rows (less vertical padding) so more models fit on screen,
  keeping name, ID, capability badges, price and context readable.

## 3. Review

- Review tab for `checks_passed` packages: show "No review needed — this
  package passed all automatic checks." and offer **Reject** (with the
  required reason) for engineering judgement. Approve stays unavailable for
  `checks_passed`. A rejected package keeps its check results visible; the
  archive records the reason.
- Approve/Reject require a **reason category** from a fixed list
  (requirements not met, too expensive, organisational policy, security
  concern, operability, too complex, other) plus the existing free-text
  reason. Store the category with the decision (API, events, archive).
- Admin-only **review history export** (CSV and JSON): run ID, variant,
  label before/after, decision, category, reason text, reviewer, timestamp.
  No secrets, no package contents. Free-text reasons are never sent to any
  LLM in this phase.

## 4. Finish

- Update screenshots under `docs/evals/phase9j-ui/round3/`.
- Vitest + Playwright for each item; API tests for categories and export
  (admin-only, no hashes/secrets).
