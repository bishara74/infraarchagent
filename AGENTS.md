# AGENTS.md — InfraArchAgent

Standing instructions for any coding agent working in this repository.
Read this file fully before every task. Phase-specific instructions come in the
task prompt; this file holds the rules that never change.

## 1. What this project is

InfraArchAgent is the implementation of a BSc thesis. It is a multi-agent
pipeline that turns a natural-language infrastructure description into three
Infrastructure-as-Code packages (cost-, performance- and security-optimised),
scans them with Checkov and tfsec, remediates violations through an LLM loop,
validates them, and shows everything in a React UI with live progress over SSE.

Stack: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) + asyncpg,
Alembic, PostgreSQL 16, pytest + pytest-asyncio + httpx. Frontend (later
phases): React 18 + TypeScript + Vite + Tailwind.

## 2. Source of truth

- `docs/spec/` contains the thesis Requirements (Chapter 3) and Design
  (Chapter 4) plus diagrams. They are the specification. Never edit them.
- If the code must differ from the spec, implement the better option AND
  record it in `docs/design-deviations.md`. Never deviate silently.
- If the spec is ambiguous or contradictory, choose the smallest reasonable
  interpretation, isolate it in one place in the code, add it to the
  "Open questions" section of `docs/design-deviations.md`, and call it out
  in your final summary. Do not invent features to resolve ambiguity.
- If a diagram in `docs/spec/images/` disagrees with the chapter text, the
  text wins. Where the text is silent, the diagram decides (see the
  Clarifications section of `docs/design-deviations.md`).
- Requirement IDs (FR-*, NFR-*, PR-*, UC-*) come from the spec. Use them in
  tests, commit messages and log entries.

## 3. Scope discipline

- Work only on the phase named in the task prompt. Do not start later phases,
  even partially, and do not add "helpful" extras.
- Do not add dependencies outside the approved list for the phase. If one is
  truly needed, add it and justify it in the implementation log.
- No real LLM calls, no real API keys, and no external network services in
  tests. Tests must pass on a machine with only Docker and Python.

## 4. Architecture boundaries (enforced in review)

```
backend/app/
  api/        HTTP only. Calls services/repositories. No SQL, no agent logic.
  core/       config, logging, error handling.
  domain/     pure Python: enums, state machines, value objects, path rules.
              Imports nothing from api/, db/ or pipeline/.
  db/         SQLAlchemy models, session, repositories, Alembic migrations.
  events/     EventLog: the ONLY code allowed to insert into agent_events.
  pipeline/   orchestrator (later phases).
  agents/, llm/, scanners/  (later phases).
```

- State changes for runs and packages must go through the transition rules in
  `app/domain/states.py`. Never assign a status string directly.
- Every event write goes through `EventLog.append()`, which takes the per-run
  advisory lock before inserting and publishes only after commit.
- All timestamps are produced by the application as timezone-aware UTC
  (`datetime.now(UTC)`) and stored in `TIMESTAMPTZ` columns.

## 5. Database rules

- Two roles: `infraarch_owner` runs migrations; `infraarch_app` is what the
  application connects as. The app role has no DELETE on `pipeline_runs` and no
  UPDATE/DELETE on `agent_events`. Do not grant extra privileges to make a test
  pass; fix the test or the code instead.
- Schema changes only through Alembic migrations. Never edit an applied
  migration; add a new one.
- Tests run against real PostgreSQL (the test database from docker-compose),
  never SQLite.

## 6. Security rules (NFR-01)

- Never commit `.env`, keys, or tokens. `.env.example` holds placeholders only.
- Never open, print, or copy `.env` or any real API key. Real keys are only used
  by the author, outside Codex runs.
- Secrets are `SecretStr` in settings and must never appear in logs, HTTP
  responses, exception messages, or database rows. The canary tests enforce
  this; keep them passing and extend them when you add new surfaces.
- Error responses to clients never include exception text or stack traces.

## 7. Testing rules

- Every behaviour you add gets a test. Tests that trace to a requirement carry
  a marker: `@pytest.mark.req("FR-S-05")` (multiple IDs allowed).
- Before finishing, run `make lint` and `make test` and report the real
  output summary (passed/failed/skipped counts). Never claim tests pass
  without running them. If something cannot be run, say so explicitly.
- Concurrency tests must be deterministic where possible (explicit
  synchronisation, not sleeps and luck). Where randomness is used, fix a seed.

## 8. Documentation — required on EVERY task

A task is not done until these are updated:

1. `docs/IMPLEMENTATION_LOG.md` — append one entry (template inside the
   file): what changed, files touched, requirement IDs, decisions, test
   results, known gaps. Newest entry at the top.
2. `docs/design-deviations.md` — add/adjust entries for any difference from
   the spec, and any new open question.
3. `README.md` — update if setup, commands, or environment variables changed.

## 9. Git

- Small, logical commits. Message format: `phase<N>: <imperative summary>`
  and requirement IDs where relevant, e.g. `phase0: add event log with
  advisory-lock ordering (FR-P-04)`.
- Do not push, rebase, or rewrite history unless asked.

## 10. Final summary format (end of every task)

1. What was built (short).
2. Test and lint results (real numbers).
3. Deviations and open questions added.
4. Anything you were unsure about or could not verify.
5. Suggested next step.

## 11. Commands

| Command | Purpose |
|---|---|
| `make up` / `make down` | start/stop PostgreSQL (docker-compose) |
| `make install` | create venv and install backend with dev extras |
| `make migrate` | apply Alembic migrations as the owner role |
| `make run` | start FastAPI with reload |
| `make test` | run the test suite against the test database |
| `make lint` | ruff check + ruff format --check + mypy on `app/` |
| `make sweep` | run the 30-day package retention sweep |
