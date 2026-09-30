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

Phase 3 adds the three pure GeneratorAgents, package completeness rules,
directive reports, and an offline model-comparison evaluator. The API
currently exposes only `GET /api/health`; pipeline orchestration, persistence
of generated packages, and the frontend arrive in later phases. See
[`docs/IMPLEMENTATION_LOG.md`](docs/IMPLEMENTATION_LOG.md) for progress and
[`docs/design-deviations.md`](docs/design-deviations.md) for where the
implementation differs from the thesis design.

## Local setup

Prerequisites: Python 3.11 or newer, Docker with Compose, and an available
port 5432. No LLM key, cloud credentials, Checkov, or tfsec are needed for
the offline tests, stub spike, or stub agent evaluations.

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

Run `make eval-architect EVAL_ARGS='--provider stub'` to exercise five
ArchitectAgent cases and one correction-loop diagnostic without network
calls. It writes per-case JSON with the validated plan, checks, and bounded
validation-error history, plus a `summary.md` under
`docs/evals/phase2-architect-stub-<timestamp>/`. The stub fixtures live in
the evaluation script; the report contains no prompts, raw responses, or keys.
The command prints redacted INFO-level LLM attempt metrics to stderr. The author
can later use `--provider openai` or `--provider anthropic`, optionally
`--model NAME` and `--pause-seconds N`. Real-provider cases run sequentially
with a 15-second pause by default; the stub skips the pause. The script
reports soft checks as PASS/FAIL without failing solely because a check fails.

Run `LLM_PROVIDER=stub make eval-generators EVAL_ARGS='--models stub --no-env-file'`
to evaluate both committed plans and all three variants without an API call or
reading `.env`. It writes `results.json` and `summary.md` under
`docs/evals/phase3-generators-<timestamp>/`; the committed example shows a
structural correction and both passing and failing directive reports. Add
`--save-packages` to inspect the generated files. For model comparisons, use
`--models model-a,model-b`; all non-stub names use the configured provider.
Use `--mode sequential --pause-seconds 15` on a rate-limited provider. Optional
cost estimates take per-million-token rates as `--price-in model-a=1,model-b=2`
and `--price-out model-a=3,model-b=4`. The evaluator never saves prompts or
keys. The `--no-env-file` mode uses placeholder database settings because
the offline evaluator does not connect to PostgreSQL.

For OpenRouter through the OpenAI-compatible adapter, its
[:nitro model suffix](https://openrouter.ai/docs/guides/routing/model-variants/nitro)
prioritizes providers with higher token throughput. Append it to a model ID
when evaluating generation speed; actual latency still depends on the model
and provider availability.

OpenAI-compatible services can use the existing `openai` adapter by setting
`LLM_BASE_URL`. For example, Groq uses these values (supply your own key):

```text
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
LLM_API_KEY=replace-with-your-groq-key
```

The URL and model follow [Groq's OpenAI compatibility guide](https://console.groq.com/docs/openai)
and [model documentation](https://console.groq.com/docs/model/openai/gpt-oss-120b).
When `LLM_BASE_URL` is unset, the OpenAI SDK uses its normal endpoint.

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
| `LLM_BASE_URL` | Optional OpenAI-compatible API root; used only with `LLM_PROVIDER=openai` | Unset |
| `LLM_ATTEMPT_TIMEOUT_SECONDS` | Per-call attempt limit | `30` |
| `LLM_MAX_ATTEMPTS` | Total attempts per call | `3` |
| `LLM_DEADLINE_SECONDS` | Overall limit per `complete_json` call | `150` |
| `AGENT_DEADLINE_SECONDS` | Shared ArchitectAgent time budget across plan attempts | `150` |
| `ARCHITECT_MAX_PLAN_ATTEMPTS` | Maximum separate plan and correction attempts | `3` |
| `GENERATOR_DEADLINE_SECONDS` | Budget per generator | `150` |
| `GENERATOR_ATTEMPT_TIMEOUT_SECONDS` | Per-call attempt limit for full packages | `120` |
| `GENERATOR_MAX_OUTPUT_TOKENS` | Output token limit for full packages | `32000` |
| `GENERATOR_MAX_PACKAGE_ATTEMPTS` | Full-package attempts, including correction | `2` |
| `LLM_BACKOFF_BASE_SECONDS` | Exponential retry backoff base | `1.0` |
| `LLM_MAX_OUTPUT_TOKENS` | Output token limit per request | `16000` |
| `MAX_REMEDIATION_ITERATIONS` | Fix-pass limit per package | `3` |
| `PACKAGE_RETENTION_DAYS` | Package sweep cutoff | `30` |
| `LOG_LEVEL` | Python log level | `INFO` |

`infraarch_owner` owns the databases and applies Alembic migrations.
`infraarch_app` serves the API and runs the retention sweep. It cannot delete
run rows, update or delete event rows, or truncate tables. Tests use the owner
role to reset test tables while exercising application code as `infraarch_app`.
