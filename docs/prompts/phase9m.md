# Codex task — Phase 9m: findings from the author's lesson test

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-58 to D-60),
the latest `docs/IMPLEMENTATION_LOG.md` entries, the results overview and cost
display (frontend and `backend/app/pipeline/results.py`), the deterministic
repair stage and generation gate, the validation runner (Terraform
init/validate, Helm, promtool), the LLM adapters and prompt builders, the
startup/health code and the migrations. Phases 0–9l are complete.

## Context (author's manual test, 2026-10-26)

Two real ECS runs with the same prompt (without and with one approved
lesson). Observations:

- All three result cards showed "Estimated infrastructure cost: unavailable".
- The performance Generator produced a second `resource "aws_lb" "api_alb"`
  block containing only `access_logs` in **both** runs; it is already present
  in the Generator's original output, and `terraform validate` fails on it.
- After the Phase 9l update, the real database was not migrated: the UI showed
  "Saved preferences could not be loaded" and the API returned 500
  (`column pipeline_runs.lessons does not exist`).

## Rules

No real LLM calls, no `.env` reads, no installs, no network, no push.
Readiness labels, blocking rules, profiles, scanners and thresholds unchanged.
Plan mode first: report findings for every section before changing code.
One commit per section, prefix `phase9m:`, requirement IDs,
implementation-log entries with real test counts. D-61 for decisions.

## 1. Cost estimate on the result cards

Find why the estimate is unavailable (not produced, not persisted, not
returned, or not rendered). Report the root cause. If the design intends an
estimate, fix it; never invent prices — use only data the system already has
and label the basis. If no estimate is produced by design, replace the line
with an accurate explanation instead of "unavailable".

## 2. Deterministic duplicate-block repair

Add a repair, inside the existing deterministic repair stage, for duplicate
Terraform blocks with the same type and name:

- Merge only when it is provably safe: the blocks have no conflicting
  arguments or nested blocks (the later block only adds arguments or nested
  blocks missing from the first, e.g. `access_logs`). Otherwise leave the
  files unchanged and keep the validation failure.
- Record the repair like the existing repairs (event, report entry, origin).
- Tests: the observed `aws_lb` + `access_logs` case, conflicting duplicates
  (no merge), identical duplicates, other resource types, `.tf.json`.
- State in D-61 that this changes generated packages, so future benchmark
  rounds are not byte-comparable with earlier ones for affected packages.

## 3. Database version check

At startup and in `/api/health`, detect when the database schema is behind
the code's latest migration. Then refuse to serve normal API requests with a
clear error ("database schema is at X, code expects Y — run `make migrate`"),
log it once, and show it in the UI instead of generic failures. No automatic
migration. Tests for behind, current and ahead.

## 4. Request-path threat model (audit, fix only real gaps)

Confirm from code and tests, with file references:

- Which tools run on generated files, with which arguments; that no
  `terraform plan`/`apply`, provisioners or `external` data sources are
  executed; whether `terraform init` can fetch remote modules or providers
  (network, module sources such as git/http/registry) and how this is
  prevented; Helm/promtool behaviour on untrusted input.
- That API keys and credentials never appear in prompts, logs, events or
  packages; how the user request is placed in the prompt and its length
  limit.
- Subprocess isolation: working directories, environment passed to tools,
  timeouts, cleanup.

Write the result as a "Request-path threat model" section in D-61 and the
thesis notes, contrasting direct injection (affects only the requester's run;
outputs untrusted and checked deterministically) with stored injection
(lessons, D-60). If a real gap is found (for example remote module fetching),
report it first and propose the fix; implement it only if it is small and
does not change readiness behaviour, with tests.

## 5. Gated actions in the UI

Audit every button or control that is disabled or conditional (for example
Download all three, Download this variant, Approve/Reject, Retry, Propose a
lesson, lesson approval, runtime switch). For each, report the condition and
what the user sees today. Every unavailable action must state why and what
to do next (for example "Review Cost and Performance first", with links to
those reviews), visible on hover, focus and click, and announced to screen
readers. Do not change any rule that decides availability. Vitest and
Playwright for each control.

## 6. Lesson filter false positive

The author's legitimate lesson was blocked with "Describe one preference
without shell or Terraform code":

> Configure load balancer access logs inside the one existing load balancer
> resource; never declare the same Terraform resource name twice

The author found that removing the semicolon made the same text pass, so the
likely trigger is treating any `;` as a shell command separator. Confirm
which rule matched. A semicolon between plain-English clauses must not count
as shell syntax on its own; shell detection needs real shell context (for
example a command-like token next to `;`, `&&`, `||`, `|`, `$(`, backticks or
redirections). Tune the Terraform/shell rule to detect code
syntax (block headers like `resource "type" "name" {`, braces,
`argument = value` assignments, shell operators, command lines) instead of
plain words such as "Terraform" or "resource". Add this sentence and similar
plain-English lessons as benign corpus cases that must pass; every existing
attack case must still be blocked. Bump the filter version (v2), keep v1
results reproducible, and report corpus results per layer for v1 and v2.

## Finish

Run `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make test-perf` and `make secret-scan` (real counts). Summary in the
`AGENTS.md` §10 format, starting with the root causes for sections 1 and 3 and
any gap found in section 4.
