# Codex task — Phase 10g: does remediation reduce violations on every package? (analysis only)

Fresh session. Read `AGENTS.md`, `docs/spec/01-introduction.tex` (success
criteria, read only), D-44 to D-66, `docs/evals/phase10f-final-report/`, the
security report model (first-scan and final counts) and the committed
benchmark evidence folders. The `v1.0` tag exists; this task adds analysis
only.

## Question

The introduction's success criterion says: "The SecurityAgent reduces the
violation count on every generated package; packages with unresolved
violations after the configured iteration limit are delivered with
violations clearly flagged." Determine from recorded evidence whether this
holds, and how to state it accurately in the thesis.

## Rules

Read-only with respect to the application: no changes to application, test,
configuration or `docs/spec/` files, and no changes to committed evidence. You
may add one analysis script under `backend/scripts/` with a focused unit
test, and a new report folder. No `.env` reads, no network, no installs, no
LLM calls, no push. Plan mode first: report which data sources hold
per-package first-scan and final counts for which rounds, before writing
anything. Commit prefix `phase10g:`.

## Analysis

For every package with the needed data, in every committed benchmark round
(final sets, broad rounds 1 and 2, the Sonnet experiment, the 10b–10d rounds,
the final 10e round), using committed evidence and, where needed,
hash-verified `.cache/` exports:

1. Compare the first scan with the final retained package for:
   blocking findings under the strict profile; HIGH/CRITICAL findings
   (combined Checkov + Trivy, as recorded); all findings if recorded.
2. Classify each package: reduced, unchanged (non-zero), already zero at
   first scan, increased, unknown (missing data). Never treat missing data
   as reduced.
3. For every unchanged or increased case, give the recorded reason (for
   example all fixes rolled back, deadline, Fixer unavailable, validation
   failure, scan error, findings introduced by deterministic templates or
   validation repair, file-input refusal) and the rule IDs involved.
4. Check that every package with unresolved violations ended in
   `pending_review` with those findings visible (the second half of the
   criterion), and list any exception.
5. Report per round, per complexity level and pooled (final round
   separately), with counts and percentages; distinguish "reduced"
   (strictly fewer) from "not increased".

## Output

A new folder `docs/evals/phase10g-remediation-effect/` with README (method,
tables, exceptions, limitations), a CSV per package, and an input manifest
with hashes. Then propose an accurate one-paragraph wording of the success
criterion's outcome for the thesis (for example "reduced on X of Y packages,
never increased" or a precise qualification). Add a short note to D-66 and the
thesis notes linking the report. Run `make lint` and `make secret-scan`
(real counts). Summary in the `AGENTS.md` §10 format, starting with the
pooled and final-round classification counts.
