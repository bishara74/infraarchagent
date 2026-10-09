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
Checkov and Trivy, automatically fixes security violations, and validates the
result. A React interface shows each agent's progress live and lets the
engineer compare the packages, review every security fix as a diff, and
approve, retry or reject packages that still need a human decision.

## Status

Phase 7 adds results snapshots, review decisions/retries, deterministic labelled
ZIP downloads and optional static API-key authentication. Phase 6 provides
deterministic structure, reference and naming checks, offline
Terraform provider-schema validation, optional local linters and persisted
reports. Clean scans plus valid packages reach `production_ready`; all three
ready packages give run `success`. Invalid or unavailable required validation
reaches `pending_review` through the existing Option C rules. See
[`docs/IMPLEMENTATION_LOG.md`](docs/IMPLEMENTATION_LOG.md) for progress and
[`docs/design-deviations.md`](docs/design-deviations.md) for where the
implementation differs from the thesis design.

## Local setup

Prerequisites: Python 3.11 or newer, Docker with Compose, and an available
port 5432. To run live scanning or `make eval-security`, put Checkov 3.3.21,
Trivy v0.69.3 and Terraform v1.16.4 on PATH. Install Checkov with the exact
pin `pipx install "checkov==3.3.21"`. Active scans use all three tools; health
reports `scanners.checkov`, `scanners.trivy`, and `scanners.terraform`.
Trivy renders Helm charts without the `helm` binary. Recorded tests
run without these scanners; real-tool checks skip when they are absent. Tests
need no LLM key or cloud credentials.

Install only the pinned, checksum-verified Trivy release below. For
reproducibility, do not use `get.trivy.dev`, apt/rpm, or “latest”. The author
confirmed that checksum verification printed
`trivy_0.69.3_Linux-64bit.tar.gz: OK`. The task records the malicious v0.69.4
release and CVE-2026-33634; this project uses v0.69.3.

```bash
V=0.69.3
cd /tmp
curl -fsSLO https://github.com/aquasecurity/trivy/releases/download/v${V}/trivy_${V}_Linux-64bit.tar.gz
curl -fsSLO https://github.com/aquasecurity/trivy/releases/download/v${V}/trivy_${V}_checksums.txt
grep " trivy_${V}_Linux-64bit.tar.gz$" trivy_${V}_checksums.txt | sha256sum -c -
tar -xzf trivy_${V}_Linux-64bit.tar.gz trivy
sudo install -m 0755 trivy /usr/local/bin/trivy
trivy --version
```

Scanner attempts use fresh temporary HOME/cache state, Trivy's pinned embedded
checks (`--skip-check-update`), disabled version checks/telemetry, and fixed
loopback refusal proxies for every tool. Tests also verify scans in a network
namespace; runtime proxies do not provide kernel isolation. Literal remote
Terraform modules have an `EXTERNAL_MODULE_NOT_SCANNED` advisory because their
contents are unavailable. Terraform runs `validate -json` without `init`; only
demonstrated HCL/configuration-loading diagnostics become CRITICAL
`TERRAFORM_SYNTAX`. Missing providers/modules, references, types, formatting and
schema validation are outside that scanner gate. The Phase 6 validator follows
with full offline provider-schema validation.
Checkov parallelism is disabled with `CHECKOV_PARALLELIZATION_TYPE=none`;
scanner timeout/cancellation kills the whole process group and bounds pipe cleanup.

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
configuration and API root. The watcher takes `API_KEY` from its process
environment and sends `X-API-Key`; it does not read dotenv or print the key.
With `LLM_PROVIDER=stub`, the API uses a
pipeline-only deterministic demo; the Phase 1 spike and Phase 2–3 evaluation
stubs are unchanged. The demo packages are scanned by the installed tools;
validation uses the real engine. With clean scans, installed Terraform and the
provider mirror, all three can reach `production_ready` and the run can end
`success`. A missing or repeatedly failing scanner places its package in
`scan_error`; unavailable required Terraform validation requires review.

The in-memory event broker requires **one backend process** (OQ-04 in
[`docs/design-deviations.md`](docs/design-deviations.md)). `make run`
explicitly starts one Uvicorn worker. Multiple workers would split subscribers
and publishers across separate brokers.

## Results, review and downloads

Apply `make migrate` as `infraarch_owner` before starting this backend version.
Migration `0003_review_retry_started_at` adds the nullable retry timestamp;
existing packages stay unchanged with a NULL marker.

`API_KEY` is optional. When set, every `/api/pipeline` endpoint, including
submission and SSE, requires `X-API-Key`. Empty/unset allows local access and
logs one startup warning. `/api/health` stays public. Missing and incorrect
headers receive the same 401; query-string keys are not accepted. The examples
below use placeholder values; omit the header when authentication is unset.

```bash
export RUN_ID="replace-with-run-uuid"
export API_KEY="replace-with-local-static-key"
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/pipeline/$RUN_ID/results"

curl -X POST -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"action":"approve"}' \
  "http://localhost:8000/api/pipeline/$RUN_ID/packages/cost/review"

curl -X POST -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"action":"retry","feedback":"Repair the reference","target_files":["terraform/main.tf"]}' \
  "http://localhost:8000/api/pipeline/$RUN_ID/packages/cost/review"

curl -H "X-API-Key: $API_KEY" -OJ \
  "http://localhost:8000/api/pipeline/$RUN_ID/download/cost"
```

Results return 200 for current snapshots, including active runs, with one
SELECT for the run, packages and latest architect `plan_created` payload.
A missing persisted plan is `null`. The exact field list is:

```text
run: id, status, input_text, start_time, end_time, provider, model,
     max_iterations, error_message
plan: DeploymentPlan | null
packages[]: variant, status, iteration_count, error, files, original_files,
            security_report, validation_report, review_feedback,
            readiness_label, downloadable, review_available, review_reasons,
            retry_targets
missing_variants[]: variant, error
```

Produced variants appear in cost/performance/security order. Generating
placeholders are excluded; failed generation rows appear only in
`missing_variants`. Retention absence is not reported as generation failure.
Baselines and reports remain nullable. OpenAPI at `/docs` describes the strict
schemas. Malformed IDs return 400 and unknown runs return 404.

Reviews require a terminal run and a `pending_review` package. An active run
returns 409 `run_in_progress`; other package states return 409
`not_pending_review`. Approve and reject return 200; approve performs no scan
or validation, and reject labels the package `not_production_ready`. Feedback
is trimmed, limited to 2,000 characters, and stored on retry/reject. Unknown
fields or incorrect types return 400.

Retry returns 202 with `stream_url`. Targets combine remaining blocking
findings, failed file-linked validation checks and up to five explicit safe,
existing package paths. Explicit targets are allowed only for retry.
Targetless requests return 422 `feedback_needs_target` when feedback exists,
or `nothing_to_retry` otherwise. Full runner capacity returns 429 without
changing package data. Each retry shares the run capacity and uses the saved
provider/model/iteration settings plus configured fixer overrides. Clean scan
and valid validation produce `production_ready`; other outcomes return to
review. Reviews never reclassify or retime the completed run.

Acceptance saves the UTC `review_retry_started_at` marker in the same
transaction as the retry state and iteration reset. Settlement clears it with
the final package state. Startup selects non-NULL markers independently of run
status, recovering active/intermediate retry stages to review with the reason
`review retry interrupted by server restart`. Automated run recovery retains
its existing behavior. Missing usable retry context returns safely to review.

Connect to the returned SSE URL with **fetch-based SSE**, sending `X-API-Key`
and `Last-Event-ID` when reconnecting. Native `EventSource` does not support
custom request headers. The stream stays open through retry scanning and
validation and closes after the final package-state frame. Keep one backend
process because the broker is in memory.

Downloads require `production_ready` or `not_production_ready`; other states
return 409 `not_downloadable`. Missing, expired or failed-generation packages
return 404; OQ-01's proposed 410 remains deferred. The ZIP uses persisted
remediated files, sorted paths, fixed metadata and DEFLATED compression level
6. Repeated downloads of unchanged data are byte-identical. The label-bearing
filename follows `infraarch-<run-prefix>-<variant>-<label>.zip`.

`INFRAARCHAGENT_READINESS.md` records the label, engineer rejection wording,
feedback, report summaries and the static-deployability caveat. **Labelled at**
and decision provenance come from the matching final package event. If that
event is missing, both use fixed unavailable text. Readiness-name collisions
use `_infraarchagent/READINESS.md`, then the first free numbered
`READINESS-2.md`, `READINESS-3.md`, etc., without overwriting package files.
Static validity does not prove deployability, such as an Aurora cluster that
still lacks required instances.

Unexpected API errors use generic `{error, message}` responses. Operator logs
keep tracebacks and correlation IDs with both configured keys redacted;
public/persisted data and archive contents remove credentials and backend
execution paths. The ASGI PR-04 acceptance measures a seeded 10 MB persisted
package; the final curl-based download measurement remains Phase 9 work.

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
`results.json` and `summary.md` under `docs/evals/phase5b-security-<timestamp>/`.
Scan-only mode does not load `.env` or connect to the database.
Checkov HIGH/CRITICAL findings on the security variant determine FR-G-05;
Trivy, Terraform, and combined counts are reported separately. Historical
reports retain their tfsec attribution. The Phase 5b report preserves both
gpt-oss `TERRAFORM_SYNTAX` findings while Trivy scans available local Terraform
resources, Kubernetes manifests and Helm templates. External-module coverage
advisories and recovered scan timeouts are recorded explicitly. Use
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
| `API_KEY` | Optional static pipeline API credential, sent as `X-API-Key`; empty leaves local access open | Unset |
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

Prompt-cache measurement: `LLM_PROMPT_CACHE=off` (default) or `system` marks
the system content for compatible Anthropic models. Cached input token metrics
are recorded when reported; cache-aware cost pricing is not implemented.

Terraform provider schemas are provisioned by `make providers` into the ignored
`.cache/terraform-providers/` mirror. This command needs network access and the
already installed Terraform; it stops on a failed download. Exact provider pins,
archive hashes, signature evidence and mirror size are recorded in
[the provider record](tools/terraform-providers/README.md). Both AWS major
versions share one mirror; committed lock records come from its local archives.
Runtime validation initializes temporary copies with `-backend=false`,
`-input=false` and `-plugin-dir=<mirror>` with black-hole proxies. Local modules
may be installed after path checks; remote modules are unavailable offline.
Health responses report validator availability/versions and mirror presence.

Built-in validation uses the existing installed Python-HCL2 8.1.4, Lark 1.3.1
and PyYAML 6.0.3; regex 2026.9.29 is locked as a required transitive dependency.
Parser diagnostics contain safe messages and package-relative locations.

Optional validation tools are Helm, hadolint, ansible-lint and promtool. The
author's reproducible installer is `tools/install_validators.sh`; Phase 6 used
the installed tools without invoking it. `VALIDATOR_TOOL_TIMEOUT_SECONDS`
defaults to 60. Missing tools and tool failures are reported as optional skips.
Helm schema downloading and Ansible dependency/schema downloading are disabled.

`VALIDATOR_MAX_PARALLEL_TOOLS` defaults to 3 (allowed range 1–3 per package),
and `VALIDATION_DEADLINE_SECONDS` defaults to 120. The complete report is saved
before outcome events. Deadline/internal aborts produce `validation_error`;
ordinary failures produce `invalid`. Naming findings and optional tool skips
remain visible for review. The reusable `app.validation.engine.validate` API
requires no database or LLM adapter.

`make eval-validation` validates the twelve original committed Phase 3 packages
with the local offline engine, without database access or LLM calls. Optional
`EVAL_ARGS='--package <package-directory> --mirror <mirror-directory>'` narrows
the inputs or selects an existing mirror. JSON/Markdown reports record results,
category failures, warnings, skip reasons, durations, tool versions and source
hashes under `docs/evals/phase6-validation-<UTC timestamp>/`. The Phase 6b rerun
measured **4 valid, 8 invalid, 0 error**, compared with the retained Phase 6
report's **2 valid, 10 invalid, 0 error**. Both known gpt-oss syntax failures
remain confirmed. [Current per-package results](docs/evals/phase6-validation-20261009T211526321570Z/summary.md)
and [previous/current comparison](docs/evals/phase6-validation-20261009T211526321570Z/comparison.md).
Sonnet monitoring cost/security now pass; performance retains a genuine Service
namespace mismatch. Sonnet three-tier security reports the safe Terraform title
`Cycle`, with a root-file remediation anchor when Terraform supplies no range.
An Aurora cluster without instances remains a semantic gap requiring review.

Validation settings are read with the existing application settings:

| Setting | Default | Purpose |
|---|---|---|
| `LLM_PROMPT_CACHE` | `off` | `system` adds an Anthropic compatible system cache marker. |
| `VALIDATOR_TOOL_TIMEOUT_SECONDS` | `60` | Maximum time for each external validator command. |
| `VALIDATOR_MAX_PARALLEL_TOOLS` | `3` | Concurrent commands per package, from 1 to 3. |
| `VALIDATION_DEADLINE_SECONDS` | `120` | Whole-package validation deadline. |

Provision the provider mirror once with `make providers` before live validation
or evaluation. This needs network access; a failed download stops provisioning.
Runtime tools use temporary copies, minimal environments and refusal proxies;
real-tool tests also use network namespaces where supported. The mirror is
ignored by Git; the pinned configurations and provenance are committed. No
provider, role, collection or Helm schema is downloaded during validation.

Built-in structural checks cover all nine artifact families. Kubernetes,
Jenkins, Nginx and Grafana use built-ins; their server/cluster integrations
are outside this offline phase. Naming findings and absent Secrets warn. An
unresolved bare Nginx proxy target fails with its file and line; package names,
IP addresses, dotted hosts and explicit external-host comments resolve, and
variables warn. D-35 records the exact rules and static naming limits.

Verified local versions: Terraform 1.16.4, Helm v4.3.0+gbec5b06, hadolint 2.15.1,
promtool 3.15.0 and ansible-lint 26.9.0. Mirror coverage is AWS 5.100.0/6.68.0,
random 3.9.1, Kubernetes 2.38.0, Helm 2.17.0, TLS 4.4.1 and null 3.3.2,
391,710,515 bytes (373.56 MiB) on linux_amd64.
