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

Phase 8 completes the four desktop screens: input, live progress, comparison,
and package diff/review/download. The shared fetch-based SSE client resumes
interruptions and distinguishes a settled close from an active retry. FastAPI
serves the optional production build from the same origin. Phase 7 provides
results snapshots, review decisions/retries, deterministic labelled ZIP downloads
and optional static API-key authentication. Phase 6 provides
deterministic structure, reference and naming checks, offline
Terraform provider-schema validation, optional local linters and persisted
reports. Clean scans plus valid packages reach `checks_passed`; all three
ready packages give run `success`. Invalid or unavailable required validation
reaches `pending_review` through the existing Option C rules. See
[`docs/IMPLEMENTATION_LOG.md`](docs/IMPLEMENTATION_LOG.md) for progress and
[`docs/design-deviations.md`](docs/design-deviations.md) for where the
implementation differs from the thesis design.

## Local setup

Prerequisites: Python 3.11 or newer, Docker with Compose, and an available
port 5432. Frontend commands and `make lint` also require Node.js ≥22.22.2
(development uses Node 24 LTS). To run live scanning or `make eval-security`,
put Checkov 3.3.21, Trivy v0.69.3 and Terraform v1.16.4 on PATH. Install Checkov with the exact
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
2. Run `make up`, `make install`, `make frontend-install`, and `make migrate`
   from the repository root.
   `make install` uses `backend/requirements.lock` as pip constraints to pin
   the runtime and dev dependencies recorded for Phase 1.
3. Run `make test` and `make lint`. The test launcher resolves the configured
   test database URLs through normal settings (environment or root `.env`), then
   starts pytest with dotenv disabled, stub defaults and empty LLM/API keys.
   Tests migrate and clean `infraarch_test`
   using the owner role; code under test connects as the app role. The default
   suite excludes wall-clock performance assertions. `make test-perf` runs
   only those assertions; final timing measurements are Phase 9 work on a
   quiet machine. Structural overlap, archive contents and process cleanup
   remain covered by `make test`.
4. Run `make run`, then open `http://127.0.0.1:8000/api/health`. A healthy
   database returns HTTP 200 even when `LLM_API_KEY` or a scanner is absent;
   the response reports scanner availability and versions.

`make down` stops PostgreSQL without deleting its named volume. `make sweep`
deletes generated package rows older than the configured retention period;
`cd backend && .venv/bin/python -m app.cli sweep-packages --dry-run` reports
the count without deleting. The CLI also accepts `--days N`.

## Frontend setup

The frontend uses React 19.3, Vite 8, TypeScript 6.0 in strict mode and plain
CSS. Use Node.js ≥22.22.2; development uses Node 24 LTS (24.21.0) and npm
11.19.0. Exact dependencies are pinned in `frontend/package.json` and the
committed `frontend/package-lock.json`. Runtime packages are limited to React,
React DOM, React Router and jsdiff. Fonts and styles are local.

```text
make frontend-install
make frontend-dev
make frontend-build
make frontend-test
make lint
```

`frontend-install` uses `npm ci --ignore-scripts` for reproducible subsequent
setup. The initial approved install was performed once with
`npm install --save-exact --ignore-scripts`; do not enable installation scripts
to work around a dependency failure. No browser is downloaded by these commands.

The dev server runs at `http://127.0.0.1:5173` and proxies `/api` to the backend
at `http://127.0.0.1:8000`, preserving one browser origin without CORS.
Vite does not load dotenv files. Start the backend separately with `make run`
when working with the API. `frontend-build` type-checks the app and tooling and
writes `frontend/dist`; `frontend-test` runs Vitest once. `make lint` checks both
backend and frontend, including ESLint and TypeScript `--noEmit`.
`make run` uses one worker without automatic reload; restart it after backend
code changes.

The backend defaults to port 8000. If it is occupied, use `make run PORT=8765`.
The API/health URL then becomes `http://127.0.0.1:8765/api/health`; a built UI
served by FastAPI is at `http://127.0.0.1:8765`. For Vite development, point its
proxy at that backend while keeping the browser at `http://127.0.0.1:5173`:

```bash
INFRAARCH_BACKEND_URL=http://127.0.0.1:8765 make frontend-dev
```

In PowerShell, set the environment variable before starting Vite:

```powershell
$env:INFRAARCH_BACKEND_URL = "http://127.0.0.1:8765"
make frontend-dev
```

`INFRAARCH_BACKEND_URL` defaults to `http://127.0.0.1:8000` and is read from
the process environment; Vite still does not load dotenv. E2E continues to use
backend port 8000 and Vite port 5173.

The four screens support submission, live progress, comparison and package
review/download. After `make frontend-build`, `make run` also serves the UI at
`http://127.0.0.1:8000`, including direct screen reloads. Without a build it
remains API-only. `/api` routes never fall back to the UI. UI responses receive
a self-only CSP, nosniff and no-referrer headers; API/docs responses are unchanged.
`make test-e2e` starts a single backend with stub/review defaults and Vite,
using one Chromium worker and a test-only API key. It deliberately does not reuse
existing servers: health cannot verify their provider/scenario defaults.
After installing dependencies, the author installs Chromium:

```bash
cd frontend
npx playwright install chromium
npx playwright install-deps chromium
```

This uses the pinned local Playwright package. Agents must not download browsers
or use `npx` to fetch tools. Manual visual checks use the existing global
`playwright-cli` directly.

`make test`, `make test-perf` and `make test-e2e` use a parent launcher that
resolves normal operator settings and passes only the test database URLs into
verification. Exported test URLs override those in `.env`. The test processes
themselves never load dotenv: they receive stub defaults and empty LLM/API keys;
canary tests still set their own fake values inside the process. E2E validates
the exact `infraarch_test` database name and ordinary app/owner roles before
starting servers.

The bootstrap activates only with `INFRAARCH_TEST_BOOTSTRAP=1` and its directory
on `PYTHONPATH`, both scoped to the verification child. Pytest's internal Alembic
subprocess and E2E's migration/server inherit that explicit opt-in. Standalone
`make migrate`, `make migrate-test`, `make run`, `make eval-*` and plain Python
retain normal dotenv loading; the `migrate-test` prerequisite also runs normally.
No bootstrap is installed in the venv and no venv cleanup is required.
Direct `npm run test:e2e` still requires exported `TEST_DATABASE_URL` and
`TEST_MIGRATION_DATABASE_URL`, since the Node configuration never loads dotenv.

```text
make test-e2e
cd backend
.venv/bin/python -m scripts.run_verification e2e --grep @perf
```

Default E2E excludes `@perf`. PR-02 writes live server-timestamp-to-badge-mutation
samples, maximum and median to `frontend/test-results/pr02.json`. This is
Phase 8 development evidence; final performance measurement remains Phase 9.
Real scanner and Terraform/mirror prerequisites remain required. Fixture capture
is explicit: with a local dotenv-disabled stub/review backend using an unset API
key, run `node frontend/e2e/support/recordFixtures.ts` from the repository root.
It rewrites the recorded pending/repaired responses and streams for contract tests.


The browser exchanges the API key for an HttpOnly session cookie; it never
persists the key. Only the active run ID lives in `sessionStorage`. A 401 returns
to login on the current route. Variant and file selections live in the URL.
Generated code and report messages render as text; downloads use the session
cookie and a revoked Blob URL. Scripts may continue using `X-API-Key`.

At stream EOF the client fetches results once. It closes normally only when the
run is terminal, no package is scanning/remediating/validating, and every package
has `retry_in_progress=false`. Otherwise it reconnects from the last accepted
sequence; after five EOF reconnect attempts without a new event it shows
“Live updates paused, Reconnect”. A retry 202 reopens a closed stream. Stage
activity uses real timestamp intervals, counting overlapping variants once and
excluding idle review time; elapsed timers do not poll the API.

The completed [Phase 8 UI evidence](docs/evals/phase8-ui-20261012T204423Z/README.md)
contains mockup comparisons, real screenshots at 1440×900 and 1024px, cancellation
regressions, and the saved PR-02 samples. Final checks: backend 1057 default and
6 perf tests passed; frontend 82 unit/component tests passed; browser 6 default
and 1 perf tests passed; lint and production build passed. The final PR-02 run
had 32 live samples, max 663ms and median 165.5ms. Exact installed versions and
approved publish dates are in the [dependency record](docs/evals/phase8-ui-20261012T204423Z/dependency-pins.md).
These are Phase 8 development checks; final performance evaluation is Phase 9.

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
For a real provider, omitting the provider or selecting the configured
`LLM_PROVIDER` inherits `LLM_MODEL`. Selecting a different real provider
requires `CONFIG_MODEL` (HTTP 400 `invalid_request` otherwise). Every stub run
records model `stub`, including when the deployment sets a real `LLM_MODEL`
or a request explicitly supplies a different model name. Stub fixers also
use model `stub`, regardless of `SECURITY_FIX_*`. Fixer overrides apply to
real runs using the configured provider.
With `LLM_PROVIDER=stub`, the API uses a
pipeline-only deterministic demo; the Phase 1 spike and Phase 2–3 evaluation
stubs are unchanged. The demo packages are scanned by the installed tools;
validation uses the real engine. With clean scans, installed Terraform and the
provider mirror, all three can reach `checks_passed` and the run can end
`success`. A missing or repeatedly failing scanner places its package in
`scan_error`; unavailable required Terraform validation requires review.

For tests/demos only, set `PIPELINE_DEMO_SCENARIO=review` with a stub run.
The security variant contains a deterministic undeclared local in
`terraform/main.tf`, caught by the built-in `terraform.local_ref` check at
line 4. Cost and performance stay clean. Security enters `pending_review`;
retrying with feedback lets the demo fixer declare the local and reach
`checks_passed`. The run's historical `partial_success` remains unchanged.
The default `clean` scenario preserves existing packages. Real-provider runs
ignore the scenario, including when their fixer is stub; startup warns when
`review` is configured with a non-stub default provider. The intentional
failure needs no external validator, but full demo settlement still requires
the installed scanners, Terraform and provider mirror. No cloud resources
or model services are called by the demo.

The in-memory event broker requires **one backend process** (OQ-04 in
[`docs/design-deviations.md`](docs/design-deviations.md)). `make run`
explicitly starts one Uvicorn worker. Multiple workers would split subscribers
and publishers across separate brokers.

## Results, review and downloads

Apply `make migrate` as `infraarch_owner` before starting this backend version.
Migration `0003_review_retry_started_at` adds the nullable retry timestamp;
existing packages stay unchanged with a NULL marker.

Manual approval produces `engineer_approved`, never `checks_passed`. Approval
and rejection require non-empty `reviewer_name` and `reason`; names are
self-declared and failed checks remain visible.

When `API_KEY` is set, browsers log in through `POST /api/auth/login` with
`{"api_key":"..."}` and use an HttpOnly, SameSite=Strict cookie scoped to `/api`.
The frontend stores no key. `GET /api/auth/session` reports authentication state;
`POST /api/auth/logout` revokes the session. Browser mutations require a matching
Origin and Host. Scripts and benchmarks keep using `X-API-Key`, including SSE
and ZIP requests. `/api/health` remains public.

Sessions expire after 30 idle minutes or 12 absolute hours. Active SSE events
and heartbeats refresh idle activity; absolute expiry and revocation still close
streams. Configure `AUTH_IDLE_SECONDS`, `AUTH_ABSOLUTE_SECONDS`,
`AUTH_LOGIN_ATTEMPTS_PER_MINUTE` (default 5), and `AUTH_COOKIE_SECURE` (false for
local HTTP; set true behind HTTPS).

With a configured key, direct startup and the existing VS Code debugger work
unchanged, from `backend/`:

```bash
python -m uvicorn app.main:app --port 8765 --workers 1
```

Without a key, open mode requires the validated localhost launcher:

```bash
make run PORT=8765
# Or, from backend/:
python -m app.server --host 127.0.0.1 --port 8765
```

An unset key with another/unknown bind refuses startup. The UI and session status
explicitly display "No authentication (local mode)". Missing/wrong authentication
returns a generic 401; keys in query strings are never accepted.

```bash
export RUN_ID="replace-with-run-uuid"
export API_KEY="replace-with-local-static-key"
curl -H "X-API-Key: $API_KEY" "http://localhost:8000/api/pipeline/$RUN_ID/results"

curl -X POST -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"action":"approve","reviewer_name":"Engineer","reason":"Reviewed remaining findings"}' \
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
            readiness_label, downloadable, review_available, retry_in_progress,
            review_reasons, retry_targets
missing_variants[]: variant, error
```

Produced variants appear in cost/performance/security order. Generating
placeholders are excluded; failed generation rows appear only in
`missing_variants`. Retention absence is not reported as generation failure.
Baselines and reports remain nullable. Required `retry_in_progress` is derived
solely from the persisted retry marker being present; status alone does not
establish whether a retry is active. The marker timestamp is not exposed.
OpenAPI at `/docs` describes the strict
schemas. Malformed IDs return 400 and unknown runs return 404.

Reviews require a terminal run and a `pending_review` package. An active run
returns 409 `run_in_progress`; other package states return 409
`not_pending_review`. Approve and reject return 200; approve performs no scan
or validation, and reject labels the package `rejected`. Feedback
is trimmed, limited to 2,000 characters, and stored on retry/reject. Unknown
fields or incorrect types return 400.

Retry returns 202 with `stream_url`. Targets combine remaining blocking
findings, failed file-linked validation checks and up to five explicit safe,
existing package paths. Explicit targets are allowed only for retry.
Targetless requests return 422 `feedback_needs_target` when feedback exists,
or `nothing_to_retry` otherwise. Full runner capacity returns 429 without
changing package data. Each retry shares the run capacity and uses the saved
provider/model/iteration settings plus configured fixer overrides. Clean scan
and valid validation produce `checks_passed`; other outcomes return to
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

Downloads require `checks_passed` or `rejected`; other states
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
| `PIPELINE_DEMO_SCENARIO` | Test/demo-only `clean` or `review`; only affects resolved stub runs | `clean` |
| `LLM_MODEL` | Model name, required for a real adapter | Unset |
| `LLM_API_KEY` | Real-adapter credential | Unset |
| `API_KEY` | Shared login key; scripts use `X-API-Key`. Unset requires verified `127.0.0.1` local mode | Unset |
| `LLM_BASE_URL` | Optional OpenAI-compatible API root; used only with `LLM_PROVIDER=openai` | Unset |
| `LLM_REASONING_EFFORT` | OpenAI-compatible reasoning control: `off`, `low`, `medium`, or `high`; Anthropic ignores it | Unset |
| `LLM_STRUCTURED_OUTPUT` | Generator-only `json_schema`, `json_object`, or `off`; strict mode uses a closed file-entry list over OpenAI-compatible requests | `json_schema` |
| `LLM_RESPONSE_FORMAT` | `json_object` sends OpenAI-compatible JSON mode; Anthropic ignores it | Unset |
| `SECURITY_FIX_PROVIDER` | Optional fixer provider for runs using configured `LLM_PROVIDER`; stub runs always use the stub fixer | Unset |
| `SECURITY_FIX_MODEL` | Optional fixer model for runs using configured `LLM_PROVIDER`; otherwise the run model, with `stub` for stub fixers | Unset |
| `SECURITY_FIX_REASONING_EFFORT` | Optional fix-only reasoning control for runs using configured `LLM_PROVIDER`; ignored for stub runs, otherwise falls back to `LLM_REASONING_EFFORT` | Unset |
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
| `GENERATOR_MAX_OUTPUT_TOKENS` | Generator-only output token limit (~60 seconds at observed throughput) | `8000` |
| `GENERATOR_MAX_PACKAGE_ATTEMPTS` | Full-package attempts, including correction | `3` |
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
| `LOG_FILE` | Optional append-only JSONL file containing allowlisted, redacted LLM call diagnostics; parent directory must exist; relative paths resolve against this repository | unset |

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

Export the compact provider schema index offline with `make provider-schema`
after provisioning the mirror. It writes version/hash manifests and indexes to
`.cache/terraform-provider-schemas/` beside the mirror; do not commit them.
This is also a Phase 10 installation prerequisite. Missing indexes degrade
repair grounding with a safe log notice; they never trigger downloads.

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

## Phase 9 evaluation tools

`make traceability` collects pytest requirement markers and Vitest/Playwright
names, including performance titles, without running tests. Reports preserve the
seven thesis TC groups, explicitly list uncovered IDs and do not imply tests pass.

`make secret-scan` checks working-tree text and file history across all refs and
reflogs. It skips dotenv secrets, dependencies/caches/build output and symlinks;
only exact documented placeholders/canaries are allowlisted. Findings contain
locations and pattern names, never matched values. Exit 1 means findings; exit 2
means the scan was incomplete. See D-42 for heuristic and coverage limitations.
Both commands write timestamped raw data, environment metadata and summaries
under `docs/evals/phase9-*`. Neither installs tools or reads `.env`.

The HTTP harness is `make benchmark BENCH_ARGS='--mode stub pr01 --runs 10'`.
It defaults to `http://127.0.0.1:8000`; place global options before the subcommand.
PR-03 reads `runner_capacity` from health and refuses values below three. It
compares three simultaneous runs with one isolated run; same-prompt PR-01 medians
are secondary references only (`pr03 --pr01-results <results.json-or-csv>`).
A terminal run is timed only through a final results response confirming all
packages settled and no retry active. Pending review does not wait for engineers.

Real mode uses exported settings only and requires a positive `--budget-usd`
minimum-credit reserve. It never loads `.env`. Sequential launch requires
remaining credit at least max(reserve, 2 × highest observed per-run cost); the
three-run cohort also requires 4.5 × that highest cost. Unknown remaining credit
or unsupported providers require explicit `--max-runs`. OpenRouter lifetime
usage deltas measure costs; cohort costs are total/3 averages with individual
costs not attributed. These safeguards are heuristics, not a guaranteed spend cap.

For a synthetic download fixture, run from `backend/` with exported development
settings: `.venv/bin/python -m scripts.seed_benchmark_package`. It prints a run ID
and records its seed/sizes. It refuses test databases and labels the fixture
`rejected`; its input explicitly says `benchmark synthetic package`.
The ZIP is calibrated just below 10 MB; source bytes are larger because compression
is included. Then run `make benchmark BENCH_ARGS='pr04 --run-id ID --repeat 10'`.
Timing includes the complete HTTP download, not fixture preparation.

For Phase 9 quiet-machine checks, use `make test-perf` and `make test-ui-perf`.
The former wraps the existing backend `perf` suite; the latter runs the existing
Playwright `@perf` test. Export all four database URLs first (test URLs point to
`infraarch_test`), using the normal app/owner roles. The wrappers disable dotenv,
clear provider/API credentials and pass only isolated test settings to children.
They write raw console/JUnit or Playwright JSON, PR-02 samples, environment metadata
and summaries to `docs/evals/phase9-backend-perf-*` or `phase9-pr02-*`.

Run each timing suite separately on an otherwise idle machine, with backend/Vite
ports 8000/5173 free, installed Chromium/scanners and the offline Terraform mirror.
Keep browser and backend on the same host clock. Close background builds/scans and
other pipeline runs; record the environment rather than adjusting thresholds.
Default E2E still excludes `@perf`; default backend tests still exclude `perf`.

## Running the Phase 9 measurements

Use the installed dependencies and tools; these measurement commands perform no
installs or downloads. Supply settings as process environment variables, without
copying or printing keys. Export `DATABASE_URL`, `MIGRATION_DATABASE_URL`,
`TEST_DATABASE_URL` and `TEST_MIGRATION_DATABASE_URL`. Development URLs use database
`infraarch`, test URLs use `infraarch_test`, with the existing app/owner roles.
When running Codex verification, also set `INFRAARCH_TEST_BOOTSTRAP=1` and put
`backend/tests/bootstrap` and `backend` on `PYTHONPATH` so Make migrations and
verification parents never load dotenv. Normal operator server startup keeps its
existing configuration behavior.

Export a matching `API_KEY` for both backend and benchmark processes. Benchmarks
require it to read `GET /api/benchmark/settings`: this endpoint always requires
a configured matching `X-API-Key`, including for stub rehearsals. Missing/wrong
keys and an unset server key return generic 401 responses with no settings.
`/api/health` remains unauthenticated and does not expose generator settings.
Never copy or print credentials into reports.

Start a single backend in a separate terminal; 8765 avoids the browser test ports:

```bash
make migrate
LLM_PROVIDER=stub LLM_API_KEY='' make run PORT=8765
```

With that backend running, rehearse the entire free procedure:

```bash
make bench-stub BASE_URL=http://127.0.0.1:8765
```

This performs 10 rotating-prompt PR-01 runs, one isolated PR-03 baseline plus
three concurrent runs, then seeds one explicitly synthetic development package
and downloads its ZIP 10 times. Installed Checkov, Trivy, Terraform and the
provider mirror are required. Stub measurements establish overhead, not real
LLM performance. The synthetic package remains rejected; no cleanup deletes its
retained run/events.

For **author-only real measurements**, restart the backend with the desired
exported provider/model/base URL and credentials. Use the same exported settings
for the measurement process. Stop other uses of that key and run on a quiet
machine. `MAX_CONCURRENT_RUNS` must be at least three. Then:

```bash
# Run this first after any generator change (three examples, same guard):
make bench-smoke BASE_URL=http://127.0.0.1:8765 BUDGET=2
make bench-real BASE_URL=http://127.0.0.1:8765 BUDGET=2
# For providers with unknown costs/credit, an explicit bound is required:
make bench-real BASE_URL=http://127.0.0.1:8765 BUDGET=2 MAX_RUNS=14
```

`BUDGET` is a minimum-credit reserve, not a total-spend cap. After the first settled
real run, the command prints and records its measured cost, remaining credit and
projected affordable count of the remaining planned runs at that same cost.
The projection applies the identical sequential/cohort guard and run cap;
it never authorizes a launch. Each launch checks fresh credit and updated costs.
Unknown cost/credit gives an unknown affordability count, not invented numbers.

Reports are under `docs/evals/phase9-bench-stub-*` or `phase9-bench-real-*`:
parent and per-measurement summaries, environment records, results/agents CSV,
normalized timing events, and (real mode) `first_real_run_advisory.json`.
Guard/prerequisite stops return nonzero and retain partial results. The primary
PR-03 verdict stays ≤1.5× its isolated baseline; exact-prompt PR-01 medians are
labelled secondary references. Concurrent cost total/3 is an average, with each
individual cost explicitly not attributed. No key, key identifier, provider error
body or generated package contents enter these artifacts.

Phase 9 verification evidence is recorded in the implementation log. The one
stub rehearsal completed all 14 pipelines and 10 downloads, while **PR-03 failed**
(2.76–2.78× the isolated baseline); PR-01, PR-04 and recorded PR-05 thresholds
passed. A completed-command exit does not imply performance criteria passed:
read `summary.md`. The real-provider results are still author-run work.

Generator format retries name the previous safe failure reason without repeating
its output. The generator has one budget across package corrections and adapter
retries. Default nominal calls are 2 × 3 × 120 = 720 seconds before backoff,
clipped by the shared 150-second budget. A valid package completing synchronous
final validation after that budget is retained with `deadline_exceeded` and
`overrun_seconds`; this does not change PR-05's 150-second timing threshold.

### Phase 9c generator configuration and evidence

Every benchmark captures the effective server values from its authenticated
settings endpoint before submitting a run: output tokens, structured mode,
attempt/completion timeouts, shared generator budget and both retry counts.
Missing, unauthorized or malformed settings stop measurement. Capture the
server values rather than the measurement process defaults: the backend may
have loaded different operator configuration. Reports add safe attempt outcomes,
format reasons (including `truncated` and `salvaged`), token counts per attempt,
failure categories and deadline flags/overruns. `agents.csv` keeps event-based
`seconds` alongside internal `generator_elapsed_seconds`; PR-05 remains 150s.
Old evidence missing these values stays unknown and is never rewritten.

Target prompts with `make benchmark BENCH_ARGS='pr01 --runs 3 --prompts 2,0'`:
indices select the fixed example set in the given order and `--runs` cycles
through them. Empty, duplicate and out-of-range indices are rejected before
submission. `bench-smoke` runs one of each example and writes
`docs/evals/phase9-bench-smoke-*`; a three-sample smoke check does not establish
full PR-01 acceptance. Budget guard stops can produce fewer than three runs.

### Broad quality schedule

`make bench-broad BASE_URL=http://127.0.0.1:8765 BUDGET=2` runs the committed
[broad-v1 registration](docs/evals/scenarios/README.md) sequentially, defaulting to
two runs per scenario (1–10 then 10–1). Override `RUNS_PER_SCENARIO` with a positive
integer; use `MODE=stub` for a free rehearsal against a stub backend. The runner
checks the registration against Git HEAD, records its SHA-256 on every scheduled
row and bounds submissions to the schedule length. PR-01 timing is descriptive;
PR-05 retains its normal thresholds. No PR-03 or PR-04 runs are launched.
Evidence is under `docs/evals/phase9-bench-broad-*`. Keep the existing matching
`API_KEY`, server-side `LOG_FILE`, installed tools and credit-reserve setup above.

### Runtime attribution and offline replay

Set `LOG_FILE=.cache/runtime-attribution/llm-calls.jsonl` in the backend process
environment after creating that directory to keep benchmark call diagnostics.
It is disabled by default. New files have mode 0600. Only structured
`app.llm.base` fields are written, through the existing redactors; prompts,
responses, arbitrary log messages and stack traces are excluded. Existing
console logging is unchanged. Keep generated logs untracked; retention is an
operator responsibility.

Results expose nullable `telemetry`, also persisted as batched `stage_notice`
events through EventLog. Per-call records retain reported `reasoning_tokens`
(including zero; absent means unknown), requested effort/format and serving
provider. Legacy env/header capability metadata is reported as unprobed rather
than a claim that the model lacks reasoning; configured effort is unchanged.
Per-invocation tool observations cover Checkov, Trivy and Terraform init/validate,
with separate semaphore wait and execution/cleanup time, retry/outcome metadata,
cache reuse, parent evaluations and partial-group timings. Invocation totals,
interval-union wall time and nested group durations are distinct measures;
never add group times to their child tool times. Benchmark results/events retain
these fields and include runtime attribution summaries. Historical omissions
stay unknown.

Offline commands read saved JSON only and never resolve dotenv or call an LLM:

```bash
cd backend
.venv/bin/python -m scripts.phase9_runtime estimate \
  --benchmark ../docs/evals/phase9-bench-smoke-20261019T222520294388Z \
  --results ../.cache/phase9h-smoke-results \
  --output ../.cache/runtime-attribution/estimate.json
.venv/bin/python -m scripts.phase9_runtime replay \
  --snapshot ../.cache/phase9h-smoke-results/3951c593-06e8-4335-91f1-fb63c3b13ffd.json \
  --mirror ../.cache/terraform-providers --concurrency 1 \
  --instrumentation on --source-label current --repetitions 1 \
  --output ../.cache/runtime-attribution/replay-current-1.json
```

Repeat replay at concurrency 3 and with instrumentation off, using fresh output
paths, on a quiet machine. Replay keeps file content fixed, uses fresh package
workspaces, and records input hashes, tool versions, load and CPU utilization.
The same replay script can run against pre-change application source via
`PYTHONPATH`; that source supports instrumentation off. This measures local work,
not full PR-01. PR-01 requires a median ≤300 seconds over ten real runs; the
three-run smoke median 266.48 seconds is descriptive only. See
`docs/phase9-runtime-attribution.md` for the counterfactual estimate and limits.

Settings precedence is explicit constructor arguments, then process environment,
then dotenv, then defaults. Duplicate dotenv assignments use the last value;
keep exactly one assignment per key and restart the backend after changes.
Codex does not read or edit the author's dotenv file. Recommended author values:

```dotenv
GENERATOR_MAX_OUTPUT_TOKENS=8000
LLM_STRUCTURED_OUTPUT=json_schema
GENERATOR_ATTEMPT_TIMEOUT_SECONDS=90
GENERATOR_DEADLINE_SECONDS=150
LLM_DEADLINE_SECONDS=150
LLM_MAX_ATTEMPTS=3
GENERATOR_MAX_PACKAGE_ATTEMPTS=3
```

At ~140 tokens/second, 8,000 tokens take ~57–60 seconds. A 90-second attempt adds
latency allowance while two ~60-second calls may fit into 150 seconds. A full
90-second timeout leaves less than 60 seconds for retry after overhead; no
completion guarantee is implied. Repository attempt defaults remain 120 seconds.
Changing the shared LLM deadline also affects other completion callers.

| Setting | Generator precedence / use |
|---|---|
| `GENERATOR_MAX_OUTPUT_TOKENS` | Always supplied; unset now means 8,000 |
| `LLM_MAX_OUTPUT_TOKENS` | General fallback, unused when the generator supplies its limit; 16,000 cannot override 8,000 |
| `GENERATOR_ATTEMPT_TIMEOUT_SECONDS` | Always supplied; clipped to remaining completion time |
| `LLM_ATTEMPT_TIMEOUT_SECONDS` | General fallback, unused when the generator supplies its timeout; 60 does not cap 90/150 |
| `GENERATOR_DEADLINE_SECONDS` | One shared budget across package attempts, adapter retries and backoff |
| `LLM_DEADLINE_SECONDS` | Each completion uses min(this limit, remaining generator budget) |
| `LLM_MAX_ATTEMPTS` | Adapter attempts per completion, default 3 |
| `GENERATOR_MAX_PACKAGE_ATTEMPTS` | Schema/layout package corrections, default 3; exhausted format retries stop generation |
| `LLM_BACKOFF_BASE_SECONDS` | Jittered exponential retry delay, consuming the same budget |
| `LLM_STRUCTURED_OUTPUT` | Generator-only format; overrides inherited `LLM_RESPONSE_FORMAT`, including `off` |

`AGENT_DEADLINE_SECONDS` controls other agents, not generators. Native Anthropic
and stub keep dictionary output and local format/schema validation; strict wire
parameters target OpenAI-compatible generators. json_schema uses closed
path/content entries and OpenRouter's required-parameter routing. Refusals retain
fixed categories and recommend json_object; no automatic fallback occurs.

The first real attempt used author-confirmed generator attempt=150, budget=270,
and completion=270 (last duplicate assignment). A slow first call leaves ~120s
for retry, matching historical 70–150s failed responses and the observed 270.03s
ceiling. General attempt=60/output=16,000 were overridden; unset generator output
used the old 32,000 default. These settings explain 15 generator intervals above
150s; they still fail PR-05. The parser's old global backtick count could also
reject valid packages, but no raw invalid responses were retained to establish
which attempts were affected. First evidence: four usable runs of eight,
median 189.81s, three settled failures and one incomplete run, $4.940978 measured.
Real reliability/cost improvements remain author-only measurements.

### Phase 9d validation feedback

Generated Terraform receives conservative declaration repairs before automatic
validation repair (VALIDATION_REPAIR_MAX_ROUNDS=2; zero disables initial LLM
rounds). All automatic rounds share the existing validation deadline, including
time spent in security between preflight and the single post-security round.
Every accepted round strictly reduces failed checks without new blocking findings.
Final validation and security scanning still run on the final files. Engineer
Retry shares patch/prompt/verification primitives and retains its acceptance rules.
The opt-in review demo retains its intentional manual-review failure.

Quality snapshots contain only package status/review reasons, failed-check
IDs/messages/locations, remaining rule IDs and numeric counts. They exclude
source, diffs, feedback and fixer text. Benchmark summaries include quality tables.
Recompute the original baseline into a separate folder (no API or model calls):

```sh
cd backend
.venv/bin/python -m scripts.benchmark quality \
  --results-dir ../docs/evals/phase9-bench-real-20261015T124330508703Z \
  --snapshots-dir ../.cache/phase9d-results \
  --output-dir ../docs/evals/phase9d-baseline-quality-new
```

For a new benchmark folder its saved `quality/` directory is the default snapshot
source. The output directory must be new and outside both input directories.
The committed `docs/evals/phase9d-baseline-quality-20261015/` reproduces 1/36
production ready, with six missing variants, without retaining generated code.

For the author's next real comparison, keep the baseline model/provider choices
and these generator overrides. New default: VALIDATION_REPAIR_MAX_ROUNDS=2;
changed default: MAX_REMEDIATION_ITERATIONS=4 (was 3). Fix attempt/output and
all other deadlines keep their previous defaults; 45 seconds is an author-run
override, while automated security iterations always have a 60-second ceiling.
Use one assignment per key; no real run is executed by the implementation agent.

```dotenv
VALIDATION_REPAIR_MAX_ROUNDS=2
MAX_REMEDIATION_ITERATIONS=4
FIX_ATTEMPT_TIMEOUT_SECONDS=45
SECURITY_DEADLINE_SECONDS=240
GENERATOR_MAX_OUTPUT_TOKENS=16000
GENERATOR_ATTEMPT_TIMEOUT_SECONDS=140
GENERATOR_DEADLINE_SECONDS=150
LLM_DEADLINE_SECONDS=150
LLM_STRUCTURED_OUTPUT=json_schema
```

The validator still accepts row panels nested inside a top-level panels array.
The sampled wrapped dashboard at run 48ce2227/security instead has a top-level
`dashboard` API envelope; the author may separately decide whether to support
that representation. Phase 9d leaves the check unchanged.

### Phase 9e syntax gates and repair budgets

Generation applies declaration repairs and two narrow Terraform idiom repairs,
then parses documents, formats Terraform and checks installed offline tools.
One generation repair shares the original generator deadline. Gate-only checks
never change final readiness criteria. A private package workspace preserves
initialized providers across validation calls, with isolated per-module data;
provider/module dependency changes trigger offline reinitialization. No shared
writable plugin cache or runtime download is used.

`SCHEMA_CONTEXT_MAX_CHARS=16000` bounds repair context.
`POST_SECURITY_REPAIR_DEADLINE_SECONDS=60` gives the post-security round its own
fresh budget. Initial repair keeps `VALIDATION_DEADLINE_SECONDS=120`; security
time cannot consume the new post-security budget. All calls remain bounded by
their enclosing stages. PR-01 is a measured threshold, not a new pipeline timer.

The package workspace exists from generation through final checks, is serialized
within a package and has private module `TF_DATA_DIR`/lock files. Success,
failure and cancellation terminate child processes before cleanup. Provider
requirements, inferred provider dependencies and local-module graph changes
invalidate initialization; ordinary edits reuse it. Failed initialization is
never a successful cache entry. Engineer Retry starts a fresh workspace.
Generation and iteration reports record safe init categories and init/reuse time.

Only two new deterministic Terraform rewrites run after generation and every
security iteration: remove empty default-security-group ingress/egress blocks,
and escape recognized AWS flow-log field placeholders. HCL and Terraform JSON
are supported; other expressions and nonempty rules are preserved. Declaration
repairs remain generation-only. An iteration restores Terraform source files
and removes added Terraform files if validation failures increase. Unavailable
comparisons require a fully valid candidate. Retained non-Terraform edits still
require syntax/render and security verification. Checks, fixes and rollback
share the existing 60-second iteration / 240-second security-stage budgets.

Repeated findings, rejected patches and validity rollbacks do not end the loop.
Each started fix attempt consumes the configured allowance
(`MAX_REMEDIATION_ITERATIONS`, default 4); terminal scans do not. A timed-out
candidate is discarded, and another attempt may start while the stage budget
and allowance remain. Fatal scanner failures still stop verification. The
retained package is always the next baseline, including verified non-Terraform
edits after a Terraform rollback. A separate, redacted previous-attempt prompt
field (at most 4,000 characters) explains rejections without treating candidate
diagnostics as failures in the retained files. Engineer feedback stays separate.

Security context measurements read canonical `security_report.sessions` history,
with a legacy top-level fallback and no double counting. Reports distinguish
positive, zero and missing measurements, Terraform versus other files, and
safe degraded-context reasons; historical reasons remain `unknown`. The
[sanitized 9e follow-up audit](docs/evals/phase9e-security-loop-audit-20261017/audit.md)
corrects the historical zero-context summary without modifying original evidence.

Benchmark `agents.csv` and descriptive PR-05 rows now measure gates, each repair
round, deterministic repairs, iteration verification, final validation and final
security scans. `validator_persistence` labels the short prepared-report write.
Quality snapshots include gate results, bounded context sizes, repair classes
and conservative failure origins (`unknown` for hidden or historical origins).
The clean stub pipeline has no fix iterations; `make bench-stub` additionally
runs a separately labelled scripted-fix rehearsal with real offline Terraform,
three concurrent private workspaces and both AWS versions. Its times, init reuse
and rollback/deadline counts are excluded from production-ready rates and PR
thresholds. A deadline-only rollback says nothing about eventual candidate
validity. Historical 9d deadline stops (four initial / nine post-security), new
stub counts and injected-clock tests are reported separately.

For the next **author-run real comparison**, retain the 9d endpoint and model
choices (`LLM_PROVIDER=openai`, `LLM_MODEL=openai/gpt-oss-120b:nitro`,
`SECURITY_FIX_PROVIDER=openai`,
`SECURITY_FIX_MODEL=openai/gpt-oss-120b:nitro`), plus all generator/fixer overrides
in the preceding 9d block. Add:

```dotenv
VALIDATION_DEADLINE_SECONDS=120
POST_SECURITY_REPAIR_DEADLINE_SECONDS=60
SCHEMA_CONTEXT_MAX_CHARS=16000
```

Build the seven offline schema indexes first. Stub verification does not predict
real benchmark quality or deadline-stop improvements; the next real comparison
must report those measured outcomes using unchanged readiness rules.

### Phase 9f guarded partial acceptance

`SECURITY_PARTIAL_MAX_GROUPS=6` bounds fallback group evaluations per security
iteration (1–64). Failed combined candidates may retain independent verified
files or Terraform blocks; dependent declarations stay together. Existing 60 s
iteration and 240 s stage ceilings remain. Only fully verified groups survive a
timeout; unchanged review retries still rescan. Reports retain rejection reasons
and newly introduced findings without exposing discarded source.

`SECURITY_FIX_MAX_RESOURCES=2` and `SECURITY_FIX_MAX_FINDINGS=12` bound each
security fixer call. Equal-severity resources rotate between attempts. The fixer
receives existing paths and editable current content; existing-path creations
can be normalized into validated edits. Reports distinguish normalized proposals
from those retained after every guard. Overlapping editable files are serialized.

Generator prompt v9 adds plan-specific security/support and quoting guidance inside the
existing 6000-character input context cap (4500 schema / 1500 checklist).
Validation remediation metadata records security-context length and truncation.
Generator and fixer output-token defaults remain unchanged.

Generation first normalizes unambiguous compact HCL blocks by inserting newlines
without changing tokens. Native Terraform/JSON/YAML syntax failures then receive
up to two syntax-only fixer rounds and, if needed, one regeneration using the
original variant generator. All steps share the original 150-second allowance,
including a five-second finalization reserve. Reports identify normalization,
repair round, regeneration, unresolved errors and steps skipped for deadlines.
Generation stays provisional until parsing succeeds: newly visible security
findings remain blocking. Later remediation retains its no-new-blocker guard.
Security iterations reserve five of their existing 60 seconds for cleanup,
restoration and publication; the public iteration/stage limits remain 60/240.

### Phase 9f author fixer comparison

Keep Architect/Generators and prompts identical for both runs. Restart the backend
between configurations and supply the same exported settings to the benchmark.
No implementation verification makes real model calls.
Run both configurations on the corrected commit/prompt v9 for a fixer-only
comparison. The preserved benchmark A used prompt v7; comparing it directly with
a corrected Haiku run also measures generation/recovery/code changes.

```sh
export SECURITY_FIX_PROVIDER=openai
export SECURITY_FIX_MODEL='openai/gpt-oss-120b:nitro'
export SECURITY_FIX_REASONING_EFFORT=low
export FIX_ATTEMPT_TIMEOUT_SECONDS=45
export SECURITY_DEADLINE_SECONDS=240 MAX_REMEDIATION_ITERATIONS=4
export SECURITY_FIX_MAX_RESOURCES=2 SECURITY_FIX_MAX_FINDINGS=12
export SECURITY_PARTIAL_MAX_GROUPS=6
export GENERATOR_MAX_OUTPUT_TOKENS=16000 GENERATOR_ATTEMPT_TIMEOUT_SECONDS=140
export GENERATOR_DEADLINE_SECONDS=150 LLM_DEADLINE_SECONDS=150
# Start/restart the configured backend, then run:
make bench-real BASE_URL=http://127.0.0.1:8765 BUDGET=2 MAX_RUNS=14
```

For the second run, set SECURITY_FIX_MODEL to the author's selected OpenRouter
Haiku-class model ID and SECURITY_FIX_REASONING_EFFORT=off, restart, and repeat.
Keep the existing OpenRouter base URL and externally supplied credentials; never
copy them into evidence. All security fixing, validation repair and syntax
repair share generator structured-output settings: `LLM_STRUCTURED_OUTPUT`
selects `json_schema` (default), `json_object`, or `off`. Strict mode sends the
closed fixer patch schema and OpenRouter `provider.require_parameters=true`,
normalizes path/content arrays into internal maps, and validates typed summaries.
Local validation, unambiguous salvage and retries remain active; unsupported
schemas never trigger an automatic downgrade. `LLM_RESPONSE_FORMAT` is the
legacy nonstructured adapter option, not the fixer mode selector.
Reports distinguish each fixer model and its effective attempt timeout; the
iteration/stage ceilings remain 60/240 seconds. The default attempt remains 90
seconds; 45 is the comparison override, clipped to remaining iteration time.

PR-04 seeding now requires only exported `DATABASE_URL`, pointing to development
`infraarch` as `infraarch_app`. It never loads dotenv or requires migration/test
URLs. `make bench-stub` preflights this setting before submitting any runs and
reports a specific configuration failure. The backend itself still requires its
normal four database settings; no owner-role privileges are granted to the seed.

### Phase 9f quality evidence

The catalogue and supporting templates are documented in D-46 in
`docs/design-deviations.md`; investigation is in `docs/phase9f-investigation.md`.
Every change still requires syntax, control-preservation, Terraform non-regression
and no-new-blocker verification. Public subnets are recorded as `context: public
subnet`; unresolved routing skips. Template-introduced blockers are reported and
rejected. No exception profile or self-logging destination is added.

Per-package `phase9f` quality metadata includes retained catalogue changes,
template outcomes/introduced rules, partial groups, existing-file recovery,
findings per call and effective fixer configurations. Near-miss tables require
final valid validation and group remaining blockers as 1, 2–3 or 4+; historical
missing measurements remain unknown. The authenticated benchmark settings endpoint
also records effective numeric security limits. Final verification and measured
stub results are recorded in `docs/phase9f-verification.md`.

Corrective verification and the benchmark-A syntax replay are in
`docs/phase9f-corrective-verification.md`. Replay the read-only saved corpus with
`cd backend && .venv/bin/python -m scripts.phase9f_syntax_replay`; this calls no
models and reports deterministic recovery separately from scripted test oracles.


Phase 9f A2 correction raises only the default full-package attempt count from
2 to 3; explicit overrides remain authoritative. Missing required types, layout
patterns and concrete suggested paths are sent explicitly to the next attempt
and recorded as source-free per-attempt diagnostics. Syntax repair still has two
rounds and regeneration one; all generation shares the original 150 seconds.
Declaration repair runs again after syntax recovery, with completion tracked by
module content rather than gate presence.

Security iterations share one absolute 60-second deadline through restoration,
notices and closing state/event persistence, reserving five seconds for that
finalization. Parsed documents and derived indexes are cached within each package;
there are no parsing workers. A failure to finish mandatory finalization fails
closed; any legal fault-recovery tail and actual overrun remain visible.
PR-05 additionally reports isolated PR-01, isolated PR-03 baseline and concurrent
PR-03 cohort workloads. The aggregate verdict and thresholds are unchanged.

A2 verification and the preserved-corpus replay are documented in
`docs/phase9f-a2-corrective-verification.md`. To replay without model calls:
`cd backend && .venv/bin/python -m scripts.phase9f_a2_replay --output /tmp/phase9f-a2-replay.json`.


Phase 9g supporting templates emit native `security_support.tf` so the installed
scanners interpret encryption/versioning blocks consistently. Existing JSON is
preserved; all strict acceptance guards still apply. Access-log destinations can
remain rejected for documented context-dependent findings.


Phase 9g accepts `config.policy_profile` (`strict` by default, or
`contextual-v1`). This selects an additional assessment, never a different
readiness or fix-acceptance rule. Results expose `run.policy_profile` and each
package's `profile_assessments`; archives and comparison/report panels retain
strict blockers alongside explicitly excepted contextual records. Contextual
results are experimental pending supervisor approval. D-48 is the full policy
appendix, including conservative omissions and references. Offline A3/B
reclassification is in `docs/evals/phase9g-reclassification-20261019/`.

### Phase 9g benchmark corrections

`make bench-stub`, `make bench-real` and `make bench-smoke` all forward
`BASE_URL`, `BUDGET` and `MAX_RUNS`. Smoke respects smaller explicit caps and
never exceeds three runs. Account `/credits` and key information are probed
without logging credentials; the guard uses the stricter available balance,
including the existing effective-budget constraint. Unavailable account balance
is explicitly unknown. A typed provider `usage_limit` from any stage stops new
submissions immediately; already submitted work is observed, and the remaining
planned runs are `not_started` with unavailable timing/cost.

Safe fixer attempt outcomes and format reasons are persisted for security,
validation and syntax repair and exported in quality snapshots/benchmark rows.
Missing historical or interrupted-call telemetry remains unknown. Mocked wire
tests verify request behavior across model families; they establish no real
provider reliability gain. Complete A3/B format-failure baselines are unknown.
The preserved partial B excerpt has 14 invalid_json/prose_before failures out of
22 non-quota Haiku attempts (eight successes); four quota failures are excluded.
This illustrative excerpt is not the complete B run. Proposal counts are not
LLM attempt counts.

### Phase 9g verification and interpretation

Migrations 0004–0006 separate historical labels/decision metadata, add hashed
browser sessions and default/backfill run `policy_profile` to `strict`. Migration
0007 requires a recorded automatic transition before retaining a legacy success
claim; clean stored reports alone do not establish decision provenance. Apply
migrations as the owner role; application permissions remain unchanged.
Historical SSE labels disclose their mapping, and ambiguous legacy success
remains pending review. Synthetic PR-04 fixtures explicitly disclose that no
engineer decision or checks were executed.

`docs/evals/phase9g-reclassification-20261019/` records read-only A3/B input
hashes and sanitized secondary assessments. Strict/contextual-v1 rates remain
1/29 and 1/29 for A3, 1/9 and 1/9 for B. These provider-limited measurements are
incomplete. Contextual results require supervisor approval before thesis use;
all current official labels still follow the strict rule.

For verification without dotenv, export isolated application/owner test URLs
and set `INFRAARCH_TEST_BOOTSTRAP=1` and
`PYTHONPATH="$PWD/backend/tests/bootstrap:$PWD/backend"` before invoking Make
from the repository root. This also disables dotenv in the migration
prerequisite. Use stub providers and empty model/API credentials. Run:

```text
make lint
make test
make frontend-test
make test-e2e
make secret-scan
make provider-schema
make bench-stub BASE_URL=http://127.0.0.1:8765
```

The last command needs a separate stub backend and exported synthetic matching
API key, plus its isolated development `infraarch` database for PR-04; the E2E
and backend suites use `infraarch_test`. Existing offline scanners, provider
mirror and browser binaries are prerequisites; verification installs nothing.

Final local results and migration counts are in the
[Phase 9g verification report](docs/evals/phase9g-verification-20261019/summary.md).
The stub rehearsal completed every observation, but its PR-03 concurrency
threshold failed; its other measured thresholds passed. It is not real-provider
quality or reliability evidence.

## Phase 9h account upgrade

Stop the backend before upgrading. Back up the existing database before running
new migrations (these commands are for the author, outside Codex):

```bash
umask 077
docker compose exec -T postgres pg_dump -U postgres -Fc infraarch > infraarch-before-9h.dump
docker compose exec -T postgres pg_dumpall -U postgres --roles-only > infraarch-roles-before-9h.sql
docker compose up -d postgres
make prepare-db-tools
make migrate
make run
```

Before these commands, add the new read-only/tool placeholders from `.env.example`
to the author-managed configuration. `prepare-db-tools` provisions the cluster
role without granting CREATEROLE to the migration owner.

Protect both backups: the role backup contains password verifiers. Open the UI
from `127.0.0.1` and create the first admin with a password of at least 12
characters. Existing shared-key browser sessions are revoked; scripts using
`X-API-Key` continue to work. Once an account exists, login is required even
when API_KEY is unset. The unset-key verified loopback bind requirement remains.
Network deployment, HTTPS and Secure-cookie deployment are future work.

### Provider encryption

Before saving keys, generate a master key outside Codex and export it in the
backend process environment (do not commit it or store it in PostgreSQL):

```bash
python3 -c 'import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())'
```

Set `CREDENTIAL_ENCRYPTION_KEY` to that value and
`CREDENTIAL_ENCRYPTION_KEY_VERSION=1`. Missing configuration disables storage.
Interactive provider precedence is selected encrypted DB credential, environment
LLM key fallback, then setup required. Revoked/unreadable selections fail visibly.
Stop the backend for rotation, export the existing key plus
`CREDENTIAL_ENCRYPTION_NEW_KEY` and a larger `CREDENTIAL_ENCRYPTION_NEW_VERSION`,
run `make rotate-credential-key`, then restart with the new key/version. Keep
old backup keys securely: rotating live rows does not re-encrypt old backups.
The author-authorised dependency additions and licenses are listed in D-51.

### Model configuration and benchmark comparability

Interactive choices resolve run overrides, personal defaults, administrator
defaults, then environment defaults. The UI groups Architect, Generators and
Fixer; Advanced supports individual generator overrides. Models with unknown
structured-output capability cannot be selected for Generators/Fixer. Thinking
controls only offer supported modes. A custom compatible endpoint needs explicit
admin capability declarations (and can use its configured static catalog offline).

Header-authenticated benchmark runs without overrides retain the pre-9h
environment requests: LLM_MODEL/LLM_REASONING_EFFORT and SECURITY_FIX_* fallback.
Unset effort means omitted reasoning, never off. All five resolved selections
are recorded. Future consumer-subscription OAuth/Responses work is described in
D-51/D-52; it is not implemented.

### Saved user state

Account drafts, role defaults, UI preferences and recent runs follow the user
through PostgreSQL. After login the server is authoritative. localStorage is a
versioned, user-scoped cache/offline fallback only; it never holds passwords,
provider keys or session tokens. A save conflict reloads the server copy and
keeps the unsaved draft available for explicit recovery. Recent-run cursors
hydrate prior event history before SSE resumes, avoiding skipped stage/log data.

### Read-only database tools

The author may pull `dpage/pgadmin4:9.8`, then run `make db-tools` and open
`http://127.0.0.1:5050`. The target uses `--pull never`. Configure
`INFRAARCH_READONLY_PASSWORD`, `PGADMIN_DEFAULT_EMAIL`, and
`PGADMIN_DEFAULT_PASSWORD` with local values. Existing volumes must run
`make prepare-db-tools` before migration 0012; fresh volumes provision the role
during initialization. Do not grant CREATEROLE to infraarch_owner.

The preconfigured server connects to postgres as infraarch_readonly. Expand
Databases → infraarch → Schemas → public → Tables to inspect pipeline_runs,
generated_packages, agent_events, users, preferences and provider_credentials.
Password hashes have the scrypt algorithm/parameters/salt/digest format; they
are not passwords. Credential ciphertext/nonce are binary fields (often shown
as hex), with key_version and last4 metadata. The master key is absent from the
database. The inspection role can SELECT but cannot insert, update, delete or
truncate application data. Protect pgAdmin's own volume and credentials.

The [agent harness tool reference](docs/agent-tools.md) describes every model and
local-tool invocation, bounds and failure path, with a sequence diagram.

## Phase 9h guided first run

1. Start the migrated backend on `127.0.0.1` and open the UI. Create the first
   administrator using a username and a password of at least 12 characters.
   Browser users do not need the backend API_KEY. The optional local-mode path
   exists only before the first account.
2. Open Settings → Provider. Follow the OpenRouter key link, paste the provider
   key and wait for the automatic test/catalog result. Check provider credit if
   the result says no credit. Save and use the provider. Keys are encrypted in
   PostgreSQL; only their final four characters are subsequently shown.
3. Open Settings → Models. Pick Architect, Generators and Fixer defaults;
   Advanced permits individual generator overrides. Thinking choices follow
   the selected model's capabilities. Context and pricing are shown when known.
   Administrator defaults and personal defaults are separate controls.
4. Return to New request, describe the infrastructure and generate. Optional
   run overrides are collapsed by default. Recent runs reopen saved requests.
5. Review reports and diffs. Account identity is recorded automatically for
   approvals/rejections; provide a decision reason. Settings → Users creates,
   disables or resets reviewers; Account changes your own password/preferences.

<!-- Screenshot placeholder: first-admin setup form at 1280x800. -->
<!-- Screenshot placeholder: model/thinking controls and context/pricing. -->

[Mocked provider setup screenshot](docs/evals/phase9h-verification-20261019/provider-mocked.png) ·
[Authenticated review screenshot](docs/evals/phase9h-verification-20261019/account-review-mocked.png).
These demonstrate the UI with synthetic credentials and mocked model HTTP,
not real-provider reliability or deployment quality.

Phase 9h verification results and limitations are recorded in the
[isolated verification report](docs/evals/phase9h-verification-20261019/summary.md).

## Reproducing the evaluation

Phase 9b adds `make eval-report`. It reads evidence blobs from Git HEAD, never
`.cache`, dirty or untracked evidence. To preserve immutable evidence, the default
`docs/evals/phase9-final-report/` must not exist when generating. Reproduce a
committed report into a fresh destination with:

```sh
make eval-report EVAL_REPORT_ARGS="--revision INPUT_REVISION --output-dir /tmp/infraarch-eval-reproduction"
```

Use the input revision from `input-manifest.json`; compare report/CSV contents
and SHA-256 input hashes. No provider, database, dotenv, scanner execution,
installation or network service is needed for report generation. Run with the
already-installed backend environment. See D-55 for descriptive statistics,
run clustering and the counts-only supplemental evidence provenance.

Benchmark `results.csv` is a compact index with explicit columns and bounded
cells (16 KiB maximum). Full `telemetry`, `runtime_attribution`, detailed attempts
and any omitted oversized compact value remain in `results.json`; `details_json`
identifies the original row. Small format/token/deadline summaries remain in CSV.
Readers accept historical CSV cells above 128 KiB without rewriting old evidence.
New CSV exports use LF newlines for byte-stable committed reproductions.

The committed final report uses input revision
`e9756383b97538d8843a56d13f80eb66ab2eec1f`. Run the reproduction command from the
final Phase 9b source tree; the revision selects evidence, not the generator
implementation. `rates.csv` includes per-set/combined exact-prompt and variant
breakdowns plus run-level sensitivity. Fisher results are descriptive; shared
plans make package-level p-values optimistic. See
[Chapter 6 material](docs/thesis-notes/chapter6-evaluation.md) and
[performance gaps](docs/phase9b-performance-gaps.md).

The [proposal supplement](docs/evals/phase9b-supplement/proposal-counts.json)
contains identifiers/counts only. A separate
[complete cached-input audit](docs/evals/phase9b-supplement-inputs/source-manifest.json)
hashes all 42 source snapshots, including the zero-package failed-run snapshot;
none of the cached source contents is committed. Both projections have a
zero-finding secret scan. Report generation needs neither the cache nor live
provider access. The traceability artifact is a committed collection snapshot;
links are coverage evidence, not passing-test or deployment claims.

To repeat the optional PR-04 attribution, explicitly configure a disposable,
migrated `infraarch_test` database and export matching DATABASE_URL /
TEST_DATABASE_URL and MIGRATION_DATABASE_URL / TEST_MIGRATION_DATABASE_URL.
Use only synthetic credentials and `LLM_PROVIDER=stub`. With
`INFRAARCH_TEST_BOOTSTRAP=1` and `PYTHONPATH=backend/tests/bootstrap:backend`, run
`backend/.venv/bin/python -m scripts.phase9b_download --output-dir /tmp/infraarch-download-reproduction`
from the repository root while no other verification workload runs. The script
also disables dotenv explicitly, refuses non-test settings and restores the real
session guard after its measurement-only control. No browser, image or package
download is needed. A new destination is required; existing evidence is immutable.

### Phase 9i offline replay

[Results and limitations](docs/evals/phase9i-offline/README.md) distinguish
historical results, the immutable pre-change baseline and final isolated replay.
The 81 original packages, 28 plans and three missing variants are hashed;
source snapshots are required locally and are never rewritten or published by
the replay. No operator settings or LLMs are used. Reproduce into a separate
directory, with the existing local provider/schema mirrors and scanner binaries:

```bash
cd backend
export INFRAARCH_TEST_BOOTSTRAP=1
export PYTHONPATH="$PWD/tests/bootstrap:$PWD"
.venv/bin/python -m scripts.phase9i_replay --mode baseline --output /tmp/phase9i-replay
unshare --user --map-root-user --net .venv/bin/python -m scripts.phase9i_replay \
  --mode changes --network-isolated --workers 3 --output /tmp/phase9i-replay
.venv/bin/python -m scripts.phase9i_report --output /tmp/phase9i-replay
```

Linux user/network namespaces must be available for the final replay. Provider
downloads, remote Helm dependency fetches, scanner updates/uploads/telemetry and
external network access are disabled. Fingerprinted caches distinguish isolated
observations. The report verifies all candidate/retained bytes and idempotence,
and preserves rejected candidate findings. A newly captured baseline uses the
checked-out implementation; the committed pre-change context measurements are
historical evidence, not regenerated measurements of old code.

[Kubernetes follow-up findings](docs/evals/phase9i-kubernetes-offline/FINDINGS.md)
report retained and rejected candidate effects, per-prompt totals and runtime risks.

The Kubernetes follow-up uses a separate evidence directory and reconstructs
previous retained packages against pinned commit `c3be20c`, checking their hashes.
It records all scanner findings, blocker/profile deltas and rejected candidates.
From `backend/`, with the same bootstrap and offline mirrors:

```bash
unshare --user --map-root-user --net .venv/bin/python -m scripts.phase9i_kubernetes_replay \
  --workers 3 --output /tmp/phase9i-kubernetes-replay
unshare --user --map-root-user --net .venv/bin/python -m scripts.phase9i_kubernetes_report \
  --verify-bytes --output /tmp/phase9i-kubernetes-replay
```

The follow-up pod catalogue fills missing security/resource settings and exposes
new Helm defaults under `infraarchSecurity`, with writable paths defaulting to
`/tmp`. Literal Helm images expose their existing identities under
`infraarchImages`; latest/blank tags and untrusted registries can remain blocking.
Ports and application configuration are preserved. Archives identify retained,
current defaults as **runtime compatibility unverified**. UID/GID, read-only
filesystems, writable paths and resources remain operator-overridable through
Helm values. Static acceptance does not establish image startup compatibility.

For dotenv-disabled verification, export `INFRAARCH_TEST_BOOTSTRAP=1` and put
`backend/tests/bootstrap:backend` first on `PYTHONPATH` (absolute paths work from
both the root and `backend/`). Explicitly set `LLM_PROVIDER=stub`, empty
`LLM_API_KEY`/`API_KEY`, and synthetic `TEST_DATABASE_URL` and
`TEST_MIGRATION_DATABASE_URL` for a disposable PostgreSQL database provisioned
with the repository's owner/app/read-only roles. Also set `DATABASE_URL` and
`MIGRATION_DATABASE_URL` to those test URLs. Then run `make lint`, `make test`,
`npm --prefix frontend test -- --run` and `make test-e2e`. Never use an author's
normal database or credentials for these commands.

Documented Terraform equivalents, standard missing Helm helpers and recognised
Grafana API envelopes have guarded deterministic repairs. Subnet, backup and VPC
default-SG repairs require proven dependencies. All other invalid arguments use
schema-grounded model repair. Strict alone governs acceptance and readiness;
contextual-v1 is preserved, and experimental contextual-v2 appears alongside it
in API, archive and UI reports. Existing responses without v2 show unavailable.
