# Kubernetes catalogue findings and thesis notes

The follow-up retains pod hardening in ten packages (three ECS and seven EKS). Relative to the freshly observed previous Phase 9i retained packages, strict blockers fall from 334 to 324, contextual-v1 from 329 to 319, and contextual-v2 from 297 to 287. All scanner findings fall by 75 occurrences: ten blocking and 65 advisory. No new finding identities are retained.

Validity and checks_passed do not increase. The unchanged strict guard still rejects all twelve format candidates that introduce blocking findings.

| Prompt | Packages | Valid | Strict checks_passed | contextual-v1 | contextual-v2 |
|---|---:|---:|---:|---:|---:|
| ECS | 47 | 29 | 5 | 5 | 5 |
| EKS | 16 | 3 | 2 | 2 | 2 |
| Static site | 18 | 13 | 13 | 13 | 13 |

`checks_passed` means valid and zero blocking findings under that assessment. The totals are 45 valid and 20 checks_passed under each profile, unchanged from the previous retained packages. The original generated-package baseline remains separately recorded: 23 valid and 15 checks_passed. Three missing variants are excluded from the 81-package denominator.

## Retained security improvements

The blocking occurrence changes are CKV_K8S_40: 4→2; KSV-0104: 4→0; KSV-0118: 4→0. Seven of the ten accepted packages improve advisory findings without removing a blocker. Image parameterisation receives no retained-corpus improvement credit: accepted cumulative catalogue records are pod defaults; literal-image preservation and overrides are verified with synthetic charts.

The other reductions concern capability restrictions, seccomp and UID/GID controls. See [rule-deltas.json](rule-deltas.json) for every occurrence count, [per-package.csv](per-package.csv) for per-package profile totals and [per-finding-deltas.json](per-finding-deltas.json) for candidate and retained finding identities, including advisory findings.

## Rejected format candidates

For the same twelve historical new-blocker rejections, before-package hashes match across the old and new cumulative format stages. The historical replay exposed 189 new strict rule/path/resource identities; the current fresh replay exposes 81, a reduction of 108. These are rejected-candidate reductions. The original files remain retained under the unchanged guard. The historical candidate observations are historical evidence, not fresh rescans of those old rejected candidates.

| Rule | Historical new identities | Current new identities | Delta |
|---|---:|---:|---:|
| CKV_K8S_10 | 13 | 4 | -9 |
| CKV_K8S_11 | 13 | 4 | -9 |
| CKV_K8S_12 | 13 | 4 | -9 |
| CKV_K8S_13 | 13 | 4 | -9 |
| CKV_K8S_14 | 11 | 11 | +0 |
| CKV_K8S_20 | 14 | 5 | -9 |
| CKV_K8S_23 | 14 | 5 | -9 |
| CKV_K8S_40 | 14 | 5 | -9 |
| KSV-0001 | 12 | 3 | -9 |
| KSV-0012 | 12 | 3 | -9 |
| KSV-0013 | 9 | 9 | +0 |
| KSV-0014 | 12 | 3 | -9 |
| KSV-0104 | 12 | 3 | -9 |
| KSV-0117 | 8 | 8 | +0 |
| KSV-0118 | 12 | 3 | -9 |
| KSV-0125 | 7 | 7 | +0 |

The residual pinning/trust/port identities are CKV_K8S_14 (11), KSV-0013 (9), KSV-0125 (7) and KSV-0117 (8). Together they account for 35 of the 81 remaining new identities. Exposing image values preserves tags and registries; it does not establish registry trust or replace latest/blank tags. No ports, Services, probes, registries, digests or image versions are invented.

Other residuals reflect preserved settings and unsupported structures. In the cumulative format stage, skipped file records include five dynamic-template structures, one uninspectable document structure and one unresolved binding. These are file-entry counts, including a package with two skipped files. Whole-document if wrappers and uniquely bound helper names are supported; inner control flow, unsupported value bindings, aliases/duplicates and nonempty flow mappings at edited structures are conservative coverage limits. Explicit low UIDs and conflicting or unresolved resource quantities remain unchanged. Per-package reasons remain in the stage rows and [changes.json](changes.json).

The complete cumulative outcomes are: equivalents 31 accepted / seven no-improvement rejections; addressing 17 accepted; formats two accepted / twelve new-blocker rejections / one no-improvement rejection; VPC/RDS defaults 15 accepted; pod catalogue ten accepted. No validity-regression, syntax-regression or unknown-verification rejection was observed in this replay.

## Verification and limits

All 81 stored strict/contextual-v1 assessments match exactly. Fresh original-package observations have zero stored/fresh validation/profile discrepancies. Historical retained bytes are reconstructed against c3be20c; 648 historical/candidate stage hash checks and 324 candidate idempotence checks pass. All nine observation stages have zero unknown scan or validation outcomes. The 56-file execution evaluator manifest still matches the checked-in evaluator.

Actual offline validation, Checkov 3.3.21, Trivy 0.69.3, Terraform 1.16.4, Helm 4.3.0 and the other recorded validators ran in an isolated network namespace with only loopback, private temporary workspaces and local provider mirrors. No downloads, real model calls or operator settings were used by replay. Old final sets, cached snapshots, prior Phase 9i evidence, the final report and docs/spec remain unchanged.

Verification: make lint passed; make test passed 1,818 tests with six performance tests deselected and zero failed/skipped; frontend passed 113 tests; stub E2E passed seven tests. Later reporting robustness checks passed eight focused tests. Python started with dotenv disabled. Both disposable PostgreSQL 16.14 containers used synthetic credentials and were removed. [Verification details](verification-results.json) and [attempt history](verification/attempts.md) preserve counts and limitations.

## Thesis interpretation and future work

The catalogue strengthens generated infrastructure through least privilege, filesystem restrictions, seccomp and bounded starting resource allocations. A lower finding count does not prove application availability or image provenance. UID/GID 10001, dropped capabilities, a read-only root filesystem and the resource defaults can break existing images. A writable /tmp does not establish other required write paths. Helm values expose identity, filesystem, writable paths and resources for operator configuration. Accepted, still-current archive records identify affected workloads with **runtime compatibility unverified**.

Future work requires verified image identities and application-specific user, port, writable-path and capacity contracts. More template structures can be supported with explicit source/render binding proofs; ambiguous inputs should continue to require guidance or model/engineer repair. No live Kubernetes deployment, image pull, workload startup, real model generation/repair, live pipeline deadline-quality experiment or new performance threshold measurement was performed here.

The previously deferred ranks 4, 6, 7 and 8 remain deferred. CloudFront VPC origins to internal ALBs remain the main future architectural option from Phase 9i; this follow-up does not implement that architecture or change readiness, blocking criteria, thresholds or profile selection.
