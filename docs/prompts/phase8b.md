# Codex task — Phase 8b: `make test` cannot load settings after Phase 8

Fresh session. Read `AGENTS.md`, the latest Phase 8 entries in
`docs/IMPLEMENTATION_LOG.md`, and D-40/D-41 in `docs/design-deviations.md`.
This is a **bug investigation and fix only**.

## Rules

- **Do not open, print, copy or modify `.env`.** You may list setting
  *names* only if strictly needed (`grep -oE '^[A-Z_]+' .env`), never values.
- No installs, no real LLM calls, no push.
- Fix the cause, not the symptom: don't add database URLs to code,
  defaults, `.env.example` values, or the Makefile.
- One or two commits prefixed `phase8b:`, each with an implementation-log
  entry.

## Symptom (on the author's machine, after Phase 8)

In a terminal, `make up` then `make test` fails at the first step
(`make migrate-test` → `alembic -x database=test upgrade head`):

```
app/db/migrations/env.py:22 migration_url -> get_settings() -> Settings()
pydantic ValidationError: 4 validation errors for Settings
database_url / migration_database_url / test_database_url /
test_migration_database_url: Field required
  [input_value={'llm_provider': 'stub', ... 'x_reasoning_effort': ''}]
```

So `Settings()` received **some** values (`llm_provider='stub'`, an empty
`*_reasoning_effort`) but **none of the four database URLs**. Before
Phase 8 the same command worked (Phase 7b: 1,000 tests passed). Codex's own
Phase 8 run reported the suites passing, so the difference is environmental:
something that differs between Codex's verification setup and a plain
`make test` in the author's shell.

## Already checked (don't repeat; these are ruled out)

1. **The author's shell is clean.** `env` shows no `LLM_*`, `DATABASE*`,
   `MIGRATION*`, `TEST_*`, `PYTHONPATH`, `*DOTENV*`, `PIPELINE_*`,
   `SECURITY_FIX*` or `API_KEY` variables.
2. **`.env` is intact and unchanged.** Root `.env` was last modified
   2026-10-02 (before Phase 8), is git-ignored, and contains all expected
   names, including `DATABASE_URL`, `MIGRATION_DATABASE_URL`,
   `TEST_DATABASE_URL`, `TEST_MIGRATION_DATABASE_URL`, `LLM_PROVIDER`,
   `LLM_API_KEY`. There is no `backend/.env`. No test or e2e code writes a
   `.env`.
3. **The Makefile is as expected:** `migrate-test` runs
   `cd backend && .venv/bin/alembic -x database=test upgrade head`; `test`
   depends on it and runs `pytest -q -m "not perf"`.
4. **`config.py` changed only trivially in Phase 8** (commit `d355c46` added
   `pipeline_demo_scenario`). It still uses
   `SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")`, with no
   custom settings sources.

## Leading hypothesis (verify, don't assume)

Phase 8 added `backend/tests/bootstrap/sitecustomize.py` to disable dotenv
for verification runs, including Alembic subprocesses. Python imports any
`sitecustomize` it finds on `sys.path` at interpreter startup. If that
directory became part of the **venv's** path (e.g. a `.pth` file in
`backend/.venv/lib/python3.12/site-packages/`, a `sitecustomize.py` copied
into site-packages, or a `PYTHONPATH` baked into an activation script or
config), then **every** Python process in the venv (plain `alembic`,
`uvicorn` via `make run`, scripts) runs the test bootstrap: dotenv off,
stub-only values injected, no database URLs. That would match the error
exactly, and would only exist on the author's machine (the venv isn't in
git), which explains why a fresh clone passes.

## What to check

1. `python -c "import sys; m=sys.modules.get('sitecustomize'); print(getattr(m,'__file__',None))"`
   using `backend/.venv/bin/python`, from both the repo root and `backend/`.
2. Every `.pth` file and any `sitecustomize.py`/`usercustomize.py` in the venv
   and in user site-packages (`python -m site`). Report which reference
   `tests/bootstrap`.
3. How the bootstrap is wired into tests and e2e: `Makefile`, `pyproject.toml`
   (pytest options/`pythonpath`), `tests/conftest.py`, Playwright config, any
   helper that launches the backend or Alembic.
4. Read `sitecustomize.py`: what it sets, and whether it guards itself
   (e.g. acts only when an explicit test flag is present).
5. If the hypothesis is wrong, find the real reason why `Settings()` gets
   `llm_provider='stub'` but no URLs (e.g. env injected by a Make or
   subprocess wrapper, a changed `ROOT`, an `env_ignore` setting), and
   report the evidence.

## Required fix

- The test bootstrap must **never** affect normal commands. `make migrate`,
  `make migrate-test`, `make run`, `make eval-*` and plain `.venv/bin/python`
  must load `.env` exactly as before Phase 8.
- Activate the bootstrap only explicitly for the test processes that need it,
  for example by setting `PYTHONPATH` (or a dedicated env flag the bootstrap
  checks) **inside** the pytest/e2e launch for that subprocess only. Make
  `sitecustomize.py` a no-op unless its explicit flag is set, as a second
  line of defence.
- `make test` must still run all tests against the **test** database with
  ordinary roles, and the dotenv-disabled guarantees from Phase 8 still hold
  for the processes they were meant for.
- If anything was written into the venv (`.pth` file etc.), remove that
  mechanism from the code and print the **exact command** the author must
  run to clean their existing venv. Don't modify the venv yourself without
  saying so.

## Tests

- A test that runs a fresh `.venv/bin/python -c "import sitecustomize"`-style
  subprocess **without** the test flag and asserts the bootstrap is inactive
  (dotenv loading untouched).
- A test that the bootstrap activates only when its flag is set.
- A test that `get_settings()` in a normal subprocess with a temporary
  `.env`-like file (use a temp dir, **not** the real `.env`) gets the
  database URLs.

## Report

- The confirmed root cause, with the evidence from "What to check".
- What changed and why, and the cleanup command for the author's venv, if
  any.
- Real counts for `make lint`, `make test`, `make test-perf`,
  `make frontend-test` and `make test-e2e`, run the way the author runs
  them (plain shell, real `.env` present but unread by you).
