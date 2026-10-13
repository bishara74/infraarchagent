# Codex task — Phase 9: Evaluation tooling and evidence (Chapter 6)

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md`, the latest
entries of `docs/IMPLEMENTATION_LOG.md`, and in `docs/spec/03-requirements.tex`:
PR-01 to PR-05, NFR-01 to NFR-04, and the traceability matrix
(TC-pipeline-01, TC-security-01, TC-ui-01, TC-generator-01, TC-perf-01,
TC-adapter-01, TC-review-01). Phases 0–8c are complete.

## How this phase works (important)

Phase 9 produces the **measured evidence** for the thesis testing chapter.
Several measurements need the **real** LLM (PR-01, PR-03, PR-05). You may not
make real LLM calls or read `.env`. So the work is split:

- **You (Codex)** build the measurement tools, test them thoroughly with the
  stub and recorded data, and write the report generator.
- **The author** runs the real measurements with the commands you document,
  on a quiet machine.
- **A short follow-up (Phase 9b)** turns the author's raw results into the
  final report. Don't invent or estimate any numbers in this phase.

## Rules

- No real LLM calls, no `.env` reads, no installs or downloads, no push.
- No new Python or npm dependencies. Use the standard library, httpx (already
  present) and the existing app code. Don't generate charts here; raw CSV/JSON
  is enough (charts are made later for the thesis).
- One commit per numbered section, prefixed `phase9:`, with requirement IDs
  and an implementation-log entry.
- Every tool writes raw results under `docs/evals/phase9-<name>-<UTC timestamp>/`
  plus a `summary.md`, and records the environment (CPU model and count, RAM,
  OS/WSL version, Python/Node/tool versions, git commit, provider and models,
  and whether the run was real or stub).

## 0. Clear provider-error categories

On a real run the UI said "Architecture planning could not reach the
language model", but the provider had actually answered **HTTP 403
"Key limit exceeded"** (the author's OpenRouter key hit its spending cap).
The message must say what happened, safely:

- In the LLM adapters, classify provider failures into a small set of safe
  categories: `auth_failed` (401), `usage_limit` (402, or 403 whose body
  says the key/credit limit is exceeded), `model_unavailable` (404),
  `rate_limited` (429), `provider_error` (5xx), `unreachable` (connection or
  DNS failure, timeout), `invalid_response`.
- The agent/run error message uses a fixed, safe sentence per category
  (e.g. "The LLM provider refused the request: usage limit reached."). No
  provider body text, URLs, key IDs or amounts in messages, events,
  responses or logs; the category name may be logged.
- Retry policy: `auth_failed`, `usage_limit` and `model_unavailable` are not
  retried (fail fast); the others keep the current retry behaviour.
- Tests with mocked HTTP responses for every category, plus the existing
  canary tests over the new messages.

## 1. Requirement traceability report

- `make traceability` → a script that:
  - extracts every requirement ID (FR-*, NFR-*, PR-*, UC-*) from
    `docs/spec/03-requirements.tex`;
  - collects which tests cover each ID: pytest `req` markers (via
    `--collect-only`), Vitest test names and Playwright titles that contain
    the IDs;
  - maps them to the seven TC groups of the traceability matrix (define the
    mapping in one data file and explain it);
  - writes `traceability.md` (table: requirement → test files/counts → TC
    group) and `traceability.json`, and lists **uncovered IDs** explicitly.
- Don't change requirement IDs. Don't add tests just to tick boxes in this
  section; just report. If something important is uncovered, list it in the
  summary.

## 2. Secret scanning (NFR-01)

NFR-01 asks for an automated secret-scanning check.

- `make secret-scan` → scan the **working tree and the full git history**
  for credentials, using a built-in Python scanner (standard library only):
  patterns for OpenRouter (`sk-or-`), Anthropic (`sk-ant-`), OpenAI (`sk-`),
  AWS access keys, private-key blocks and generic `*_API_KEY=<value>`
  assignments with real-looking values. It must ignore the documented
  placeholders in `.env.example` and the known test canary values, skip
  `.env` itself (never open it), `node_modules`, `.venv` and `.cache`, and
  print only file, line/commit and pattern name, **never the matched
  value**.
- Exit non-zero on any finding. Tests with temporary repositories containing
  planted fake keys (in the working tree and in an earlier commit) and
  clean ones.
- Document in D-42 why a built-in scanner instead of gitleaks (no new
  installs; offline), and what it does not catch.

## 3. Benchmark harness (PR-01, PR-03, PR-05)

Add `backend/scripts/benchmark.py`, run against a **running** backend over
its HTTP API (`--base-url`, default `http://127.0.0.1:8000`), with
subcommands:

- `pr01 --runs N` (default 10): sequential runs from one fixed prompt set
  (use the three example prompts in rotation; store the exact texts in the
  results). Per run record:
  - submit time → the time the run is terminal **and** no package is active
    (`scanning`, `remediating`, `validating`), using the SSE stream and a
    final results check; that is the PR-01 duration;
  - run status and each package's final status;
  - per-agent wall-clock durations from event timestamps (PR-05): Architect,
    each Generator, each SecurityAgent iteration per package, Validator;
  - LLM attempt counts and token totals from the stream/report data where
    available.
- `pr03`: one isolated baseline run, then 3 simultaneous runs; record each
  wall-clock time and the ratio to the baseline (PR-03 allows ≤ 1.5×). Also
  record the server's runner capacity setting; if it is below 3, stop with a
  clear message (don't change it silently).
- `--mode real|stub`: `stub` sends `{"provider": "stub"}` (free; measures
  system overhead only); `real` uses the server's configured provider.
- **Cost tracking and budget guard (real mode).** Before and after each run,
  read the remaining credit from the provider's key-info endpoint
  (`GET {LLM_BASE_URL}/key` for OpenRouter), using the settings' `SecretStr`
  inside the script, never printing or saving the key, its ID or the raw
  response. Record the cost delta per run. `--budget-usd X`: stop before a
  run when the remaining credit is below `max(X, 2 × the highest per-run cost
  so far)`, and write partial results plus the reason. If the endpoint isn't
  available (non-OpenRouter provider), record cost as unknown and require
  `--max-runs` instead.
- Output: `results.csv` (one row per run), `agents.csv` (one row per agent
  timing), `summary.md` with median, p90 and max, pass/fail against PR-01
  (median ≤ 300 s), PR-03 (each ≤ 1.5× baseline) and PR-05 (per-agent
  thresholds: Architect ≤ 150 s, each Generator ≤ 150 s, one security
  iteration ≤ 60 s per package), plus the total cost.
- Tests: the harness against the stub backend in-process (or the test
  server), with a fake key-info endpoint for the budget guard (normal,
  low-budget stop, unknown cost), and a check that no output contains a
  canary key.

## 4. PR-04 download measurement

- `backend/scripts/seed_benchmark_package.py`: create one clearly marked
  synthetic run with a labelled ~10 MB package (non-trivially compressible,
  seeded content) in the **dev** database through the existing repositories
  and state rules, printing the run ID. Mark it in the run input text as
  "benchmark synthetic package" so it's never mistaken for a real run.
- `benchmark.py pr04 --run-id ID --repeat 10`: download the ZIP through the
  real HTTP endpoint and record total time per request (like `curl -w
  %{time_total}`), with median and max against PR-04 (≤ 2 s).

## 5. PR-02 and quiet-machine timing

- Document how to run the existing frontend `@perf` Playwright test and the
  backend `make test-perf` on a quiet machine, and have both write their
  results into the same `docs/evals/phase9-…` structure with the environment
  record.

## 6. One command for the author

- `make bench-stub`: the stub benchmark set (pr01 with 10 runs, pr03, pr04
  with a seeded package), so the author can rehearse the whole procedure for
  free.
- `make bench-real BUDGET=…`: pr01 (10 runs) and pr03 in real mode with the
  budget guard.
- README: a "Running the Phase 9 measurements" section with exact steps
  (start the backend, which port, quiet-machine advice, budget, where the
  results go).

## 7. Documentation

- D-42 (secret scanner) and anything else you decide.
- "Thesis text to update": NFR-04 still names tfsec 1.x (now Trivy); note
  the PR-03 method (stub vs real mode) and the cost-tracking method.
- Implementation log per commit with real test counts.

## 8. Out of scope

- Running real benchmarks, estimating results, or writing thesis text.
- Phase 10 packaging (Dockerfiles, clean-Ubuntu install).
- Changes to agents, scanners, validator or UI beyond section 0's error
  message.

Finish with `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make traceability` and `make secret-scan` (report real results), and
`make bench-stub` once, with its summary. Summary in the `AGENTS.md` §10
format.
