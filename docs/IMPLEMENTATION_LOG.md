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
