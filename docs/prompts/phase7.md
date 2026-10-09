# Codex task — Phase 7: Results, download and review API

You are starting a **fresh session**. First read:
- `AGENTS.md`;
- `docs/design-deviations.md`, especially D-06 (Option C), D-33 to D-35 and
  OQ-09;
- `docs/IMPLEMENTATION_LOG.md`, especially the Phase 4, 5, 5b, 6 and 6b
  entries;
- the spec in `docs/spec/`: the REST API list in Chapter 4 (§ API design),
  FR-S-07 to FR-S-10, FR-UI-06, FR-UI-07, PR-04, NFR-01, UC-08, the
  security section of Chapter 4, and the package state diagram.

Phases 0–6b are complete. This task is **Phase 7 only**. It is the last
backend phase; the frontend (Phase 8) will be built on exactly this API.

## Goal

Add the three remaining endpoints from Chapter 4 and the services behind
them:

1. `GET /api/pipeline/{run_id}/results`: everything the frontend needs
   after a run, in one JSON response.
2. `POST /api/pipeline/{run_id}/packages/{variant}/review`: the engineer's
   decision on a `pending_review` package: approve, retry or reject
   (FR-S-08, FR-S-09, FR-S-10, UC-08).
3. `GET /api/pipeline/{run_id}/download/{variant}`: a ZIP of a labelled
   package (FR-UI-06, PR-04).

Plus an optional static API key (Chapter 4 security section), and two
small Phase 6 follow-ups (section 0).

The existing pieces you build on (do not rewrite them):
- `SecurityAgent.remediate_from_review(ctx, variant, package, feedback,
  validation_failures)`, which already resets the iteration counter and puts
  feedback and failed validation checks into the fix prompt;
- `ValidatorAgent` and `ValidationEngine`;
- `PipelineStateWriter`, `EventLog.append()`, the package state machine in
  `app/domain/states.py`, and `PipelineRunner`'s bounded task ownership;
- the SSE stream, which already stays open while a package is in
  `scanning`, `remediating` or `validating`;
- the `review_feedback` column, which already exists;
- `make sweep` / `app.cli sweep-packages`, the 30-day package retention
  sweep, which **already exists**. Do not rebuild it; only check that the
  README documents it.

## Rules

- No installs, upgrades or downloads. No real LLM calls (use the stub
  adapter and stub fixers in tests). Do not read `.env`. Do not push.
- Commit after each numbered section, prefixed `phase7:`, with the
  requirement IDs, and add an implementation-log entry per commit.
- Every state change goes through the existing state rules and
  `PipelineStateWriter`; every event goes through `EventLog.append()`.
- The run's own status is **frozen** once set (Chapter 4: it records what
  the automated pipeline achieved). Review actions never change the run
  status.
- No response, event, log line, ZIP entry or error message may contain an
  API key, a raw tool output, an absolute server path or a stack trace
  (NFR-01). Extend the existing canary tests to the new endpoints.
- Error responses keep the existing shape: `{"error": <code>, "message":
  <text>}`.

## Decisions already made by the author (do not revisit)

1. **API key (D-36).**
   - New setting `API_KEY`, unset by default. When unset, the API is open
     (local development, as now), and startup logs one warning saying so.
   - When set, every `/api/pipeline/...` endpoint, **including the SSE
     stream**, requires the header `X-API-Key: <key>`. `/api/health` stays
     open.
   - Compare with `hmac.compare_digest`. A missing or wrong key returns 401
     `{"error": "unauthorized", ...}`, and never says which part was wrong.
   - **No query-parameter fallback**, because URLs end up in logs and
     browser history. The browser's built-in `EventSource` cannot send
     headers, so Phase 8 will use a fetch-based SSE client. Record this in
     D-36, so the Phase 8 roadmap item "`useRunStream` around
     `EventSource`" becomes "around a fetch-based SSE client".
   - Add `API_KEY=` (empty) to `.env.example`, with a comment.
2. **OQ-09 is resolved by explicit targets (D-37).**
   - The review body gains an optional field `target_files`: a list of up
     to 5 package-relative file paths, each of which must exist in the
     package.
   - The retry's fix targets are, in order: the remaining blocking
     findings, the file-linked failed validation checks, and the
     `target_files`. Deduplicate per file, so there is still at most one
     fix call per file per pass.
   - A retry that has feedback but would have **no target at all** (no
     blocking findings, no file-linked failures, no `target_files`) is
     refused **before any state change** with 422
     `{"error": "feedback_needs_target", ...}`. The UI will then ask the
     engineer to pick files. Without feedback and without any target, a
     retry is also refused with 422 `nothing_to_retry`.
   - Mark OQ-09 resolved, pointing to D-37.
3. **A review retry that cannot finish returns to review (D-38).**
   - During a review retry, if scanning fails after its one automatic
     retry, or the validator cannot run, the package goes back to
     `pending_review` with the reason recorded. It must not become the
     terminal `scan_error`, because the engineer still has a package to
     decide on.
   - At startup, a package left in `remediating`, `scanning` or
     `validating` by a **review retry** that a restart interrupted goes back
     to `pending_review`, with the reason "review retry interrupted by
     server restart". Extend the existing startup recovery in
     `app/main.py`; do not touch how interrupted runs are recovered.
   - Implement both as explicit, narrowly named transitions in
     `app/domain/states.py`, allowed only for review retries (for example
     a `review_retry_aborted` path). Do not loosen the automated pipeline's
     transitions. Add a "thesis text to update" note: the package state
     diagram needs these two arrows.
   - Use the event history to tell whether a package is inside a review
     retry, or add a narrow marker if that is not reliable. Explain which
     in the plan. A migration is acceptable only if really needed.
4. **Retries share the pipeline capacity.**
   - A retry reserves a slot from `PipelineRunner` exactly like a new run.
     If no slot is free, return 429 `too_many_runs`, with no state change.
   - The retry task is owned by the runner, so shutdown cancels it like a
     run, and the D-38 startup recovery handles the rest.

## 0. Phase 6 review follow-ups

- **Helm templates without a namespace.** A Helm template resource with a
  literal `kind` and `name` but **no** `metadata.namespace` deploys into the
  release namespace. Treat it like a templated namespace: a reference that
  would only resolve to it becomes a **warning**, not a failure. Add tests
  for both the warning case and a genuinely missing Service that still
  fails.
- **Raw manifest versus Helm template with the same key.** Add a test that
  fixes which declaration wins when a raw `k8s/` manifest and a Helm
  template declare the same `(namespace, kind, name)`. The raw manifest
  must win, and its literal ports must be checked normally.
- Run `ruff format` on `backend/scripts/run_pipeline.py` (pre-existing
  formatting noted in Phase 6b).

## 1. Results endpoint (`GET /api/pipeline/{run_id}/results`)

- 400 for a malformed run ID, 404 for an unknown run, 200 otherwise, also
  while the run is still in progress (it returns the current snapshot).
- **One** database round trip for the run and its packages (a join or a
  single eager-loading query). Add a test that counts the statements.
- Response, as a Pydantic response model (strict, documented in the
  OpenAPI schema):
  - `run`: id, status, input text, start and end time, provider, model,
    max iterations, error message;
  - `plan`: the architect's deployment plan if it is persisted. If it only
    lives in an event payload, take it from there; if neither exists,
    `null`. Say in the plan which applies; don't add a column unless
    needed;
  - `packages`: one entry per variant that exists, in the order cost,
    performance, security, each with:
    - `variant`, `status`, `iteration_count`, `error`;
    - `files` and `original_files` (path → content), so the frontend can
      build the file tree and the diff itself;
    - `security_report` and `validation_report`, as persisted;
    - `review_feedback`;
    - derived fields, computed in **one** domain function and tested
      separately:
      - `readiness_label`: `production_ready`, `not_production_ready` or
        `null`;
      - `downloadable`: true only for the two labels;
      - `review_available`: true only in `pending_review`;
      - `review_reasons`: why it is under review, from this list:
        `unresolved_security_findings`, `validation_failed`,
        `validation_error`, `retry_aborted`;
      - `retry_targets`: the files a retry would target right now
        (blocking findings plus file-linked failed checks), so the UI can
        decide whether to ask for `target_files`;
  - `missing_variants`: variants that failed to generate, with their safe
    error message.
- No raw tool output, prompts or LLM responses beyond what the reports
  already store.

## 2. Review endpoint (`POST .../packages/{variant}/review`)

- Body (strict, unknown fields → 400):
  `{"action": "approve" | "retry" | "reject", "feedback"?: string,
  "target_files"?: [string]}`.
  - `feedback`: at most 2,000 characters after trimming. An empty string
    counts as absent. Store it in `review_feedback` on retry and reject.
  - `target_files` is allowed only with `retry`.
- Status codes:
  - 400: malformed run ID, unknown variant name or bad body;
  - 404: unknown run, or a variant that was never generated;
  - 409 `not_pending_review`: the package is not in `pending_review`;
  - 422: `feedback_needs_target` or `nothing_to_retry` (decision 2);
  - 429: `too_many_runs` (decision 4).
- **Approve (FR-S-08):** `pending_review → production_ready` with **no**
  scan, fix or validation call. Returns 200 with the new package status.
  The event records the review reasons at the time of approval.
- **Reject (FR-S-10):** `pending_review → not_production_ready`. 200. The
  package stays downloadable, with the rejection labelled (section 3).
- **Retry (FR-S-09):** returns **202** with `stream_url`, and then in the
  background:
  1. `pending_review → remediating`, iteration counter reset (the
     existing `remediate_from_review`);
  2. the fix loop with feedback, failed validation checks and
     `target_files` as targets (decision 2);
  3. rescan, then the existing ValidatorAgent on the persisted remediated
     files;
  4. the existing Option C rule: clean scan and `valid` →
     `production_ready`; anything else → `pending_review` again;
  5. scan failure, validator failure or interruption → `pending_review`
     (decision 3).
- **Concurrency:** read and change the package under a row lock in one
  transaction, so two simultaneous review requests on the same package
  give exactly one success and one 409. Add a test with two concurrent
  requests for each action.
- The SSE stream must show the whole retry, and close again once no
  package is active. Add an integration test that connects after a retry
  starts and sees it through to the final package state.

## 3. Download endpoint (`GET .../download/{variant}`)

- 400 malformed ID or unknown variant name; 404 unknown run or a variant
  that was never generated; 409 `not_downloadable` for any status other
  than `production_ready` or `not_production_ready` (this includes
  `pending_review` and packages still being worked on).
- Builds the ZIP in memory from the persisted (remediated) `files`:
  - entries sorted by path, with a fixed timestamp, so the same package
    always gives a byte-identical archive (test it);
  - every entry path checked with the existing `validate_relative_path`;
  - plus a readiness file at `INFRAARCHAGENT_READINESS.md` at the archive
    root. If the package already has a file with that name, put it at
    `_infraarchagent/READINESS.md` instead. It contains:
    - the label, in capitals, at the top. A rejected package says **NOT
      PRODUCTION READY — rejected by the reviewing engineer**;
    - the run ID, variant, model and download time;
    - whether the label was automatic (clean scan and valid) or an
      engineer decision, and the review feedback if any;
    - a short security summary (scan outcome, remaining blocking findings
      count) and validation summary (result and counts);
    - the Aurora-style caveat from D-35: static validity does not prove
      deployability.
- `Content-Type: application/zip`, and `Content-Disposition` with the file
  name `infraarch-<first 8 chars of run id>-<variant>-<label>.zip`.
- **PR-04:** a test that downloads a generated 10 MB package in under
  2 seconds through the ASGI test client, and records the measured time in
  the implementation log. (The final curl-based measurement happens in
  Phase 9.)
- `IaCPackage` gets a `to_zip()` method (as in the class diagram), or a
  domain function next to it; the endpoint only calls it.

## 4. API key

Implement decision 1 as one FastAPI dependency applied to the pipeline
router. Tests:
- no key configured: everything works as before;
- key configured: every pipeline endpoint, including the stream, returns
  401 without the header or with a wrong one, and works with the right
  one; health works without it;
- the key never appears in any response, event or log (canary).

## 5. Tests and acceptance

Use requirement markers as before. Required coverage:

| Area | Tests |
|---|---|
| FR-S-08 | approve: `production_ready`, and no SecurityAgent or validator call (spy) |
| FR-S-09 | retry with feedback: the stub fixer's prompt contains the feedback and the failed validation checks, consumed iterations is zero, then clean rescan and `valid` → `production_ready`; a retry that is still invalid → `pending_review` again |
| FR-S-09 / D-37 | feedback-only retry: with `target_files` it targets those files; without targets → 422 and no state change; an unknown `target_files` path → 400 |
| FR-S-10 | reject: `not_production_ready`, downloadable, label in the ZIP and the file name |
| FR-UI-06 | download 200 for both labels; 409 for `pending_review` and an active state; 404 for a failed variant; ZIP file tree equals `files` plus the readiness file |
| D-38 | scan failure during a retry → `pending_review`; startup recovery of an interrupted retry → `pending_review`; an interrupted **automated** run is still recovered exactly as before |
| Run status | approve, reject and retry never change the run status |
| Concurrency | double approve, approve and reject at once, double retry: one success, one 409 |
| Capacity | a retry when the runner is full → 429, no state change |
| Results | one query; derived fields for every package status; missing variants |
| NFR-01 | canary key absent from results, review responses, events, logs and the ZIP |
| PR-04 | 10 MB package downloads in under 2 s |

Finish with `make lint` and `make test` and report the real counts.

## 6. Documentation

- **D-36** (API key and fetch-based SSE), **D-37** (OQ-09 retry targets),
  **D-38** (review retries return to review). Mark OQ-09 resolved.
- **"Thesis text to update", add:**
  - the review body's `target_files` field, and the two 422 codes;
  - the two new package state arrows (retry aborted → `pending_review`);
  - the `X-API-Key` header and the open-when-unset rule;
  - the readiness file in the downloaded ZIP.
- **README:** the three endpoints with one `curl` example each (results,
  review approve and retry, download), the `API_KEY` setting, and the
  existing `make sweep` command.
- **Implementation log:** an entry per commit, with real test counts and
  the measured PR-04 time.

## 7. Out of scope

- Frontend (Phase 8).
- Changes to the security policy, the fix prompts beyond adding
  `target_files` as targets, or the validator's checks (except section 0).
- User accounts or per-user sessions (the design uses one static key).
- Any change to how the run status is classified.

Finish with the summary format from `AGENTS.md` §10, and state explicitly:
- the exact JSON shape of the results response (field list);
- the measured PR-04 download time;
- how an interrupted review retry is detected at startup;
- the test counts.
