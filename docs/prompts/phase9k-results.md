# Codex task — Phase 9k results: document the Architect experiment

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-59),
`docs/evals/phase9k-architect-report/` (report.md, experiment-*.json/csv,
architect-diagnostics.json, provider-routing.json), the two experiment folders
`docs/evals/phase9-bench-broad-smoke-20261024T220546075719Z` and
`docs/evals/phase9-bench-broad-20261024T233240471733Z`, the LLM adapter
(`backend/app/llm/`), its golden-wire tests, `backend/scripts/phase9b_report.py`
and `docs/thesis-notes/chapter6-evaluation.md`.

## Rules

No real LLM calls, no `.env` reads, no installs, no network, no push. Do not
change committed evidence folders, prompts, readiness, profiles or thresholds.
Plan mode first. Prefix `phase9k:`, requirement IDs, implementation-log
entries with real test counts.

## 1. Record the results (D-59 and thesis notes)

Recompute every number from the committed evidence and report any mismatch
with the author's figures below instead of copying them:

- Full round: strict checks_passed 24/56 (42.9%) vs pooled gpt-oss 43/120
  (35.8%), Fisher p ≈ 0.41; 4 missing variants.
- Levels 1–3: passed 24/30 vs 39/60 (p ≈ 0.22); valid 28/30 vs 43/60
  (p ≈ 0.026). Levels 4–5: passed 0/26 vs 4/60 (p ≈ 0.31); valid 8/26 vs
  29/60 (p ≈ 0.16).
- Plans at levels 4–5: Sonnet planned a public LB in 10/10 runs (never
  internal); gpt-oss planned none in 12/20 runs, while Generators still
  produced public LBs (e.g. scenario 7). AWS-0053 remains the top blocker.
- Routing: Cerebras served all Generator/Fixer calls, 0 fallbacks; all
  Architect calls served by Claude Platform on AWS.
- Truncation: 8 `finish_reason=length` calls, all gpt-oss Fixer; none from
  the Architect.
- Cost: measured known cost from the evidence; Architect share as recorded.
- Canonical model snapshot reported by OpenRouter for the author's inspected
  request: `anthropic/claude-sonnet-5.5-20260928` (author-observed in the
  OpenRouter activity view; label it as such).

Statistics wording: package-level Fisher tests; level splits are
**exploratory, chosen after seeing the data**, uncorrected for multiple
comparisons, and packages of one run share a plan (add run-level tests where
the data allows). Historical code/prompt differences remain confounders.

Interpretation to record (as the author's reading, not a causal claim): a
much stronger Architect improves validity on simpler scenarios but does not
remove the level 4–5 wall; the public LB follows from internet-facing
requirements and appears even when the plan omits it, so the blocker lies
downstream of plan quality.

## 2. Thinking limitation (offline wire check, no fix)

All 42 Architect calls report `reasoning_tokens=0` although
`reasoning_effort=medium` was requested; the author's billing check
(2,245 in / 1,260 out = $0.0171) shows no hidden reasoning output. From code
and golden-wire tests only, report exactly which reasoning fields the adapter
sends for this model through OpenRouter, how `response_format` is combined,
and from which response field `reasoning_tokens` is parsed. List possible
causes as **unverified hypotheses**; do not cite provider documentation from
memory. Record in D-59: "thinking requested at medium; no reasoning tokens
reported or billed; the experiment therefore tests a stronger Architect model
without extended thinking". Do not change the adapter.

## 3. Bug: eval-report output directory

`make eval-report` runs from `backend/`, so a relative `--output-dir`
(e.g. `docs/evals/x`) is written to `backend/docs/evals/x`. Resolve relative
output directories against the repository root (absolute paths unchanged),
refuse paths outside the repository, and add tests. Update the README
example.

## 4. Future work

Add to the thesis notes and D-59: an Architect run with verified extended
thinking; CloudFront VPC origin in front of an internal ALB for levels 4–5;
KSV-0125 remains a limitation.

## Finish

Run `make lint`, `make test`, `make secret-scan` (real counts). One commit per
section. Summary in the `AGENTS.md` §10 format, starting with any number that
differs from the author's figures.
