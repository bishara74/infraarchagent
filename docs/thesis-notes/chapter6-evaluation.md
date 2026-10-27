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

## Phase 9k — Stronger Architect experiment results

Requirements: FR-A-01, FR-P-04, PR-01, NFR-01; decision record: D-59.
The [committed comparison](../evals/phase9k-architect-report/report.md),
[configuration and groups](../evals/phase9k-architect-report/experiment-comparison.json),
[plan audit](../evals/phase9k-architect-report/experiment-plans.json) and
[package architecture audit](../evals/phase9k-architect-report/experiment-architecture.json)
compare the twenty-run Sonnet round with the two pooled twenty-run gpt-oss broad
rounds (2026-10-20 and 2026-10-21). The
[three-run real smoke](../evals/phase9-bench-broad-smoke-20261024T220546075719Z/summary.md)
is separate from the [full round](../evals/phase9-bench-broad-20261024T233240471733Z/summary.md).
All counts below were recomputed from committed `results.json` telemetry and
per-run `quality/<run_id>/<variant>.json`, joined by run ID to scenario complexity;
plan and original/retained scheme counts were checked against the committed audits.
Fisher calculations use `scripts.phase9b_stats.fisher(successes, total, successes,
total)`, a two-sided fixed-margin test.

| Package comparison | Sonnet Architect | Pooled gpt-oss Architect | Fisher p |
|---|---:|---:|---:|
| Full round, strict checks_passed | 24/56 (42.9%) | 43/120 (35.8%) | 0.40692 |
| Levels 1–3, strict checks_passed | 24/30 (80.0%) | 39/60 (65.0%) | 0.22199 |
| Levels 1–3, validation valid | 28/30 (93.3%) | 43/60 (71.7%) | 0.02634 |
| Levels 4–5, strict checks_passed | 0/26 (0.0%) | 4/60 (6.7%) | 0.31013 |
| Levels 4–5, validation valid | 8/26 (30.8%) | 29/60 (48.3%) | 0.15898 |

These package counts and the author's approximate p-values agree with the
committed evidence. Four of sixty full-round variant slots are missing, all at
levels 4–5; generated-package denominators exclude them. The baseline has no
missing variants. The smoke generated eight of nine variants, zero strictly
passing and six validation-valid; it is not pooled with the full round.

The level splits are **exploratory, chosen after seeing the data**, and
uncorrected for multiple comparisons. Packages of one run share a plan, so
package-level tests assume more independence than the design provides. As a
clustering sensitivity, count settled runs with at least one passing (or valid)
package, retaining runs with missing packages in the run denominator:

| Run-level comparison | Sonnet Architect | Pooled gpt-oss Architect | Fisher p |
|---|---:|---:|---:|
| Full round, any strict pass | 10/20 | 23/40 | 0.59569 |
| Full round, any valid package | 16/20 | 34/40 | 0.71810 |
| Levels 1–3, any strict pass | 10/10 | 19/20 | 1.00000 |
| Levels 1–3, any valid package | 10/10 | 19/20 | 1.00000 |
| Levels 4–5, any strict pass | 0/10 | 4/20 | 0.27203 |
| Levels 4–5, any valid package | 6/10 | 15/20 | 0.43108 |

These run-level tests reduce within-run clustering but do not eliminate repeated
scenario, time or provider dependence. In particular, the exploratory validity
signal at package level does not survive this any-valid-run sensitivity. This is
not evidence of equivalence, deployment success or a causal Architect effect.
Recorded baseline revisions are `6b343e6138c9dac8fd5d119212ac737d8e806d39` and
`d6ba66eb044d5747fb244c3692a6cafb2163f188`; the full experiment records
`87cb3c50a11f551f88768d400409dc9b44af4617`. Historical code/prompt differences,
provider preferences and actual serving backends remain confounders even though
the Generator/Fixer model and low thinking selections are unchanged.

At levels 4–5, Sonnet plans a public LB in 10/10 runs and never an internal LB.
The pooled gpt-oss plans classify eight as public and twelve as absent. Absence
means no explicit structured LB service, not private ingress. In baseline
scenario 7 all four plans omit an LB, yet ten of twelve original Generator
packages classify as public and two as unknown; retained schemes are ten
public, one internal and one unknown. The full Sonnet level 4–5 packages classify
originally as fifteen public, three absent and eight unknown; retained schemes are sixteen
public, one internal, three absent and six unknown. These are static configured
schemes, not verified network reachability.

Summing retained `remaining_findings` from the full round gives AWS-0053 = 27,
CKV_AWS_130 = 24 and AWS-0164 = 21, making AWS-0053 the leading blocker. The
baseline AWS-0053 count is 18 + 23 = 41. The author's reading is that a much
stronger Architect improves validity on simpler scenarios but does not remove
the level 4–5 wall. Public LBs follow from internet-facing requirements and
appear even when the plan omits them, placing the blocker downstream of plan
quality in that interpretation. This is an observational interpretation, not a
causal finding; not every scenario explicitly requires public ingress.

Routing recomputed from unique LLM `call_id` records agrees with
[provider-routing.json](../evals/phase9k-architect-report/provider-routing.json):
the full round has 395 known Generator/Fixer calls, all Cerebras, zero recorded
fallbacks and **one additional cancelled Fixer call with unknown serving
provider**. Thus “all calls served by Cerebras” needs that qualification.
All 21 full-round Architect calls were served by Claude Platform on AWS.
Smoke adds 83 Cerebras Generator/Fixer calls and three Architect calls served
by Claude Platform on AWS, with no unknowns or fallbacks. Historical baseline
routing includes Groq as well as Cerebras; no explicit baseline preference
means no comparable baseline fallback-share denominator.

The author's call totals differ from the evidence: the full round contains
**21 unique Architect calls across twenty runs, not 42**; smoke plus full round
contains 24. All report zero reasoning tokens with medium requested. There are
**two unique `finish_reason=length` calls, not eight**, both full-round gpt-oss
Fixer calls (scenarios 9 and 10); smoke has none and no Architect call is
length-terminated. Count a call once by `call_id` rather than counting its
repeated projections in telemetry, attempt details, events and CSV files.

Measured known costs, summed as decimal `cost_usd` values, are $1.85209835 for
the full round, $0.35977435 for smoke and $2.69311165 for the pooled baseline
($1.27561460 + $1.41749705). All twenty/three/forty respective run costs are
recorded. Full-round Architect usage is 48,412 input / 27,030 output tokens;
smoke is 6,774 / 5,215. At the captured `expected_pricing_per_token` of
$0.000002 input and $0.000010 output, those Architect usages price to
$0.367124 (19.82% of full-round known cost) and $0.065698 (18.26% of smoke).
This is token-priced attribution using recorded rates, not separately measured
role billing. The recorded $0.222781 Architect / $1.5549969 full-round estimate
is a pre-experiment historical-token projection, not the measured experiment
cost. Usage-delta timing and caching/billing attribution remain limitations.

The configured/routed model is `anthropic/claude-sonnet-5.5`. The canonical
snapshot `anthropic/claude-sonnet-5.5-20260928` is **author-observed in the
OpenRouter activity view for the inspected request**; it is not independently
established for every call by the committed telemetry.

### Thinking limitation: offline wire inspection only

The full round's 21 unique Architect calls (24 including smoke, rather than the
author's stated 42) all record `requested_effort=medium`,
`request_style=openrouter`, `response_format=json_object` and
`reasoning_tokens=0`. The
[Architect diagnostics](../evals/phase9k-architect-report/architect-diagnostics.json)
agree with the full-round telemetry. The author's inspected billing observation
is 2,245 input / 1,260 output tokens, $0.0171: using the captured prices gives
`2245 * 0.000002 + 1260 * 0.000010 = 0.01709`, rounded to $0.0171, with no
additional hidden reasoning output reported or billed. That billing observation
comes from the author, not a new provider request or an independently fetched
billing record.

Offline code and existing mocked wire tests establish the following boundary:

- `ModelSelectionService` selects OpenRouter request style for the explicit
  Architect model; `AgentFactory.selected_adapter()` applies its resolved
  medium effort and reasoning capability to `OpenAIAdapter`.
- `OpenAIAdapter.send_prompt()` puts `{"reasoning":{"effort":"medium"}}`
  in SDK `extra_body`; the SDK merges it into the top-level Chat Completions
  JSON. It does not send native OpenAI `reasoning_effort`, Anthropic `thinking`
  or `output_config`, `budget_tokens`, `max_tokens` inside `reasoning`, or an
  explicit `enabled`/`exclude` flag for this medium OpenRouter request.
  `max_completion_tokens` is the ordinary output cap, not a separate thinking
  budget. There is no model-name-specific Sonnet branch.
- The same body contains `"model":"anthropic/claude-sonnet-5.5"` and
  `"response_format":{"type":"json_object"}`. Architect calls do not
  activate the response-validator structured-request context, so they do not
  get a strict `json_schema` or its `provider.require_parameters=true` option.
  Local DeploymentPlan validation follows the JSON response. Architect provider
  order is empty in the evidence. On Generator/Fixer schema requests, the
  adapter merges `provider.require_parameters` and optional routing order into
  `extra_body` without removing `reasoning`; that path is separate from this
  Architect wire.
- The adapter reads exactly
  `completion.usage.completion_tokens_details.reasoning_tokens` after SDK
  response parsing. A nonnegative integer, including zero, is retained;
  absent/unusable detail is `None`, not silently zero. It does not derive
  reasoning usage from message `reasoning`/`reasoning_details`, text, billing or
  `completion_tokens`. Reported output usage already includes any reported
  reasoning; the report does not add it again.

Evidence for these statements is repository code in
[`openai.py`](../../backend/app/llm/openai.py),
[`model_selection.py`](../../backend/app/core/model_selection.py),
[`factory.py`](../../backend/app/agents/factory.py), the frozen
[`phase9h-baseline-wire.json`](../../backend/tests/fixtures/phase9h-baseline-wire.json)
and its integration test, the medium-effort Architect override wire test in
[`test_phase9k_architect.py`](../../backend/tests/integration/test_phase9k_architect.py),
and the reasoning-body/optional-usage tests in
[`test_llm_providers.py`](../../backend/tests/unit/test_llm_providers.py).
Mocked wire tests prove adapter serialization and parsing, not that the selected
real model/backend honors the parameter.

Possible causes are **unverified hypotheses**: the router/backend may ignore or
map the effort field without activating extended thinking; this model/endpoint
may require a different activation/budget mechanism; the combination with
JSON-object output may affect support; or provider usage reporting may omit
reasoning accounting or expose it elsewhere. No provider documentation or live
request was consulted, so none is established as the cause. The observed zero
detail and the author's billing check constrain interpretation but do not
diagnose the provider implementation. The adapter is unchanged.

**Thinking requested at medium; no reasoning tokens reported or billed; the
experiment therefore tests a stronger Architect model without extended
thinking.**

### Future work and retained limitations

1. Repeat the Architect experiment with **verified extended thinking**. Before
   interpreting results as a thinking intervention, verify the actual serialized
   request, selected endpoint, returned reasoning usage and billed output for an
   author-run probe. Keep this experiment's evidence and labels intact and
   record any new transport, prompt or budget changes as additional confounders.
2. Investigate **CloudFront VPC origin in front of an internal ALB for levels
   4–5** as a proposed ingress design that might meet public-access requirements
   without a public ALB. Endpoint support, workload compatibility, Terraform
   validity and scanner outcomes require a separate experiment; this task makes
   no deployment or blocker-removal claim and changes no readiness policy.
3. **KSV-0125 remains a limitation.** Summing retained findings gives four
   occurrences in the full Sonnet round (two in smoke; seven in the pooled
   baseline). A stronger plan alone does not establish that generated container
   images meet the trusted-registry rule. Report this limitation independently
   of AWS-0053 and retain the existing strict policy.


## Phase 9l — Human-curated lessons

The [curated-lessons design and verification notes](phase9l-curated-lessons.md)
describe the OWASP LLM01 threat boundary, immutable human approval, layered
corpus counts, disabled-request compatibility and retained provenance. This
phase verifies controls with local mocked inference; it adds no evidence that
lessons improve generated outputs and does not change the experiments above.


## Phase 10b — Exposure preservation counter-audit

The [new immutable-input counter-audit](../evals/phase10b-exposure-audit/README.md)
separates scanner cleanliness from functional exposure. Across 998 packages in
33 folders, 312 have source or committed exposure projections; 703 outcomes are
unknown under the audit definition. Three plan-public LBs changed from public
originals to internal retained configurations. One was a passing broad-baseline
cost package under all three profiles. That round changes 24/60 to 23/60; the
pooled baseline changes from 43/120 (35.8%) to 42/120 (35.0%) on confirmed cases.
A separate passing package has unresolved original exposure, so the bounded
corrected result is 41–42/120 (34.2–35.0%). Do not silently assume it was public.
The affected Architect experiment/smoke packages already failed; 24/56 remains.
Final sets retain 7/40 and 8/41 strict/v1 passes with no confirmed plan-public
flips; historical v2 data is absent. Earlier broad/stub/source gaps are explicit.

These are static configured-property observations, not deployment tests or
causal model comparisons. Historical folders, labels and profiles are unchanged.
The new guard preserves supported exposure changes and returns conflicting fixes
to engineer review. Other plan semantics, dynamic values and cloud reachability
remain bounded or unverified. FR-S-07 is qualified as partly met; the current
59-ID register is 45 met, 12 partly met, one not met, one unverified.
