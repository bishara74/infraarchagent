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
