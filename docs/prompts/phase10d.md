# Codex task — Phase 10d: remaining final-round regression in simple scenarios

Fresh session. Read `AGENTS.md`, D-56 to D-64, the 9m/10/10b/10c entries in
`docs/IMPLEMENTATION_LOG.md`, `docs/evals/phase10c-diagnosis/`,
`docs/evals/phase10c-replay/`, and the security loop, candidate acceptance
(`backend/app/security/acceptance.py`), plan-conformance guard, file-input
guard, validation repair and partial-group code.

Raw results API exports (ignored, never commit `.cache/`):

- round 2 (19/60): `.cache/broad-2-results/`
- regression round (7/60): `.cache/broad-final-results/`
- **rerun after 10c (11/59): `.cache/broad-final2-results/`**, committed
  evidence `docs/evals/phase9-bench-broad-20261027T155607468680Z`

## Symptoms (rerun after 10c vs round 2, same scenarios and models)

- Levels 1–3: **10/30** vs 39/60 pooled earlier (Fisher p ≈ 0.007).
  Scenario 1 (private S3 backup bucket, no internet exposure): **1/6** vs
  10/12; scenario 4 (private EC2 with SSM): 1/6 vs 8/12. Levels 4–5
  unchanged (1/30 vs 4/60).
- From `quality.json`, rerun vs round 2:
  - security rollbacks **with an empty reason: 65** vs 9;
  - rollbacks `terraform_verification_unavailable`: **17** vs 0;
  - validation-repair rejections with reason `unknown`: **~20** vs 0;
  - partial groups discarded 138 vs 72; accepted security fixes 74 vs 94;
  - validation gate `error`: 5 vs 0; `plan_conformance_conflict` in 16
    packages.

The 10c replay covered only rejections recorded as guard decisions; the
empty-reason rollbacks, `terraform_verification_unavailable` and `unknown`
repair rejections were not explained.

## Rules

No real LLM calls, no `.env` reads, no installs, no network, no push. Do not
modify committed evidence. Profiles, scanner rules, blocking rules and
thresholds unchanged. The guarantees stay: planned public exposure is never
weakened (the three historical ALB flips stay rejected), and dynamic file
reads stay blocked. **Plan mode first: complete section 1 and report before
changing code.** One commit per section, prefix `phase10d:`, requirement IDs,
implementation-log entries with real counts, D-65.

## 1. Diagnosis

- For every empty-reason rollback, every `terraform_verification_unavailable`
  rollback and every `unknown` validation-repair rejection in the rerun:
  identify the exact code path that produced it and why no reason was
  recorded. Tabulate by path, scenario and variant.
- Compare scenarios 1 and 4 stage by stage with round 2 (same scenario
  slots): generation validity, deterministic repairs, fixes proposed /
  accepted / rolled back by reason, final blockers. Name what makes these
  packages fail now.
- Check whether any check that cannot evaluate (file-input refusal,
  Terraform evaluation unavailable, unknown binding) causes **whole**
  candidates or partial groups to be discarded although the rejected part
  is unrelated to the refusal.
- Attribute the level 1–3 decline to causes with numbers; state what stays
  unexplained (model variance).

## 2. Fixes (proven causes only)

- Every rollback and rejection records a specific reason; no empty or
  `unknown` reasons from new code paths.
- A refusal or unavailable evaluation must only reject the changes it
  actually concerns; unrelated fixes and partial groups proceed through the
  normal gates.
- Keep fail-closed behaviour on the exposure path and for file reads.

## 3. Verification

- Regression tests from real rerun cases (synthetic copies), including at
  least one scenario-1 package, plus the 10b replay fixtures.
- Offline replay over the rerun packages: before/after counts of
  empty-reason rollbacks, `terraform_verification_unavailable`, `unknown`
  rejections, discarded partial groups and conditionally resolved findings.
  No pass-rate claim.
- Run `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
  `make test-perf`, `make secret-scan`, traceability and evidence index.

## Finish

Summary in the `AGENTS.md` §10 format, starting with the diagnosis table,
then the replay counts, then the exact rerun command (backend on port 8765
with the benchmark environment and no Architect override).
