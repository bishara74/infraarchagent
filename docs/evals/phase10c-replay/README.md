# Phase 10c section 3 — offline final-round replay

This replay compares the section-1 guard at `95cdb9f` with the section-2 fixes
at `ce205ea`. The frozen cohort is
`phase9-bench-broad-20261027T015443795826Z`: 20 runs and 60 packages.
The author-exported source snapshots and observation cache remain uncommitted
under `.cache/`. No inference, credentials, dotenv reads, downloads, installs,
deployment or provider API calls are used.

Machine-readable totals are in [summary.json](summary.json), per-package
observations in [packages.json](packages.json), and proposal comparisons in
[candidates.json](candidates.json). [manifest.json](manifest.json) records raw
input hashes, baseline revision, runtime source hashes, provider-schema manifest
hash and installed tool versions. All 180 plan/original/retained canonical hash
checks must match the committed cohort before replay starts.

## Measured results

| Observation | Before | After |
|---|---:|---:|
| Invalid multi-line-string diagnostics | 76 in one original package | 76 after declaration repair and in retained bytes |
| Guard-rejected available proposal occurrences | 213 | 8 |
| Original first-scan file-input errors | 3 reproduced refusals | 0 scan errors; 3 critical blocking file-input findings |
| Historical ALB flip fixtures | 3 rejected | 3 rejected in regression tests, including database rollbacks |

All 60 packages were observed. Security baselines reconstruct exactly for 56;
three first-scan refusals have no iterations, and one accepted post-security
repair lacks a patch. The 322 proposal occurrences comprise 208 security
deterministic proposals, five hash-matched deterministic validation proposals,
and 109 recorded retained iteration changes. None of the 109 retained changes
acquires a new guard rejection.

The guard clears **205 occurrences / 143 distinct proposals across 23 packages**.
Of those, **169 occurrences / 117 distinct proposals** pass the remaining
acceptance checks; 36 access-log occurrences still fail for new blocking findings.
All 23 packages have at least one such accepted paired proposal. Eight guard
rejections remain: four atomic catalogue occurrences involving unknown EC2
exposure and four EIP validation-repair occurrences. A package with one diagnosed
false-positive reason can still have an independent exposure-path rejection;
the 24 packages in section 1 therefore do not imply 24 wholly unblocked packages.
The other 16 conflict packages still lack sufficiently complete rejected Fixer
evidence. [guard-by-action.csv](guard-by-action.csv) separates action/occurrence
counts; [remaining-catalogue-guards.json](remaining-catalogue-guards.json) retains
the four current unknown EC2 exposure assessments.

Accepted paired proposals remove **89 distinct frozen open blocking identities**
across nine rules: AWS-0132 (4), AWS-0164 (17), AWS-0178 (16), CKV2_AWS_11 (16),
CKV2_AWS_12 (5), CKV_AWS_130 (17), CKV_AWS_145 (3), CKV_AWS_18 (2), and
CKV_AWS_354 (9). These are conditional resolutions, not 89 established exclusive
historical guard-only causes. The original 400 guard-annotated findings remain
a different, unproven causal denominator.

Fresh validation of unchanged retained bytes reports 26 valid, 29 invalid and
five errors. All 60 retained scans complete; the three old file refusals now have
one critical TERRAFORM_FILE_INPUT finding each and validation still reports
error. The integration test demonstrates the existing pending-review path and
unavailable download; this replay does not rewrite the historical stored status.
The malformed package remains byte-identical with 78 Terraform syntax blockers
in the frozen report. No synthetic quote repair or prompt-v9 change is justified.
[analysis.json](analysis.json) and [package-outcomes.csv](package-outcomes.csv)
contain the detailed counts. These observations establish no new pass rate.

## Method and limits

The replay reruns block normalization and syntax-gated declaration repair from
each Generator original, then native syntax checks on original, repaired and
retained sources. Retained packages receive fresh offline scanner and validation
observations. Existing Terraform file-input safety checks stay active.

Complete security session diffs are reversed from retained bytes, then retained
iteration diffs are applied forward with exact context checking. Reconstructed
final bytes must equal the export. Atomic catalogue/pod and supporting-template
proposals follow recorded order and retained decisions. Deterministic validation
proposals are included only when recorded before/after hashes match the actual
transform. Rejected LLM candidate bodies are absent; they are never invented.
One accepted post-security repair lacks a patch and prevents that package's
security-baseline reconstruction. The three first-scan refusals have no security
iterations to reconstruct.

Each available candidate is compared with both guards. Candidates that clear
the corrected guard receive paired native scanner/Terraform observations and the
existing CandidateGuard checks. Validation-repair proposals additionally need
an improvement under the existing validation rule. Other blocking findings,
validation failures and unknown exposure paths retain their existing gates.

Repeated identical source/plan/variant/runtime observations are cached; proposal
occurrences still count separately. Guard-conflict totals count proposal
decisions, rather than service/property entries or package UI notices. Findings
are identified by run, variant, rule, resource and file path. The
`guard_only_resolvable_open_findings` field is the union of frozen open blocking
identities removed by at least one accepted paired proposal. It is conditional
on that proposal and these tool observations: it does not establish exclusive
historical causation or simultaneous resolution in a new trajectory.

Paired observations use installed offline tools and warm cached evidence. They
do not replay historical wall-clock deadlines or combine newly accepted
proposals into a cumulative remediation run. They cannot establish a new pass
rate, successful deployment, or the outcome of missing rejected Fixer candidates.
See [verification](../phase10c-verification/README.md) for tests and the author's
real-round rerun command.

Correction to section 1: the historical scanner version projection has
`helm: null`; that does **not** prove Helm was unavailable. The generic version
probe uses unsupported `helm --version`. The explicit installed-tool probe
returns `v4.3.0+gbec5b06`, which this replay records and uses. No installation or
unrelated version-probe implementation change was made. The frozen diagnosis
files are preserved, and this correction supersedes their availability claim.

## Reproduction

From the repository root, using the existing tools/provider mirrors and the
author's local exports:

```bash
INFRAARCH_TEST_BOOTSTRAP=1 \
PYTHONPATH="$PWD/backend/tests/bootstrap:$PWD/backend" \
backend/.venv/bin/python -m scripts.phase10c_replay \
  --snapshots "$PWD/.cache/broad-final-results" \
  --output-dir "$PWD/docs/evals/phase10c-replay-$(date -u +%Y%m%dT%H%M%SZ)"
```

The output directory must be fresh; replay cannot overwrite historical evidence.
The bootstrap disables dotenv loading before Python imports application code.
