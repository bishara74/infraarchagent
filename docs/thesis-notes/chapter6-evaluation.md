# Chapter 6 — Evaluation material

Ready to adapt to the thesis. Tables derive from the committed Phase 9b report
inputs; this text does not claim deployment success or general model superiority.
See [final report](../evals/phase9-final-report/report.md), its input manifest and
[D-55](../design-deviations.md).

## Setup and method

InfraArchAgent was evaluated on the captured i5-1135G7 / approximately 8 GB WSL2
host using Checkov 3.3.21, Trivy 0.69.3 and Terraform 1.16.4. The matched final
sets use openai/gpt-oss-120b:nitro for Architect, three generators and fixer,
with configured/requested low effort and commit 20281387. Full captured settings,
versions and usage measurements remain in the evidence folders.

Each final set contains fourteen runs across **three distinct prompt texts**:
ten PR-01 runs repeat ECS/EKS/static-site prompts 4/3/3; an isolated PR-03 baseline
and three concurrent runs reuse the ECS prompt. This is not fourteen distinct
prompts. Both sets share captured settings and a clean recorded code revision.
Earlier phases change prompts, budgets, recovery, fixer model/transport or local
work; they are longitudinal descriptive comparisons, not matched interventions.
A3 and B stopped during provider usage exhaustion and are incomplete schedules.

An automatic strict checks_passed label requires the existing clean scan and
valid validation rules. It does not prove deployment, security completeness or
human approval. Historical production_ready benchmark labels are preserved with
an explicit compatibility qualification; early compact snapshots omit some
validation metadata. Missing variants are disclosed and excluded from package
rate denominators. Contextual-v1 is experimental, requires supervisor approval
before adopted thesis use, and never changes strict labels (D-47/D-48).

## Package results

| Benchmark | Passed/generated | Rate | Wilson 95% interval | Missing observed variants |
|---|---:|---:|---:|---:|
| baseline | 1/36 | 2.78% | 0.49–14.17% | 6 |
| 9d | 1/40 | 2.50% | 0.44–12.88% | 2 |
| 9e | 1/40 | 2.50% | 0.44–12.88% | 2 |
| 9e2 | 1/40 | 2.50% | 0.44–12.88% | 2 |
| A | 3/41 | 7.32% | 2.52–19.43% | 1 |
| A2 | 1/36 | 2.78% | 0.49–14.17% | 6 |
| A3 | 1/29 | 3.45% | 0.61–17.18% | 4 |
| B | 1/9 | 11.11% | 1.99–43.50% | 24 |
| final set 1 | 7/40 | 17.50% | 8.75–31.95% | 2 |
| final set 2 | 8/41 | 19.51% | 10.23–34.01% | 1 |
| final combined | 15/81 | 18.52% | 11.56–28.33% | 3 |

Baseline quality comes from [the preserved baseline projection](../evals/phase9d-baseline-quality-20261015/summary.md).
Final evidence is [set 1](../evals/phase9-bench-real-20261020T010134093069Z/summary.md)
and [set 2](../evals/phase9-bench-real-20261020T013911945957Z/summary.md).
A3/B observed eleven of fourteen planned runs: four/twenty-four missing observed
variants do not include the nine slots from their unstarted concurrent cohort.
No incomplete or differently configured sets are silently pooled.

## Concentration by prompt and variant

| Set | Dimension | Group | Passed/generated | Rate | Wilson 95% interval | Missing |
|---|---|---|---:|---:|---:|---:|
| final set 1 | prompt | ECS application | 1/23 | 4.35% | 0.77–20.99% | 1 |
| final set 1 | prompt | Static site | 6/9 | 66.67% | 35.42–87.94% | 0 |
| final set 1 | prompt | EKS microservices | 0/8 | 0.00% | 0.00–32.44% | 1 |
| final set 1 | variant | cost | 4/12 | 33.33% | 13.81–60.94% | 2 |
| final set 1 | variant | performance | 2/14 | 14.29% | 4.01–39.94% | 0 |
| final set 1 | variant | security | 1/14 | 7.14% | 1.27–31.47% | 0 |
| final set 2 | prompt | ECS application | 0/24 | 0.00% | 0.00–13.80% | 0 |
| final set 2 | prompt | Static site | 7/9 | 77.78% | 45.26–93.68% | 0 |
| final set 2 | prompt | EKS microservices | 1/8 | 12.50% | 2.24–47.09% | 1 |
| final set 2 | variant | cost | 3/14 | 21.43% | 7.57–47.59% | 0 |
| final set 2 | variant | performance | 2/13 | 15.38% | 4.33–42.23% | 1 |
| final set 2 | variant | security | 3/14 | 21.43% | 7.57–47.59% | 0 |
| final combined | prompt | ECS application | 1/47 | 2.13% | 0.38–11.11% | 1 |
| final combined | prompt | Static site | 13/18 | 72.22% | 49.13–87.50% | 0 |
| final combined | prompt | EKS microservices | 1/16 | 6.25% | 1.11–28.33% | 2 |
| final combined | variant | cost | 7/26 | 26.92% | 13.70–46.08% | 2 |
| final combined | variant | performance | 4/27 | 14.81% | 5.92–32.48% | 1 |
| final combined | variant | security | 4/28 | 14.29% | 5.70–31.49% | 0 |

Thirteen of fifteen passing packages came from the static-site prompt. The other
two prompts together passed 2/63 generated packages. Thus the aggregate 18.52%
rate is strongly driven by a simpler workload, and does not demonstrate reliable
success on the larger ECS/EKS application descriptions. Cost variants have the
highest observed combined rate, but wide, clustered intervals do not establish
a general variant advantage. ECS has more samples because PR-03 reuses it.

## Statistics and clustering sensitivity

Wilson 95% intervals summarize binomial proportions. Fisher exact tests are
two-sided with fixed margins, summing tables no more likely than observed;
implementation uses integer combinations and no statistical dependency.

| Unit | Comparison | Counts | Fisher two-sided p |
|---|---|---|---:|
| Package | Final combined versus baseline | 15/81 versus 1/36 | 0.02121 |
| Package | Final combined versus A3 | 15/81 versus 1/29 | 0.06448 |
| Package | Set 1 versus set 2 | 7/40 versus 8/41 | 1.00000 |
| Run | Final combined versus baseline | 8/28 versus 1/14 | 0.23017 |

The package-level calculation assumes independent packages. Its p-values are
optimistic because the three variants of one run share a plan. The run-level
sensitivity counts complete runs with at least one checks_passed package;
complete failed runs stay in the denominator. Baseline is 7.14% (Wilson
1.27–31.47%); final combined is 28.57% (15.25–47.06%). Each final set has four
such runs. The run-level comparison does not provide conventional 0.05-level
evidence against equal proportions. It also does not eliminate repeated-prompt,
provider or temporal dependence. All p-values are descriptive exploratory
comparisons; p=1 is not proof of equivalence or repeatability.

## Remaining failures and remediation

Final review-reason totals are 58 validation_failed and 52 unresolved security
cases; reasons overlap. Unsupported argument contributes 42 failed checks.
The final report lists blocking-rule counts, validation-valid near misses,
catalogue retention, template rejections/introduced rules and stage medians.
Contextual-v1 removes nine blocker occurrences in set 1 and twelve in set 2,
but remaining blockers and validation failures prevent additional package passes.
Plan-to-resource address binding is still missing for broader context-dependent
rules (D-48); it is not the sole explanation for equal strict/contextual rates.

Security proposal acceptance before verification increased from A3 12/140 to
smoke 47/49, then final set 1 142/147 and set 2 153/157 (combined 295/304).
The 47/49 figure belongs to the earlier three-run smoke benchmark. These are
proposal records, not LLM attempt counts, verified retained changes or passing
packages. The [counts-only supplement](../evals/phase9b-supplement/proposal-counts.json)
records cached source filenames/SHA-256 without generated content. Missing A3
attempt/latency/reasoning coverage remains unknown (D-46/D-54).

## Performance and cost

PR-01 passes both matched sets: ten-run medians 162.39 and 164.27 seconds versus
300 seconds. This is API settlement as the documented D-43 UI-availability proxy;
PR-02 has separate emission-to-DOM evidence. Aggregate and isolated/concurrent
PR-05 views pass both final sets. Official PR-03 ratios 1.901–2.025 and
1.662–2.021 exceed 1.5, so both sets fail. Secondary PR-01-prompt-median ratios
reach 2.124 and do not replace the official isolated-baseline method.

D-54 attribution is consistent with shared CPU-heavy local-tool contention, but
uncontrolled host/provider load prevents exact causal allocation. Independent
stage medians cannot be added, and overlapping tool spans require interval
unions. The 266.48 → 239.74-second smoke projection is counterfactual; it is not
measured speedup. See [runtime attribution](../phase9-runtime-attribution.md).

The historical 9h stub PR-04 benchmark remains FAIL (median 1.988 s, maximum
2.653 s). New quiet offline measurements use an identical 9,989,906-byte ZIP,
real disposable PostgreSQL, two warm-ups and ten alternating HTTP samples per
condition: session median/max 0.700893/0.721118 s, shared key
0.698920/0.730615 s, prevalidated-session control 0.695996/0.734234 s.
The approximately 4.9 ms median difference does not establish a causal overhead;
no clear authentication bottleneck justified a production change. The control
is attribution only. Revocation with the real guard restored returns 401.
HTTP-client versus specified curl timing remains a disclosed method difference.
See [performance gaps and supervisor draft](../phase9b-performance-gaps.md).

Known measured final costs are $1.566230 and $1.644783 after rounding to six
decimal places. Concurrent cohort totals are counted once; per-run concurrent
costs are not attributed. Usage-delta zeros and provider metering delays limit
cost interpretation. Historical model/phase costs are not controlled cost-effect
comparisons. Exact observed totals and unknown counts are in costs.csv.

## Threats to validity

- One resource-constrained WSL2 machine and uncontrolled physical-host load.
  The new download experiment records kernel 6.18 versus historical 5.15, so
  historical/new download latency is not a controlled auth before/after result.
- One model family in the matched final comparison, with provider routing/load
  variability; historical Sonnet/Haiku runs are differently configured evidence.
- Three prompt texts with unequal repeated exposure, not fourteen independent
  infrastructure tasks per set; variants share plans and repeated runs cluster.
- Missing generated variants, incomplete provider-limited schedules, limited
  sample size and multiple descriptive comparisons.
- Real-provider measurements versus deterministic stub functional checks;
  timing proxies, synthetic download fixtures and usage-delta cost uncertainty.
- Scanners and terraform validate do not establish deployability or complete
  security. NFR-04 clean-environment deployment remains unverified.
- NFR-02 replacement doubles exercise injection, not every concrete recovery/
  private-metadata path; manual contract review remains necessary.

## Findings for discussion

1. **Sonnet latency and reliability:** initial recorded PR-01 median 189.81 s
   covers only four usable runs; the Sonnet smoke median 145.46 s covers two.
   Neither establishes ten-run compliance, and PR-05 fails. Large outputs and
   differing budgets prevent a clean model-only comparison (D-43; initial and
   smoke folders dated 2026-10-14).
2. **Haiku prose before JSON:** the preserved B excerpt reports 14/22 non-quota
   invalid_json/prose_before failures and eight successes; four additional
   quota failures are excluded. It is a partial excerpt, not a complete format
   failure rate (D-46; B folder dated 2026-10-18).
3. **Fixer schema correction:** until 9g the generator response-validator context
   did not reach fixer wire requests. The acceptance jump exposes more local
   verification work; high proposal acceptance still does not imply high
   checks-passed package rates (D-46/D-54).
4. **Trivy Terraform-JSON artifacts:** parser/representation false positives
   motivate native-HCL correction; historical findings remain preserved rather
   than silently reclassified as successful model outputs (D-46).
5. **Access-log target versus KMS rules:** delivery-compatible AES256 log targets
   conflict with generic KMS/logging controls, contributing template rejection.
   Contextual exceptions require parsed relationships and do not weaken strict
   template acceptance (D-46/D-48).
6. **Remaining validity:** Unsupported argument is the leading final failed
   check class. Provider-schema grounding is helpful but does not encode every
   conditional constraint; native validation remains authoritative (D-45).
7. **Plan-to-resource binding:** broad public-tier/NAT intent cannot justify
   exceptions without resource-address mapping. Current exact parsed exceptions
   reduce blockers but do not add passing packages (D-48).

8. **Provider major-version drift:** broad scenario 4 had 6/6 validation-valid
   packages in the first broad cohort, with AWS constraints selecting 5.100.0.
   The second cohort had 2/6 valid packages: generators selected or permitted
   6.68.0 while emitting removed v5 fields. Three retained packages used
   aws_eip.vpc=true; a fourth retained aws_ssm_association.instance_id and a
   separately mistyped commands parameter. These defects are present in saved
   generator output, rather than being introduced by retained repairs. The
   newer EIP guidance already labelled vpc as v5-only, illustrating that correct
   version-labelled context does not ensure internally consistent model output.
   The new plans also emitted previously unmapped subnet/ssm labels. The source
   model, actual serving backend, plan structure, Architect schema and guidance
   all form potential covariates; these cohorts do not isolate their causal
   effects. Terraform/scanner versions and configured generation budgets match.

   The [offline migration replay](../evals/phase9i-v6-migrations-offline/README.md)
   measures narrow documented equivalents on the saved final package bytes.
   It preserves selected provider majors and the existing validity/security
   guard. Every changed proposal receives paired native offline checks/scans;
   identity cases reuse explicitly labelled frozen observations with matched
   versions and unchanged observational code. Original-only legacy fields are
   audited separately and cannot create replay gains. The remaining SSM commands
   list is invalid under both majors and is intentionally not treated as a
   version migration. Guidance changes alone receive no package-quality gain.
   Report per-scenario candidate and retained validity/strict/v1/v2 deltas;
   In broad cohort 2, scenario 4 rises from 2/6 to 5/6 valid and passing under
   each profile; every other scenario has zero validity/profile pass delta.
   Scenario 10 and the remaining scenario-4 cost package each lose one native
   error while staying invalid. All five proposals pass the existing guard;
   blocker-count deltas are zero. Other cohorts remain unchanged. These are
   offline effects on saved bytes: static acceptance is not deployment evidence
   or a newly measured real benchmark. See D-56 and the provider's [v6 migration guide](https://github.com/hashicorp/terraform-provider-aws/blob/v6.68.0/website/docs/guides/version-6-upgrade.html.markdown).

9. **Package layout and local file reads:** two packages improved by the v6
   equivalents remained invalid. Broad cohort 2 scenario 4 cost supplied an SSM
   commands tuple where both pinned provider schemas require a string-valued
   parameters map. This cause occurs in one saved package and one scenario, so
   it fails the author's recurrence criterion and remains untouched. Scenario 10
   performance used `file("helm/eks-cluster/values.yaml")` inside the Terraform
   module although the artifact is in a sibling package directory. Both defects
   exist in original generator bytes and survive repairs; they are not introduced
   by the v6 equivalents, and neither depends on the provider major.

   The same path cause occurs in ten of 201 saved packages across broad scenarios
   8/9/10 and final-set EKS: nine Helm values reads and one nginx user-data
   interpolation. All ten expressions exist in generator snapshots. A narrow
   deterministic equivalent can select the exact existing package artifact when
   the module-relative file is absent, then rebase through `path.module` while
   preserving contents and string type. Dynamic, ambiguous, missing and escaping
   inputs skip; valid existing reads remain authoritative. The unchanged
   validity/security guard still decides retention, so a path defect masked by
   another Terraform error does not automatically justify an accepted edit.

   The [path-only offline replay](../evals/phase9i-file-paths-offline/README.md)
   uses the prior v6-retained bytes for all 201 packages, with paired native
   validation/scans for changed proposals and explicit hash-verified prior
   observations for identity cases. Per-scenario results distinguish native
   validation gains from strict/v1/v2 security acceptance. Seven of ten proposals
   are retained; three are rejected for no improvement. Only broad cohort 2
   scenario 10 gains a valid package (2/6 to 3/6), taking all-cohort validity from
   98/201 to 99/201. Its two KSV-0125 trusted-registry blockers remain. Strict/v1/v2
   package-pass deltas and blocker-count deltas are zero for every scenario;
   every other scenario also has zero validity delta. Ten changed proposals
   receive paired native observations; 191 unchanged packages reuse the prior
   observations, with 58 unchanged observational source hashes and an additive
   repair-kind model proof. This is an offline
   correction of package layout references, not a new inference benchmark or
   evidence of Helm deployment or instance startup. See D-56 and Terraform's
   [file() documentation](https://developer.hashicorp.com/terraform/language/functions/file).

Evidence for the discussion findings: [initial Sonnet](../evals/phase9-bench-real-20261014T101701420278Z/summary.md),
[Sonnet smoke](../evals/phase9-bench-smoke-20261014T122810075341Z/summary.md),
[partial Haiku excerpt](../evals/phase9-bench-real-20261018T231027886459Z/fixer-log-excerpt.txt),
[A3](../evals/phase9-bench-real-20261018T213645241170Z/summary.md),
[post-9h smoke](../evals/phase9-bench-smoke-20261019T222520294388Z/summary.md),
[9g reclassification](../evals/phase9g-reclassification-20261019/summary.md),
and [accepted deviations D-43–D-55](../design-deviations.md).
