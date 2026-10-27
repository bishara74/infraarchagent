# Codex task — Phase 10e: plan-conformance guard becomes detect-only

Fresh session. Read `AGENTS.md`, D-63 to D-65, the 10b/10c/10d entries in
`docs/IMPLEMENTATION_LOG.md`, the plan-conformance guard, candidate
acceptance (`backend/app/security/acceptance.py`), validation repair, the
readiness/review-reason logic and the 10b replay fixtures.

## Why (author decision)

Two final rounds after 10b–10d each reached 11 passes (22/116 = 19%) versus
42/120 (35%) before 10b (Fisher p ≈ 0.008). In the latest round
`docs/evals/phase9-bench-broad-20261027T205119472235Z`,
`plan_conformance_regression` is the most frequent rollback reason (about 66
counted security rollbacks, 19 packages), and the guard even rejects
validation repairs that only add missing `variable` declarations. The guard
was built to prevent one rare outcome: a false `checks_passed` after the
Fixer weakens a planned public exposure (3 confirmed cases in 998 historical
packages). Blocking costs far more than it protects.

## Change

Make the plan-conformance guard **detect-only**:

- Remove every rollback or rejection whose only reason is
  `plan_conformance_regression`, in security iterations, partial groups,
  deterministic/supporting candidates and validation repair. All other
  gates (syntax, references, Terraform regression, new blocking findings,
  security-control removal, deadlines, file-input refusal) stay exactly as
  they are.
- After the security and validation stages, compare the **final retained
  files** with the plan and the Generator original. If a planned public
  service's exposure was weakened (for example `internal`/`scheme` changed to
  internal, moved to private-only subnets, required listener or ingress
  removed) or a planned private service became public, the package **must
  not** receive `checks_passed`: it goes to `pending_review` with the
  existing review reason `plan_conformance_conflict` and a clear explanation
  naming the service, resource and property. Unknown or ambiguous bindings
  never block fixes; they only add an informational note, and they never
  prevent `checks_passed` on their own.
- Keep the Fixer prompt v8 and its plan network context unchanged.
- Keep the 9m file-input refusal and its blocking finding unchanged.
- Readiness rules, profiles, scanner rules and thresholds unchanged.

## Rules

No real LLM calls, no `.env` reads, no installs, no network, no push. Do not
modify committed evidence. Plan mode first: list every code path that
currently rolls back or rejects on `plan_conformance_regression`, and the
final-stage check you will add, before changing code. Commits prefix
`phase10e:`, requirement IDs (FR-S-02, FR-S-03, FR-S-07), implementation-log
entries with real counts, D-66 (record the decision, the evidence above and
that this round counts as the final result regardless of outcome).

## Verification

- The three historical ALB flips (10b replay fixtures): the flipped files
  are no longer rolled back, but each package ends in `pending_review` with
  `plan_conformance_conflict` and **never** `checks_passed`.
- A package where a fix only adds variable declarations, logging,
  encryption or an EIP `domain` migration: no guard involvement.
- Ambiguous bindings: fixes proceed; no `checks_passed` block from ambiguity
  alone.
- Offline replay over `.cache/broad-final2-results/` and the latest round's
  packages if exported: report how many guard rollbacks disappear, and how
  many packages would be flagged by the final-stage check. No pass-rate
  claim.
- Run `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
  `make test-perf`, `make secret-scan`, traceability and evidence index.

## Finish

Summary in the `AGENTS.md` §10 format, then the exact command for the
author's final round (backend on port 8765, benchmark environment, no
Architect override). State in D-66 and the summary that this next round is
the final reported result.
