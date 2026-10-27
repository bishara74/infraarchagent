# Phase 10d section 1 — accepted diagnosis

The author accepted this diagnosis before application changes. No real model,
network service, credential, dotenv read, install or historical evidence edit was
used. Source-free JSON tables contain every package and anomalous attempt.

| Symptom | Attempts | Error-class counts | Exact reason/path |
|---|---:|---:|---|
| Empty exported rollback reason | 52 | 65 | 46 plan_conformance_regression and 6 security_control_removed; CandidateGuard -> _fix_iteration -> quality_snapshot |
| Terraform verification unavailable | 17 | 17 | file-input guard skip -> failure_count=None -> CandidateGuard |
| Unknown exported repair reason | 15 | 33 | ValidationRepair -> plan_regressions -> quality_snapshot |

All raw reasons exist. The compact reason allowlists discard the two security
codes and replace the repair conformance code with unknown. Class summaries
count each error class, so they are not attempt counts. Security accepted counts
are 65 iterations / 74 error-class occurrences, versus round 2's 89 / 94.

[anomalies.json](anomalies.json) enumerates scenario/repetition/variant/index,
raw reasons, producing path and multiplicity for every requested occurrence.
[packages.json](packages.json) and [round2-packages.json](round2-packages.json)
retain full stage counts, final blockers and failed-check locations.
[input-manifest.json](input-manifest.json) hashes the 40 raw exports. All 177
rerun plan/original/retained canonical comparisons match committed projections.
The older cohort has no architecture projections; its raw hashes are recorded
separately rather than claiming equivalent canonical verification.

## Scenarios 1 and 4

| Stage | Scenario 1 round 2 -> rerun | Scenario 4 round 2 -> rerun |
|---|---|---|
| Generation gate valid/invalid/error | 6/0/0 -> 1/2/3 | 1/5/0 -> 1/5/0 |
| Deterministic records | 8 applied -> 0 | 16 applied -> 14 applied + 16 rejected |
| Validation repairs accepted/rejected | 0/0 -> 0/6 | 2/12 -> 2/14 |
| Fixer proposed/retained | 12/8 -> 18/4 | 4/4 -> 11/4 |
| Security accepted/rolled back | 4/9 -> 3/15 | 6/1 -> 6/8 |
| Groups kept/discarded/unevaluated | 11/10/2 -> 1/30/4 | 1/1/1 -> 1/8/0 |
| Final valid/invalid/error | 6/0/0 -> 1/2/3 | 2/4/0 -> 1/5/0 |
| Final blockers | 4 -> 13 | 0 -> 6 |
| Published passes | 4/6 -> 1/6 | 2/6 -> 1/6 |

Generation gates follow generation-stage repairs. Fresh current-tool checks of
untouched originals found scenario 1: round 2 one valid/two invalid/three
unavailable; rerun zero valid/three invalid/three unavailable. Scenario 4 has six
invalid originals in each cohort. These fresh observations do not rewrite old
results or imply old safety coverage was equivalent.

Scenario 1's rerun has three dynamic Lambda archive hashes, a forbidden resource
reference in a variable default (repetition 1/performance), and missing literal
lambda.zip (repetition 2/security). Both new plans introduce Lambda despite the
bucket-only request. Its rollback reasons are 12 unavailable, two Terraform
regressions and one new-blocker rejection.

Scenario 4 has 16 rejected eip_v6_domain attempts across all six packages. Five
retain vpc=true under AWS v6. A NAT EIP with no instance/ENI attachment is included
by the reverse attachment fallback in EC2 exposure/ingress projections. The guard
also follows private NAT egress into public-subnet auto-addressing and mistakes
that setting for the private instance's exposure. Four catalogue and four focused
fix iterations reject the public-subnet change. Another four focused iterations
reject ingress changes: D-63 explicitly protects existing unbound ingress, and
missing candidate bodies prevent labelling those intentional decisions defects.

Five isolated retained EIP migrations were checked natively: each removes its one
Terraform failure, introduces zero blocker identities and preserves existing
blockers (2, 0, 0, 4, 0). This is candidate evidence, never a pass-rate prediction.

## Unavailability scope and attribution

All 17 unavailable iterations come from five unchanged dynamic
filebase64sha256(var.lambda_zip_path) inputs: scenario 1 repetition 1 cost/security
and repetition 2 performance; scenario 3 repetition 1 performance and repetition
2 cost. They discard 33 partial groups (27 in scenario 1, six in scenario 3),
including KMS, S3 and DynamoDB edits. Twelve whole scenario-1 supporting candidates
(eight access-log, four KMS) are also rejected without group salvage.

All 138 discarded groups: 58 conformance, 33 unavailable, 25 new blockers,
15 Terraform regression, six control removal and one reference regression.
Five groups report unknown service binding (four scenario 8/repetition 1/
performance and one scenario 7/repetition 2/cost); absent Fixer bodies prevent
proving those individual decisions false positives. Security session bytes
reconstruct for 58 packages; one accepted post-security repair lacks its patch.

Levels 1–3 decline 18/30 -> 10/30 against round 2 alone: ten losses and two gains,
listed in [matched-slots.json](matched-slots.json). Loss buckets: four dynamic
file refusals, two EIP validation failures, two missing literal Lambda archives,
one dependency cycle, one invalid ACM data source. Gains: scenario 4/repetition
1/security and scenario 5/repetition 1/performance. These are observed final
failure buckets, not exclusive causal attribution or recoverable passes.

All 20 plans and 59 available originals differ from round 2. Current file safety
also refuses seven historically passing low-complexity packages. Model variance,
missing rejected bodies and historical coverage differences prevent assigning an
exclusive share of the end-to-end decline to code. No threshold/policy change or
recovery of the old pass rate is an acceptance criterion.

## Verification and reproduction

Existing offline checks: 110 passed, zero failed/skipped, three database-loop
cases deselected. Includes three historical ALB fixture candidates. Full lint
passes. Logs are [tests.txt](tests.txt) and [lint.txt](lint.txt). Full suites and
paired Phase 10d replay belong to section 3. No new specification open question.

From the repository root, with the existing author exports available:

```bash
INFRAARCH_TEST_BOOTSTRAP=1 \
PYTHONPATH="$PWD/backend/tests/bootstrap:$PWD/backend" \
backend/.venv/bin/python -m scripts.phase10d_diagnosis \
  --output-dir "$PWD/docs/evals/phase10d-diagnosis-new"
```

The destination must be fresh. The bootstrap disables dotenv before imports.
