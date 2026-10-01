# Codex task — Phase 4: Orchestrator, pipeline API and live progress (SSE)

Read `AGENTS.md`, `docs/design-deviations.md` and `docs/IMPLEMENTATION_LOG.md`
first. The specification is in `docs/spec/`. This task is **Phase 4 only**.
Phases 0–3 are complete. Reuse their components; do not re-implement them.

## Goal

Run the pipeline end to end for the first time:
- `POST /api/pipeline/run` validates the input, **persists the run first**, and
  returns immediately;
- a background `PipelineOrchestrator` runs the ArchitectAgent, then the three
  GeneratorAgents **in parallel with a barrier**, stores the packages, and
  hands each package to post-generation stages;
- every state change becomes an ordered event: `EventLog` (Phase 0) → an
  in-memory broker → `GET /api/pipeline/{run_id}/stream` (SSE);
- a command-line watcher lets the author watch a real run live.

This is thesis contribution **C1** (parallel orchestration), plus the backend
half of **C3** (live streaming).

Relevant spec:
- FR-I-01 to FR-I-04;
- FR-A-04;
- FR-G-01, FR-G-06, FR-G-07;
- **FR-P-01 to FR-P-04**;
- PR-02, PR-03;
- UC-01, UC-02;
- Section 4.4, the API and SSE design: the replay-then-subscribe rule, the
  stream close rule, and the frozen run status;
- the sequence diagram's sequencing rule: the run is persisted **before** the
  Architect is invoked.

## Decisions already made by the author (do not revisit)

1. **Pluggable post-generation stages, with an honest placeholder.** The
   Security and Validation stages are interfaces. Their real implementations
   come in Phases 5 and 6. Until then, production wiring uses
   `UnavailableSecurityStage`:
   - it moves each generated package `generated → scanning → scan_error`, with
     the message "security scanning is not available in this build";
   - under `classify_run`, such runs end `failed`. That is intended and
     truthful;
   - **never** add a stage that marks unscanned packages as passing.

   The tests exercise the full success, partial-success and pending-review
   flows with **fake** stages.
2. **A command-line watcher**, `make run-pipeline`, prints the SSE events of a
   real run live (section 9).
3. **Existing components are reused:**
   - input rules and `RunConfig` (Phase 2);
   - `AgentFactory`, `ArchitectAgent` and the generators (Phases 2–3);
   - the state machines, repositories, `EventLog` (the single instance on
     `app.state`) and `classify_run` (Phase 0).
4. **No new dependencies.** Implement SSE with FastAPI's `StreamingResponse`
   (`text/event-stream`).

## Definition of done

- `make test` and `make lint` pass. No test touches the network.
- With `LLM_PROVIDER=stub`, `make run` plus `make run-pipeline TEXT="..."`
  shows a full stream ending in `failed`, because of the placeholder stage.
- Docs are updated per `AGENTS.md` §8.

Commit after each numbered section. Do not read `.env`. Make no real API
calls.

---

## 0. JSON robustness (OQ-08) and the model decision record (D-17)

**Background:** Claude Sonnet 5 without reasoning produced `invalid_json` in 3
of 14 real calls. Retries recovered every time, but one case succeeded only on
its third and last attempt. The cause is invisible, because response text is
never logged, and that must stay so.

**a) Safe diagnostics.** When `extract_json_object` rejects a response, the
`LLMResponseFormatError` carries a **reason code**, and the attempt log line
records it as `format_reason=`. Never include response text. The codes are:
- `empty`;
- `prose_before`;
- `prose_after`;
- `multiple_blocks`;
- `not_object`;
- `truncated`;
- `syntax_error`, with the character offset only, e.g. `syntax_error@1532`.

Test every code.

**b) Optional structured output.** Add the setting `LLM_RESPONSE_FORMAT`:
- unset (the default) means today's behaviour;
- `json_object` means the OpenAI-compatible adapter sends `response_format:
  {"type": "json_object"}`.

Check OpenRouter's current documentation for support and shape. The Anthropic
adapter ignores it; document that. Add tests with the httpx2 mock transport:
the field is absent when unset and present when set. Record it as **OQ-08** in
`design-deviations.md`: mechanism implemented; its effect is to be measured by
the author on real runs.

**c) D-17, the default evaluation model.** Record the author's decision:
- **The default model is `anthropic/claude-sonnet-5` via OpenRouter** (the
  OpenAI-compatible adapter), with `LLM_REASONING_EFFORT=off`.
- **Evidence** (the committed evaluations under `docs/evals/`):
  - Architect: 5/5 plans valid on the first plan attempt;
  - generators: 6/6 packages, 100% heuristic compliance, median ~72 s per
    package, ~$0.65 for 6 packages;
  - with reasoning on, only 3/6 packages, because of truncation at 32K tokens
    and the deadlines;
  - `openai/gpt-oss-120b:nitro`: 6/6 packages at ~3 s and ~2¢, with 87.5–93.8%
    compliance, kept as the fast, low-cost configuration;
  - `qwen/qwen3-coder`: 3/6 packages, too slow for the budget.
- **Also record, in "Thesis text to update":**
  - a model-comparison table in the evaluation chapter;
  - the "quality versus latency" discussion;
  - the Aurora finding: a structurally complete package defined an Aurora
    cluster with no instances. None of the structural checks, Checkov,
    tfsec or the planned Validator checks would detect it. This is a known
    limit, and an argument for human review.

## 1. Event vocabulary and SSE message format (`app/events/kinds.py`)

- `EventKind` (StrEnum):
  - `run_status`;
  - `agent_state`;
  - `plan_created`;
  - `package_status`;
  - `package_generated`;
  - `stage_notice`.
- Typed payload builders, one per kind. Every event stored through `EventLog`
  carries `payload.kind`. Package events carry `payload.variant`.
  - `plan_created`: the plan as JSON (≤ 32 KB, guaranteed by Phase 2).
  - `package_generated`: `variant`, `file_count`, `total_chars`, `paths` (the
    list of file paths), `notes` (bounded) and the generator metrics
    (attempts, elapsed, tokens, prompt version). **Never file contents.**
    This event is the durable record of which variants existed. Update
    **OQ-01** accordingly: the 410 decision can now be based on it, in
    Phase 7.
- **The SSE message format.** The spec requires the `agent`, `status` and
  `message` fields. Each message is:

  ```
  id: <seq>
  event: <kind>
  data: {"seq":…, "kind":…, "agent":…, "status":…, "previous_status":…,
         "message":…, "variant":…, "timestamp":…, "payload":{…}}
  ```

  `status` and `previous_status` are the new and previous state values.
  `variant` is `null` for non-package events. Provide one function,
  `to_sse(record) -> str`, and test it. Record it as **D-18**.

## 2. Broker (`app/events/broker.py`)

- **`InMemoryBroker` implements the Phase 0 `Publisher` protocol.** It keeps
  per-run subscriber queues.
- **`subscribe(run_id)`** is an async context manager, yielding an async
  iterator of `EventRecord`.
- **`publish(record)`** delivers to that run's subscribers only, never to
  other runs.
- **Each subscriber queue is bounded** (setting `BROKER_QUEUE_SIZE`, default
  1000). On overflow, the subscriber is marked `overflowed` and its iterator
  ends. The client reconnects with `Last-Event-ID` and recovers through replay
  (the Phase 0 design).
- **Replace `NullPublisher` with the broker in `create_app`.** It is the
  single broker instance on `app.state.broker`, with a dependency accessor.
  `EventLog` remains the single instance and publishes to the broker.
- **Record** the single-process assumption (OQ-04) as now concretely relied
  upon.

## 3. State-changing helpers (`app/pipeline/state.py`)

A small `PipelineStateWriter`, used by the orchestrator and by stages. It is
the **only** way pipeline code changes a run or package status:
- `run_transition(run_id, target, *, message, error_message=None)`;
- `package_transition(run_id, variant, target, *, message, error=None)`;
- `agent_state(run_id, agent_name, state, *, message, variant=None)`.

Each one:
1. applies the transition through the repository, which uses
   `assert_transition` and the row lock (Phase 0) in its own transaction;
2. **then** appends the event through `EventLog`.

The order is database state first, then the event. If the process dies between
the two, the state is correct and the event is missing. Document that
trade-off in the module docstring.

**Extend the repositories only as needed:**
- `set_status(..., error_message=...)` for runs;
- `set_status(..., error=...)` for packages;
- `mark_interrupted(...)` for section 7.

**State machine addition, recorded as D-19:** add the run edge `created →
failed`, for a run that was persisted but never started (a launch failure, or
a restart before the start). Update the transition tests.

## 4. Stage interfaces and the placeholder (`app/pipeline/stages.py`)

```python
class SecurityStage(Protocol):
    async def run(self, ctx: StageContext, variant: Variant, package: IaCPackage) -> PackageStatus: ...
    # returns scan_clean | scan_exhausted | scan_error; moves the package through
    # scanning/remediating itself via ctx.writer

class ValidationStage(Protocol):
    async def run(self, ctx: StageContext, variant: Variant, package: IaCPackage) -> PackageStatus: ...
    # returns valid | invalid | validation_error, having moved the package through validating
```

- **`StageContext`** carries the run id, the `PipelineStateWriter`, the plan,
  and a clock.
- **The orchestrator,** not the stages, applies `readiness_after_validation`
  (Phase 0) and the final `production_ready` / `pending_review` transition.
  Packages ending in `scan_error` skip validation.
- **`UnavailableSecurityStage`:**
  - moves `generated → scanning → scan_error`, with the message "security
    scanning is not available in this build";
  - emits a `stage_notice` event explaining it;
  - returns `scan_error`.
- **`UnavailableValidationStage`:** it exists for symmetry and is never
  reached, because every package ends in `scan_error`.
- **Test fakes live under `tests/`:** configurable fake stages that return any
  outcome after optional delays and walk the legal transitions.
- **Record it as D-20:** a temporary placeholder, removed in Phase 5, whose
  runs honestly end `failed`.

## 5. `PipelineOrchestrator` (`app/pipeline/orchestrator.py`)

`PipelineOrchestrator(run_id, text, run_config, *, factory, session_factory,
writer, security_stage, validation_stage, clock)`, with `async def run() ->
RunStatus`.

**The sequence:**
1. `created → running`.
2. **Architect.** `agent_state(architect, running)`, then `parse_input` and
   `generate_plan`.
   - On `ArchitectError`: `agent_state(architect, failed)`, and the run moves
     to `failed` with `error_message` = the error's plain-English message
     (FR-A-04, FR-P-03). **No package rows are created, and no generator is
     constructed or invoked.** Return.
   - On success: `agent_state(architect, completed)` and a `plan_created`
     event.
3. **Generators (FR-G-01, FR-P-02).**
   - Create the 3 package rows (`generating`) and emit their events.
   - Build the generators through `AgentFactory.create_generators(run_config)`.
   - Run them with `asyncio.gather(..., return_exceptions=True)`. **This is
     the barrier.**
   - Per generator:
     - `agent_state(generator_<variant>, running)`;
     - on success: `save_files` (FR-G-07), `generating → generated`,
       `package_generated`, and `agent_state(completed)`;
     - on `GeneratorError`: `generating → failed` with `error` set to its
       message, and `agent_state(failed)`.
   - Unexpected exceptions from one generator are treated as that generator
     failing, with a generic message; the details are logged, redacted.
4. **After the barrier.** If no package is `generated`, the run moves to
   `failed` ("no package could be generated"). Return.
5. **Post-generation (per generated package, concurrently).**
   - Run the security stage, and then the validation stage unless the result
     is `scan_error`.
   - Apply `readiness_after_validation` and the final transition.
   - Wrap each stage call so an unexpected exception becomes that package's
     `scan_error` or `validation_error`, never a stuck state.
6. **Settle.** `classify_run(architect_succeeded=True, statuses)`, then the
   final run transition. `end_time` is set by the repository. The run status
   is **frozen** after this.

**Robustness:**
- **A top-level guard:** any unexpected exception moves the run to `failed`
  with a generic message ("internal error; see server logs"). Log it,
  redacted. A run must **never** remain `running` because of a bug.
- **On `CancelledError`** (shutdown): try to move the run to `failed` with
  "interrupted by server shutdown", then re-raise.

## 6. Runner (`app/pipeline/runner.py`)

- **`PipelineRunner`** lives on `app.state`. It owns the background tasks:
  - `start(run_id, text, run_config)` creates an `asyncio` task and tracks it;
  - finished tasks are removed.
- **A new setting, `MAX_CONCURRENT_RUNS`** (default 5). When that many runs
  are active, `POST /run` returns **HTTP 429** with a plain message and
  creates **no** run. Record it as **D-21**. PR-03 requires at least 3.
- **On app shutdown** (lifespan), cancel active tasks, await them with a
  timeout, and let the orchestrator mark the runs failed.

## 7. API (`app/api/pipeline.py`) and startup recovery

**`POST /api/pipeline/run`:**
- **Body:** `{"text": str, "config": RunConfig | null}`.
- **Errors, in this order:**
  - **400** `{"error":"invalid_request","message":…}` for:
    - malformed JSON;
    - a missing or non-string `text`;
    - an invalid `config`, e.g. `max_iterations` 0 or an unknown provider;
    - a run config that can't be built, e.g. a real provider with no key or
      model configured (checked **before** persisting, with a clear message
      and no secrets).

    Use a route-scoped handler for FastAPI's validation errors, so FastAPI's
    default 422 is not used for malformed bodies.
  - **400** for `InputLengthError` / `InputContentError`, with their codes and
    messages (FR-I-01).
  - **422** `{"error":"no_infrastructure_intent","message":…}` (FR-I-02).
  - **429** for the concurrency limit.
- **On acceptance:**
  - persist the run (`created`) with the resolved provider, model and
    `max_iterations` (FR-I-04);
  - **only then** start the task (the design's sequencing rule);
  - respond **202** `{"run_id":…, "status":"created",
    "stream_url":"/api/pipeline/<id>/stream"}`.
- Nothing about a rejected request is persisted.

**`GET /api/pipeline/{run_id}/stream`:**
- **404** for an unknown run, and **400** for a malformed id.
- **The replay-then-subscribe algorithm** (Phase 0 design):
  1. **subscribe first**;
  2. replay `list_after(run_id, last_event_id)`;
  3. drain live events, skipping `seq` ≤ the last sent.
- Honour the `Last-Event-ID` header.
- Send a keep-alive comment (`: keepalive`) every `SSE_KEEPALIVE_SECONDS`
  (default 15).
- **The close rule (spec 4.4):** end the stream when the run status is
  terminal **and** no package is in `scanning`, `remediating` or
  `validating`. Check this after the replay and after each live event. A run
  that is already settled replays its full history and closes.
- On broker overflow, end the stream. The client reconnects with
  `Last-Event-ID`.

**Startup recovery,** in the lifespan: runs in `created` or `running` are
moved to `failed` with "interrupted by server restart", with events. Package
rows are left as they are, since their last state is recorded. Document it.

## 8. Tests (offline, tagged with `req` markers)

Use stub-scripted agents: build them through the real `AgentFactory` with
`provider=stub`, then load the scripts (the Phase 2–3 pattern). Also use fake
stages, a real PostgreSQL, and httpx `AsyncClient` with `ASGITransport`,
streaming the SSE.

**API:**
- **400** for:
  - malformed JSON;
  - a missing `text`;
  - a non-string `text`;
  - too short and too long;
  - a control character;
  - a bad config;
  - a real provider with no key.
- **422** for "tell me a joke about cats".
- In every rejected case, **no run row** is created.
- **202:** the run row exists **before** the Architect stub is called
  (instrument the stub to assert that the row exists when it's invoked).
- The run row stores the resolved provider, model and max_iterations
  (`req("FR-I-01","FR-I-02","FR-I-03","FR-I-04")`).

**Orchestrator:**
- **The happy path** (fake stages clean/valid): the run is `success`, and
  every package is `production_ready`. Assert the **exact ordered list** of
  `(agent, status)` events and that each has a timestamp
  (`req("FR-P-01")`).
- **One generator fails:**
  - that package is `failed` with its error;
  - the others continue;
  - the run is `partial_success` (`req("FR-P-03","FR-G-06")`).
- **An exhausted scan** leads to `pending_review`, and the run is
  `partial_success`.
- **The Architect fails** (`req("FR-P-03","FR-A-04")`):
  - the run is `failed`, and `error_message` is persisted;
  - no package rows exist;
  - **the factory's `create_generators` was never called**.
- **All generators fail:** the run is `failed`.
- **The barrier** (`req("FR-P-02")`):
  - make one generator finish instantly and two wait on `asyncio.Event`s;
  - assert that the security stage has **not** been invoked for anything
    until both are released.
- **The placeholder stage:**
  - every package ends `scan_error` with the notice;
  - the run is `failed`;
  - no package is ever `production_ready`.
- **An unexpected exception** in a stage becomes that package's error state,
  and one in the orchestrator core makes the run `failed`. It is never stuck
  `running`.
- **`package_generated` payloads** contain paths and metrics, **no file
  contents**, and are within the size limit (`req("FR-G-07")`).

**Broker:**
- per-run isolation;
- ordering;
- multiple subscribers;
- overflow ends the subscriber.

**SSE** (`req("FR-P-04","PR-02")`):
- **A full stub run:**
  - the events arrive in `seq` order, with **no duplicates or gaps** relative
    to `list_after`;
  - the stream closes after settling.
- **A late connect:** the full replay, then close.
- **A mid-run connect with `Last-Event-ID`:** exactly the events after it,
  with no duplicates, while writes continue.
- **An already-settled run:** replay and close.
- **An unknown run:** 404.
- **Keep-alive,** with a short interval setting.

**Concurrency** (`req("PR-03")`):
- **3 runs** start simultaneously, with stub agents adding fixed simulated
  delays. All complete.
- **The events never cross runs.**
- **Each run's wall-clock time is ≤ 1.5× the solo baseline,** measured in the
  same test.
- **With `MAX_CONCURRENT_RUNS=2`,** the third request gets 429 and creates no
  run.

**Recovery and shutdown:**
- a `running` run left in the database is `failed` after startup;
- runner shutdown cancels tasks and marks their runs `failed`.

**`created → failed`:** the new edge is allowed, and the other illegal edges
still raise.

**Canary** (`req("NFR-01")`): a provider error containing the canary key during
a run does not leak into `pipeline_runs.error_message`, into any event, or
into the SSE output.

**JSON diagnostics** (section 0): each reason code, and `response_format`
present or absent.

## 9. Command-line watcher (`backend/scripts/run_pipeline.py`, `make run-pipeline`)

- **Usage:**
  - `make run-pipeline TEXT="..."`;
  - optional `CONFIG_PROVIDER` / `CONFIG_MODEL` / `API_URL` (default
    `http://localhost:8000`).
- **POSTs to the running backend** and prints the run id, or the 400/422/429
  body with its message.
- **Connects to the stream and prints one line per event,** e.g.
  `[+12.4s] #17 generator_security  package security: generating → generated  (6 files)`.
- **When the stream ends,** prints a final summary: the run status, each
  package's final status, and the total wall-clock time.
- **Reconnects with `Last-Event-ID`** if the connection drops.
- **It never reads `.env`.** It only talks to the API. The backend, started
  with `make run`, uses its own configuration.
- Test it offline against the ASGI app via an injectable transport.

## 10. Documentation

- **D-17:** the model decision (section 0c).
- **D-18:** the SSE message format.
- **D-19:** the `created → failed` edge.
- **D-20:** the placeholder stage.
- **D-21:** `MAX_CONCURRENT_RUNS` and 429.
- **OQ-01:** updated by `package_generated`.
- **OQ-04:** now relied upon.
- **OQ-08:** diagnostics plus `response_format`, whose effect is to be
  measured.
- **"Thesis text to update", add:**
  - the 202 response;
  - 429 as a new status code;
  - the SSE event fields;
  - startup recovery;
  - the `created → failed` edge (the run state diagram);
  - the model-comparison table;
  - the Aurora finding.
- **README:** a "Running a pipeline" section with the two-terminal workflow
  (`make run`, then `make run-pipeline TEXT="..."`), the new settings, and a
  note that until Phase 5 real runs end `failed` because of the placeholder.
- **Implementation log:** entry with real test counts.

## 11. Out of scope

- The results, review and download endpoints (Phase 7).
- Real scanning and remediation (Phase 5).
- Real validation (Phase 6).
- Frontend (Phase 8).
- Authentication.
- Real API calls.

Finish with the summary format from `AGENTS.md` §10.
