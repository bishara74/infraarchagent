# Codex task — Phase 0: Foundations

Read `AGENTS.md`, `docs/design-deviations.md` and `docs/IMPLEMENTATION_LOG.md`
first. The specification is in `docs/spec/` (thesis Chapter 3 Requirements,
Chapter 4 Design, and the diagrams). This task is **Phase 0 only**.

## Goal

Build the foundation every later phase depends on: project structure, local
PostgreSQL, configuration, logging, the domain vocabulary and state machines,
the database schema and repositories, the event log with guaranteed per-run
ordering, the package retention sweep, and a health endpoint. There is no
agent logic, no LLM calls, no SSE endpoint and no frontend code in this phase.

## Definition of done

- `make up && make install && make migrate && make test && make lint` all
  succeed on a machine with only Docker and Python 3.11+.
- `make run` starts the API, and `GET /api/health` returns 200 with no LLM
  key set.
- Every acceptance test listed in section 10 exists and passes.
- `docs/IMPLEMENTATION_LOG.md`, `docs/design-deviations.md` and `README.md`
  are updated as described in `AGENTS.md` §8.

Work in this order, and commit after each numbered section (see `AGENTS.md`
§9).

---

## 1. Repository layout

```
.
├── AGENTS.md
├── README.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docker/postgres/init/01-roles-and-databases.sh
├── docs/  (spec/, IMPLEMENTATION_LOG.md, design-deviations.md — already exist)
├── frontend/.gitkeep
└── backend/
    ├── pyproject.toml
    ├── alembic.ini
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── cli.py
    │   ├── api/{__init__.py, health.py}
    │   ├── core/{__init__.py, config.py, logging.py, errors.py}
    │   ├── domain/{__init__.py, enums.py, states.py, paths.py, models.py}
    │   ├── db/{__init__.py, base.py, models.py, session.py}
    │   ├── db/repositories/{__init__.py, runs.py, packages.py}
    │   ├── db/migrations/{env.py, script.py.mako, versions/0001_initial_schema.py}
    │   └── events/{__init__.py, log.py, publisher.py}
    └── tests/
        ├── conftest.py
        ├── unit/ ...
        └── integration/ ...
```

## 2. Dependencies (approved list; add nothing else without justification)

Runtime: `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `pydantic-settings`,
`sqlalchemy[asyncio]>=2.0`, `asyncpg`, `alembic`.
Dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`.
Python `>=3.11`. Use `pyproject.toml` with a `[project.optional-dependencies]
dev` group, installed with `pip install -e ".[dev]"`.

## 3. Docker, database roles and Makefile

- `docker-compose.yml`: a single `postgres:16` service, port 5432, a named
  volume, and a healthcheck. Credentials come from `.env` (see
  `.env.example`).
- The init script (runs on an empty volume only) creates:
  - roles `infraarch_owner` (LOGIN) and `infraarch_app` (LOGIN);
  - databases `infraarch` and `infraarch_test`, both owned by
    `infraarch_owner`;
  - `REVOKE ALL ON DATABASE ... FROM PUBLIC`, then `GRANT CONNECT` to both
    roles.
- Table privileges are granted in the Alembic migration, not the init script,
  so they are versioned with the schema.
- Makefile targets: `up`, `down`, `install`, `migrate`, `migrate-test`, `run`,
  `test` (runs `migrate-test` first), `lint`, `sweep`. `make test` must work
  from a clean database.

## 4. Configuration (`app/core/config.py`)

Use `pydantic-settings`, reading from environment variables and `.env`:

| Variable | Type | Default | Notes |
|---|---|---|---|
| `DATABASE_URL` | str | — | asyncpg URL for **infraarch_app** |
| `MIGRATION_DATABASE_URL` | str | — | URL for **infraarch_owner** (Alembic only) |
| `TEST_DATABASE_URL` / `TEST_MIGRATION_DATABASE_URL` | str | — | used by tests |
| `LLM_PROVIDER` | `anthropic` \| `openai` \| `stub` | `stub` | |
| `LLM_MODEL` | str \| None | None | |
| `LLM_API_KEY` | `SecretStr \| None` | None | **optional**; only required when a real adapter is built (later phase) |
| `MAX_REMEDIATION_ITERATIONS` | int ≥ 1 | 3 | |
| `PACKAGE_RETENTION_DAYS` | int ≥ 1 | 30 | |
| `LOG_LEVEL` | str | `INFO` | |

- Database URLs contain passwords, so treat them as secrets too: store them as
  `SecretStr` or make sure `repr()` and logs never show the password.
- Add a helper `require_llm_key()` that raises a clear configuration error if
  the key is missing. Nothing in Phase 0 calls it except its own test.

## 5. Logging (`app/core/logging.py`)

- A `logging.Filter` installed on the root handler that redacts:
  - the exact configured `LLM_API_KEY` value (exact match, strongest rule);
  - patterns `sk-ant-[A-Za-z0-9_\-]{8,}` and `sk-[A-Za-z0-9_\-]{16,}`;
  - `Bearer <token>`;
  - passwords inside `postgresql://user:password@host` URLs.
- Redaction must apply to the formatted message, including `args` and
  exception text.
- SQLAlchemy `echo` is off.

## 6. Errors and health (`app/core/errors.py`, `app/api/health.py`, `app/main.py`)

- App factory `create_app()`. The global exception handler returns
  `{"error": "internal_error", "request_id": "<uuid>"}` with status 500, logs
  the exception server-side (redacted), and never includes exception text in
  the response.
- `GET /api/health`:
  - 200 `{"status": "ok", "database": "ok", "llm_configured": <bool>}` when
    `SELECT 1` succeeds as the app role;
  - 503 `{"status": "degraded", "database": "unavailable",
    "llm_configured": <bool>}` when the database is unreachable;
  - must work with no LLM key set.
- Do **not** add a custom 400 handler for FR-I-01 yet; that belongs to
  Phase 2.

## 7. Domain layer (`app/domain/`), pure Python with no DB or API imports

### 7.1 Enums (`enums.py`), `StrEnum`, values exactly as below

- `RunStatus`: `created, running, success, partial_success, failed`
- `PackageStatus`: `generating, generated, failed, scanning, remediating,
  scan_clean, scan_exhausted, scan_error, validating, valid, invalid,
  validation_error, pending_review, production_ready, not_production_ready`
- `Variant`: `cost, performance, security`
- `LLMProvider`: `anthropic, openai, stub`
- `AgentName`: `orchestrator, architect, generator_cost,
  generator_performance, generator_security, security, validator`
- `AgentState`: `pending, running, completed, failed`
- `ReviewAction`: `approve, retry, reject`

### 7.2 State machines (`states.py`)

Implement explicit transition tables and an `assert_transition(current,
target)` function for each machine. It raises `IllegalTransition` (a domain
exception carrying both states).

**Run:**
```
created  -> running
running  -> success | partial_success | failed
success, partial_success, failed: terminal
```

**Package (Option C: automatic `production_ready` only for a clean scan AND
passing validation; every other outcome that produces a package goes to
engineer review):**
```
generating       -> generated | failed
generated        -> scanning
scanning         -> remediating | scan_clean | scan_error
remediating      -> scanning | scan_exhausted
scan_clean       -> validating
scan_exhausted   -> validating
validating       -> valid | invalid | validation_error
valid            -> production_ready | pending_review
invalid          -> pending_review
validation_error -> pending_review
pending_review   -> production_ready | not_production_ready | remediating
terminal: failed, scan_error, production_ready, not_production_ready
```
- The iteration limit is checked in `remediating`, matching the package
  state diagram (CL-01). If the budget is used up, the package moves to
  `scan_exhausted` without applying a fix; otherwise a fix pass is applied,
  `iteration_count` is incremented, and it returns to `scanning`.
- `pending_review -> remediating` is the review retry path (FR-S-09).
- `invalid` and `validation_error` are intermediate states. They are
  recorded as events and later shown as the *reason* a package needs
  review, but a package never ends in them (D-06).

Also implement these helpers:
- `readiness_after_validation(scan_outcome, validation_outcome) ->
  PackageStatus`:
  - `scan_clean` + `valid` → `production_ready`;
  - any other combination of `scan_outcome` in {`scan_clean`,
    `scan_exhausted`} and `validation_outcome` in {`valid`, `invalid`,
    `validation_error`} → `pending_review`;
  - any other input raises `ValueError`.
- `review_reasons(scan_outcome, validation_outcome) -> list[str]`: returns
  machine-readable reasons (`"unresolved_violations"`,
  `"validation_failed"`, `"validation_unavailable"`); empty for
  `production_ready`. The UI uses these in Phase 8.
- `is_settled(status)`: true for terminal states and for `pending_review`.
- `is_downloadable(status)`: true **only** for `production_ready` and
  `not_production_ready` (FR-UI-06). False for `pending_review` and every
  other state.
- `classify_run(architect_succeeded: bool, packages: Mapping[Variant,
  PackageStatus | None]) -> RunStatus`. It raises if any package is not
  settled. Rules, in order:
  1. The Architect failed → `failed`.
  2. "Available" means the package is not `None`, not `failed`, and not
     `scan_error`. No available packages → `failed`.
  3. All three variants are present and all are `production_ready` →
     `success`.
  4. Otherwise → `partial_success`.

### 7.3 Paths (`paths.py`)

`validate_relative_path(path: str) -> str` returns the normalised path or
raises `UnsafePathError`. A path is rejected if it:
- is empty;
- is absolute, or starts with `/`;
- starts with a Windows drive letter (`C:`);
- contains a backslash or a NUL byte;
- contains a `..`, `.` or empty segment (so `a//b` is rejected);
- uses characters outside `[A-Za-z0-9._\-/]`;
- is longer than 255 characters or deeper than 8 segments.

Also add `validate_file_map(files: Mapping[str, str])`, which validates every
path and rejects case-insensitive duplicates (e.g. `Main.tf` and `main.tf`).
Content must be `str`.

### 7.4 Value objects (`models.py`), Pydantic models, immutable where practical

- `Violation`: `rule_id, severity, file_path, resource, message, tool
  (checkov|tfsec)`, plus `fingerprint()` returning a stable
  `(rule_id, file_path, resource)` key.
- `DeploymentPlan`: fields per the spec (services, dependencies, network,
  storage, file_types, ambiguities). Keep it permissive in Phase 0; Phase 2
  tightens it.
- `IaCPackage`: `variant, files, security_report, validation_report`. Files
  are validated with `validate_file_map` at construction. `to_zip()` is
  **not** implemented in Phase 0, but the ZIP writer in Phase 7 must call
  `validate_relative_path` again.

## 8. Database (`app/db/`)

### 8.1 Migration `0001_initial_schema` (run as `infraarch_owner`)

**pipeline_runs**

| Column | Type / constraint |
|---|---|
| `run_id` | UUID PK |
| `input_text` | TEXT NOT NULL |
| `status` | VARCHAR(32) NOT NULL, CHECK in RunStatus values |
| `start_time` | TIMESTAMPTZ NOT NULL |
| `end_time` | TIMESTAMPTZ NULL |
| `llm_provider` | VARCHAR(32) NOT NULL, CHECK in LLMProvider values |
| `model` | VARCHAR(128) NULL |
| `max_iterations` | INTEGER NOT NULL, CHECK ≥ 1 |
| `error_message` | TEXT NULL |

Index on `start_time`.

**generated_packages**

| Column | Type / constraint |
|---|---|
| `package_id` | UUID PK |
| `run_id` | UUID NOT NULL, FK → `pipeline_runs.run_id` **ON DELETE RESTRICT** |
| `variant` | VARCHAR(16) NOT NULL, CHECK in Variant values |
| `files` | JSONB NOT NULL DEFAULT `'{}'`, CHECK `jsonb_typeof(files) = 'object'` |
| `security_report` | JSONB NULL |
| `validation_report` | JSONB NULL |
| `remediation_diff` | TEXT NULL |
| `iteration_count` | INTEGER NOT NULL DEFAULT 0, CHECK ≥ 0 |
| `status` | VARCHAR(32) NOT NULL, CHECK in PackageStatus values |
| `review_feedback` | TEXT NULL |
| `error` | TEXT NULL |
| `created_at` | TIMESTAMPTZ NOT NULL |

UNIQUE `(run_id, variant)`. Index on `created_at` (for retention).

**agent_events**

| Column | Type / constraint |
|---|---|
| `event_id` | UUID PK |
| `seq` | BIGINT GENERATED ALWAYS AS IDENTITY (**CACHE 1**), UNIQUE, NOT NULL |
| `run_id` | UUID NOT NULL, FK → `pipeline_runs.run_id` **ON DELETE RESTRICT** |
| `agent_name` | VARCHAR(32) NOT NULL, CHECK in AgentName values |
| `previous_state` | VARCHAR(32) NULL |
| `new_state` | VARCHAR(32) NOT NULL |
| `timestamp` | TIMESTAMPTZ NOT NULL |
| `message` | TEXT NULL |
| `payload` | JSONB NOT NULL DEFAULT `'{}'`, CHECK object |

Index on `(run_id, seq)`.

- `CACHE 1` is required. With a larger cache, sessions pre-allocate values and
  per-run ordering breaks. Add a comment explaining this.
- CHECK constraints are generated from the Python enums in the migration file,
  written out literally. Add a unit test asserting that the migration's
  literal lists equal the enum values, so they cannot drift.

**Privileges** (end of the migration):
- `REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC`
- `GRANT USAGE ON SCHEMA public TO infraarch_app`
- `pipeline_runs`: SELECT, INSERT, UPDATE → `infraarch_app` (**no DELETE**)
- `agent_events`: SELECT, INSERT → `infraarch_app` (**no UPDATE, no DELETE**)
- `generated_packages`: SELECT, INSERT, UPDATE, DELETE → `infraarch_app`
- No TRUNCATE for the app role. Grant sequence USAGE only if identity inserts
  require it; verify this with the tests.

`downgrade()` drops everything cleanly.

### 8.2 Session (`session.py`)

Async engine and `async_sessionmaker` built from settings, with a separate
factory for the owner URL that is used only by migrations and test setup.

### 8.3 Repositories

- `RunRepository`: `create(...)`, `get(run_id)`, `set_status(run_id,
  target)`. `set_status` loads the current status, calls
  `assert_transition`, and updates with a row lock (`SELECT ... FOR
  UPDATE`). It sets `end_time` when the run reaches a terminal state.
  **There is no delete method.**
- `PackageRepository`: `create(run_id, variant)` (status `generating`),
  `get(run_id, variant)`, `list_for_run(run_id)`, `set_status(...)` (same
  locking and transition rules), `save_files(...)` (validates the file map),
  and `delete_expired(now: datetime, retention_days: int, dry_run: bool) ->
  int`. `delete_expired` deletes **only** from `generated_packages` where
  `created_at < now - retention_days`.

## 9. Event log (`app/events/`)

### 9.1 Publisher (`publisher.py`)

A `Publisher` Protocol with `async def publish(event: EventRecord) -> None`,
plus two implementations: `NullPublisher` and `RecordingPublisher`, which
stores published events for tests. The real broker arrives in Phase 4.

### 9.2 `EventLog.append(...)` (`log.py`)

`EventLog.append(run_id, agent_name, new_state, previous_state=None,
message=None, payload=None) -> EventRecord`. This is the **only** code path
that inserts into `agent_events`. The protocol is mandatory and must follow
this exact order:

1. Acquire the per-run `asyncio.Lock`. Keep locks in a
   `weakref.WeakValueDictionary` keyed by run id so the map does not grow
   without bound.
2. Begin a transaction.
3. `SELECT pg_advisory_xact_lock(hashtextextended(:run_id, 0))`. This must
   happen **before** the INSERT.
4. `INSERT ... RETURNING event_id, seq`, with `timestamp =
   datetime.now(UTC)` set by the application.
5. `COMMIT`, which releases the advisory lock.
6. Only after the commit succeeds, `await publisher.publish(record)`. If
   publishing raises, log it (redacted) and return the record anyway: the
   event is durable, and subscribers recover it through replay.
7. Release the asyncio lock.

Validation before inserting:
- `new_state` and `previous_state` must be values of `RunStatus`,
  `PackageStatus` or `AgentState`.
- `payload` must be a JSON-serialisable dict, at most 64 KB when serialised.

Add `EventLog.list_after(run_id, after_seq: int | None) -> list[EventRecord]`,
ordered by `seq`. It is used by the prefix test now and by SSE replay in
Phase 4.

**Documented guarantee (write this as the module docstring):** per run,
commit order equals `seq` order, provided every writer uses `append()`.
`seq` values for one run are increasing but **not consecutive**, because
other runs draw from the same identity. Publish order equals `seq` order
within a single process.

## 10. Retention CLI (`app/cli.py`)

`python -m app.cli sweep-packages [--days N] [--dry-run]` calls
`PackageRepository.delete_expired` as the app role and prints the number of
packages deleted (or that would be deleted). It never touches runs or
events. `make sweep` wraps it.

## 11. Tests (all must exist and pass)

### Test infrastructure (`tests/conftest.py`)

- Session-scoped: run Alembic upgrade on the test database using the owner
  URL.
- Per test: truncate all three tables **using the owner connection** (the app
  role cannot, by design).
- Code under test uses the **app-role** engine.
- Register the `req` marker in `pyproject.toml`.
- A canary fixture sets `LLM_API_KEY=sk-ant-api03-CANARY-7f3c9e2a1b4d5e6f`
  and resets settings caches.

### Unit tests

1. **Run state machine.** Every allowed edge passes, and a representative set
   of illegal edges raises `IllegalTransition`. Terminal states have no
   outgoing edges.
2. **Package state machine.** Same as above, plus:
   - the full retry path `scanning → remediating → scanning → remediating →
     scan_exhausted → validating → valid → pending_review → remediating →
     scanning → scan_clean → validating → valid → production_ready`;
   - the validation-failure path `scan_clean → validating → invalid →
     pending_review → not_production_ready`.

   Mark it `req("FR-S-07","FR-S-09")`. Assert that `validation_error →
   production_ready` and `scanning → scan_exhausted` are illegal (CL-01).
3. **Package state helpers** (Option C). Cover all six scan/validation
   combinations of `readiness_after_validation`. **Include
   `scan_clean` + `validation_error` → `pending_review`** (the old diagram
   wrongly made this `production_ready`) and `scan_clean` + `invalid` →
   `pending_review`. Also test `review_reasons` for each combination, and
   that `is_downloadable` is false for `pending_review`, `invalid` and
   `validation_error` (`req("FR-UI-06","FR-V-05","FR-S-07")`). Assert that
   `invalid` and `validation_error` are not terminal.
4. **`classify_run`.** Covers every rule: Architect failure, zero available
   packages, all `scan_error`, three `production_ready`, one `failed`
   generator, one `pending_review`, and an unsettled package raising an
   error.
5. **Path validation.** A table of accepted and rejected inputs, including
   `../x`, `a/../b`, `/etc/passwd`, `C:/x`, `a\\b`, `a//b`, `./a`, NUL, a
   256-character path, 9-level depth, and case-insensitive duplicates.
6. **Log redaction.** The exact key, both key patterns, a Bearer token and a
   DB URL password are all redacted. This includes values passed as `args`
   and inside exception text.
7. **Migration and enum parity.** The CHECK literals in the migration equal
   the Python enum values.

### Integration tests (real PostgreSQL)

8. **Repository round trip.** Create a run, then packages with a file map,
   then events; read them back and verify that timestamps are tz-aware UTC.
9. **Invalid values rejected.** An invalid status string is rejected by the
   database CHECK when inserted directly as the owner.
10. **Illegal transitions.** An illegal transition through the repository
    raises, and the database is left unchanged.
11. **Privileges** (`req("NFR-01")`), all as the app role:
    - `DELETE FROM pipeline_runs` fails with insufficient privilege;
    - `UPDATE agent_events` and `DELETE FROM agent_events` fail;
    - `TRUNCATE` on any table fails;
    - `DELETE FROM generated_packages` succeeds.
12. **RESTRICT.** As the owner, deleting a run that has events fails with a
    foreign-key violation.
13. **Retention sweep.** One package older than 30 days and one fresh.
    `delete_expired` removes only the old one. The run row and all its events
    still exist afterwards, and `--dry-run` deletes nothing.
14. **Advisory lock (deterministic).** Transaction A takes the advisory lock
    and inserts, but does not commit. Writer B starts appending to the same
    run. Assert B has **not** inserted within 300 ms. Commit A, then B
    completes and `B.seq > A.seq`. Use the lower-level pieces of `EventLog`,
    or a test hook, so that A can be held open.
15. **Prefix property** (`req("FR-P-04")`):
    - Two separate `EventLog` instances (so the asyncio locks are **not**
      shared and only the advisory lock serialises them) append 200 events
      to run R.
    - A third writer appends events to another run S at the same time, so
      that R's `seq` values have gaps.
    - Meanwhile a reader repeatedly snapshots `list_after(R, None)`.
    - Assert every snapshot's list of `event_id`s is a **prefix of R's final
      committed event list**, and that `seq` is strictly increasing within
      each snapshot.
    - Do **not** assert that `seq` values are consecutive.
    - Use a fixed random seed.
16. **Publish after commit.** A publisher that, on each `publish`, queries the
    database through a separate connection and asserts the event is already
    visible.
17. **Publish failure.** A publisher that raises: `append` still returns, the
    event is in the database, and the error is logged with the key redacted.
18. **Health.** 200 with no LLM key. 503 when the engine points to an
    unreachable database (override the dependency).
    `llm_configured` reflects the settings.
19. **Canary, NFR-01** (`req("NFR-01")`). With the canary key set:
    - exercise `/api/health`, a forced 500 route (added to the app instance
      in the test only), logging of the settings object, and repository and
      event writes;
    - then assert the canary string appears in none of: captured log
      output, any response body, `repr(settings)`, or any database row
      (`SELECT t::text FROM <table> t` for all three tables).

## 12. Documentation (required, see `AGENTS.md` §8)

- **`README.md`:** prerequisites, setup commands, environment variables
  table, how to run tests, and the two-role database explanation (short).
- **`docs/IMPLEMENTATION_LOG.md`:** one entry per numbered section above, or
  one consolidated Phase 0 entry with a subsection for each, including real
  test counts.
- **`docs/design-deviations.md`:** add an "Implemented in Phase 0" line to each of D-01 to D-06 and CL-01, and
  record anything new you had to decide, e.g. whether identity inserts
  needed a sequence grant.

## 13. Out of scope for Phase 0 — do not build

- LLM adapters.
- Agents and prompts.
- Orchestrator.
- SSE endpoint and broker.
- Pipeline, results, review and download endpoints.
- ZIP writing.
- Checkov, tfsec and Terraform.
- The 400/422 input handling.
- HTTP 410 (see OQ-01).
- Frontend code.
- Dockerfile for the backend (Phase 10).

Finish with the summary format from `AGENTS.md` §10.
