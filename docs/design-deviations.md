# Design Deviations and Open Questions

Every place where the implementation differs from the thesis specification
(`docs/spec/`), and every unresolved ambiguity. This file feeds the
"Design deviations" section of thesis Chapter 5.

Status values:
- **In thesis:** the decision was made during design review and is now part
  of the thesis design (text and diagrams). No difference remains, but
  Chapter 5 may still describe it as a design refinement.
- **Accepted:** implemented; the thesis does not yet describe it.
- **Proposed:** awaiting the author's confirmation.
- **Superseded:** replaced by a later entry.

---

## Deviations

### D-01 — `agent_events.seq` ordering column (In thesis)
- **Spec:** `agent_events` has UUID `event_id` and `timestamp`; SSE replays
  history from the database.
- **Implementation:** add `seq BIGINT GENERATED ALWAYS AS IDENTITY (CACHE 1)`,
  unique, with an index on `(run_id, seq)`. `event_id` stays the primary key.
- **Reason:** UUIDs are not orderable and timestamps can tie. SSE reconnection
  (`Last-Event-ID`) needs a monotonic value to resume from.
- **Guarantee and its conditions:** An identity value is assigned at insert
  time, before commit, so on its own `seq` does not guarantee that commit
  order equals `seq` order. The guarantee holds because every writer goes
  through `EventLog.append()`, which takes
  `pg_advisory_xact_lock(<run id>)` before inserting and publishes to the
  in-memory broker only after commit. Per run, therefore, commit order equals
  `seq` order. Across runs, `seq` values interleave, so one run's `seq`
  values have gaps; nothing may assume they are consecutive.
- **Publish order:** `seq` order is guaranteed per `EventLog` instance, not
  merely by running in one process. The application constructs exactly one
  instance in `create_app()` and exposes it through one accessor; tests may
  construct additional instances to verify database ordering. In Phase 4,
  SSE subscribers will skip live events with `seq` at or below the last sent.
  Out-of-order publication from multiple app instances in one process could
  therefore silently drop an event for a subscriber.
- **In thesis:** ERD (`seq` column note) and sequence diagram (EventLog
  note).
- **Assumption:** single application process (the in-memory broker already
  requires it). The advisory lock keeps database ordering correct even with
  several writers; live publish ordering relies on using one `EventLog`
  instance in that process.
- **Implemented in Phase 0:** identity sequence with `CACHE 1`, advisory-lock
  append, ordered replay, and app-owned singleton access.

### D-02 — `TIMESTAMPTZ` instead of `TIMESTAMP` (In thesis)
- **Spec:** ERD uses `TIMESTAMP`.
- **Implementation:** all time columns are `TIMESTAMPTZ`; the application
  writes timezone-aware UTC values.
- **Reason:** unambiguous durations for PR-01 and the retention cutoff.
- **In thesis:** ERD.
- **Implemented in Phase 0:** application UTC timestamps and `TIMESTAMPTZ`
  columns.

### D-03 — Retention enforcement and foreign keys (In thesis)
- **Spec:** "Generated package data older than 30 days is eligible for
  deletion. `pipeline_runs` and `agent_events` rows are retained indefinitely
  for audit purposes."
- **Implementation:**
  - The retention sweep deletes only from `generated_packages`, by
    `created_at`, which is indexed. It never touches runs or events.
    **The retention policy is enforced by this sweep.**
  - Foreign keys from both child tables use `ON DELETE RESTRICT`. This is
    protection only: it blocks deleting a run that still has child rows, but
    a run with no events or packages could still be deleted by a privileged
    role, so RESTRICT alone does not guarantee retention.
  - Database-level prohibition: the application role `infraarch_app` has no
    DELETE privilege on `pipeline_runs` and no UPDATE or DELETE on
    `agent_events` (append-only audit log). See D-04.
- **In thesis:** ERD (RESTRICT on both relationships, `created_at` index
  note, retention note). Section 4.2 text still describes retention only as
  "eligible for deletion"; see the list at the end.
- **Implemented in Phase 0:** package-only sweep, retention index, RESTRICT
  foreign keys, and app-role prohibitions.

### D-04 — Two database roles (Accepted; privileges in thesis)
- **Spec:** not specified.
- **Implementation:** `infraarch_owner` owns the schema and runs migrations;
  `infraarch_app` is used at runtime with least-privilege grants:
  - `pipeline_runs`: SELECT, INSERT, UPDATE
  - `agent_events`: SELECT, INSERT
  - `generated_packages`: SELECT, INSERT, UPDATE, DELETE
- **Reason:** enforces D-03 in the database and limits damage from bugs.
- **In thesis:** the privilege consequences are noted on the ERD. The
  two-role setup itself (owner for migrations, app role at runtime) is an
  implementation detail for Chapter 5.
- **Implemented in Phase 0:** both roles, databases, and versioned table
  grants. App-role insertion into the identity column succeeded without
  sequence `USAGE`, so no sequence grant was added.

### D-05 — `files` JSONB shape and path validation (In thesis)
- **Spec:** `files JSONB`, `IaCPackage.files: dict`.
- **Implementation:** a map of relative POSIX path → file content. Paths are
  validated when an `IaCPackage` is constructed and again by the ZIP writer:
  relative only; no leading `/`, drive letters, backslashes, NUL bytes,
  `..`, `.` or empty segments; restricted character set; at most 255
  characters and 8 levels; no case-insensitive duplicates.
- **Reason:** prevents path traversal (e.g. `../`) when writing ZIPs or
  scanning files on disk.
- **In thesis:** class diagram (`IaCPackage.files: dict[str, str]` note).
- **Implemented in Phase 0:** path validation in `IaCPackage` and the package
  repository. The ZIP writer repeats validation in Phase 7.

### D-06 — Package outcomes after validation: Option C (In thesis)
- **Spec conflict (original):** the package state diagram showed
  `validation_error → production_ready` (unvalidated code labelled
  production-ready), while FR-UI-06, FR-V-05 and the run-state table treated
  `invalid` and `validation_error` as final, downloadable states. That let a
  package be delivered without an engineer decision, even with unresolved
  security violations. Both readings contradicted the human-in-the-loop
  principle (Section 3.1).
- **Decision (Option C):** a package becomes `production_ready`
  automatically only if its scan was clean AND validation passed. Every
  other outcome that produces a package (`scan_exhausted`, `invalid`,
  `validation_error`) goes to `pending_review`.
  - `invalid` and `validation_error` are intermediate states, recorded as
    events and shown as review reasons.
  - Final labels are only `production_ready` and `not_production_ready`, and
    only those are downloadable.
  - A retry's fix prompt includes the engineer's feedback and any failed
    validation checks (Phase 5).
- **Where in code:** `app/domain/states.py` (transition table,
  `readiness_after_validation`, `review_reasons`, `is_downloadable`).
- **In thesis:** text (FR-S-07, FR-S-09, FR-V-05, FR-UI-06, UC-08,
  run-state table, Chapter 4) and diagrams (package states, run states,
  sequence diagram 5/5a, class diagram `SecurityAgent.remediate`).
- **Implemented in Phase 0:** transition and readiness rules, review reasons,
  and downloadability predicate; agent and review flows follow later.

### D-07 — Async LLM template method and SDK transport (Accepted)
- **Spec:** the class diagram shows `LLMAdapter` with two provider methods;
  ADR-02 names `send_prompt` and `parse_response`.
- **Implementation:** `send_prompt` is async, `parse_response` is synchronous,
  and the concrete `complete_json` template method owns retry, timeout,
  backoff, and strict JSON handling. A new provider still implements only
  the two abstract methods (NFR-03).
- **Prompt correction:** Anthropic 1.8.0 and OpenAI 3.19.2 use `httpx2` for
  custom SDK clients. Provider tests therefore inject `httpx2.AsyncClient`
  with `httpx2.MockTransport`, rather than the prompt's `httpx` equivalents.
  Phase 0 FastAPI tests continue using `httpx` without global aliasing.
- **Reason:** the pipeline is asyncio-based and the installed SDK transport
  types reject or do not natively type-check with legacy `httpx` clients.
  The shared template keeps the retry policy out of provider classes.
- **Implemented in Phase 1:** adapter contract, shared wrapper, both real
  providers, stub, factory, and offline tests.

### D-08 — OpenAI-compatible base URL (Accepted)
- **Spec:** ADR-02 names Anthropic and OpenAI as the supported LLM APIs;
  endpoint configuration is not specified.
- **Implementation:** optional `LLM_BASE_URL` is passed by the factory only
  to `OpenAIAdapter`, which supplies it to `AsyncOpenAI` when set. The default
  remains the SDK's OpenAI endpoint. Compatible services use
  `LLM_PROVIDER=openai` and their own model and key; no provider class or
  enum value is added.
- **Reason:** an OpenAI-compatible Chat Completions endpoint can use the
  existing adapter contract and retry policy.
- **Implemented in Phase 1 follow-up:** setting, factory and SDK wiring,
  mocked request-URL tests, and a README Groq example.

### D-09 — Respect provider rate-limit retry delay (Accepted)
- **Spec:** LLM calls retry transient failures with exponential backoff;
  provider-directed rate-limit delays are not specified.
- **Implementation:** on HTTP 429, both adapters parse a finite,
  nonnegative `retry-after` value in seconds from the SDK response. The
  shared wrapper waits for the greater of this value and jittered backoff,
  within the remaining call deadline. A delay that leaves no time for another
  attempt raises `LLMDeadlineExceeded` without sleeping. Missing or invalid
  headers use ordinary backoff.
- **Reason:** retrying before the provider's stated limit expires wastes an
  attempt and can repeat the rate limit. Only the parsed number reaches the
  shared error; raw response headers are never logged.
- **Implemented in Phase 1 follow-up:** both SDK mappings, shared retry
  policy, and deterministic `httpx2.MockTransport` tests.

### D-10 — Strict deployment plan (Accepted)
- **Spec:** FR-A-01--03 require a structured plan, named IaC file types, and
  recorded ambiguities; the class diagram leaves field types open.
- **Implementation:** replace Phase 0's permissive placeholder with frozen
  Pydantic models that forbid extra fields. The AWS plan names services,
  dependencies, network, storage, file types, and ambiguities. It checks
  references, uniqueness, cycles, Terraform inclusion, and a 32,768-byte
  compact UTF-8 JSON limit. The previous `app.domain.models` import remains.
- **Reason:** generator input must be internally consistent and small enough
  for a later event payload; validation errors must be actionable for retry.
- **Implemented in Phase 2:** plan model, error collector, and offline tests.

### D-11 — Schema-derived ArchitectAgent correction prompt (Accepted)
- **Spec:** FR-A-01--04 require a JSON plan, ambiguity notes, and failure
  handling, but do not define prompt construction or correction feedback.
- **Implementation:** the versioned system prompt embeds the model's JSON
  schema and treats tagged user text as data. A failed plan attempt supplies
  numbered validation errors and at most 8,000 characters of prior output
  to the next attempt. Neither prompts nor responses are logged.
- **Reason:** the schema and prompt stay aligned, and a correction targets
  concrete plan defects without persisting untrusted text.
- **Implemented in Phase 2:** prompt builder and ArchitectAgent tests.
- **Evaluation follow-up:** reports include at most ten validation messages
  per failed plan attempt and the safe LLM failure category. They omit
  prompts, raw responses, and credentials; console attempt metrics pass
  through the existing redacting logger.

## Clarifications (spec is silent; the diagrams decide)

### CL-01 — Where the iteration limit is checked
- **Spec:** the text says only that the loop "exits with unresolved
  violations". The package state diagram draws `remediating →
  scan_exhausted` ("iteration limit reached with violations remaining") and
  has no `scanning → scan_exhausted` edge.
- **Implementation:** `scanning → remediating | scan_clean | scan_error`;
  `remediating → scanning | scan_exhausted`. When a scan finds violations,
  the package enters `remediating`. There, if the iteration budget is used
  up, it moves to `scan_exhausted` without applying a fix; otherwise it
  applies a fix pass, increments `iteration_count` and returns to
  `scanning`. `iteration_count` therefore counts completed fix passes, and
  it never exceeds `max_iterations`.
- **Implemented in Phase 0:** pure remediation-budget decision and transition
  tests; actual fix application follows in the SecurityAgent phase.

### CL-02 — Validation follows exhausted remediation
- **Spec:** FR-S-07 says unresolved violations lead to `pending_review`,
  while FR-S-05 says an exhausted package proceeds to ValidatorAgent. The
  package state diagram routes `scan_exhausted` through `validating` first.
- **Implementation:** exhausting the budget stops automated remediation,
  then validation runs. Its result is recorded as `valid`, `invalid`, or
  `validation_error` before the package enters `pending_review`.
- **Implemented in Phase 0:** package transition table and readiness tests.

### CL-03 — LLM retry arithmetic
- **Spec conflict:** Section 3.2 states both "30 seconds per attempt, up to
  3 attempts" and "30s + 60s + 60s = maximum 150 seconds including backoff".
- **Implementation:** each attempt is limited to 30 seconds, with at most 3
  attempts. Backoff has a 1-second then 2-second exponential ceiling before
  full jitter. The wrapper has a separate hard 150-second deadline that clips
  attempts and backoff when needed. Ordinary three-attempt timeouts finish
  well before 150 seconds.
- **Implemented in Phase 1:** `RetryPolicy` and `LLMAdapter.complete_json`.

### CL-04 — Input length and validation order
- **Spec:** FR-I-01 sets a 10--2,000-character limit, and FR-I-02 calls for
  a 422 when infrastructure intent is absent; simultaneous failures have no
  stated priority.
- **Implementation:** reject control characters first, then measure Unicode
  code points after stripping surrounding whitespace and reject out-of-range
  input with the future HTTP 400 error, then apply the intent gate and use
  the future HTTP 422 error. Thus `hello` is a length error. The word-list
  gate favours false accepts over false rejects: one whole-word
  infrastructure term, including simple single-word inflections, is enough
  to proceed.
- **Implemented in Phase 2:** pure input rules and boundary tests. HTTP
  mapping remains Phase 4 work.

### CL-05 — Valid vague-description example
- **Spec conflict:** FR-A-03's verification input `a web app` has nine
  characters, below FR-I-01's ten-character minimum.
- **Implementation:** use `build a web app` in Phase 2 acceptance and
  evaluation tests; explicitly test that `a web app` fails the length rule.
- **Implemented in Phase 2:** input, agent, and evaluation tests.

---

## Open questions

### OQ-01 — HTTP 410 for expired packages (Deferred)
A missing package row cannot justify 410 on its own: the ERD allows 0–3
packages per run, so absence may mean "generation failed" or "removed by
retention". 410 needs a durable record of which variants once existed, for
example an `agent_events` row with a defined payload such as
`{"kind": "package_stored", "variant": "cost"}`. Decide in Phase 4 (event
payload schema) or Phase 7 (download/results endpoints). Until then, no 410.

### OQ-02 — Terminality of `invalid` and `validation_error` (Resolved)
Resolved by D-06 (Option C).

### OQ-03 — 30-second per-attempt LLM timeout
A full multi-file package may take longer than 30 s to generate. Measure it
in the Phase 1 spike before building on it.

**Measurement (2026-09-26):** Groq free tier via the OpenAI-compatible adapter,
model `openai/gpt-oss-120b`. The [full-package spike](spikes/phase1-llm-timing-openai-20260926T004541Z.md)
completed in one call in 24.6 s, at about 474 output tokens/s. It returned
11,660 output tokens; JSON parsed and was not truncated. In split mode, all
9 parallel file-group calls returned HTTP 429 and none generated output.
Groq's published free-plan limits for this model are 8K tokens/minute,
30 requests/minute, and 200K tokens/day ([rate limits](https://console.groq.com/docs/rate-limits)).
This measurement shows that full-package latency fits 30 s on a fast provider,
but free-tier per-minute token limits prevent parallel generation in this
setup. The stub result remains a report-format check only. **OQ-03 stays open**
until the evaluation provider is chosen.

### OQ-04 — Single-process assumption
The in-memory SSE broker requires a single backend process. This should be
stated explicitly in the thesis design (Section 4.4 or the deployment
section).

### OQ-05 — End-to-end agent deadline (Resolved)
One monotonic `AgentBudget` tracks elapsed time across plan attempts, prompt
construction, validation, and LLM calls. Before each call, the agent passes the remaining
budget to `complete_json`; the call uses the shorter of that value and its
own policy deadline for attempts and backoff. If fewer than one second
remains before a call, the agent stops. A valid response returned within
its call deadline is accepted after validation without another budget check.
Implemented in Phase 2 and tested with an injectable clock.

### OQ-06 — Evaluation provider throughput
Evaluation provider must allow ~3 concurrent full generations (~36K
tokens/min); Groq free (8K TPM) does not. Decide before PR-01/PR-05
measurements.

---

## Thesis text to update (collected)
- Tighten FR-S-07 wording to say that exhausted remediation stops fix passes,
  then validation runs before the package enters `pending_review` (CL-02).
- Section 4.2 retention paragraph: say that the sweep deletes only packages
  and that the app role cannot delete runs or modify events (D-03, D-04).
  The ERD already shows this; the paragraph does not yet.
- Section 4.4: state the single-process assumption for SSE (OQ-04).
- Fix the "30s + 60s + 60s" sentence in Section 3.2 (CL-03).
- Add the concrete `complete_json` method and async `send_prompt` to the
  LLMAdapter class diagram (D-07).
- Optional class-diagram polish: `run_id: UUID`, `llm_provider:
  LLMProvider`, `variant: Variant`, and field types for `DeploymentPlan`
  and `Violation`.
- Add an ADR row: agents are plain Python classes over the custom adapter;
  reject agent frameworks such as LangChain, LangGraph, and CrewAI because
  the pipeline is fixed and direct control of retries and deadlines keeps
  dependencies and contributions explicit.
- Add the strict `DeploymentPlan` field types to the class diagram.
- State that the orchestrator stores the plan in the `plan_created` event
  payload (Phase 4), since the ERD has no plan column.
- In FR-A-03, change the nine-character verification input `a web app` to
  `build a web app` so it meets FR-I-01's ten-character minimum (CL-05).
