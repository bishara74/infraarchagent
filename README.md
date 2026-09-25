# InfraArchAgent

**A Multi-Agent System for Secure Cloud Infrastructure Generation from Natural Language**

This repository contains the implementation for my BSc thesis at
**Eötvös Loránd University (ELTE), Faculty of Informatics**.

- **Author:** Alhodali Bishara
- **Supervisor:** Gregory Reynolds Morse
- **Year:** 2026

## About the project

InfraArchAgent takes a plain-English description of the infrastructure you
need and produces three alternative Infrastructure-as-Code packages:
cost-optimised, performance-optimised and security-optimised. A pipeline of
LLM-driven agents plans the architecture, generates the files, scans them with
Checkov and tfsec, automatically fixes security violations, and validates the
result. A React interface shows each agent's progress live and lets the
engineer compare the packages, review every security fix as a diff, and
approve, retry or reject packages that still need a human decision.

## Status

Phase 1 adds the LLM adapter layer and an offline timing spike. The API
currently exposes only `GET /api/health`; the generation pipeline and
frontend arrive in later phases. See
[`docs/IMPLEMENTATION_LOG.md`](docs/IMPLEMENTATION_LOG.md) for progress and
[`docs/design-deviations.md`](docs/design-deviations.md) for where the
implementation differs from the thesis design.

## Local setup

Prerequisites: Python 3.11 or newer, Docker with Compose, and an available
port 5432. No LLM key, cloud credentials, Checkov, or tfsec are needed for
the offline Phase 1 tests and stub spike.

1. Copy `.env.example` to `.env`. Replace the three placeholder passwords and
   make the passwords in the four database URLs match their roles. `.env` is
   ignored by Git.
2. Run `make up`, `make install`, and `make migrate` from the repository root.
   `make install` uses `backend/requirements.lock` as pip constraints to pin
   the runtime and dev dependencies recorded for Phase 1.
3. Run `make test` and `make lint`. Tests migrate and clean `infraarch_test`
   using the owner role; code under test connects as the app role.
4. Run `make run`, then open `http://127.0.0.1:8000/api/health`. A healthy
   database returns HTTP 200 even when `LLM_API_KEY` is unset.

`make down` stops PostgreSQL without deleting its named volume. `make sweep`
deletes generated package rows older than the configured retention period;
`cd backend && .venv/bin/python -m app.cli sweep-packages --dry-run` reports
the count without deleting. The CLI also accepts `--days N`.

Run `make spike` with the default `stub` provider to create a JSON result
and Markdown summary under `docs/spikes/`. To pass arguments, use for example
`make spike SPIKE_ARGS='--provider stub --runs 1 --mode both --max-output-tokens 8000'`.
The script also accepts `--model`. It uses a 240-second, one-attempt policy
for measurement; `--max-output-tokens` defaults to `LLM_MAX_OUTPUT_TOKENS`.
The report stores counts and sizes, never prompts, generated files, or keys.
Its truncation column and verdict show whether responses hit the token limit.
The author can later run the same command with a real provider and key to
measure OQ-03. Stub timings only verify the report format.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `POSTGRES_PASSWORD` | Local PostgreSQL superuser password | Required |
| `INFRAARCH_OWNER_PASSWORD` | Migration role password | Required |
| `INFRAARCH_APP_PASSWORD` | Runtime role password | Required |
| `DATABASE_URL` | Runtime asyncpg URL for `infraarch_app` | Required |
| `MIGRATION_DATABASE_URL` | Migration asyncpg URL for `infraarch_owner` | Required |
| `TEST_DATABASE_URL` | App-role URL for `infraarch_test` | Required |
| `TEST_MIGRATION_DATABASE_URL` | Owner-role URL for `infraarch_test` | Required |
| `LLM_PROVIDER` | `anthropic`, `openai`, or `stub` | `stub` |
| `LLM_MODEL` | Model name, required for a real adapter | Unset |
| `LLM_API_KEY` | Real-adapter credential | Unset |
| `LLM_ATTEMPT_TIMEOUT_SECONDS` | Per-call attempt limit | `30` |
| `LLM_MAX_ATTEMPTS` | Total attempts per call | `3` |
| `LLM_DEADLINE_SECONDS` | Overall limit per `complete_json` call | `150` |
| `LLM_BACKOFF_BASE_SECONDS` | Exponential retry backoff base | `1.0` |
| `LLM_MAX_OUTPUT_TOKENS` | Output token limit per request | `16000` |
| `MAX_REMEDIATION_ITERATIONS` | Fix-pass limit per package | `3` |
| `PACKAGE_RETENTION_DAYS` | Package sweep cutoff | `30` |
| `LOG_LEVEL` | Python log level | `INFO` |

`infraarch_owner` owns the databases and applies Alembic migrations.
`infraarch_app` serves the API and runs the retention sweep. It cannot delete
run rows, update or delete event rows, or truncate tables. Tests use the owner
role to reset test tables while exercising application code as `infraarch_app`.
