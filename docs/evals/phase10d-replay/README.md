# Phase 10d section 3 — paired offline rerun replay

This report compares the accepted diagnosis revision `d7f82a1` with the Phase 10d
fixes, using the frozen `phase9-bench-broad-20261027T155607468680Z` cohort.
All 59 generated packages receive fresh retained-file observations. The 20 raw
exports remain uncommitted under `.cache/broad-final2-results/`; all 177 canonical
plan/original/retained hashes match committed projections. No real inference,
credentials, dotenv read, install, provider download or external network service
is used. Historical results and source bytes are unchanged.

## Measured counts and denominators

| Observation | Before | After | Denominator |
|---|---:|---:|---|
| Empty rollback reason exports | 52 attempts / 65 error-class counts | 0 / 0 | Re-export all frozen raw reports |
| Unknown repair reason exports | 15 attempts / 33 error-class counts | 0 / 0 | Re-export all frozen raw reports |
| Terraform-unavailable candidate rejections | 12 | 0 | Available paired supporting-resource candidates |
| Plan-conformance candidate rejections | 18 | 0 | Available paired catalogue/EIP candidates |
| Accepted paired candidates | 0 | 26 | 30 proposal occurrences |
| New-blocker candidate rejections | 0 | 4 | Same 30 occurrences, remaining gates enforced |
| Derived partial groups discarded | 46 | 4 | Derived groups of those available proposals |
| Derived partial groups kept | 0 | 42 | Same 46 derived groups |
| Conditional frozen finding resolutions | 0 | 7 | Union of identities removed by accepted pairs |

The 30 occurrences are **14 distinct source/plan/variant/action pairs**: 13
accepted and one rejected for new blocking findings. They comprise eight
access-log occurrences, four KMS supporting-resource occurrences, four catalogue
occurrences and 14 hash-matched EIP repair records. The duplicate identity includes
run, variant, action and both source-map hashes; iteration/repair-record indexes
are occurrence identifiers, not distinct proposal identities.

The seven conditional identities are CKV_AWS_18 (1), AWS-0132 (2), CKV_AWS_145 (2),
AWS-0164 (1) and CKV_AWS_130 (1). Unchanged file-input refusals do not disappear:
all five frozen TERRAFORM_FILE_INPUT blocker identities remain in the fresh
retained observations. Retained validation is 25 valid / 29 invalid / five errors.
This is validation of unchanged bytes, not a new package pass rate.

The historical 17 unavailable rolled-back iterations and 138 discarded groups
remain historical observations. The available-candidate denominator above is
separate: **12→0 is not a replay of all 17 missing focused candidates, and
46→4 must not be subtracted from 138**. A supporting candidate and a focused
candidate can occur in the same iteration. Derived groups are reconstructed
from available deterministic candidates, not fabricated historical Fixer bodies.

## Reconstruction and limits

[summary.json](summary.json) gives totals; [candidates.json](candidates.json),
[groups.json](groups.json) and [packages.json](packages.json) retain decisions,
source hashes, native observations and package keys. [manifest.json](manifest.json)
records input hashes, baseline revision, evaluator source hashes, installed tools
and the provider-schema manifest hash. Raw sources and the observation cache stay
under `.cache/` and are never committed.

Security session diffs reconstruct exactly in 58 packages; one accepted
post-security validation repair has no patch. All retained iteration diffs are
applied with exact context checks and final-byte equality checks. The 118 changed
retained iteration pairs gain **zero new conformance rejections** in the structural
conformance audit; that audit does not claim a fresh full-gate replay of every
historically retained Fixer candidate.

Deterministic catalogue and supporting-resource candidates follow recorded order
and retained decisions. EIP proposals are admitted only when their changed-file
before/after hashes match a recorded repair, using known package snapshots.
This proves that file's transformation identity, not every byte of an otherwise
missing historical whole-package validation-repair context. Fourteen of sixteen
EIP records match; two unmatched contexts are explicitly omitted.

[missing.json](missing.json) lists the 114 rolled-back security iterations without
complete exported focused candidate bodies, 83 rejected validation-repair rounds
without complete exported bodies, one missing accepted post-security patch and
two unmatched deterministic contexts. These are evidence-availability identifiers;
they do not prove that an otherwise unrecorded complete LLM response existed.
No missing model proposal is invented or credited with an improvement.

Candidates use independent recorded/reconstructed baselines. Identical native
observations are cached against source, plan, variant, evaluator, configuration,
tools and provider-schema identity. Both guards run the same remaining checks;
validation-repair proposals additionally require validation improvement. Derived
groups use the unchanged grouping algorithm and six-group cap. Generous replay
budgets do not reproduce historical deadlines or a cumulative new trajectory.
No deployment success, exclusive historical causal attribution, new pass rate,
or simultaneous resolution of all seven findings follows from this replay.

## Reproduction

From the repository root, with the author's existing exports and offline tools:

```bash
INFRAARCH_TEST_BOOTSTRAP=1 \
PYTHONPATH="$PWD/backend/tests/bootstrap:$PWD/backend" \
backend/.venv/bin/python -m scripts.phase10d_replay \
  --output-dir "$PWD/docs/evals/phase10d-replay-new"
```

Use a fresh output directory. The bootstrap disables dotenv before application
imports. Verification and the single author-run real command are documented in
[phase10d-verification](../phase10d-verification/README.md).
