# Phase 9i offline replay

81 generated packages from 28 runs; three missing variants remain separate in [the immutable manifest](input-manifest.json). Original final sets, cached snapshots and final report are unchanged. Zero LLM calls.

Strict controls repair acceptance, readiness and downloads. Both contextual assessments are experimental reporting only; run-profile selection and persistence remain unchanged. All 81 stored strict/v1 assessments match exactly.

## Retained outcomes

| Stage | Valid / 81 | Strict blockers | v1 blockers | v2 blockers | Strict / v1 / v2 passes |
|---|---:|---:|---:|---:|---|
| Stored historical | 23 | 391 | 370 | 318 | 15 / 15 / 15 |
| Fresh isolated baseline | 23 | 391 | 370 | 318 | 15 / 15 / 15 |
| schema_guidance | 23 | 391 | 370 | 318 | 15 / 15 / 15 |
| contextual_v2 | 23 | 391 | 370 | 318 | 15 / 15 / 15 |
| independent_equivalents | 45 | 391 | 366 | 312 | 20 / 20 / 20 |
| cumulative_equivalents | 45 | 391 | 366 | 312 | 20 / 20 / 20 |
| independent_addressing | 23 | 349 | 346 | 316 | 15 / 15 / 15 |
| cumulative_addressing | 45 | 349 | 344 | 312 | 20 / 20 / 20 |
| independent_formats | 23 | 391 | 370 | 318 | 15 / 15 / 15 |
| cumulative_formats | 45 | 349 | 344 | 312 | 20 / 20 / 20 |
| independent_defaults | 23 | 376 | 355 | 303 | 15 / 15 / 15 |
| cumulative_defaults | 45 | 334 | 329 | 297 | 20 / 20 / 20 |

The schema-guidance and contextual-v2 rows use original bytes. Guidance receives zero attributed package improvement. Any strict-to-v2 difference is policy classification, not an infrastructure security improvement. Independent changes start from original packages; cumulative changes retain the preceding accepted candidate.

## Candidates and guards

| Stage | Accepted | Unchanged | Rejected | Findings removed (retained) | New findings (candidate / retained) | Unknown scan outcomes |
|---|---:|---:|---:|---:|---:|---:|
| independent_equivalents | 31 | 43 | 7 | 0 | 0 / 0 | 0 |
| cumulative_equivalents | 31 | 43 | 7 | 0 | 0 / 0 | 0 |
| independent_addressing | 17 | 64 | 0 | 42 | 0 / 0 | 0 |
| cumulative_addressing | 17 | 64 | 0 | 42 | 0 / 0 | 0 |
| independent_formats | 2 | 66 | 13 | 0 | 189 / 0 | 0 |
| cumulative_formats | 2 | 66 | 13 | 0 | 189 / 0 | 0 |
| independent_defaults | 15 | 66 | 0 | 15 | 0 / 0 | 0 |
| cumulative_defaults | 15 | 66 | 0 | 15 | 0 / 0 | 0 |

Each stage directory preserves every before/candidate/retained assessment, failed check, blocker, exception, rejection reason, repair record and byte hash. [Per-package deltas](per-package-deltas.json) include rejected candidates; [CSV](per-package.csv) supports comparisons. Finding identity is rule, package-relative file and resource; duplicate counts remain in assessment totals. No candidate with new strict blockers is retained.

## Context measurements

| Component | Before min–max | After min–max |
|---|---:|---:|
| schema characters | 595–4493 | 4478–4489 |
| checklist characters | 404–1010 | 404–1190 |
| total characters | 999–5503 | 4889–5668 |

Truncated context: 43/81 before; 81/81 after. [Every saved plan's sizes and resource coverage](context-sizes.json) include requested/included types and the exact source-free schema entries. Caps remain 4,500 schema / 1,500 checklist / 6,000 total characters; configured repair-context cap is unchanged.

## Baseline and verification limits

[Baseline discrepancies](baseline-discrepancies.json) contain 162 package/comparison records, with check details and finding deltas. Stored historical results, pre-change fresh offline results and final-validator isolated results remain distinct. The pre-change baseline used tool offline flags and dead proxies; the final-validator baseline and all final candidates also ran in a Linux user/network namespace containing only loopback.

Tool versions, provider schema manifest, evaluator hash, package/plan/variant hashes and timeout configuration are recorded with every final row. Cached observations require matching fingerprints; isolated and nonisolated caches cannot collide. Providers use only the local filesystem mirror; remote chart dependencies are not fetched; Checkov/Trivy updates, uploads and telemetry are disabled. Terraform validates configuration; nothing is planned against AWS or deployed. Offline replay does not measure live pipeline deadline success or LLM generation quality.

All 648 independent/cumulative transformations were reconstructed against the final implementation, checked idempotent and matched to observed candidate/retained hashes. Unknown expressions, external modules, ambiguous references and resolver limits (64/declaration, 1,024/module, 16 local levels) remain conservative omissions.

## Security interpretation and deferred work

Documented argument equivalents and lossless Grafana/Helm repairs improve validity; they do not by themselves harden deployed infrastructure. Seven-day RDS retention improves recovery. Disabling inherited public addresses reduces accidental exposure only where consumers prove connectivity is preserved. Managing a proven-unused VPC default SG removes latent permissive defaults. Longer backups, explicit public-IP choices, live SG rules and unknown dependencies are preserved.

Ranks 4, 6, 7 and 8 remain future work: workload/container hardening (including KSV-0125), compatible logging and log-destination controls, broader schema-grounded repair of unsupported security/availability intent, and architectural isolation. The main architectural option is CloudFront VPC origins to an internal ALB, supported by the mirrored AWS providers' aws_cloudfront_vpc_origin schemas. None is implemented or credited with reductions here. D-56 and thesis notes describe the remaining evidence limits.

## Final retained packages by prompt

| Prompt | Packages | Valid | Strict / v1 / v2 blockers | Strict passes |
|---|---:|---:|---|---:|
| ECS | 47 | 29 | 250 / 246 / 217 | 5 |
| EKS | 16 | 3 | 83 / 82 / 79 | 2 |
| static | 18 | 13 | 1 / 1 / 1 | 13 |

## Approved rank outcomes and risk

| Rank | Measured effect | Risk / security meaning |
|---|---|---|
| 1 | 31 equivalent candidates retained; 22 more valid packages; 0 strict findings removed | Low semantic risk for documented equivalents. Validity gain; no hardening claim. Guidance alone has no measured generation gain. |
| 2 | 17 packages retained addressing changes; 42 strict findings removed | Connectivity risk requires complete parsed consumer evidence. Explicit public IP overrides survive; safer defaults reduce accidental future exposure. |
| 3 | 2 format candidates retained; 12 rejected with 189 newly observable strict findings; 1 rejected without validity improvement | Standard helpers can expose workload checks when charts render. No hardening claim; guards preserve all rejected originals. |
| 5 | 15 default candidates retained; 15 strict findings removed | Seven-day backups improve recovery. Unknown consumers preserve connectivity. Empty default SG rules are tested separately; this corpus supplies no safe default-SG proposal. |

Original-byte v2 reclassifies 73 strict findings, versus 21 in v1. After repairs, v2 reclassifies 37 residual strict findings, versus 5 in v1. Exceptions are reporting classifications and do not change infrastructure. Canonical route repairs can also make existing routing evidence understandable to an evaluator; that contextual delta is distinct from removing a strict finding.

Grafana and helper changes in the same proposed format candidate share its acceptance decision. 4 of 6 envelope unwrappings therefore roll back alongside helper proposals; retained unwrappings can still leave other validation errors. Candidate findings are preserved individually; rendering can reveal pre-existing workload risks rather than introduce new vulnerabilities. KSV-0125 in the saved results means an untrusted image registry, and image references remain unchanged.

The primary execution manifest is preserved. Secondary assessments were recomputed from those exact scans under the final v2 policy. A source-AST proof isolates the generator-only schema compaction from every validator function; final generation context sizes are refreshed independently. No changed tool evaluation or candidate bytes are reused under a mismatched fingerprint. Policy lookup follows the checked-in mapping sourced from [AWS's NLB protocol tables](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/describe-ssl-policies.html).

Repair-schema previews in context-sizes.json are calculated offline at the existing 16,000-character default cap; they are not actual LLM requests. Historical configured overrides are not inferable from a package snapshot. Generation context coverage is bounded and truncated, even after common version fields are compacted; full mirrors remain available to schema-grounded repair.

Independent/cumulative replay applies these approved changes to saved final bytes; it does not replay an entire live agent loop or reapply every legacy catalogue control. A live combined proposal can have different acceptance and timing. Static consumer analysis cannot observe out-of-band cloud resources. Review and actual deployment validation remain necessary before applying infrastructure.

## Baseline discrepancy interpretation

Validity changes across comparisons: 0; removed finding identities: 0; introduced finding identities: 0. Historical diagnostic changes: 14 packages; historical finding-order differences: 6 packages. The explicit terraform_unknown flag was absent in the original projection; its false value is recorded as a representation change. Helm locations/messages are more specific. Raw comparisons remain available.

Field-change combinations (both comparisons): blockers, failed_checks, terraform_unknown: 6; blockers, terraform_unknown: 5; failed_checks, terraform_unknown: 22; terraform_unknown: 129.

## Verification

[Verification evidence](verification.json) includes logs, exact counts and remaining limits. Verification used dotenv-disabled Python and disposable PostgreSQL with synthetic credentials. No real LLM calls, .env reads, new database migration or push was performed by Phase 9i.

| Command | Result |
|---|---|
| `make lint` | passed |
| `make test` | 1771 passed; 6 performance tests deselected |
| `npm --prefix frontend test -- --run` | 113 passed |
| `make test-e2e` | 7 passed |
| `pytest -q tests/unit/test_secure_generation.py tests/unit/test_schema_context.py tests/unit/test_generator_schema.py tests/unit/test_phase9i_report.py tests/unit/test_phase9i_deterministic.py` | 25 passed |