# Codex task — Phase 9k: Architect-model experiment and provider preference (preparation only)

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-56, D-57,
D-58), `docs/evals/scenarios/broad-v1.json` and its README, the broad
benchmark runner and report (`backend/scripts/phase9i_broad*.py`,
`run_phase9_benchmarks.py`), the LLM adapters and model-selection code, and
the golden-wire tests. Phases 0–9j are complete.

## Why

The author will test whether a stronger Architect model (an Anthropic Sonnet
model via OpenRouter) produces better plans — especially fewer public
load-balancer designs, the main blocker at complexity levels 4–5 — while
Generators and Fixer stay on `openai/gpt-oss-120b:nitro`. Benchmarks should
also become more reproducible through an optional preferred provider.

Context since this prompt was drafted: Phase 9j rounds 1–3 are complete, and
commit `f1dd0d7` fixed role-default leakage (an Architect choice no longer
changes Generator/Fixer models; tier-first precedence; wire tests prove
Generator/Fixer requests unchanged). Reuse that resolution path — do not add a
second one. Review decisions now carry categories (D-47); the author will
review some experiment packages with categories as input for Phase 9l.

## Rules

No real LLM calls (mocked HTTP only), no `.env` reads, no installs, no push.
Readiness, blocking criteria, profiles, thresholds and the pre-registered
scenario file stay unchanged (verify its SHA-256 `285bcb48…` in the run
manifest). No feedback/lessons injection exists or is added in this phase;
the experiment uses exactly the current prompts, and the manifest records
the Architect model, thinking level and provider settings. Plan mode first:
report where the Architect model is resolved for header-authenticated runs,
how provider routing is sent today, and which `served_by` data is recorded,
before changing code. One commit per section,
prefix `phase9k:`, requirement IDs, implementation-log entries with real test
counts.

## 1. Architect-only override

- Optional `ARCHITECT_MODEL` and `ARCHITECT_THINKING` for `make bench-broad`
  (header-authenticated runs). Generators and Fixer keep sending exactly
  today's requests. Record all five resolved selections as now.
- Golden-wire tests: with only the Architect override set, only Architect
  requests change; Generator and Fixer requests stay byte-identical.

## 2. Provider preference (optional, off by default)

- Optional `PROVIDER_PREFERENCE` (e.g. `Cerebras`) for benchmark runs: OpenRouter
  provider order with that provider first and fallbacks **allowed**.
- The preference is **per role**: a provider that does not serve the role's
  model (Cerebras does not serve Anthropic models) must not be sent for that
  role. Default: the preference applies to Generators and Fixer only; the
  Architect keeps today's routing unless `ARCHITECT_PROVIDER_PREFERENCE` is
  set. Validate against the catalogue's endpoint list and fail before the run
  if a configured provider does not serve the model.
- An error from the preferred provider falls back to the next provider
  (OpenRouter `allow_fallbacks: true`); existing retry and
  `require_parameters` behaviour stays unchanged.
- Record the serving provider per call (existing `served_by`); report the share
  of calls served by a fallback provider per run and flag runs with any
  fallback.
- Free preflight before a benchmark: query OpenRouter's model endpoint/status
  data for the preferred provider (no inference; mocked in tests). If it is
  unavailable or degraded, warn and require confirmation (or a `--force` flag).
- With the option off, requests stay byte-identical to today (golden-wire).

## 3. Model check and cost estimate

From mocked or cached catalogue data: list the pinned Anthropic Sonnet model
IDs available (never a `~`/`-latest` alias) and recommend one; confirm it
supports the strict `json_schema` the Architect uses with
`provider.require_parameters`, and how its reasoning/thinking setting is sent
through the OpenAI-compatible adapter; propose the Architect thinking level
for the experiment with a short justification; report price and context
length; estimate the extra cost per run from the broad runs' recorded
Architect token counts, and the total for a 3-run smoke and a 20-run round.
The benchmark credit guard must use this estimate.

## 4. Report

Extend the broad report to compare an experiment folder with the pooled
gpt-oss broad rounds per scenario and complexity level (same scenario file;
state that only the Architect differs), including how often each plan uses a
public/internet-facing load balancer vs a private/internal design (determined
deterministically from the plan and the generated Terraform, e.g.
`aws_lb.internal`, and listed per package so the author can audit it), how
often AWS-0053 and CKV_AWS_91 block, validity,
strict/v1/v2 checks-passed, and serving-provider/fallback statistics.

## 5. Docs and finish

D-59 (experiment method, provider preference). README: exact author commands
for a 3-run smoke (Architect override, provider preference on) and one full
broad round. Run `make lint`, `make test`, `make frontend-test`,
`make test-e2e`, `make secret-scan` and a stub rehearsal of the experiment
(real counts). Summary in the `AGENTS.md` §10 format, with the per-run cost
estimate.
