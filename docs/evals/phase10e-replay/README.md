# Phase 10e — offline detect-only replay

Both author exports are evaluated against their matching frozen benchmark source
projections. All 348 canonical plan/original/retained hashes match before native
work begins. Raw exports and observation caches remain uncommitted.

| Measure | final2 | final3 | Combined |
|---|---:|---:|---:|
| Retained packages | 59 | 57 | 116 |
| Matching canonical hashes | 177 | 171 | 348 |
| Security iterations with conformance reason | 51 | 62 | 113 |
| Security iterations with conformance as sole reason | 46 | 55 | 101 |
| Weighted error-class counts (including unknown) | 65 | 66 | 131 |
| Packages with security conformance reason | 21 | 24 | 45 |
| Partial-group conformance rejections | 58 | 62 | 120 |
| Validation Fixer conformance rejections | 15 | 19 | 34 |
| Deterministic validation conformance rejections | 16 | 0 | 16 |
| Catalogue conformance rejections | 4 | 0 | 4 |
| Reconstructable candidate occurrences | 30 | 0 | 30 |
| Distinct reconstructable candidate file pairs | 14 | 0 | 14 |
| Candidates accepted before / after | 26 / 26 | 0 / 0 | 26 / 26 |
| Candidates rejected for new blockers before / after | 4 / 4 | 0 / 0 | 4 / 4 |
| Newly cleared current-baseline guard rejections | 0 | 0 | 0 |
| Final retained packages with confirmed conflict | 0 | 0 | 0 |
| Final retained packages with informational notes | 34 | 39 | 73 |

## What these counts mean

Recorded conformance reasons are retired acceptance gates, not proven recovered
fixes. Other gates still apply, including deadlines when a historical attempt
recorded both causes. The 101 sole-conformance reasons must not be represented as
101 accepted candidates or passes. Partial groups, validation rounds, catalogue
records and weighted error classes are different units and must not be summed.

Paired candidates compare the pre-10e revision
`69ff06758eee01afe77b87a46221c8ed4b48ac4d` with current acceptance. Phase 10d
had already cleared all guard rejections among final2's available deterministic
proposals. Their current-baseline decisions therefore stay 26 accepted / four
new-blocker rejections, across 30 occurrences and 14 distinct source pairs.
Final3 has no reconstructable rejected deterministic candidate bodies in the
supported replay paths. Its model proposals are not invented. There are zero
newly demonstrated guard-cleared candidates in this available subset.

The final-stage check assesses exact frozen retained files independently of
scanner findings: zero confirmed conflicts, 73 packages with information only.
This says nothing about the missing rejected candidates' exposure changes or the
trajectory of a future detect-only run. The three historical ALB flips are instead
covered by fixed regression fixtures: the flip is retained when other gates pass,
but final readiness is pending_review with plan_conformance_conflict.

The author's task rationale supplied approximately 66 counted security rollbacks
in 19 packages for final3. This raw inventory finds 62 reason-bearing security
iterations in 24 packages, with 66 weighted error-class counts. The rationale is
preserved as supplied in D-66; its approximate 19-package figure is not reproduced
by this raw reason-bearing inventory. These counting units are kept explicit.

## Missing evidence and reproduction

Exact security baselines reconstruct for 58/59 final2 and 56/57 final3 packages.
One accepted post-security patch is absent in each cohort. Missing-body records
cover 114 / 98 rejected security attempts and 83 / 63 rejected validation attempts
across all reasons; they are not exclusively conformance rejections. Two final2
EIP contexts cannot be matched. Per-cohort missing.json retains the identities.

The [manifest](manifest.json) pins input hashes, baseline revision, native tool
versions, provider schema and application source hashes. Paired checks use current
offline tools and identical runtime-scoped caches; they do not reproduce historical
wall-clock deadlines. Final detection does not require rescanning every retained
package. Native checks/scans are used for the reconstructable paired proposals.
A report-only regeneration added complete before/after decision counts, with
identical native identity and all previous totals; see
[verification](../phase10e-verification/replay-regeneration.json).

From the repository root, with the existing offline tools and provider mirrors:

```bash
INFRAARCH_TEST_BOOTSTRAP=1 \
PYTHONPATH="$PWD/backend/tests/bootstrap:$PWD/backend" \
backend/.venv/bin/python -m scripts.phase10e_replay \
  --output-dir "$PWD/docs/evals/phase10e-replay-new"
```

Inputs: `.cache/broad-final2-results/` corresponds to
`phase9-bench-broad-20261027T155607468680Z`; `.cache/broad-final3-results/`
corresponds to `phase9-bench-broad-20261027T205119472235Z`.
No real model calls, downloads or external services are used.
No pass-rate, causal recovery or cloud deployment claim follows from this replay.
