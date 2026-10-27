# Phase 10c section 1 — final-round diagnosis

Diagnosis completed on 2026-10-27 at implementation revision `727d7fd`.
No application, test, prompt, scanner, profile, threshold or state-rule changes.
Raw API snapshots remain uncommitted in `.cache/broad-final-results/`.

| Symptom | Established cause / scope | Attribution limit |
|---|---|---|
| 76 invalid multi-line strings; 78 TERRAFORM_SYNTAX blockers | One Generator-original missing closing quote, scenario 10 / repetition 1 / cost; malformed main.tf is byte-identical in retained files | No evidence of repair/guard escape-decoding corruption or a prompt-v8 origin |
| 40 current guard-conflict packages | 24 contain reproduced false-positive deterministic rejections; 16 remain unknown/ambiguous | Mixed attempts can include valid exposure-path rejections; 400 annotated findings are not 400 proved guard-only failures |
| 3 scan_error packages | Dynamic Lambda archive hashing is refused by the 9m file-input guard before Terraform launches, during the first security scan | This is an intentional safety refusal, not a Checkov/Trivy crash; allowing unknown host paths would be unsafe |
| 24→7 published passes | 18 matched slots lose a pass, one gains a pass: 14 guard-associated losses, 2 scan-error losses, 1 other validation loss, 1 other security loss | All 20 plans and all 60 Generator originals differ; no exact causal allocation or projected rerun pass rate |

## Inputs and method

The 20 final API exports cover all 60 variants. All **180** per-package plan,
original-file-map and retained-file-map comparisons match the committed final
architecture hashes, using the original canonical JSON digest (sorted keys,
compact separators). Plan checks repeat for each variant. The 40 older raw
exports exactly match the committed phase9k-baseline-audit source hashes.
The Sonnet experiment remains a separate, differently modelled cohort.

[input-manifest.json](input-manifest.json) hashes 236 committed quality files and
60 local raw exports. It commits no raw export. Committed evidence folders are
unchanged. New source-free projections are in this new folder only.

Native `terraform fmt -write=false -no-color` checked 248 HCL source snapshots:
108 original files and 140 retained files. Eight original files in seven
packages have syntax errors; one retained file in one package does. Native fmt
is a syntax observation, not provider validity, scanner acceptance or deployment.
No init, provider download, inference, dotenv read or network call was performed.

For security baselines, reverse each complete recorded session diff from the
retained source, then apply each retained iteration diff forward with exact
context matching. Reconstructable packages with security iterations total 56;
three scan-error packages have no iterations. One further package (scenario 2 /
repetition 2 / performance) has an accepted post-security repair whose patch is
not retained, so its exact security baseline is unavailable and excluded.

Reconstruct catalogue/pod and supporting-template candidates in their original
order, applying recorded retained decisions. All **208** recorded guard rejections
that were reconstructed reproduce under the unchanged guard: 52 atomic catalogue
proposals, 44 access-log proposals, 64 flow-log proposals and 48 KMS proposals.
These are repeated occurrences across iterations, not independent packages or
newly accepted fixes. Reconstructed final security bytes match the exports.
Candidate scanner/validation acceptance has not been replayed in this section.
Helm is unavailable locally. The 52 catalogue reconstructions reproduce the
Terraform portions relevant to the network guard and available plain-manifest
repairs; full byte identity of the recorded atomic Helm/pod candidates is not
claimed. The 16 recorded pod entries are not separately credited as rejected
standalone fixes. Supporting-template proposals require no Helm rendering.

## Invalid strings: all 76 occurrences traced to Generator original

The package is run `5e8a8141-421a-45c5-a822-6db2deb26447`, cost. Every final
multi-line diagnostic is in its `terraform/main.tf`, starting at line 225 and
cascading through the remaining file. That entire file is unchanged from the
Generator original, SHA-256:
`c8e1e786bc8632632947b888416f05eb22ff4a16671e3ecfa532f6c19ebdfa80`.
[multiline-occurrences.json](multiline-occurrences.json) lists each of the 76
locations and its first stage. Native fmt independently reproduces 76 multi-line
errors plus one unterminated-template and one invalid-character error in both
original and retained bytes. The last two become the sanitized generic Terraform
diagnostics in the stored validation report.

Three minimal excerpts below are from this same cascade, not three independent
malformed packages. They contain no credentials.

Root defect, original and retained lines 223–227:

```hcl
filter {
  name   = "name"
  values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*]
}
```

The unclosed string consumes subsequent declarations, including lines 229–232:

```hcl
resource "aws_lb" "alb" {
  name     = "public-alb"
  internal = false
```

The cascade persists at lines 292–294:

```hcl
bucket = "infra-logs-${var.region}"
force_destroy = true
}
```

Stage evidence:

- Generator original already contains the missing quote and all 78 native errors.
- Nine `multiline_arguments` normalization records affect `terraform/variables.tf`
  only. The malformed main file has no declaration or duplicate-block repair.
- Both syntax-only Fixer attempts are rejected for `plan_conformance_regression`;
  regeneration fails. The syntax record reports 78 initial errors. Rejected
  syntax-candidate bodies are not retained, so their correctness is not asserted.
- The generation gate still has all 76 multi-line diagnostics. Later security
  iteration diffs leave main.tf unchanged; before/after validation repair rounds
  are also guard-rejected. Neither introduces the offending text.
- The four deterministic records for this package concern Kubernetes pod defaults,
  rejected for no improvement. They do not rewrite the Terraform file.

Across the entire final cohort, the five 9m `duplicate_block` records are on
other packages: 1/1 security (S3 public-access block), 5/1 performance (flow log),
7/2 performance (RDS), and 10/2 cost/security (LB). Reconstructing them after
recorded block normalization reproduces **5/5 before/after hash pairs** exactly.
They introduce no additional retained invalid-multi-line-string case.

The path guard decodes JSON quoted literals for comparison, but never writes
that decoded text back to files. `file_paths.py` decodes templates to locate
literal spans, maps positions back and emits quoted replacements with json.dumps.
Duplicate consolidation copies original source spans. HCL attribute repair uses
source-span edits and JSON-escapes emitted values; `.tf.json` paths use JSON
serialization. No whole-HCL serializer/decoded-text writeback was found in the
inspected repair/guard paths. Fixer prompt v8's network context JSON serialization
creates prompt text, not file rewrites. There is no proven string-corruption
cause warranting a prompt-v9 or duplicate-repair change.

## Plan guard: false positives and uncertainty

The causal code defects are in `app/security/plan_conformance.py`:

1. Unsupported service types produce an empty type set. `unresolved_projection`
   then compares all network-like resources and any resource with broadly named
   fields such as `policy` or `enabled`. A new logging role policy or KMS policy
   can therefore reject an unrelated change for Redis, Prometheus/Grafana, IAM,
   subnet or NAT service bindings. Adding a log bucket can also change an empty
   network projection. Unknown binding is being treated as a package-wide veto.
2. For bound services, changing any dependency projection causes the guard to
   compare the *new* exposure/placement with the plan, even when the relevant
   exposure/placement is unchanged. In 10/1 performance, a subnet default change
   leaves EKS exposure public→public but is labelled a regression against private
   intent. In 6/2 performance, a safe subnet-default proposal leaves the ECS
   service's placement public→public but is rejected against private intent.
   Those existing mismatches deserve review; they are not introduced by the fix.
3. Repairing malformed syntax can change an unparseable binding into a parseable
   one, which the guard rejects before the syntax-preservation checks. This
   occurred in both syntax attempts for the missing-quote package. Candidate
   bodies are absent, so their exact scope/validity remains unverified.

All reconstructed deterministic candidates concern logging, encryption, proven
unused default security groups, TLS policy hardening, safe subnet defaults and
preserving pod defaults. They do not change planned endpoint exposure. There
are **24 packages with at least one proved false-positive rejection**; their
other Fixer attempts can still contain uncertain or legitimate exposure changes.
The other **16 packages** are classified unknown/ambiguous, not assumed safe.
No final-round rejected public→private flip can be independently confirmed from
retained candidate bytes: those rejected Fixer bodies were not exported.
The guard itself records 26 `regression` entries across five packages; these are
not 26 independently confirmed exposure flips, as the reproduced examples above
show. Unknown entries and repeated evaluations are separate from package counts.

The three existing 10b synthetic cases (run-3 cost/security, run-4 performance)
do retain complete candidate bytes and prove actual public-LB internal flips.
All three are still rejected by the unchanged guard. They differ from unrelated
logging/KMS proposals and must remain rollback regressions in section 3.

### All 40 currently annotated packages

`scenario/repetition` identifies a registered slot, not an old benchmark cohort.
FP present means at least one reconstructed unrelated candidate was rejected;
other decisions in the same package are not thereby declared false positives.
Unknown includes exposure-path edits, ambiguous binding and missing candidate
bytes. Counts below are reproduced deterministic rejection occurrences.

| Scenario/repetition | Variant | Classification | Reproduced occurrences | Final validation |
|---|---|---|---:|---|
| 4/1 | cost | FP present | 8 | invalid |
| 4/1 | performance | FP present | 8 | valid |
| 4/1 | security | FP present | 8 | valid |
| 6/1 | performance | Unknown | 0 | valid |
| 6/1 | security | Unknown | 0 | valid |
| 7/1 | cost | FP present | 8 | valid |
| 7/1 | performance | FP present | 12 | invalid |
| 7/1 | security | FP present | 8 | invalid |
| 8/1 | cost | Unknown | 0 | invalid |
| 8/1 | performance | Unknown | 0 | invalid |
| 8/1 | security | Unknown | 0 | valid |
| 9/1 | cost | FP present | 12 | invalid |
| 9/1 | performance | FP present | 16 | valid |
| 9/1 | security | FP present | 16 | invalid |
| 10/1 | cost | Unknown | 0 | invalid |
| 10/1 | performance | FP present | 8 | invalid |
| 10/1 | security | FP present | 12 | invalid |
| 10/2 | cost | FP present | 12 | invalid |
| 10/2 | performance | FP present | 12 | invalid |
| 10/2 | security | FP present | 8 | invalid |
| 9/2 | cost | Unknown | 0 | invalid |
| 8/2 | cost | Unknown | 0 | invalid |
| 8/2 | performance | Unknown | 0 | invalid |
| 8/2 | security | Unknown | 0 | invalid |
| 7/2 | cost | FP present | 4 | valid |
| 7/2 | performance | FP present | 8 | valid |
| 7/2 | security | FP present | 8 | valid |
| 6/2 | cost | Unknown | 0 | valid |
| 6/2 | performance | FP present | 4 | valid |
| 6/2 | security | Unknown | 0 | valid |
| 5/2 | performance | Unknown | 0 | invalid |
| 5/2 | security | Unknown | 0 | valid |
| 4/2 | cost | FP present | 8 | invalid |
| 4/2 | performance | FP present | 4 | invalid |
| 4/2 | security | FP present | 8 | invalid |
| 3/2 | security | FP present | 4 | valid |
| 2/2 | cost | FP present | 8 | invalid |
| 2/2 | performance | Unknown | 0 | invalid |
| 2/2 | security | FP present | 4 | invalid |
| 1/2 | security | Unknown | 0 | valid |

[guard-packages.csv](guard-packages.csv) includes run UUIDs, services and rule IDs
for every row. [packages.json](packages.json) covers all 60 packages. The 53 rule
IDs in its `full_candidate_targeted_rules` union were sent in full Fixer
candidates encountering a guard rejection; some partial groups were retained,
so that union does not assert that every target stayed unresolved.

Deterministic rejected targets include AWS-0164/CKV_AWS_130 (subnet defaults),
CKV2_AWS_12 (unused default SG), CKV_AWS_103 (TLS policy), CKV_AWS_91/18 (logging),
AWS-0178/CKV2_AWS_11 (flow logging), AWS-0132/CKV_AWS_145/354 (KMS), plus the
complete pod rule lists in the CSV/JSON. The original records show 99 rejected
catalogue entries (including 16 pod entries), 164 rejected supporting-template
proposals and 14 rejected `eip_v6_domain` validation-repair records. Catalogue
entries share an atomic candidate; an individual pod rule is not thereby proved
to have independently triggered the guard.

**Findings held open only by the guard: not identifiable from these exports.**
Exactly **400 still-open findings in 40 packages** carry a matching UI guard
annotation. These include the 78 syntax findings from one malformed file.
That is an association, not a counterfactual resolution count. CandidateGuard
returns before syntax/validation/scanning when conformance fails. The missing
Fixer candidates and absence of post-guard checks prevent an exclusive causal
count. Zero exclusive resolutions have been established in section 1; that
must not be presented as proof that the actual number is zero. Section 3 can
measure counterfactuals only where candidate reconstruction is possible, and
must still enforce every other unchanged gate.

## Scan errors

| Run UUID | Repetition / variant | Source line | Cause / stage |
|---|---|---:|---|
| 3fdbf756-39d7-451f-9a74-f400b8065eb7 | 1 / performance | main.tf:51 | filebase64sha256(var.lambda_zip_path); first security scan |
| 3fdbf756-39d7-451f-9a74-f400b8065eb7 | 1 / security | main.tf:71 | Same dynamic input; first security scan |
| 5c8ae47a-c276-4b66-8212-844ffe886365 | 2 / cost | main.tf:56 | Same dynamic input; first security scan |

All are scenario 3. Validation already records `uninspectable_file_input`, with
zero Terraform init runs. The process runner converts the nonempty guard result
into `ToolFailure(terraform, unsafe_file_input)` before launching init/validate.
The scanner retries twice and the security stage enters `scan_error`, without
any fixing iteration. This is the 9m expanded hashing/entrypoint safety coverage;
literal escape decoding does not corrupt a source file. Variable defaults are
not trusted deployment values. A safe change may improve the diagnostic or
classification, but must not evaluate a dynamic host path or claim validity.

The other two scenario-3 validation errors use the archive provider, whose
requested version is absent from the mirror (`provider_version_not_in_mirror`).
They are separate from the three scan errors. No missing provider is downloaded.

## Stage comparison and 24→7 attribution

These are stored outcomes, with complete raw reason labels restored from the
hash-verified API exports. Gate validity is after generation repairs, not validity
of untouched Generator output. Rolled-back iterations can retain partial groups.
Reason occurrences overlap when an iteration has multiple reasons.

| Stage / count | Round 1 | Round 2 | Final |
|---|---:|---:|---:|
| Packages | 60 | 60 | 60 |
| Generation gate valid / invalid / error | 33 / 25 / 2 | 29 / 31 / 0 | 24 / 31 / 5 |
| Final validation valid / invalid / error | 35 / 23 / 2 | 37 / 23 / 0 | 26 / 29 / 5 |
| Deterministic metadata records, all outcomes | 301 | 237 | 262 |
| Declaration/idiom records applied without outcome field | 175 | 103 | 111 |
| Explicit deterministic accepted / rejected / skipped | 15 / 96 / 15 | 20 / 111 / 3 | 19 / 126 / 6 |
| LLM validation repair accepted / rejected | 8 / 70 | 14 / 74 | 10 / 84 |
| Security iteration accepted / rolled_back | 81 / 81 | 89 / 79 | 37 / 162 |
| Security no_change / stopped | 1 / 0 | 4 / 0 | 9 / 1 |
| Partial groups kept / discarded / unevaluated | 51 / 74 / 8 | 44 / 72 / 14 | 90 / 236 / 8 |
| Catalogue entries retained | 60 | 52 | 30 |
| Supporting templates retained | 55 | 61 | 23 |
| Final blocking finding occurrences | 111 | 152 | 481 |
| Published checks_passed | 24 | 19 | 7 |

| Security rejection reason occurrences | Round 1 | Round 2 | Final |
|---|---:|---:|---:|
| plan_conformance_regression | 0 | 0 | 132 |
| terraform_regression | 20 | 29 | 6 |
| new_blocking_findings | 28 | 34 | 14 |
| iteration_deadline | 21 | 16 | 7 |
| terraform_verification_unavailable | 8 | 0 | 8 |
| reference_regression | 3 | 1 | 0 |
| security_control_removed | 9 | 9 | 1 |

Final partial groups add 188 guard rejections; validation repairs add 29.
The compact benchmark reason allowlist predates the new guard reason, so it
exports 29 validation reasons as `unknown` and omits that reason from security
rejection lists. This explains much of the apparent missing-reason telemetry;
it is not evidence that the rejected attempts had no reason.

The separate Sonnet experiment has 56 packages, 24 passes, 36 final valid,
18 invalid and two error outcomes; it has three TERRAFORM_SYNTAX blockers but
no final invalid-multi-line-string title. Thus 'syntax absent earlier' is true
for rounds 1/2, not every earlier experiment. Its Architect model differs and
four variants are missing. It is not a control for the final round.

Matching scenario/repetition/variant slots against published round-1 outcomes:
18 losses and one gain give the net drop of 17. Fourteen losses carry a guard
notice: ten also fail validation and four remain valid with security findings.
Two losses are the dynamic-file scan errors. One is unsupported-argument
validation without a current guard notice; one has other security findings.
The malformed-string package was already a failing slot in round 1, so its
76 diagnostic occurrences explain **zero of these matched pass losses**.
The third scan-error package was also already a failing slot in round 1.
Against round 2 there are 14 losses and two gains, a net drop of 12.
[stage-counts.json](stage-counts.json) lists the exact slots and counts.

These are disjoint outcome buckets, not 14 proven passes recoverable by removing
the guard. All 20 plans and all 60 Generator originals differ from each prior
round. Generation validity, provider/schema choices and other retained blockers
also change. Guard false positives are proven code causes for rejected unrelated
repairs; the 9m input safeguard proves the scan refusals; missing-quote generation
proves the string cascade. Their exact shares of the end-to-end pass decline
cannot be isolated from this one round. Model variance cannot be excluded.
D-63 also already corrects one historical round-1 published pass to 23/60 for a
confirmed exposure flip; this diagnosis preserves the requested published 24→7
comparison rather than silently rewriting that older evidence.

## Decisions for the next sections; verification

Fix only the proven guard dependency/change-scope defects. Preserve fail-closed
behavior for changes that can affect the planned exposure path, including the
three real 10b ALB-flip fixtures. Do not weaken scanner/profile/readiness rules,
accept unknown file reads, download archive providers, or change prompt v8 on
unsupported string-corruption speculation. Retain the safety refusal unless a
separate safe diagnostic/classification correction is demonstrated.

`make lint`: exit 0; Ruff/format 47 scripts plus 406 app/test files, mypy 189
sources, frontend ESLint and both TypeScript checks pass. Existing offline
10b conformance/replay, 9m duplicate and tool-input checks: **72 passed, 0 failed,
0 skipped, 3 deselected** (the database security-loop variants). This includes
all three complete retained-candidate ALB fixture checks. `make secret-scan`
also exits 0: **0 findings, 0 scan errors** across working files and all existing
refs/reflogs (dotenv/cache excluded). Its result and environment are retained in
this report folder. No tests were added
because implementation behavior is unchanged.

Full `make test`, frontend, E2E, performance, traceability and evidence-index
finish checks are deferred to section 3; this user-requested section-1 boundary
makes no full-suite claim. No code fix or rerun pass-rate projection is included.
README setup/commands/environment are unchanged. No new specification ambiguity
or open question is introduced; missing candidate evidence is an evaluation limit.
