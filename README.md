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

Phase 5 adds local Checkov and tfsec scanning, bounded per-file remediation,
versioned security reports, and cumulative diffs. Validation arrives in
Phase 6; until then scanned packages pass through `validation_error` to
`pending_review`, so stub pipeline runs end `partial_success`. See
[`docs/IMPLEMENTATION_LOG.md`](docs/IMPLEMENTATION_LOG.md) for progress and
[`docs/design-deviations.md`](docs/design-deviations.md) for where the
implementation differs from the thesis design.

## Local setup

Prerequisites: Python 3.11 or newer, Docker with Compose, and an available
port 5432. To run live scanning or `make eval-security`, put Checkov 3.3.21
and tfsec v1.28.14 on PATH. The author's WSL setup uses
`pipx install checkov==3.3.21`, the tfsec v1.28.14 release binary installed
on PATH, and Terraform v1.16.4 from HashiCorp's apt repository. Helm scanning
also needs `helm`, which is absent in the Phase 5 environment. Recorded tests
run without these scanners; real-tool checks skip when they are absent. Tests
need no LLM key or cloud credentials.

1. Copy `.env.example` to `.env`. Replace the three placeholder passwords and
   make the passwords in the four database URLs match their roles. `.env` is
   ignored by Git.
2. Run `make up`, `make install`, and `make migrate` from the repository root.
   `make install` uses `backend/requirements.lock` as pip constraints to pin
   the runtime and dev dependencies recorded for Phase 1.
3. Run `make test` and `make lint`. Tests migrate and clean `infraarch_test`
   using the owner role; code under test connects as the app role.
4. Run `make run`, then open `http://127.0.0.1:8000/api/health`. A healthy
   database returns HTTP 200 even when `LLM_API_KEY` or a scanner is absent;
   the response reports scanner availability and versions.

`make down` stops PostgreSQL without deleting its named volume. `make sweep`
deletes generated package rows older than the configured retention period;
`cd backend && .venv/bin/python -m app.cli sweep-packages --dry-run` reports
the count without deleting. The CLI also accepts `--days N`.

## Running a pipeline

Start PostgreSQL and the backend in one terminal with `make up` and `make run`.
In another terminal, run:

```text
make run-pipeline TEXT="Deploy a small AWS web service"
```

The watcher submits the request, prints SSE progress, reconnects with
`Last-Event-ID` if necessary, and shows the final run and package statuses.
Optional `CONFIG_PROVIDER`, `CONFIG_MODEL`, and `API_URL` select a request
configuration and API root. With `LLM_PROVIDER=stub`, the API uses a
pipeline-only deterministic demo; the Phase 1 spike and Phase 2–3 evaluation
stubs are unchanged. The demo packages are scanned by the installed tools;
validation is still unavailable, so they reach `pending_review` and the run
ends `partial_success`. A missing or repeatedly failing scanner places its
package in `scan_error`.

The in-memory event broker requires **one backend process** (OQ-04 in
[`docs/design-deviations.md`](docs/design-deviations.md)). `make run`
explicitly starts one Uvicorn worker. Multiple workers would split subscribers
and publishers across separate brokers.

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

Run `make eval-security EVAL_ARGS='--scan-only'` to scan the committed gpt-oss
v3 and Sonnet reasoning-off packages without LLM calls. The command writes
`results.json` and `summary.md` under `docs/evals/phase5-security-<timestamp>/`.
Scan-only mode does not load `.env` or connect to the database.
Checkov HIGH/CRITICAL findings on the security variant determine FR-G-05;
tfsec and combined counts are reported separately. The latest committed
Phase 5 report marks two generated packages with CRITICAL
`TERRAFORM_SYNTAX` findings; tfsec could not run its other checks until those
files are repaired. Their Checkov counts remain available. Use
`--packages DIR [DIR ...]` for other saved
package directories. `--remediate` explicitly enables LLM calls and writes
evaluation runs to PostgreSQL; `--max-iterations`, `--price-in`, `--price-out`,
and `--save-diffs` control its report. Remediation summaries show each
package's before/after blocking count, stop reason, fixes, tokens, elapsed
time, and cost when input and output price rates are provided for the fixing
model. Real LLM calls can cost money.

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
| `LLM_REASONING_EFFORT` | OpenAI-compatible reasoning control: `off`, `low`, `medium`, or `high`; Anthropic ignores it | Unset |
| `LLM_RESPONSE_FORMAT` | `json_object` sends OpenAI-compatible JSON mode; Anthropic ignores it | Unset |
| `SECURITY_FIX_PROVIDER` | Optional provider for SecurityAgent fix calls; otherwise the run provider | Unset |
| `SECURITY_FIX_MODEL` | Optional model for SecurityAgent fix calls; otherwise the run model | Unset |
| `SECURITY_FIX_REASONING_EFFORT` | Optional fix-only reasoning control; otherwise `LLM_REASONING_EFFORT` | Unset |
| `BROKER_QUEUE_SIZE` | Maximum queued events per SSE subscriber | `1000` |
| `MAX_CONCURRENT_RUNS` | Maximum active or reserved pipeline runs | `5` |
| `SSE_KEEPALIVE_SECONDS` | Idle interval before an SSE keep-alive comment | `15` |
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
| `SECURITY_DEADLINE_SECONDS` | Overall security budget per package | `240` |
| `SCANNER_TIMEOUT_SECONDS` | Limit for each local scanner call | `120` |
| `FIX_ATTEMPT_TIMEOUT_SECONDS` | Limit for each LLM fix attempt | `90` |
| `FIX_MAX_OUTPUT_TOKENS` | Output limit for a per-file fix | `16000` |
| `SECURITY_MAX_PARALLEL_FIXES` | Maximum concurrent file fixes | `4` |
| `PACKAGE_RETENTION_DAYS` | Package sweep cutoff | `30` |
| `LOG_LEVEL` | Python log level | `INFO` |

When `LLM_REASONING_EFFORT` is unset, requests omit reasoning controls.
With the OpenAI-compatible adapter, `off` sends OpenRouter's
`reasoning.enabled=false`; `low`, `medium`, and `high` send
`reasoning.effort`. Model and upstream support vary; see
[OpenRouter's reasoning documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).
The Anthropic adapter currently records the configured value in attempt logs
but does not alter its request. The effect on generation quality is assessed
in evaluation results.

Security fix calls can use a different provider or model from architecture
and generation by setting the `SECURITY_FIX_*` variables. The same
`LLM_API_KEY` and, for OpenAI-compatible calls, `LLM_BASE_URL` are used.
The selected fixing provider, model, and reasoning effort are stored in each
security report session and the latest report. Unset overrides preserve the
run's model selection.

`infraarch_owner` owns the databases and applies Alembic migrations.
`infraarch_app` serves the API and runs the retention sweep. It cannot delete
run rows, update or delete event rows, or truncate tables. Tests use the owner
role to reset test tables while exercising application code as `infraarch_app`.

For a quick security evaluation, pass `--packages-limit N` in `EVAL_ARGS`.
Per-package and scanner-attempt progress goes to stderr; timeout records are
retained even when a retry succeeds.
