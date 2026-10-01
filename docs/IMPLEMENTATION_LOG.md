# Implementation Log

Chronological record of every implementation change. Newest entry at the top.
This file is the raw material for thesis Chapter 5 (Implementation) and
Chapter 6 (Testing), so be factual and specific. Never delete old entries;
if something was wrong, add a new entry that corrects it.

## Entry template

```markdown
## YYYY-MM-DD — Phase N — <short title>

**Summary:** One or two sentences on what changed and why.

**Requirements addressed:** FR-..., NFR-..., PR-... (or "none — infrastructure").

**Files:** added / changed / removed (paths).

**Decisions:** Any choice made during the task, with the reason. Link to a
deviation ID (D-xx) or open question (OQ-xx) if relevant.

**Tests:** Command run and real result, e.g. `make test` → 42 passed,
0 failed, 1 skipped. List new test files and what they prove.

**Known gaps / follow-ups:** What is intentionally not done yet.
```

---

## 2026-10-01 — Phase 4 follow-up — Stream closure and core failure guards

**Summary:** Added integration tests for SSE closure after a terminal run with
an active remediation retry, and for unexpected orchestrator failures settling
the run without exposing exception text in persisted or streamed data.

**Requirements addressed:** FR-P-03, FR-P-04, FR-S-09, NFR-01.

**Files:** changed `backend/tests/integration/test_pipeline_sse.py`,
`backend/tests/integration/test_pipeline_orchestrator.py`, and this log.

**Decisions:** The stream test uses a 0.01-second keep-alive setting and
two-second timeouts on every read, so premature closure or a stalled stream
fails promptly. No design deviation or new open question was introduced.

**Tests:** `make test` passed with **374 passed, 0 failed, 0 skipped**.
`make lint` passed Ruff check, Ruff format check (100 files), and mypy
(61 source files). Replacing the active-package condition in `_can_close`
with `True` made the stream test fail before the keep-alive. Removing the
generic exception handler's `_fail_unexpected` call made the core failure
test fail because the persisted run remained `running`. Both mutations were
restored before the full checks.

**Known gaps / follow-ups:** None from this test-only follow-up.

---

## 2026-10-01 — Phase 4 — Pipeline orchestration and live progress

**Summary:** Added the asynchronous pipeline API, Architect-to-parallel-generator
barrier, durable state/event writing, bounded in-memory SSE broker, recovery,
and command-line watcher. The production security placeholder leaves generated
packages in `scan_error`, so Phase 4 runs truthfully settle as `failed`.

**Requirements addressed:** FR-I-01--04, FR-A-04, FR-G-01, FR-G-06--07,
FR-P-01--04, PR-02, PR-03, UC-01, UC-02, NFR-01.

**Files:** added `backend/app/events/{kinds,broker}.py`,
`backend/app/pipeline/{state,stages,demo_stub,orchestrator,runner}.py`,
`backend/app/api/pipeline.py`, `backend/scripts/run_pipeline.py`, and Phase 4
unit and integration tests; changed the LLM parser and OpenAI adapter,
repositories, state machine, app wiring, settings, `Makefile`, `.env.example`,
`README.md`, and `docs/design-deviations.md`.

**Decisions:** D-17--D-21 record the evaluation model, SSE format, launch
failure edge, unavailable security stage, and capacity limit. OQ-01 now has a
durable `package_generated` variant record; OQ-04 is enforced by one Uvicorn
worker; OQ-08 implements safe format diagnostics and optional JSON mode.
The deterministic pipeline demo is an explicit factory opt-in, preserving all
Phase 1--3 stub consumers. State commits before the event transaction, so a
hard crash in that window can leave a missing event. The spec's `failed = 0
packages` wording is recorded for correction to `0 usable packages`.

**Tests:** `make lint` passed Ruff check, Ruff format check (100 files), and
mypy (61 source files). `make test` passed with **372 passed, 0 failed, 0
skipped**. New tests cover API rejection and persistence, the generator
barrier, success and partial outcomes with fake stages, placeholder failure,
startup recovery, cancellation, canary redaction, broker isolation and
overflow, replay/live overlap, keep-alives, concurrency, and stub regression.
With `LLM_PROVIDER=stub`, `make run` and `make run-pipeline TEXT="Deploy a small
AWS web service"` produced a full stream ending `failed`, with all
three packages in `scan_error`. No real LLM API call was made.

**Known gaps / follow-ups:** Real scanning and remediation (Phase 5), real
validation (Phase 6), results/review/download APIs (Phase 7), and frontend
(Phase 8) remain. A database outage or hard crash cannot be settled until
recovery; an event missing from the state/event commit window cannot be
reconstructed by replay.

---

## 2026-09-30 — Phase 2 follow-up — Architect evaluation placement checks

**Summary:** Corrected the architect evaluator's three-tier relational
database check so a database represented in `storage` no longer causes a
false FAIL. The object storage, CDN, and queue checks now recognize their
schema-compatible service and storage placements too.

**Requirements addressed:** FR-A-01, FR-A-02.

**Files:** changed `backend/scripts/eval_architect.py`,
`backend/tests/unit/test_eval_architect.py`,
`docs/design-deviations.md`, and this log.

**Decisions:** The report calls the check `relational database`. It passes
for an RDS/Aurora-labelled service or a storage entry whose kind is
`relational_db`; an RDS label on storage of another kind does not suffice.
D-10 records that the evaluation accepts equivalent placements allowed by
the plan schema. These are advisory evaluation checks, not plan validation.

**Tests:** `make test` passed with 331 passed, 0 failed, 0 skipped.
`make lint` passed Ruff check, Ruff format check (84 files), and mypy
(52 source files). Added positive and negative examples for both placements
and asserted the renamed check in the saved stub report. No real provider
calls were made.

**Known gaps / follow-ups:** These soft checks detect named components; they
do not establish deployability or service compatibility. Existing untracked
evaluation reports were left untouched.

---

## 2026-09-30 — Phase 3 follow-up — Configurable reasoning effort

**Summary:** Added optional `LLM_REASONING_EFFORT` control for
OpenAI-compatible requests and recorded its configured value in each LLM
attempt log. Unset leaves request bodies unchanged.

**Requirements addressed:** PR-05, NFR-01.

**Files:** changed `backend/app/core/config.py`, `backend/app/llm/base.py`,
`backend/app/llm/openai.py`, `backend/app/llm/anthropic.py`,
`backend/app/llm/stub.py`, `backend/app/llm/factory.py`, their configuration,
factory, adapter, and log tests, `.env.example`, `README.md`,
`docs/design-deviations.md`, and this log.

**Decisions:** D-16 maps `off` to OpenRouter's
`reasoning: {enabled: false}` and `low`/`medium`/`high` to
`reasoning: {effort: <value>}` in SDK `extra_body`. Anthropic does not send
the setting; it only records it in the common attempt log. The default logs
`reasoning_effort=unset`. OQ-07's request mechanism is resolved, while the
quality effect remains an evaluation question.

**Tests:** `make test` passed with 326 passed, 0 failed, 0 skipped.
`make lint` passed Ruff check, Ruff format check (84 files), and mypy
(52 source files). Mock transport tests assert absence when unset and exact
request shapes for all configured values, plus Anthropic's unchanged body.
No real provider calls were made.

**Known gaps / follow-ups:** Provider/model support and any quality benefit
must be assessed in evaluation; the adapters do not discover supported
reasoning levels per model.

---

## 2026-09-30 — Phase 3 follow-up — Generator prompt v3 autoscaling

**Summary:** Advanced the generator prompt to version 3 and replaced the
performance directive's Kubernetes-only HPA sentence with per-service
autoscaling guidance for Kubernetes Deployments, ECS services, and EC2 Auto
Scaling groups.

**Requirements addressed:** FR-G-04.

**Files:** changed `backend/app/agents/prompts/generator.py`,
`backend/app/agents/generators/performance.py`,
`backend/tests/unit/test_generator_prompt.py`,
`docs/design-deviations.md`, and this log.

**Decisions:** D-14 records the directive expansion. The shared prompt rules
and generation algorithm remain the same; only the performance strategy text
and prompt version changed.

**Tests:** `make test` passed with 312 passed, 0 failed, 0 skipped. `make lint`
passed Ruff check, Ruff format check (84 files), and mypy (52 source files).
The prompt test asserts the complete new instruction and confirms all three
system prompts are byte-identical after replacing the marked directives.
No real provider calls were made.

**Known gaps / follow-ups:** The prompt directs generation but does not
establish that generated autoscaling resources deploy correctly; later
validation and evaluation must assess the packages.

---

## 2026-09-30 — Phase 3 follow-up — Evaluation logging, prompt, and Aurora check

**Summary:** Fixed the LLM attempt log separator, recorded optional
OpenRouter serving and reasoning diagnostics, shortened the generator's
prompt-v2 output guidance, required Kubernetes HPAs in the performance
directive, and corrected the Aurora multi-AZ report after the first real
model comparison.

**Requirements addressed:** PR-05, NFR-01, FR-G-04.

**Files:** changed `backend/app/llm/base.py`,
`backend/app/llm/openai.py`, `backend/app/agents/prompts/generator.py`,
`backend/app/domain/directive_checks.py`, their unit tests,
`docs/design-deviations.md`, and this log.

**Decisions:** D-13 now recognizes an Aurora cluster with multiple instance
declarations or multiple distinct explicit availability zones. The check
remains a text heuristic and does not resolve Terraform references or prove
placement. D-14 records the compact prompt-v2 guidance and the performance
HPA instruction. Serving diagnostics are optional and never required for a
successful response. Attempt log fields are complete `key=value` tokens
joined with single spaces.

**Tests:** Before the first three commits, `make lint` passed each time and
`make test` reported 304, 307, and 307 passed respectively. Before the
Aurora commit, `make lint` passed Ruff check, Ruff format check (84 files),
and mypy (52 source files); `make test` reported 312 passed, 0 failed,
0 skipped. New tests parse every attempt outcome, exercise OpenRouter mock
transport with and without optional fields, compare directive-neutralized
prompts, and cover Aurora pass and fail cases. No real provider calls were
made.

**Known gaps / follow-ups:** The Aurora result remains an advisory heuristic;
subsequent validation and scanning must establish package validity and
deployed behaviour. The untracked report from the first real evaluation was
left outside these commits.

---

## 2026-09-30 — Phase 3 — Generator agents and offline evaluation

**Summary:** Added a shared full-package generation template, three
optimisation strategies, deterministic path completeness, report-only
directive checks, factory methods, and a stub-first model comparison
evaluator. One package response keeps cross-file names together; structural
defects can request one complete correction.

**Requirements addressed:** FR-A-05, FR-G-02--05, partial FR-G-01 and
FR-G-06, PR-05, NFR-01. Pipeline concurrency, status, and FR-G-07
persistence remain Phase 4 work.

**Files:** added `app/domain/package_layout.py` and `directive_checks.py`,
`app/agents/generators/*`, `app/agents/prompts/generator.py`,
`scripts/eval_generators.py` and its committed plan/package fixtures, new
unit tests, and a stub report under `docs/evals/phase3-generators-*`;
changed `app/core/config.py`, `app/llm/base.py`, `app/agents/factory.py`,
existing tests, `.env.example`, `Makefile`, `README.md`, and
`docs/design-deviations.md`.

**Decisions:** D-12 fixes package paths and treats the plan's file-type list
as the contract. D-13 reports directive heuristics without rejecting a
package. D-14 requests one whole package per attempt. D-15 combines the
Template Method generation algorithm with directive-based Strategy
subclasses. CL-06 gives full-package LLM attempts a configurable 120-second
limit inside a 150-second agent budget. Generator notes remain in
`GeneratorRunInfo` and the evaluation report; Phase 4 will persist them in
the package-generated event payload. File limits use decimal UTF-8 bytes
(200,000 per file and 2,000,000 per package).

**Tests:** `make lint` passed: Ruff check, Ruff format check (84 app/test
files), and mypy (52 source files). The offline unit suite passed with
270 passed, 0 failed, 0 skipped. The provider canary subset passed with
2 passed, 0 failed, 1 deselected. The stub `make eval-generators` command
with `--models stub --no-env-file --price-in stub=1 --price-out stub=2`
completed with six successful package cases and one visible correction;
the report contains PASS and FAIL directive findings. `make test` stopped
before pytest at Alembic migration because PostgreSQL refused the connection
at 127.0.0.1:5432. `make up` failed because Docker is unavailable in this
WSL distro.

**Known gaps / follow-ups:** The full PostgreSQL-backed test suite needs
Docker Desktop WSL integration or another PostgreSQL 16 instance. The stub
report verifies workflow and format, not real-provider quality, deployability,
or FR-G-05's Checkov first-scan criterion. Phase 4 owns the pipeline
integration and persistence tests for FR-G-01, FR-G-06, and FR-G-07.

---

## 2026-09-27 — Phase 1/2 follow-up — Rate-limit hints and architect corrections

**Summary:** LLM adapters now fall back from an unusable `retry-after` to
the larger parseable token or request reset duration and log only the
parsed wait and recognized header names. Architect prompt version 2
clarifies the roles of services, storage and file types; plan validation
now gives specific corrections when dependencies name storage or tools.

**Requirements addressed:** FR-A-01, FR-A-02, FR-A-04, PR-05, NFR-01.

**Files:** changed `backend/app/llm/errors.py`, `base.py`, `anthropic.py`,
`openai.py`, `backend/app/agents/prompts/architect.py`,
`backend/app/domain/plan.py`, their unit tests, the committed offline
stub report under `docs/evals/`, and `docs/design-deviations.md` (D-09,
D-11).

**Decisions:** D-09 now accepts finite nonnegative numeric seconds and
durations such as `7.66s`, `1m2.5s`, and `250ms`. A valid `retry-after`
takes precedence; otherwise the larger valid reset hint wins. The
existing deadline cap is unchanged. Per-attempt logs show the parsed
wait and fixed header names, never header values. D-11 records prompt
version 2 and actionable dependency-reference feedback. The stub report
was refreshed with explicit settings and `.env` loading disabled.

**Tests:** Before each of the three commits, `make lint` passed: Ruff
check, Ruff format check (69 app/test files), and mypy (43 source files).
`make test` was attempted before each commit but stopped at the Alembic
migration because PostgreSQL refused the connection at 127.0.0.1:5432;
pytest did not start. `make up` failed because Docker is unavailable in
this WSL distro, and the Windows Docker executable could not connect.
The offline unit suite passed after each code change: 214 tests after
the rate-limit change and 218 after prompt v2. Tests cover all requested
duration formats, precedence, invalid values, header-name-only logs,
deadline clipping, the revised prompt, and both actionable messages.
No real API call was made.

**Known gaps / follow-ups:** The full database-backed test suite needs
PostgreSQL or Docker Desktop WSL integration restored. The author's real
Groq run informed these changes but was not repeated in this task.

---

## 2026-09-27 — Phase 2 follow-up — Evaluation failure details

**Summary:** The ArchitectAgent now retains up to ten validation messages
per plan attempt for evaluation. The ArchitectAgent evaluator writes those
messages to its Markdown summary and per-case JSON, and records a safe LLM
failure category when applicable. The CLI configures redacted INFO logging
to show adapter attempt metrics on stderr.

**Requirements addressed:** FR-A-01, FR-A-04, NFR-01.

**Files:** changed `backend/app/agents/architect.py`,
`backend/scripts/eval_architect.py`, their unit tests, the committed stub
report under `docs/evals/`, `README.md`, and `docs/design-deviations.md`
(D-11).

**Decisions:** `ArchitectRunInfo.validation_errors_by_attempt` contains
only validation messages, capped at ten per attempt; the existing count
retains the full number. Every case now has a JSON report, including
failures, with the validated plan nested under `plan`. The evaluator writes
`ArchitectLLMFailure.llm_category` when present. CLI logging uses the
existing `configure_logging` redacting setup at INFO level; it logs metrics
without prompts or raw responses.

**Tests:** `make test` → 222 passed, 0 failed, 0 skipped. `make lint` →
Ruff check passed, Ruff format check passed (69 app/test files), mypy passed
(43 source files). Stub tests verify diagnostic error text in Markdown and
JSON, the ten-message cap, LLM failure category, CLI logger setup, stderr
attempt metrics, and canary redaction. The stub format example was refreshed
with explicit settings and `.env` loading disabled. No network call was made.

**Known gaps / follow-ups:** Real-provider output was not evaluated in this
task. The stored plan is validated JSON; raw provider responses and prompts
remain excluded from reports.

---

## 2026-09-27 — Phase 2 follow-up — Broader intent gate and no-call deadline test

**Summary:** Widened the deterministic infrastructure-intent gate to accept
realistic descriptions that omit product-specific cloud terms. Added a
deadline regression test that checks the stub receives no second prompt
when fewer than one second remains after an invalid first plan.

**Requirements addressed:** FR-I-02, FR-A-04, PR-05.

**Files:** changed `backend/app/domain/input_rules.py`,
`backend/tests/unit/test_input_rules.py`,
`backend/tests/unit/test_architect.py`, and
`docs/design-deviations.md` (CL-04).

**Decisions:** Single-word terms accept optional whole-word suffixes `s`,
`es`, `ing`, and `ed`. Added terms for stores, online platforms, serving,
scheduled jobs, applications, and WebSockets while keeping the list at 100
terms. CL-04 now states that this coarse gate favours false accepts over
false rejects. The budget test uses a fake clock: the first invalid plan
consumes 149.5 of 150 seconds, leaving too little time to start another call.

**Tests:** `make test` → 218 passed, 0 failed, 0 skipped. `make lint` →
Ruff check passed, Ruff format check passed (69 app/test files), mypy passed
(43 source files). The new tables cover 14 accepted descriptions, six
rejected descriptions, and all four suffixes; existing intent tests still
pass. With the pre-call `remaining < 1` guard temporarily removed, the new
budget test failed as intended because the stub recorded two prompts;
after restoring the guard, it passed with exactly one prompt. No network
call was made.

**Known gaps / follow-ups:** The word list is intentionally lenient and
can accept text that merely mentions an infrastructure term. No HTTP
mapping or real-provider evaluation was added in this follow-up.

---

## 2026-09-27 — Phase 2 — Input rules and ArchitectAgent

**Summary:** Added deterministic input validation, per-run configuration,
a strict AWS deployment plan, schema-derived prompts, an agent-wide budget,
the ArchitectAgent and factory, and a sequential evaluation runner. The
offline stub report covers five cases and an invalid-then-valid correction.

**Requirements addressed:** FR-I-01, FR-I-02, FR-I-04, FR-A-01,
FR-A-02, FR-A-03, FR-A-04, partial preparation for FR-A-05, PR-05,
NFR-01, NFR-03, UC-01.

**Files:** added `backend/app/domain/input_rules.py`, `run_config.py`,
`plan.py`, `backend/app/agents/*`, `backend/scripts/eval_architect.py`,
eight new unit test modules, and the stub report under `docs/evals/`;
changed `backend/app/domain/models.py`, `app/core/config.py`,
`app/llm/base.py`, `app/llm/stub.py`, existing unit and canary tests,
`.env.example`, `Makefile`, `README.md`, and `docs/design-deviations.md`.

**Decisions:** D-10 makes the plan strict and limits compact UTF-8 JSON to
32,768 bytes; D-11 records the versioned schema-derived correction prompt.
CL-04 sets validation order to controls, length, then intent. CL-05 replaces
the nine-character `a web app` example with `build a web app`. OQ-05 is
resolved by passing the agent's remaining budget into each call, where the
Phase 1 policy may impose a shorter deadline. A valid call result is returned
after validation without a second budget check. The evaluation loads fixture
scripts into the factory-created stub adapter through its public method;
the fixtures remain outside `app/`.

**Tests:** `make test` → 193 passed, 0 failed, 0 skipped. `make lint` →
Ruff check passed, Ruff format check passed (69 app/test files), mypy passed
(43 source files). `make eval-architect EVAL_ARGS='--provider stub'` produced
five passing case reports and a passing correction diagnostic. New tests
cover input boundaries and precedence, schema and graph failures, prompt
tag neutralization, shared deadlines and near-deadline success, correction
feedback, factory overrides, post-construction stub scripting, and report
format. No network call was made.

**Known gaps / follow-ups:** HTTP 400/422 mapping, run persistence and
`plan_created` events, generators, and real-provider evaluation belong to
later phases. On a permanent LLM failure after possible internal retries,
the Phase 1 error does not expose the exact transport attempt count;
`ArchitectRunInfo.total_llm_attempts` is `None` rather than an invented
number. The schema requires an `ambiguities` field, but the completeness of
an LLM's ambiguity notes remains a semantic evaluation question. OQ-03 and
OQ-06 remain open pending the author's provider choice and measurements.

---

## 2026-09-26 — Phase 1 follow-up — Rate-limit retry and real timing result

**Summary:** Both LLM adapters now carry parsed `retry-after` seconds on
HTTP 429 into the shared retry wrapper. Recorded the author's real Groq
timing spike and the free-tier throughput limit it exposed.

**Requirements addressed:** FR-A-04, PR-05, NFR-01.

**Files:** changed `backend/app/llm/errors.py`, `base.py`, `anthropic.py`,
and `openai.py`; changed `backend/tests/unit/test_llm_base.py` and
`test_llm_providers.py`; changed `docs/design-deviations.md`; added the
metrics-only real-provider JSON and Markdown files under `docs/spikes/`.

**Decisions:** D-09 respects a finite nonnegative `retry-after` value in
seconds on 429, taking the greater of that delay and jittered backoff.
If the delay consumes the remaining call budget, the wrapper raises
`LLMDeadlineExceeded` without sleeping. Invalid or missing headers fall back
to ordinary backoff; raw header text is neither retained nor logged. OQ-03
records the 2026-09-26 Groq free-tier spike: one full call finished in
24.6 s with 11,660 output tokens, while all nine split calls were rate
limited. OQ-06 defers evaluation-provider throughput choice.

**Tests:** Before the first commit, `make test` → 137 passed, 0 failed,
0 skipped; `make lint` → Ruff check passed, Ruff format check passed
(52 app/test files), mypy passed (34 source files). Deterministic
`httpx2.MockTransport` tests cover both providers' 429 headers, a 20-second
delay before success, deadline rejection without sleep, and fallback for
missing or invalid headers. Both commands were rerun before the second
commit with the same results.

**Known gaps / follow-ups:** The real spike is one measurement on Groq's
free tier. OQ-03 remains open until the evaluation provider is selected;
OQ-06 requires enough token throughput for parallel generation. No real API
call was made by Codex.

---

## 2026-09-26 — Phase 1 follow-up — OpenAI-compatible base URL

**Summary:** Added optional `LLM_BASE_URL` so the existing OpenAI adapter can
send Chat Completions requests to a compatible endpoint without a new
provider class. The unset value keeps the SDK's default endpoint.

**Requirements addressed:** FR-I-04, NFR-03.

**Files:** changed `backend/app/core/config.py`,
`backend/app/llm/factory.py`, `backend/app/llm/openai.py`,
`backend/tests/unit/test_config.py`, `backend/tests/unit/test_llm_factory.py`,
`.env.example`, `README.md`, and `docs/design-deviations.md`.

**Decisions:** D-08 documents this endpoint override. Empty
`LLM_BASE_URL` is treated as unset, matching the optional model and key
settings. Only `OpenAIAdapter` receives the override. The README Groq
example uses the endpoint and model documented by Groq; no real key was
used.

**Tests:** `make test` → 121 passed, 0 failed, 0 skipped. `make lint` → Ruff
check passed, Ruff format check passed (52 app/test files), mypy passed
(34 source files). New tests verify the optional setting and the final SDK
request URL through `httpx2.MockTransport`, both with and without an
override.

**Known gaps / follow-ups:** No real OpenAI-compatible provider was called;
OQ-03 still awaits the author's timing measurement with a real key.

---

## 2026-09-25 — Phase 1 — LLM adapters and timing spike

**Summary:** Added the provider-independent async JSON completion wrapper,
Anthropic/OpenAI/Stub adapters, configuration factory, offline provider and
retry tests, and a timing spike with full/split and truncation reporting.
No agent or pipeline behavior was added.

**Requirements addressed:** NFR-01, NFR-03, FR-I-04; partial timing evidence
for FR-A-04 and PR-05 at the single-call boundary.

**Files:** added `backend/app/llm/*`, `backend/scripts/*`, four Phase 1 unit
test modules, and a stub JSON/Markdown pair under `docs/spikes/`; changed
`AGENTS.md`, `backend/pyproject.toml`, `backend/requirements.lock`,
`backend/app/core/config.py`, `backend/tests/unit/test_config.py`,
`backend/tests/integration/test_canary.py`, `.env.example`, `Makefile`,
`README.md`, and `docs/design-deviations.md`.

**Decisions:** D-07 adds concrete `complete_json` while keeping exactly two
abstract provider methods. The installed SDKs are Anthropic 1.8.0 and OpenAI
3.19.2; both use `httpx2` custom transports, so `httpx2` is an explicit
runtime dependency for adapter type signatures and offline mocks. Phase 0's
`httpx` remains installed and unaliased. OpenAI 3.19.2 has Chat Completions,
so no Responses API deviation was needed. Anthropic Messages sends no
`temperature`, `top_p`, or `top_k`. CL-03 resolves contradictory retry
arithmetic. The spike includes Dockerfile, missing from the prompt's workload
list but present in the spec. OQ-03 awaits a real-provider measurement; OQ-05
defers the end-to-end agent deadline to Phase 2. The spike's
`--max-output-tokens` defaults to the configured 16000 and its verdict fails
when calls truncate.

**Tests:** `make install` succeeded with the regenerated lock. `make spike`
with `LLM_PROVIDER=stub` produced the committed format example (3 full calls
and 27 split calls). `make test` → 118 passed, 0 failed, 0 skipped. `make lint`
→ Ruff check passed, Ruff format check passed (52 app/test files), mypy passed
(34 source files). New tests in `test_llm_base.py`, `test_llm_providers.py`,
`test_llm_factory.py`, and `test_spike_llm_timing.py` cover retries, deadlines,
strict parsing, both SDK status and transport-error mappings with
`httpx2.MockTransport`, factory
selection, spike output, and truncation. The existing canary module now tests
both SDKs with a canary in mocked 401 headers and bodies.

**Known gaps / follow-ups:** The stub example is only a format check; the
author must run the spike with a real key to assess OQ-03. The 150-second
wrapper deadline applies to one `complete_json` call; Phase 2 must design
the stage-wide agent budget (OQ-05). No real API call was made.

---

## 2026-09-25 — Phase 0 — Harden concurrency and privilege tests, pin dependencies

**Summary:** Made the event prefix test sensitive to loss of the PostgreSQL
advisory lock, required the exact insufficient-privilege SQLSTATE in denied
operation tests, pinned installed dependencies, and made the PostgreSQL init
script executable.

**Requirements addressed:** FR-P-04, NFR-01.

**Files:** changed `backend/tests/integration/test_events.py`,
`backend/tests/integration/test_privileges.py`, `Makefile`, `README.md`, and
`docker/postgres/init/01-roles-and-databases.sh` (mode 100755); added
`backend/requirements.lock`.

**Decisions:** The three prefix-test writers share a seeded random generator
(`23`) and hold each inserted event for up to 5 ms before commit. The
`TRUNCATE` check covering `pipeline_runs` names all three tables so a foreign
key cannot explain its failure; each denied statement must yield SQLSTATE
`42501`. `make install` uses the frozen versions as pip constraints.

**Tests:** With the advisory-lock query temporarily changed to `SELECT 1`,
the prefix test failed on 3 of 3 runs; after restoration, it passed on 3 of
3 runs. `make install` succeeded with the constraints file. `make test` →
63 passed, 0 failed, 0 skipped. `make lint` → Ruff check passed, Ruff format
check passed (41 files), mypy passed (27 source files).

**Known gaps / follow-ups:** None for this review fix. No new specification
deviation or open question was introduced.

---

## 2026-09-25 — Phase 0 — Foundations implemented

**Summary:** Built the Python backend foundation, PostgreSQL schema and
least-privilege roles, durable event log, retention command, and health API.
No agent, LLM, SSE, download, or frontend feature is present yet.

**Requirements addressed:** FR-S-03, FR-S-05, FR-S-07, FR-S-09, FR-V-05,
FR-G-07, FR-P-04, FR-UI-06, NFR-01.

**Sections and files:**
1. Repository layout: added backend package directories and frontend
   placeholder; extended `.gitignore` while retaining its existing entries.
2. Dependencies: added `backend/pyproject.toml` with only approved packages.
3. Database setup: added `docker-compose.yml`, the PostgreSQL init script,
   `.env.example`, and `Makefile`.
4. Configuration: added `app/core/config.py` and its unit tests.
5. Logging: added `app/core/logging.py` and redaction tests.
6. Errors and health: added the app factory, safe error handler, health route,
   and resource accessor with unit tests.
7. Domain: added enums, transition tables, remediation-budget decision,
   path rules, value objects, and corresponding unit tests.
8. Database: added Alembic configuration and initial migration, SQLAlchemy
   models and repositories, test fixtures, migration-parity and PostgreSQL
   integration tests, including a two-session stale-state transition check.
9. Events: added `EventLog`, publisher types, app-owned instance, and
   concurrency, replay, publication, and singleton tests.
10. Retention: added `app/cli.py` and integration coverage for dry-run and
    package-only deletion.
11. Acceptance: added real-database health and secret-canary tests and ran
    the full suite.
12. Documentation: updated this log, `README.md`, and
    `docs/design-deviations.md`.

**Decisions:** D-01 to D-06 and CL-01 are implemented as described in the
deviation log. CL-02 resolves FR-S-07 sequencing: stop remediation, validate,
then enter review. Application code uses one EventLog instance per process;
database ordering still holds across independent writers. App-role identity
insertion succeeded without a sequence grant, so none was added. Run status
is classified at automated completion and remains terminal during review.

**Tests:** `make test` → 63 passed, 0 failed, 0 skipped; `make lint` → Ruff
check passed, Ruff format check passed (41 files), mypy passed (27 source
files). `make install`, `make migrate`, and `make migrate-test` succeeded.
`make run` served `/api/health` with HTTP 200, `database: ok`, and
`llm_configured: false`. `make sweep` completed with 0 packages deleted.

**Known gaps / follow-ups:** The Phase 0 boundary excludes agent logic,
real LLM calls, SSE, review/download endpoints, ZIP writing, and frontend
code. OQ-01, OQ-03, and OQ-04 remain for their later phases.

---

## 2026-09-25 — Phase 0 (setup) — Repository initialised

**Summary:** Repository created with specification (`docs/spec/`), agent
instructions (`AGENTS.md`), this log, and the design-deviation log seeded with
decisions agreed during design review. The spec includes the redrawn
diagrams (package states, run states, sequence, ERD, class diagram), which
now agree with the chapter text.

**Requirements addressed:** none — infrastructure.

**Files:** added `AGENTS.md`, `docs/IMPLEMENTATION_LOG.md`,
`docs/design-deviations.md`, `docs/spec/*`.

**Decisions:** See D-01 to D-06, CL-01 and OQ-01 to OQ-04 in
`docs/design-deviations.md`. OQ-02 is resolved by Option C. D-01 to D-03,
D-05 and D-06 are already part of the thesis design.

**Tests:** none yet.

**Known gaps / follow-ups:** Phase 0 implementation.
