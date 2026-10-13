# Codex task — Phase 8c: UI polish from the author's manual review

Fresh session. Read `AGENTS.md`, `.agents/skills/infraarch-frontend/SKILL.md`,
`.interface-design/system.md`, and the latest entries of
`docs/IMPLEMENTATION_LOG.md`. Phase 8 and 8b are complete and accepted.
This is a **small polish pass**: no new features, no new dependencies, no
schema or endpoint changes.

## Rules

- No installs, no real LLM calls, do not read `.env`, do not push.
- One commit per item below, prefixed `phase8c:`, each with an
  implementation-log entry.
- Keep all existing tests passing; add or adjust tests for every change.

## Items

1. **Validator stage card hides failures.** On the progress screen, the
   ValidatorAgent card shows the message of whichever variant finished
   last (e.g. "validation valid") even when another variant is invalid.
   When the stage aggregates several variants, show a summary built from
   the per-variant outcomes, e.g. "2 valid · 1 invalid" (and include
   "error" when present). Apply the same rule to the SecurityAgent card
   (e.g. "2 clean · 1 exhausted"). Use real event data only. Test with a
   mixed-outcome event sequence.

2. **Readiness label origin after a retry.** The downloaded
   `INFRAARCHAGENT_READINESS.md` says "Label origin: automatic (clean scan
   and valid validation)" for a package that reached `production_ready`
   only after an engineer-requested retry. Distinguish three origins:
   automatic (no review), automatic after an engineer-requested retry, and
   engineer decision (approve or reject). Derive it from the existing event
   history; no new database fields. Update the archive tests, and show the
   same origin text on screen 4 next to the label.

3. **Duplicate readiness badge on screen 4.** The "production ready" badge
   appears both in the page header and in the action panel. Keep one, in
   the action panel next to Download ZIP, and keep the header clean. Check
   the pending-review state still reads clearly.

4. **Blob URL revoked too early.** In `src/api/client.ts`, the download
   revokes the object URL synchronously right after `link.click()`. Some
   browsers (notably Firefox) can cancel the download when that happens.
   Revoke it after a short delay (e.g. `setTimeout(..., 1000)`), still
   guaranteed in a `finally`-style path, and update the unit test to assert
   the URL is eventually revoked.

5. **Reconnect tests should fail cleanly, not hang.** Removing the
   five-EOF reconnect cap (or the `seq` de-duplication, or the cursor
   advance) in `src/api/sse.ts` is currently detected only because the test
   worker loops until it is killed. Give these tests a bounded fake client
   (a fixed list of responses) and an explicit assertion on the number of
   `openStream` calls and the final state (`paused` / `closed`), plus a
   per-test timeout, so each of those mutations fails with a clear
   assertion message.

6. **Configurable backend port.** On the author's Windows machine, ports
   8000 and 8001 are taken by other Windows programs, so the browser
   reaches the wrong app. Add `PORT ?= 8000` to the Makefile and use it in
   `make run` (`--port $(PORT)`), keep the Vite proxy target configurable
   through an environment variable with 8000 as the default, and document
   `make run PORT=8765` in the README, including that the browser URL then
   changes. Don't change the e2e defaults.

7. **Stale text in `AGENTS.md` and the README.** `AGENTS.md` §1 still says
   "Checkov and tfsec" (tfsec was replaced by Trivy in Phase 5b), and §11
   says `make run` starts FastAPI "with reload" (it runs `--workers 1`
   without reload). Correct both, and fix any other README statement that
   contradicts the current commands. Historical eval reports stay as they
   are.

## Finish

Run `make lint`, `make test`, `make frontend-test` and `make test-e2e`, and
report the real counts. Summary in the `AGENTS.md` §10 format.
