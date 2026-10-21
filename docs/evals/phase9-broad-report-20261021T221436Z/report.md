# Phase 9 final evaluation

Committed evidence revision: `006eb5496dcdd3cee9082191980cbe33e453d71d`.

Descriptive evaluation of generated candidate IaC; no successful deployment is implied. Original evidence, thresholds and readiness rules are unchanged.

## Main results

Intervals are Wilson 95%. Missing variants are excluded from generated-package denominators and shown separately. Contextual-v1 is experimental (D-48), never an official readiness policy.

| Benchmark | Change | Settled/planned | Strict; CI | Contextual; CI | Missing | PR-01 median s | PR-03 | PR-05 | Known USD |
|---|---|---|---|---|---|---|---|---|---|
| baseline | Generator format enforcement; original quality baseline | 14/14 (14 usable) | 1/36 (2.78%; 0.49–14.17%) | unavailable | 6 | 41.62084038749981 | FAIL | PASS | 0.42849895 |
| 9d | Declaration repairs, generation checklist, validation repair | 14/14 (14 usable) | 1/40 (2.50%; 0.44–12.88%) | unavailable | 2 | 120.08073360800154 | FAIL | PASS | 0.09105495 |
| 9e | Syntax gates and schema-grounded repair | 14/14 (14 usable) | 1/40 (2.50%; 0.44–12.88%) | unavailable | 2 | 75.51232989599976 | FAIL | PASS | 0.1242728 |
| 9e2 | Continue bounded repair after unchanged findings | 14/14 (14 usable) | 1/40 (2.50%; 0.44–12.88%) | unavailable | 2 | 94.47920793199955 | FAIL | PASS | 1.55955195 |
| A | Catalogue/templates, partial groups, prompt v7 | 14/14 (14 usable) | 3/41 (7.32%; 2.52–19.43%) | unavailable | 1 | 133.92153543949826 | FAIL | FAIL | 1.71957595 |
| A2 | Syntax recovery and corrected prompt v8 | 14/14 (14 usable) | 1/36 (2.78%; 0.49–14.17%) | unavailable | 6 | 121.09235275599985 | FAIL | FAIL | 1.40304135 |
| A3 | Declaration/deadline recovery, v9/three attempts; provider-limited | 11/14 (10 usable) | 1/29 (3.45%; 0.61–17.18%) | 1/29 (3.45%; 0.61–17.18%) | 4 | 134.6745607595003 | INCOMPLETE | PASS | 1.13546510 |
| B | Haiku fixer; provider-limited incomplete schedule | 11/14 (3 usable) | 1/9 (11.11%; 1.99–43.50%) | 1/9 (11.11%; 1.99–43.50%) | 24 | 315.7148181560042 | INCOMPLETE | PASS | 0.2401718 |
| final set 1 | 9g fixer wire schema and 9h/runtime changes | 14/14 (14 usable) | 7/40 (17.50%; 8.75–31.95%) | 7/40 (17.50%; 8.75–31.95%) | 2 | 162.3922934154998 | FAIL | PASS | 1.56622995 |
| final set 2 | Matched repeat of final set 1 | 14/14 (14 usable) | 8/41 (19.51%; 10.23–34.01%) | 8/41 (19.51%; 10.23–34.01%) | 1 | 164.27101094950103 | FAIL | PASS | 1.64478280 |
| final combined | Only the matched final repetitions pooled | 28/28 | 15/81 (18.52%; 11.56–28.33%) | 15/81 (18.52%; 11.56–28.33%) | 3 | see individual sets | FAIL both | PASS both | 3.21101275 |

A3 and B are HTTP-402/provider-usage-limited incomplete schedules. Each observed 11/14 runs, including a failed PR-03 baseline; their missing counts omit nine unobserved variant slots. Other phases differ in prompts/settings/code and are not silently pooled. Costs are observed usage deltas; zeros do not establish free inference. Cohort totals are counted once, without per-run attribution.

## Statistics and clustering sensitivity

| Unit | Comparison | Left | Right | Fisher two-sided p |
|---|---|---|---|---|
| package | final combined vs baseline | 15/81 | 1/36 | 0.02121030291909499 |
| package | final combined vs A3 | 15/81 | 1/29 | 0.06447834317899723 |
| package | final set 1 vs final set 2 | 7/40 | 8/41 | 1.0 |
| run | final combined vs baseline | 8/28 | 1/14 | 0.23017361543375287 |

Fisher tests condition on margins and sum probabilities no greater than the observed table. Package-level p-values assume independent packages and are optimistic because the three variants of a run share one plan. Run-level sensitivity counts complete runs with at least one checks_passed package, including complete failed runs in the denominator. It reduces within-run dependence but does not remove repeated-prompt/provider effects. P-values are descriptive; p=1 is not proof of reproducibility or equivalence.

## Final breakdowns

Three exact prompt texts, not fourteen distinct prompts, were used per set. Ten PR-01 runs repeat them 4/3/3; PR-03 adds four runs of the first prompt. Denominators below are generated packages; missing variants are separate. Intervals are descriptive and retain clustering limitations.

| Set | Dimension | Prompt text / variant | Passed/generated; CI | Missing |
|---|---|---|---|---|
| final set 1 | prompt | A Node.js REST API with a PostgreSQL database, autoscaling on ECS, a Jenkins CI/CD pipeline, Nginx reverse proxy, and Prometheus + Grafana monitoring stack on AWS. | 1/23 (4.35%; 0.77–20.99%) | 1 |
| final set 1 | prompt | A static website hosted in a private AWS S3 bucket behind CloudFront with HTTPS, access logging, and Terraform infrastructure. | 6/9 (66.67%; 35.42–87.94%) | 0 |
| final set 1 | prompt | Python microservices on AWS EKS with autoscaling, a PostgreSQL database, a Jenkins CI/CD pipeline, and Prometheus monitoring with Grafana dashboards. | 0/8 (0.00%; 0.00–32.44%) | 1 |
| final set 1 | variant | cost | 4/12 (33.33%; 13.81–60.94%) | 2 |
| final set 1 | variant | performance | 2/14 (14.29%; 4.01–39.94%) | 0 |
| final set 1 | variant | security | 1/14 (7.14%; 1.27–31.47%) | 0 |
| final set 2 | prompt | A Node.js REST API with a PostgreSQL database, autoscaling on ECS, a Jenkins CI/CD pipeline, Nginx reverse proxy, and Prometheus + Grafana monitoring stack on AWS. | 0/24 (0.00%; 0.00–13.80%) | 0 |
| final set 2 | prompt | A static website hosted in a private AWS S3 bucket behind CloudFront with HTTPS, access logging, and Terraform infrastructure. | 7/9 (77.78%; 45.26–93.68%) | 0 |
| final set 2 | prompt | Python microservices on AWS EKS with autoscaling, a PostgreSQL database, a Jenkins CI/CD pipeline, and Prometheus monitoring with Grafana dashboards. | 1/8 (12.50%; 2.24–47.09%) | 1 |
| final set 2 | variant | cost | 3/14 (21.43%; 7.57–47.59%) | 0 |
| final set 2 | variant | performance | 2/13 (15.38%; 4.33–42.23%) | 1 |
| final set 2 | variant | security | 3/14 (21.43%; 7.57–47.59%) | 0 |
| final combined | prompt | A Node.js REST API with a PostgreSQL database, autoscaling on ECS, a Jenkins CI/CD pipeline, Nginx reverse proxy, and Prometheus + Grafana monitoring stack on AWS. | 1/47 (2.13%; 0.38–11.11%) | 1 |
| final combined | prompt | A static website hosted in a private AWS S3 bucket behind CloudFront with HTTPS, access logging, and Terraform infrastructure. | 13/18 (72.22%; 49.13–87.50%) | 0 |
| final combined | prompt | Python microservices on AWS EKS with autoscaling, a PostgreSQL database, a Jenkins CI/CD pipeline, and Prometheus monitoring with Grafana dashboards. | 1/16 (6.25%; 1.11–28.33%) | 2 |
| final combined | variant | cost | 7/26 (26.92%; 13.70–46.08%) | 2 |
| final combined | variant | performance | 4/27 (14.81%; 5.92–32.48%) | 1 |
| final combined | variant | security | 4/28 (14.29%; 5.70–31.49%) | 0 |

## Final failure and remediation analysis

| Review reason | Packages (overlap allowed) |
|---|---|
| unresolved_security_findings | 52 |
| validation_failed | 58 |

| Failed validation check | Occurrences |
|---|---|
| terraform.validate: Unsupported argument | 42 |
| terraform.validate: Terraform configuration diagnostic | 18 |
| helm.lint: helm optional lint failed | 14 |
| grafana.panels: Dashboard requires panels | 6 |
| terraform.validate: Unsupported block type | 4 |
| terraform.validate: Invalid index | 3 |
| terraform.validate: Unsupported attribute | 3 |
| ansible-lint.lint: ansible-lint optional lint failed | 1 |
| document.parse: Document could not be parsed | 1 |
| k8s.configmap_ref: ConfigMap reference must resolve in its namespace | 1 |

### strict remaining blockers

| Rule | Occurrences |
|---|---|
| CKV_AWS_130 | 39 |
| CKV_AWS_91 | 37 |
| AWS-0053 | 36 |
| AWS-0164 | 36 |
| AWS-0104 | 25 |
| CKV_AWS_378 | 20 |
| KSV-0125 | 20 |
| CKV2_AWS_12 | 17 |
| AWS-0077 | 15 |
| CKV_AWS_260 | 13 |
| CKV_AWS_144 | 12 |
| CKV_AWS_157 | 11 |
| AWS-0090 | 10 |
| CKV_AWS_21 | 10 |
| CKV_AWS_18 | 9 |

### contextual-v1 remaining blockers

| Rule | Occurrences |
|---|---|
| CKV_AWS_91 | 37 |
| AWS-0053 | 35 |
| CKV_AWS_130 | 29 |
| AWS-0164 | 26 |
| AWS-0104 | 25 |
| CKV_AWS_378 | 20 |
| KSV-0125 | 20 |
| CKV2_AWS_12 | 17 |
| AWS-0077 | 15 |
| CKV_AWS_260 | 13 |
| CKV_AWS_144 | 12 |
| CKV_AWS_157 | 11 |
| AWS-0090 | 10 |
| CKV_AWS_21 | 10 |
| CKV_AWS_18 | 9 |

Contextual-v1 removes 9/12 blocker occurrences in set 1/2, but remaining blockers and invalid validation prevent any extra package passing. Missing plan-to-resource bindings restrict broader context rules (D-48); this is not the sole reason equal pass rates persist.

### Valid-package near misses

| Set | One blocker | 2–3 blockers | 4+ blockers |
|---|---|---|---|
| final set 1 | 1 | 0 | 1 |
| final set 2 | 0 | 2 | 4 |

### Catalogue and template outcomes

| Retained catalogue rule | Occurrences |
|---|---|
| AWS-0028 | 15 |
| AWS-0131 | 12 |
| CKV_AWS_103 | 23 |
| CKV_AWS_8 | 12 |

| Template | Outcome | Occurrences |
|---|---|---|
| access_logs | rejected | 194 |
| access_logs | retained | 10 |
| access_logs | skipped | 4 |
| flow_logs | rejected | 7 |
| flow_logs | retained | 28 |
| kms | rejected | 8 |
| kms | retained | 46 |
| kms | skipped | 16 |

Introduced template-rule occurrences (including rejected candidates): {"AWS-0132": 120, "CKV_AWS_144": 76, "CKV_AWS_145": 144, "CKV_AWS_18": 120}

### Security proposal acceptance before verification

| Benchmark | Accepted | Proposals |
|---|---|---|
| A3 | 12 | 140 |
| smoke | 47 | 49 |
| final set 1 | 142 | 147 |
| final set 2 | 153 | 157 |

The 47/49 figure belongs to the three-run smoke benchmark. Final proposal acceptance is 295/304. Proposals are not LLM attempts, verified retained changes or package pass counts. A3 attempt/format coverage remains unknown. Counts-only supplemental provenance hashes the read-only cached source snapshots without committing their contents.

## Timing and runtime attribution

| Benchmark | Stage | Count | Median s | Max s | Verdict |
|---|---|---|---|---|---|
| baseline | pr01 | 10 | 41.62084038749981 | 60.01117616299962 | PASS |
| baseline | deterministic_repairs | 0 | unknown | unknown | descriptive |
| baseline | final_security_scan | 0 | unknown | unknown | descriptive |
| baseline | final_validation | 0 | unknown | unknown | descriptive |
| baseline | generation_gate | 0 | unknown | unknown | descriptive |
| baseline | initial_validation | 0 | unknown | unknown | descriptive |
| baseline | post_security_validation | 0 | unknown | unknown | descriptive |
| baseline | security_iteration_verification | 0 | unknown | unknown | descriptive |
| baseline | validation_repair_round | 0 | unknown | unknown | descriptive |
| 9d | pr01 | 10 | 120.08073360800154 | 142.71156639100082 | PASS |
| 9d | deterministic_repairs | 0 | unknown | unknown | descriptive |
| 9d | final_security_scan | 0 | unknown | unknown | descriptive |
| 9d | final_validation | 0 | unknown | unknown | descriptive |
| 9d | generation_gate | 0 | unknown | unknown | descriptive |
| 9d | initial_validation | 0 | unknown | unknown | descriptive |
| 9d | post_security_validation | 0 | unknown | unknown | descriptive |
| 9d | security_iteration_verification | 0 | unknown | unknown | descriptive |
| 9d | validation_repair_round | 0 | unknown | unknown | descriptive |
| 9e | pr01 | 10 | 75.51232989599976 | 123.97397773300054 | PASS |
| 9e | deterministic_repairs | 84 | 0.047704692000479554 | 0.5786761919998753 | descriptive |
| 9e | final_security_scan | 40 | 4.908768710000004 | 12.06780247200004 | descriptive |
| 9e | final_validation | 40 | 0.1070776994993139 | 4.08563557800062 | descriptive |
| 9e | generation_gate | 40 | 28.143088118000378 | 119.87594170400007 | descriptive |
| 9e | initial_validation | 40 | 0.13176282650056237 | 7.310586949000026 | descriptive |
| 9e | post_security_validation | 40 | 0.1206731020006373 | 5.93382687599933 | descriptive |
| 9e | security_iteration_verification | 44 | 4.181310285000109 | 23.46391187000154 | descriptive |
| 9e | validation_repair_round | 71 | 18.458363826000095 | 69.6457880550006 | descriptive |
| 9e2 | pr01 | 10 | 94.47920793199955 | 161.34975938699972 | PASS |
| 9e2 | deterministic_repairs | 194 | 0.037618906500938465 | 0.6657897969998885 | descriptive |
| 9e2 | final_security_scan | 40 | 4.461502938999729 | 14.330641795000702 | descriptive |
| 9e2 | final_validation | 40 | 0.10006491300100606 | 9.119828795001013 | descriptive |
| 9e2 | generation_gate | 40 | 25.370663541499198 | 82.31395736599916 | descriptive |
| 9e2 | initial_validation | 40 | 0.1134167330001219 | 9.249846120999791 | descriptive |
| 9e2 | post_security_validation | 40 | 0.12344601950007927 | 12.54974291200051 | descriptive |
| 9e2 | security_iteration_verification | 154 | 3.9419845355005236 | 37.2485766389982 | descriptive |
| 9e2 | validation_repair_round | 87 | 14.769448056000329 | 75.50719103099982 | descriptive |
| A | pr01 | 10 | 133.92153543949826 | 157.25570357299875 | PASS |
| A | deterministic_repairs | 186 | 0.058249506502761506 | 1.1343296599952737 | descriptive |
| A | final_security_scan | 40 | 4.742411507500947 | 12.119209108997893 | descriptive |
| A | final_validation | 40 | 0.0797336739997263 | 5.702813989999413 | descriptive |
| A | generation_gate | 41 | 20.539721125998767 | 49.990478615996835 | descriptive |
| A | initial_validation | 41 | 0.08000004600035027 | 0.7263854170014383 | descriptive |
| A | post_security_validation | 40 | 0.09868282550087315 | 4.7714139750023605 | descriptive |
| A | security_iteration_verification | 146 | 9.325800148501003 | 46.0864812600048 | descriptive |
| A | validation_repair_round | 91 | 8.39982121900539 | 47.206021455000155 | descriptive |
| A2 | pr01 | 10 | 121.09235275599985 | 179.96733002999827 | PASS |
| A2 | deterministic_repairs | 168 | 0.03846404700016137 | 0.5765045850002934 | descriptive |
| A2 | final_security_scan | 36 | 5.405711739499566 | 16.105378233998636 | descriptive |
| A2 | final_validation | 36 | 0.14310144699811644 | 11.91665338799794 | descriptive |
| A2 | generation_gate | 36 | 22.669258846999583 | 81.96561143999861 | descriptive |
| A2 | initial_validation | 36 | 0.2543482814999152 | 3.555138504001661 | descriptive |
| A2 | post_security_validation | 36 | 0.15781453750059882 | 3.649152812002285 | descriptive |
| A2 | security_iteration_verification | 138 | 8.770428061005077 | 50.50675335099913 | descriptive |
| A2 | validation_repair_round | 77 | 8.494878804998734 | 39.67673861200092 | descriptive |
| A3 | pr01 | 10 | 134.6745607595003 | 203.15571544499835 | PASS |
| A3 | deterministic_repairs | 142 | 0.05228676100159646 | 0.8405360809992999 | descriptive |
| A3 | final_security_scan | 29 | 5.301197323999077 | 8.367508132003422 | descriptive |
| A3 | final_validation | 29 | 0.003442614004597999 | 0.5723178109983564 | descriptive |
| A3 | generation_gate | 29 | 23.3953002690032 | 44.02472685599787 | descriptive |
| A3 | initial_validation | 29 | 0.0030640229961136356 | 0.3542267640004866 | descriptive |
| A3 | post_security_validation | 29 | 0.002587781003967393 | 4.7335922089987434 | descriptive |
| A3 | security_iteration_verification | 115 | 10.368643825007894 | 50.84316083401063 | descriptive |
| A3 | validation_repair_round | 59 | 8.388891604998207 | 22.440721694001695 | descriptive |
| B | pr01 | 3 | 315.7148181560042 | 349.87597833299515 | INCOMPLETE |
| B | deterministic_repairs | 39 | 0.060429304001445416 | 0.7358206200005952 | descriptive |
| B | final_security_scan | 9 | 4.054718937994039 | 6.564914622002107 | descriptive |
| B | final_validation | 9 | 0.003712056997756008 | 0.2813665219946415 | descriptive |
| B | generation_gate | 9 | 36.38067308999598 | 60.45757596399926 | descriptive |
| B | initial_validation | 9 | 0.005641668998578098 | 0.2793766390022938 | descriptive |
| B | post_security_validation | 9 | 0.00444896499539027 | 0.46551047800312517 | descriptive |
| B | security_iteration_verification | 31 | 23.71133067300252 | 35.42415359199367 | descriptive |
| B | validation_repair_round | 19 | 30.109537698997883 | 56.18776279299345 | descriptive |
| final set 1 | pr01 | 10 | 162.3922934154998 | 198.03473391599982 | PASS |
| final set 1 | deterministic_repairs | 154 | 0.07884860100057267 | 1.091612518999682 | descriptive |
| final set 1 | final_security_scan | 40 | 5.812661208000463 | 14.285626754000987 | descriptive |
| final set 1 | final_validation | 40 | 0.006600960000469058 | 9.440075974000138 | descriptive |
| final set 1 | generation_gate | 40 | 17.49628770399977 | 80.68769021200023 | descriptive |
| final set 1 | initial_validation | 40 | 0.004339576499660325 | 3.3542337030012277 | descriptive |
| final set 1 | post_security_validation | 40 | 0.004774545000145736 | 3.653664110999671 | descriptive |
| final set 1 | security_iteration_verification | 129 | 24.46424147900143 | 54.72378266399937 | descriptive |
| final set 1 | validation_repair_round | 100 | 7.244098973499604 | 67.97272502799933 | descriptive |
| final set 2 | pr01 | 10 | 164.27101094950103 | 243.74560717200075 | PASS |
| final set 2 | deterministic_repairs | 167 | 0.08602844900087803 | 1.5198054170014075 | descriptive |
| final set 2 | final_security_scan | 41 | 5.6367478009997285 | 15.819555353999021 | descriptive |
| final set 2 | final_validation | 41 | 0.003398374001335469 | 16.636046707000787 | descriptive |
| final set 2 | generation_gate | 41 | 16.304251339000984 | 61.46782082199934 | descriptive |
| final set 2 | initial_validation | 41 | 0.0033070769986807136 | 4.157495392999408 | descriptive |
| final set 2 | post_security_validation | 41 | 0.004653052001231117 | 6.2998148890001175 | descriptive |
| final set 2 | security_iteration_verification | 140 | 28.489838280002004 | 54.822730673997285 | descriptive |
| final set 2 | validation_repair_round | 87 | 6.031977059001292 | 66.8678740230007 | descriptive |
| final combined | deterministic_repairs | 321 | 0.08286017299906234 | 1.5198054170014075 | descriptive |
| final combined | final_security_scan | 81 | 5.6388878140005545 | 15.819555353999021 | descriptive |
| final combined | final_validation | 81 | 0.0046396779998758575 | 16.636046707000787 | descriptive |
| final combined | generation_gate | 81 | 17.308257950000552 | 80.68769021200023 | descriptive |
| final combined | initial_validation | 81 | 0.0034520829995017266 | 4.157495392999408 | descriptive |
| final combined | post_security_validation | 81 | 0.004653052001231117 | 6.2998148890001175 | descriptive |
| final combined | security_iteration_verification | 269 | 26.665100596999764 | 54.822730673997285 | descriptive |
| final combined | validation_repair_round | 187 | 6.642477483999755 | 67.97272502799933 | descriptive |
| quiet stub PR-04 | session | 10 | 0.7008928024988563 | 0.7211179790028837 | PASS |
| quiet stub PR-04 | shared_key | 10 | 0.698919811500673 | 0.730614627005707 | PASS |
| quiet stub PR-04 | prevalidated_session | 10 | 0.6959961885004304 | 0.7342335089997505 | PASS |

### final set 1: PR-05 workloads

| Workload | Verdict | Observations | Failures | Missing |
|---|---|---|---|---|
| isolated_pr01 | PASS | 151 | 0 | 0 |
| isolated_pr03_baseline | PASS | 16 | 0 | 0 |
| concurrent_pr03_cohort | PASS | 57 | 0 | 0 |
| unclassified | INCOMPLETE | 0 | 0 | 0 |

### final set 2: PR-05 workloads

| Workload | Verdict | Observations | Failures | Missing |
|---|---|---|---|---|
| isolated_pr01 | PASS | 160 | 0 | 0 |
| isolated_pr03_baseline | PASS | 19 | 0 | 0 |
| concurrent_pr03_cohort | PASS | 53 | 0 | 0 |
| unclassified | INCOMPLETE | 0 | 0 | 0 |

### Final runtime telemetry

Per-run interval-union wall time and summed invocation work are distinct. Medians below are independent, non-additive and include only recorded observations.

| Set | Metric | Runs | Median | Maximum |
|---|---|---|---|---|
| final set 1 | tool_wall_seconds | 14 | 154.82429206371307 | 320.99525690078735 |
| final set 1 | tool_invocation_seconds | 14 | 348.0483885950089 | 977.5199585160008 |
| final set 1 | tool_queue_seconds | 14 | 0.0005436070023279171 | 108.80645844299215 |
| final set 1 | tool_invocations | 14 | 121.5 | 177 |
| final set 1 | cache_reuses | 14 | 47.5 | 61 |
| final set 2 | tool_wall_seconds | 14 | 166.415682554245 | 329.4101378917694 |
| final set 2 | tool_invocation_seconds | 14 | 447.71032700750675 | 940.4159280660115 |
| final set 2 | tool_queue_seconds | 14 | 0.0007000534969847649 | 85.79102293300821 |
| final set 2 | tool_invocations | 14 | 130.0 | 182 |
| final set 2 | cache_reuses | 14 | 51.0 | 71 |

D-54 runtime attribution: independent stage medians are not additive, nested/parallel tool intervals require unions, and missing historical reasoning/latency stays unknown. The historical 266.48 → 239.74 s smoke projection is counterfactual, not measured speedup. One fixed-input replay per configuration cannot isolate host load or cache warming. See ../../phase9-runtime-attribution.md.

### PR-03 reference methods

| Set | Isolated-baseline ratios (official ≤1.5) | PR-01 prompt-median ratios (secondary) |
|---|---|---|
| final set 1 | [2.024947737190979, 1.9599465459073915, 1.9008490768807509] | [2.0794701288193576, 2.0127187588312117, 1.9520300707862541] |
| final set 2 | [1.6624905968424453, 2.0215062779437973, 1.8348503001487426] | [1.7467541419974113, 2.1239665780838934, 1.9278499185603222] |

The i5-1135G7 / approximately 8 GB WSL2 host runs CPU-heavy local scanners and Terraform alongside concurrent runs. Resource contention is consistent with the evidence, but uncontrolled host load prevents a precise causal decomposition. No threshold or readiness condition changes.

## Inventory and comparability

### phase9-bench-real-20261014T101701420278Z

Captured settings: `null`.

### phase9-bench-real-20261015T124330508703Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[]`.

### phase9-bench-real-20261015T180417396510Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[]`.

### phase9-bench-real-20261016T210350514549Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[]`.

### phase9-bench-real-20261017T144629709424Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[]`.

### phase9-bench-real-20261017T220548142797Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 2, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 165, "max": 12, "median": 3, "p90": 12}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "openai/gpt-oss-120b:nitro", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 41}]`.

### phase9-bench-real-20261018T163731511036Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 2, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 182, "max": 12, "median": 3.0, "p90": 12}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "openai/gpt-oss-120b:nitro", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 36}]`.

### phase9-bench-real-20261018T213645241170Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 140, "max": 12, "median": 4.0, "p90": 12}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "openai/gpt-oss-120b:nitro", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 29}]`.

### phase9-bench-real-20261018T231027886459Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 32, "max": 12, "median": 4.0, "p90": 7}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "anthropic/claude-haiku-5.5", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 9}]`.

### phase9-bench-real-20261020T010134093069Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 147, "max": 12, "median": 3, "p90": 8}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "openai/gpt-oss-120b:nitro", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 40}]`.

### phase9-bench-real-20261020T013911945957Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 157, "max": 12, "median": 3, "p90": 9}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "openai/gpt-oss-120b:nitro", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 41}]`.

### phase9-bench-smoke-20261014T122810075341Z

Captured settings: `{"attempt_timeout_seconds": 90.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

### phase9-bench-smoke-20261019T222520294388Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 49, "max": 12, "median": 4, "p90": 12}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "openai/gpt-oss-120b:nitro", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 9}]`.

### phase9-bench-stub-20261013T182956518992Z

Captured settings: `null`.

### phase9-bench-stub-20261014T121247036453Z

Captured settings: `{"attempt_timeout_seconds": 120.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

### phase9-bench-stub-20261015T135741234853Z

Captured settings: `{"attempt_timeout_seconds": 120.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[]`.

### phase9-bench-stub-20261016T203756960530Z

Captured settings: `{"attempt_timeout_seconds": 120.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[]`.

### phase9-bench-stub-20261016T204355321818Z

Captured settings: `{"attempt_timeout_seconds": 120.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[]`.

### phase9-bench-stub-20261017T113847606154Z

Captured settings: `{"attempt_timeout_seconds": 120.0, "completion_timeout_seconds": 150.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 2, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[]`.

### phase9-bench-stub-20261017T213158569704Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 2, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 0, "max": null, "median": null, "p90": null}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "stub", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 42}]`.

### phase9-bench-stub-20261017T233345373191Z

Captured settings: `null`.

### phase9-bench-stub-20261017T233429468115Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 2, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 0, "max": null, "median": null, "p90": null}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "stub", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 42}]`.

### phase9-bench-stub-20261018T185418022034Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 0, "max": null, "median": null, "p90": null}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "stub", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 42}]`.

### phase9-bench-stub-20261018T191346950459Z

Captured settings: `{"attempt_timeout_seconds": 140.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 45.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 16000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 0, "max": null, "median": null, "p90": null}, "fix_attempt_timeout_seconds": [45.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "stub", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 42}]`.

### phase9-bench-stub-20261019T025515537899Z

Captured settings: `{"attempt_timeout_seconds": 120.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 90.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 0, "max": null, "median": null, "p90": null}, "fix_attempt_timeout_seconds": [90.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "stub", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 42}]`.

### phase9-bench-stub-20261019T154315214134Z

Captured settings: `{"attempt_timeout_seconds": 120.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 90.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

### phase9-bench-stub-20261019T154457135290Z

Captured settings: `{"attempt_timeout_seconds": 120.0, "completion_timeout_seconds": 150.0, "fix_attempt_timeout_seconds": 90.0, "generator_budget_seconds": 150.0, "llm_max_attempts": 3, "max_output_tokens": 8000, "max_package_attempts": 3, "security_deadline_seconds": 240.0, "security_fix_max_findings": 12, "security_fix_max_resources": 2, "security_iteration_timeout_seconds": 60.0, "security_partial_max_groups": 6, "structured_output": "json_schema"}`.

Recorded fixer configurations: `[{"calls_missing_measurements": 0, "findings_per_call": {"count": 0, "max": null, "median": null, "p90": null}, "fix_attempt_timeout_seconds": [90.0], "fix_max_findings": [12], "fix_max_resources": [2], "iteration_timeout_seconds": [60.0], "model": "stub", "partial_max_groups": [6], "security_stage_timeout_seconds": [240.0], "sessions": 42}]`.

| Folder | Date UTC | Commit | Generation model | Fixer model | Effort | Prompt G/F/A | Settled | Observed | Planned pipeline runs | Unknown variant slots | Packages | Passed | Missing observed | Stop | PR-01 | PR-03 | PR-04 | PR-05 | Known USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| phase9-bench-real-20261014T101701420278Z | 2026-10-14T10:17:01.426686+00:00 | 973926bc379607e050e4b42f894cb676d61432cc | anthropic/claude-sonnet-5 | openai/gpt-oss-120b:nitro | unknown; fixer details below | 3/1/2 | 7 | 8 | 14 | 3 | 10 | 1 | 14 | incomplete observation | INCOMPLETE | UNMEASURED | UNMEASURED | FAIL | 4.94097840 |
| phase9-bench-real-20261015T124330508703Z | 2026-10-15T12:43:30.585170+00:00 | 9d70323077550c25113b2d656b3f6939b3d6759c | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | unknown; fixer details below | 4/1/2 | 14 | 14 | 14 | 0 | 36 | 1 | 6 | schedule settled | PASS | FAIL | UNMEASURED | PASS | 0.42849895 |
| phase9-bench-real-20261015T180417396510Z | 2026-10-15T18:04:17.399958+00:00 | 77eefd1ac4d9db802cd9143573bbb558a0d1b5c5 | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | unknown; fixer details below | 5/2/2 | 14 | 14 | 14 | 0 | 40 | 1 | 2 | schedule settled | PASS | FAIL | UNMEASURED | PASS | 0.09105495 |
| phase9-bench-real-20261016T210350514549Z | 2026-10-16T21:03:50.517524+00:00 | dede5c884a7836ea1e2a8ff25b48327569efdd03 | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | unknown; fixer details below | 6/3/2 | 14 | 14 | 14 | 0 | 40 | 1 | 2 | schedule settled | PASS | FAIL | UNMEASURED | PASS | 0.1242728 |
| phase9-bench-real-20261017T144629709424Z | 2026-10-17T14:46:29.712948+00:00 | 887a4b77ce7d0a80c99210ec8f791c785b5fb441 | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | unknown; fixer details below | 6/4/2 | 14 | 14 | 14 | 0 | 40 | 1 | 2 | schedule settled | PASS | FAIL | UNMEASURED | PASS | 1.55955195 |
| phase9-bench-real-20261017T220548142797Z | 2026-10-17T22:05:48.145694+00:00 | 27d6a124ce3e695502d5480c58258c915e895c7d | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | unknown; fixer details below | 7/5/2 | 14 | 14 | 14 | 0 | 41 | 3 | 1 | schedule settled | PASS | FAIL | UNMEASURED | FAIL | 1.71957595 |
| phase9-bench-real-20261018T163731511036Z | 2026-10-18T16:37:31.518422+00:00 | acafb82d961151b222d441cea2317efe09426a15 | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | unknown; fixer details below | 8/6/2 | 14 | 14 | 14 | 0 | 36 | 1 | 6 | schedule settled | PASS | FAIL | UNMEASURED | FAIL | 1.40304135 |
| phase9-bench-real-20261018T213645241170Z | 2026-10-18T21:36:45.247215+00:00 | 6c0073b94bb002b1b5935e64011c1a313de5e799 | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | unknown; fixer details below | 9/6/2 | 11 | 11 | 14 | 0 | 29 | 1 | 4 | PR-03 baseline did not complete successfully. | PASS | INCOMPLETE | UNMEASURED | PASS | 1.13546510 |
| phase9-bench-real-20261018T231027886459Z | 2026-10-18T23:10:27.895208+00:00 | 6c0073b94bb002b1b5935e64011c1a313de5e799 | openai/gpt-oss-120b:nitro | anthropic/claude-haiku-5.5 | unknown; fixer details below | 9/6/2 | 11 | 11 | 14 | 0 | 9 | 1 | 24 | PR-03 baseline did not complete successfully. | INCOMPLETE | INCOMPLETE | UNMEASURED | PASS | 0.2401718 |
| phase9-bench-real-20261020T010134093069Z | 2026-10-20T01:01:34.101764+00:00 | 2028138727012df0f0d46a7666f5b0ab97ed8c39 | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | ['low'] | 9/7/2 | 14 | 14 | 14 | 0 | 40 | 7 | 2 | schedule settled | PASS | FAIL | UNMEASURED | PASS | 1.56622995 |
| phase9-bench-real-20261020T013911945957Z | 2026-10-20T01:39:11.954849+00:00 | 2028138727012df0f0d46a7666f5b0ab97ed8c39 | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | ['low'] | 9/7/2 | 14 | 14 | 14 | 0 | 41 | 8 | 1 | schedule settled | PASS | FAIL | UNMEASURED | PASS | 1.64478280 |
| phase9-bench-smoke-20261014T122810075341Z | 2026-10-14T12:28:10.078111+00:00 | 9d70323077550c25113b2d656b3f6939b3d6759c | anthropic/claude-sonnet-5 | openai/gpt-oss-120b:nitro | unknown; fixer details below | 4/1/2 | 3 | 3 | 3 | 0 | 4 | 1 | 5 | schedule settled | INCOMPLETE | UNMEASURED | UNMEASURED | FAIL | 1.34931195 |
| phase9-bench-smoke-20261019T222520294388Z | 2026-10-19T22:25:20.298681+00:00 | 84c0198f09e6ebdcda5d9865516fd7f1e0b70cd3 | openai/gpt-oss-120b:nitro | openai/gpt-oss-120b:nitro | ['low'] | 9/7/2 | 3 | 3 | 3 | 0 | 9 | 1 | 0 | schedule settled | INCOMPLETE | UNMEASURED | UNMEASURED | PASS | 0.32251365 |
| phase9-bench-stub-20261013T182956518992Z | 2026-10-13T18:29:56.523837+00:00 | 62098492b7d1458d19d67c17289a0e53544aa722 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261014T121247036453Z | 2026-10-14T12:12:47.043109+00:00 | 6bb0977f5f8fde4f17885d3c6e0bec4193fd3fbb | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261015T135741234853Z | 2026-10-15T13:57:41.238363+00:00 | da65d3e47f4c851065884125e049975b122fb929 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261016T203756960530Z | 2026-10-16T20:37:56.968357+00:00 | d48ff31d3e1be36b9b9a65faad4eaff898e9bf70 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261016T204355321818Z | 2026-10-16T20:43:55.327131+00:00 | d48ff31d3e1be36b9b9a65faad4eaff898e9bf70 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261017T113847606154Z | 2026-10-17T11:38:47.639282+00:00 | 99d9ce3ee89ca8b1015d6ae2815aca50aed33bd8 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | FAIL | PASS | 0.0 |
| phase9-bench-stub-20261017T213158569704Z | 2026-10-17T21:31:58.576704+00:00 | cce74b2d860b17647148f5504628d630791d7cb8 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261017T233345373191Z | 2026-10-17T23:33:45.392444+00:00 | 9e76fcb4e833b39e66e00ad03fd1501bd0cbe855 | stub | unknown | unknown; fixer details below | unknown | 0 | 0 | 14 | 0 | 0 | 0 | 0 | Authenticated benchmark settings require API_KEY on server and client. | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0 |
| phase9-bench-stub-20261017T233429468115Z | 2026-10-17T23:34:29.474818+00:00 | 9e76fcb4e833b39e66e00ad03fd1501bd0cbe855 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261018T185418022034Z | 2026-10-18T18:54:18.032115+00:00 | 7724efee4f525f486b56e0d5d3417d7ab5870714 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | FAIL | PASS | 0.0 |
| phase9-bench-stub-20261018T191346950459Z | 2026-10-18T19:13:46.967047+00:00 | 42b06ada96d09afead4cb03e82401149d58cfd9d | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261019T025515537899Z | 2026-10-19T02:55:15.547173+00:00 | 3c610ab00690757216a8da91b4337cf046833233 | stub | stub | unknown; fixer details below | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | PASS | PASS | 0.0 |
| phase9-bench-stub-20261019T154315214134Z | 2026-10-19T15:43:15.244113+00:00 | 10b814f7f713fc9ab60950141109dd9a7accf4af | stub | unknown | unknown; fixer details below | unknown | 0 | 0 | 14 | 0 | 0 | 0 | 0 | Seeding requires the development infraarch database and app role. | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0 |
| phase9-bench-stub-20261019T154457135290Z | 2026-10-19T15:44:57.144877+00:00 | 10b814f7f713fc9ab60950141109dd9a7accf4af | stub | stub | ['None'] | unknown | 14 | 14 | 14 | 0 | 42 | 42 | 0 | schedule settled | PASS | FAIL | FAIL | PASS | 0.0 |

Only final sets 1 and 2 are pooled: same commit, three prompt texts, settings and resolved low-effort gpt-oss-120b selections. All other phases are descriptive comparisons. A3/B are incomplete; B changes fixer model. Smoke samples cannot establish ten-run PR-01. Stub timings are rehearsal evidence, not real-provider performance. Historical production_ready preserves the recorded benchmark label when no failures/blockers were stored; early validity metadata is absent. Automatic labels do not establish deployment success.

## Threats to validity

Single WSL2 machine; one model family in the matched final comparison; three prompt texts repeatedly sampled; shared plans and repeated prompts; changing local work and provider routing/load; incomplete provider-limited sets; usage-delta cost limitations; stub/real differences; no deployment validation; exploratory multiple comparisons. NFR-04 clean deployment remains unverified.

## PR-04 attribution

# PR-04 offline session-check attribution

Synthetic rejected package; no LLM/scanner/validator executed. Same near-10 MB archive and SHA-256 in every condition. Two warm-ups and ten alternating measured requests per condition; loopback HTTP timing includes full response consumption. Test-only prevalidated_session skips the session touch lookup and is attribution only, not a production endpoint or authenticated compliance result.

| Condition | Count | Median s | Max s | ≤2 s every request |
|---|---:|---:|---:|---|
| session | 10 | 0.700893 | 0.721118 | PASS |
| shared_key | 10 | 0.698920 | 0.730615 | PASS |
| prevalidated_session | 10 | 0.695996 | 0.734234 | PASS |

Per-request session/user time, SQL execution totals and ZIP work are recorded in timings.csv. SQL totals overlap their enclosing operations and must not be added to them. Shared-key skips session/user work; prevalidated_session retains user lookup. Revocation after restoring the original guard returns HTTP 401. These are local descriptive samples, not proof for other machines or provider conditions. Prior 9h measurements remain unchanged. No production authentication guard was removed.

## Broad scenario benchmark

Descriptive statistics for one model family, with two runs per scenario by default. Actual repetition counts and model selections are recorded below. Complexity is pre-assigned, not inferred from generated resources. PR-01 timing has no verdict; PR-05 retains the existing thresholds. Stub results are rehearsals, separate from real results.

Rates use generated packages; missing variants count only settled runs. Unstarted slots are excluded, and incomplete accepted runs have unknown variant slots. Timing includes eligible success/partial-success runs; cost medians use known settled sequential costs. Missing measurements remain unavailable.

### phase9-bench-broad-20261020T225308383413Z (stub)

Runs per scenario: 2; registration SHA-256: `285bcb48c0d569bf06bd6b06d3a5cef52e28c0970ba6662ddc5380fafb6c288f`; registration commit: `7884c2f251c02737e02c04a4b3bd109e440f60ce`.

Recorded model: stub; fixer: stub.

Resolved selections: `{"14fac2fd-e4bc-47f7-82be-abd9b8d1e923": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "282b9469-215f-4829-8ec3-5ce161de0d69": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "2d045502-0068-43c0-8fe4-f6231e4d28e0": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "401b189e-2297-4eb6-b93a-cefb11736e6f": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "66f5425f-c48b-43d0-9509-055835bed131": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "87e79f22-e62f-41ce-a1a6-1a6a78f98a5a": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "96bac0cd-be0f-4b8d-83fd-505fda0f6235": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "9b63b932-0df5-4c29-a773-b65b1bf004fe": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "9be0398f-d705-4c62-808a-76aa1e77ec09": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "a0b332e2-03cb-4d54-85f8-29e857b92882": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "a34d858d-40cc-4bb7-b5d9-d2433a0117fd": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "b69a3eee-4358-492d-b4da-a30706416560": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "b6d0abaa-6be5-466a-baef-533e3709357a": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "b99e8b3a-6259-42fd-8555-bb4ef55903d8": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "bd2e3e38-8309-4c35-89de-50c0b914c02a": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "bf3686c5-a935-47e2-8447-98956e2799e2": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "bfaa0172-b364-4770-8c0e-22c58e2b3378": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "d2b51308-5011-4b63-92f0-002b104aa7be": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "d6c89d21-6184-43f3-95a2-6cbab6e672cd": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}, "eaac45c9-a1ff-430b-b088-cfefc4a4ed42": {"architect": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "fixer": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_cost": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_performance": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}, "generator_security": {"configured_thinking": null, "model": "stub", "provider": "stub", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": null}}}`.

#### Per scenario

| ID / level | Packages | Valid | Strict; Wilson 95% | Contextual-v1; Wilson 95% | Contextual-v2; Wilson 95% | Missing | Unstarted | Incomplete | Unknown slots | Failed runs | Median s | Median USD | Top blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Backup bucket | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 14.743904712500807 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 2. Static website | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 14.891027908000979 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 3. Serverless REST API | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 17.602080266500707 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 4. Private EC2 with SSM | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 20.386221117005334 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 5. Private RDS application | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 19.463125138492614 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 6. Fargate HTTPS application | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 18.296702694002306 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 7. Fargate database and cache | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 16.84659178799484 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 8. EKS Helm application | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 18.73515728649363 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 9. ECS application anchor | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 24.529713367504883 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 10. EKS microservices anchor | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 23.346537671997794 (n=2) | 0.0 (n=2) | none observed / unavailable |

#### Per complexity level

| ID / level | Packages | Valid | Strict; Wilson 95% | Contextual-v1; Wilson 95% | Contextual-v2; Wilson 95% | Missing | Unstarted | Incomplete | Unknown slots | Failed runs | Median s | Median USD | Top blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 14.743904712500807 (n=2) | 0.0 (n=2) | none observed / unavailable |
| 2 | 12 | 12 | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 0 | 0 | 0 | 0 | 0 | 16.49902841000585 (n=4) | 0.0 (n=4) | none observed / unavailable |
| 3 | 12 | 12 | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 0 | 0 | 0 | 0 | 0 | 20.386221117005334 (n=4) | 0.0 (n=4) | none observed / unavailable |
| 4 | 18 | 18 | 18/18 (100.00%; 82.41–100.00%) | 18/18 (100.00%; 82.41–100.00%) | 18/18 (100.00%; 82.41–100.00%) | 0 | 0 | 0 | 0 | 0 | 17.641757124496507 (n=6) | 0.0 (n=6) | none observed / unavailable |
| 5 | 12 | 12 | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 0 | 0 | 0 | 0 | 0 | 23.346537671997794 (n=4) | 0.0 (n=4) | none observed / unavailable |

#### Pass rate versus complexity level

| Level | Packages | strict | contextual-v1 | contextual-v2 |
|---|---|---|---|---|
| 1 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) |
| 2 | 12 | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) |
| 3 | 12 | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) |
| 4 | 18 | 18/18 (100.00%; 82.41–100.00%) | 18/18 (100.00%; 82.41–100.00%) | 18/18 (100.00%; 82.41–100.00%) |
| 5 | 12 | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) | 12/12 (100.00%; 75.75–100.00%) |

PR-05 recorded verdict: PASS.

### phase9-bench-broad-20261020T234203035108Z (real)

Runs per scenario: 2; registration SHA-256: `285bcb48c0d569bf06bd6b06d3a5cef52e28c0970ba6662ddc5380fafb6c288f`; registration commit: `7884c2f251c02737e02c04a4b3bd109e440f60ce`.

Recorded model: openai/gpt-oss-120b:nitro; fixer: openai/gpt-oss-120b:nitro.

Resolved selections: `{"113c0c5b-49cc-468b-a712-74c7c2d1adf1": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "14decd94-ff04-45f7-9b4f-5c2a0e0ab35e": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "2917b836-744c-443e-8a7a-10d97ad8f659": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "34568752-de05-4ede-a5d9-0d22aafeffc6": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "5c6df590-c0db-4e15-b602-335adc304e94": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "5fff70ec-0135-4c61-acda-683e7aebb59a": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "73bb48ca-8599-48a7-854e-79482225406e": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "73e03ef0-86b8-45bc-91b1-2148e8a12e65": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "7e050439-3155-40f7-a612-823e7244ff06": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "9872a498-f18a-4a9a-a2fa-919c3ca9e983": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "a4ce7d9a-54e9-4a64-b158-c0e0896c519f": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "a9e7620f-df79-4124-b53f-50d0f0d00da1": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "b7c1aa22-26fa-45a7-9754-ea487df14e75": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "bf044f12-fcbf-4155-ae14-17d7921b6288": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "bf327ada-0041-4c90-bea9-de01039fd1b0": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "c81ea7ea-2559-4e20-8173-47f699e12546": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "da77c0c2-59a4-4a45-bafe-5ae68abf8318": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "e6dd4c58-6020-4708-bc4a-306885186454": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "f5fd82a1-8048-4d3e-a78b-f4d2e4ecbd5c": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "f7bdc81f-5f5b-46e4-8cb8-88cc99257710": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}}`.

#### Per scenario

| ID / level | Packages | Valid | Strict; Wilson 95% | Contextual-v1; Wilson 95% | Contextual-v2; Wilson 95% | Missing | Unstarted | Incomplete | Unknown slots | Failed runs | Median s | Median USD | Top blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Backup bucket | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 128.65904808649793 (n=2) | 0.0257203 (n=2) | none observed / unavailable |
| 2. Static website | 6 | 3 | 3/6 (50.00%; 18.76–81.24%) | 3/6 (50.00%; 18.76–81.24%) | 3/6 (50.00%; 18.76–81.24%) | 0 | 0 | 0 | 0 | 0 | 119.8478454589931 (n=2) | 0.04026335 (n=2) | none observed / unavailable |
| 3. Serverless REST API | 6 | 3 | 3/6 (50.00%; 18.76–81.24%) | 3/6 (50.00%; 18.76–81.24%) | 3/6 (50.00%; 18.76–81.24%) | 0 | 0 | 0 | 0 | 0 | 85.57098201800545 (n=2) | 0.03258605 (n=2) | strict:AWS-0024=2; strict:AWS-0001=1; contextual-v1:AWS-0024=2; contextual-v1:AWS-0001=1; contextual-v2:AWS-0024=2; contextual-v2:AWS-0001=1 |
| 4. Private EC2 with SSM | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 61.1981602090018 (n=2) | 0.01707975 (n=2) | none observed / unavailable |
| 5. Private RDS application | 6 | 4 | 3/6 (50.00%; 18.76–81.24%) | 3/6 (50.00%; 18.76–81.24%) | 3/6 (50.00%; 18.76–81.24%) | 0 | 0 | 0 | 0 | 0 | 117.08632078699884 (n=2) | 0.0458753 (n=2) | strict:AWS-0104=2; strict:CKV_AWS_157=1; contextual-v1:AWS-0104=2; contextual-v1:CKV_AWS_157=1; contextual-v2:AWS-0104=2; contextual-v2:CKV_AWS_157=1 |
| 6. Fargate HTTPS application | 6 | 4 | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0 | 0 | 0 | 0 | 0 | 195.89313230900734 (n=2) | 0.083976675 (n=2) | strict:CKV_AWS_91=6; strict:AWS-0053=5; strict:AWS-0164=2; strict:CKV_AWS_130=2; strict:CKV_AWS_260=2; contextual-v1:CKV_AWS_91=6; contextual-v1:AWS-0053=5; contextual-v1:AWS-0164=2; contextual-v1:CKV_AWS_130=2; contextual-v1:CKV_AWS_260=2; contextual-v2:CKV_AWS_91=6; contextual-v2:AWS-0164=2; contextual-v2:CKV_AWS_130=2; contextual-v2:AWS-0104=1; contextual-v2:CKV_AWS_260=1 |
| 7. Fargate database and cache | 6 | 4 | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0 | 0 | 0 | 0 | 0 | 183.733859992004 (n=2) | 0.11204982499999999 (n=2) | strict:AWS-0053=5; strict:CKV_AWS_130=5; strict:CKV_AWS_91=5; strict:AWS-0164=2; strict:CKV_AWS_157=2; contextual-v1:AWS-0053=5; contextual-v1:CKV_AWS_130=5; contextual-v1:CKV_AWS_91=5; contextual-v1:AWS-0164=2; contextual-v1:CKV_AWS_157=2; contextual-v2:CKV_AWS_130=5; contextual-v2:CKV_AWS_91=5; contextual-v2:AWS-0164=2; contextual-v2:CKV_AWS_157=2; contextual-v2:AWS-0045=1 |
| 8. EKS Helm application | 6 | 1 | 1/6 (16.67%; 3.01–56.35%) | 1/6 (16.67%; 3.01–56.35%) | 1/6 (16.67%; 3.01–56.35%) | 0 | 0 | 0 | 0 | 0 | 175.30071511500137 (n=2) | 0.065404025 (n=2) | strict:AWS-0104=1; contextual-v1:AWS-0104=1; contextual-v2:AWS-0104=1 |
| 9. ECS application anchor | 6 | 4 | 2/6 (33.33%; 9.68–70.00%) | 2/6 (33.33%; 9.68–70.00%) | 2/6 (33.33%; 9.68–70.00%) | 0 | 0 | 0 | 0 | 0 | 204.12713290949614 (n=2) | 0.06898805 (n=2) | strict:AWS-0053=3; strict:CKV_AWS_91=3; strict:AWS-0054=1; strict:AWS-0090=1; strict:CKV2_AWS_12=1; contextual-v1:CKV_AWS_91=3; contextual-v1:AWS-0053=2; contextual-v1:AWS-0054=1; contextual-v1:AWS-0090=1; contextual-v1:CKV2_AWS_12=1; contextual-v2:CKV_AWS_91=3; contextual-v2:AWS-0053=1; contextual-v2:AWS-0054=1; contextual-v2:AWS-0090=1; contextual-v2:CKV2_AWS_12=1 |
| 10. EKS microservices anchor | 6 | 0 | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0 | 0 | 0 | 0 | 0 | 340.7944723184992 (n=2) | 0.14586397499999998 (n=2) | strict:AWS-0053=5; strict:AWS-0090=3; strict:CKV_AWS_21=3; strict:CKV_AWS_91=3; strict:AWS-0039=2; contextual-v1:AWS-0053=5; contextual-v1:AWS-0090=3; contextual-v1:CKV_AWS_21=3; contextual-v1:CKV_AWS_91=3; contextual-v1:AWS-0039=2; contextual-v2:AWS-0053=3; contextual-v2:AWS-0090=3; contextual-v2:CKV_AWS_21=3; contextual-v2:CKV_AWS_91=3; contextual-v2:AWS-0039=2 |

#### Per complexity level

| ID / level | Packages | Valid | Strict; Wilson 95% | Contextual-v1; Wilson 95% | Contextual-v2; Wilson 95% | Missing | Unstarted | Incomplete | Unknown slots | Failed runs | Median s | Median USD | Top blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 6 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 0 | 0 | 0 | 0 | 0 | 128.65904808649793 (n=2) | 0.0257203 (n=2) | none observed / unavailable |
| 2 | 12 | 6 | 6/12 (50.00%; 25.38–74.62%) | 6/12 (50.00%; 25.38–74.62%) | 6/12 (50.00%; 25.38–74.62%) | 0 | 0 | 0 | 0 | 0 | 119.01644014349586 (n=4) | 0.04026335 (n=4) | strict:AWS-0024=2; strict:AWS-0001=1; contextual-v1:AWS-0024=2; contextual-v1:AWS-0001=1; contextual-v2:AWS-0024=2; contextual-v2:AWS-0001=1 |
| 3 | 12 | 10 | 9/12 (75.00%; 46.77–91.11%) | 9/12 (75.00%; 46.77–91.11%) | 9/12 (75.00%; 46.77–91.11%) | 0 | 0 | 0 | 0 | 0 | 87.16303857449384 (n=4) | 0.028573575000000004 (n=4) | strict:AWS-0104=2; strict:CKV_AWS_157=1; contextual-v1:AWS-0104=2; contextual-v1:CKV_AWS_157=1; contextual-v2:AWS-0104=2; contextual-v2:CKV_AWS_157=1 |
| 4 | 18 | 9 | 1/18 (5.56%; 0.99–25.76%) | 1/18 (5.56%; 0.99–25.76%) | 1/18 (5.56%; 0.99–25.76%) | 0 | 0 | 0 | 0 | 0 | 193.67541224000888 (n=6) | 0.08524527500000001 (n=6) | strict:CKV_AWS_91=11; strict:AWS-0053=10; strict:CKV_AWS_130=7; strict:AWS-0164=4; strict:AWS-0104=3; contextual-v1:CKV_AWS_91=11; contextual-v1:AWS-0053=10; contextual-v1:CKV_AWS_130=7; contextual-v1:AWS-0164=4; contextual-v1:AWS-0104=3; contextual-v2:CKV_AWS_91=11; contextual-v2:CKV_AWS_130=7; contextual-v2:AWS-0164=4; contextual-v2:AWS-0104=3; contextual-v2:CKV_AWS_157=2 |
| 5 | 12 | 4 | 2/12 (16.67%; 4.70–44.80%) | 2/12 (16.67%; 4.70–44.80%) | 2/12 (16.67%; 4.70–44.80%) | 0 | 0 | 0 | 0 | 0 | 282.9110638639977 (n=4) | 0.10320357499999999 (n=4) | strict:AWS-0053=8; strict:CKV_AWS_91=6; strict:AWS-0090=4; strict:CKV_AWS_21=4; strict:CKV2_AWS_12=3; contextual-v1:AWS-0053=7; contextual-v1:CKV_AWS_91=6; contextual-v1:AWS-0090=4; contextual-v1:CKV_AWS_21=4; contextual-v1:CKV2_AWS_12=3; contextual-v2:CKV_AWS_91=6; contextual-v2:AWS-0053=4; contextual-v2:AWS-0090=4; contextual-v2:CKV_AWS_21=4; contextual-v2:CKV2_AWS_12=3 |

#### Pass rate versus complexity level

| Level | Packages | strict | contextual-v1 | contextual-v2 |
|---|---|---|---|---|
| 1 | 6 | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) | 6/6 (100.00%; 60.97–100.00%) |
| 2 | 12 | 6/12 (50.00%; 25.38–74.62%) | 6/12 (50.00%; 25.38–74.62%) | 6/12 (50.00%; 25.38–74.62%) |
| 3 | 12 | 9/12 (75.00%; 46.77–91.11%) | 9/12 (75.00%; 46.77–91.11%) | 9/12 (75.00%; 46.77–91.11%) |
| 4 | 18 | 1/18 (5.56%; 0.99–25.76%) | 1/18 (5.56%; 0.99–25.76%) | 1/18 (5.56%; 0.99–25.76%) |
| 5 | 12 | 2/12 (16.67%; 4.70–44.80%) | 2/12 (16.67%; 4.70–44.80%) | 2/12 (16.67%; 4.70–44.80%) |

#### Anchors versus final sets

| Scenario | Final set | Profile | Unit | Broad | Final | Fisher two-sided p |
|---|---|---|---|---|---|---|
| 2 | final set 1 | strict | package | 3/6 | 6/9 | 0.6223776223776224 |
| 2 | final set 1 | strict | run | 2/2 | 3/3 | 1.0 |
| 2 | final set 1 | contextual-v1 | package | 3/6 | 6/9 | 0.6223776223776224 |
| 2 | final set 1 | contextual-v1 | run | 2/2 | 3/3 | 1.0 |
| 2 | final set 1 | contextual-v2 | package | 3/6 | None/9 | unknown |
| 2 | final set 1 | contextual-v2 | run | 2/2 | None/3 | unknown |
| 2 | final set 2 | strict | package | 3/6 | 7/9 | 0.32867132867132864 |
| 2 | final set 2 | strict | run | 2/2 | 3/3 | 1.0 |
| 2 | final set 2 | contextual-v1 | package | 3/6 | 7/9 | 0.32867132867132864 |
| 2 | final set 2 | contextual-v1 | run | 2/2 | 3/3 | 1.0 |
| 2 | final set 2 | contextual-v2 | package | 3/6 | None/9 | unknown |
| 2 | final set 2 | contextual-v2 | run | 2/2 | None/3 | unknown |
| 2 | final combined | strict | package | 3/6 | 13/18 | 0.36176409402954024 |
| 2 | final combined | strict | run | 2/2 | 6/6 | 1.0 |
| 2 | final combined | contextual-v1 | package | 3/6 | 13/18 | 0.36176409402954024 |
| 2 | final combined | contextual-v1 | run | 2/2 | 6/6 | 1.0 |
| 2 | final combined | contextual-v2 | package | 3/6 | None/18 | unknown |
| 2 | final combined | contextual-v2 | run | 2/2 | None/6 | unknown |
| 9 | final set 1 | strict | package | 2/6 | 1/23 | 0.09989053092501368 |
| 9 | final set 1 | strict | run | 2/2 | 1/8 | 0.06666666666666667 |
| 9 | final set 1 | contextual-v1 | package | 2/6 | 1/23 | 0.09989053092501368 |
| 9 | final set 1 | contextual-v1 | run | 2/2 | 1/8 | 0.06666666666666667 |
| 9 | final set 1 | contextual-v2 | package | 2/6 | None/23 | unknown |
| 9 | final set 1 | contextual-v2 | run | 2/2 | None/8 | unknown |
| 9 | final set 2 | strict | package | 2/6 | 0/24 | 0.034482758620689655 |
| 9 | final set 2 | strict | run | 2/2 | 0/8 | 0.022222222222222223 |
| 9 | final set 2 | contextual-v1 | package | 2/6 | 0/24 | 0.034482758620689655 |
| 9 | final set 2 | contextual-v1 | run | 2/2 | 0/8 | 0.022222222222222223 |
| 9 | final set 2 | contextual-v2 | package | 2/6 | None/24 | unknown |
| 9 | final set 2 | contextual-v2 | run | 2/2 | None/8 | unknown |
| 9 | final combined | strict | package | 2/6 | 1/47 | 0.03094851873986169 |
| 9 | final combined | strict | run | 2/2 | 1/16 | 0.0196078431372549 |
| 9 | final combined | contextual-v1 | package | 2/6 | 1/47 | 0.03094851873986169 |
| 9 | final combined | contextual-v1 | run | 2/2 | 1/16 | 0.0196078431372549 |
| 9 | final combined | contextual-v2 | package | 2/6 | None/47 | unknown |
| 9 | final combined | contextual-v2 | run | 2/2 | None/16 | unknown |
| 10 | final set 1 | strict | package | 0/6 | 0/8 | 1.0 |
| 10 | final set 1 | strict | run | 0/2 | 0/3 | 1.0 |
| 10 | final set 1 | contextual-v1 | package | 0/6 | 0/8 | 1.0 |
| 10 | final set 1 | contextual-v1 | run | 0/2 | 0/3 | 1.0 |
| 10 | final set 1 | contextual-v2 | package | 0/6 | None/8 | unknown |
| 10 | final set 1 | contextual-v2 | run | 0/2 | None/3 | unknown |
| 10 | final set 2 | strict | package | 0/6 | 1/8 | 1.0 |
| 10 | final set 2 | strict | run | 0/2 | 1/3 | 1.0 |
| 10 | final set 2 | contextual-v1 | package | 0/6 | 1/8 | 1.0 |
| 10 | final set 2 | contextual-v1 | run | 0/2 | 1/3 | 1.0 |
| 10 | final set 2 | contextual-v2 | package | 0/6 | None/8 | unknown |
| 10 | final set 2 | contextual-v2 | run | 0/2 | None/3 | unknown |
| 10 | final combined | strict | package | 0/6 | 1/16 | 1.0 |
| 10 | final combined | strict | run | 0/2 | 1/6 | 1.0 |
| 10 | final combined | contextual-v1 | package | 0/6 | 1/16 | 1.0 |
| 10 | final combined | contextual-v1 | run | 0/2 | 1/6 | 1.0 |
| 10 | final combined | contextual-v2 | package | 0/6 | None/16 | unknown |
| 10 | final combined | contextual-v2 | run | 0/2 | None/6 | unknown |

PR-05 recorded verdict: PASS.

### phase9-bench-broad-20261021T200436165739Z (real)

Runs per scenario: 2; registration SHA-256: `285bcb48c0d569bf06bd6b06d3a5cef52e28c0970ba6662ddc5380fafb6c288f`; registration commit: `7884c2f251c02737e02c04a4b3bd109e440f60ce`.

Recorded model: openai/gpt-oss-120b:nitro; fixer: openai/gpt-oss-120b:nitro.

Resolved selections: `{"0452eefa-601d-4cd3-8934-d23d13c5b5cb": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "1c410860-15e7-495e-8567-50debdd8d438": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "3f908f47-88ef-41a9-82e5-11a9c2301141": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "67345bcd-26be-493f-89fa-abfeed909159": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "69217b2c-061b-4c15-a364-37d1c2bb220b": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "7b0493ba-e06b-4b1c-9f1e-18d1df8b7d23": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "8d9ef032-7f22-426b-9b73-fbe63647c663": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "8e7ace81-03e9-4fcf-9258-a326211fb0d9": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "93c30ed8-db20-44ba-b701-054f8f6e15b4": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "9a277d2d-e667-4a06-9f21-f369f64786d4": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "a62094cd-8a5a-42c5-9970-c583a56c1129": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "c1fa2eef-8460-440e-8742-3fc06d34b519": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "c566276f-6530-4b68-9c10-ddf0e2ea11bc": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "cda319c1-6b38-4534-96aa-ca36b37795de": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "d08be9f7-dc06-4d8a-a7dc-649fd495b96f": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "d3a112fe-ff76-4c33-812f-9d997b210f74": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "da8bc90b-31d5-44d6-bf01-e149ee3b362c": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "e9c9567c-b94a-4281-9107-410c9650348a": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "eeaba55a-cb17-46a9-89b4-8d015263e414": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}, "f46d7016-5b7d-4e38-bee2-3ca0bfe8df07": {"architect": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "fixer": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_cost": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_performance": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}, "generator_security": {"configured_thinking": "low", "model": "openai/gpt-oss-120b:nitro", "provider": "openai", "reasoning_capability_source": "unprobed", "reasoning_capable": null, "request_style": "legacy", "thinking_mode": "low"}}}`.

#### Per scenario

| ID / level | Packages | Valid | Strict; Wilson 95% | Contextual-v1; Wilson 95% | Contextual-v2; Wilson 95% | Missing | Unstarted | Incomplete | Unknown slots | Failed runs | Median s | Median USD | Top blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Backup bucket | 6 | 6 | 4/6 (66.67%; 30.00–90.32%) | 4/6 (66.67%; 30.00–90.32%) | 4/6 (66.67%; 30.00–90.32%) | 0 | 0 | 0 | 0 | 0 | 158.49294543200006 (n=2) | 0.021506749999999998 (n=2) | strict:AWS-0132=1; strict:CKV_AWS_111=1; strict:CKV_AWS_145=1; strict:CKV_AWS_18=1; contextual-v1:AWS-0132=1; contextual-v1:CKV_AWS_111=1; contextual-v1:CKV_AWS_145=1; contextual-v1:CKV_AWS_18=1; contextual-v2:AWS-0132=1; contextual-v2:CKV_AWS_111=1; contextual-v2:CKV_AWS_145=1; contextual-v2:CKV_AWS_18=1 |
| 2. Static website | 6 | 3 | 2/6 (33.33%; 9.68–70.00%) | 2/6 (33.33%; 9.68–70.00%) | 2/6 (33.33%; 9.68–70.00%) | 0 | 0 | 0 | 0 | 0 | 145.6661768135 (n=2) | 0.050696450000000004 (n=2) | strict:AWS-0010=2; strict:AWS-0011=2; strict:CKV_AWS_18=2; strict:AWS-0013=1; contextual-v1:AWS-0010=2; contextual-v1:AWS-0011=2; contextual-v1:CKV_AWS_18=2; contextual-v1:AWS-0013=1; contextual-v2:AWS-0010=2; contextual-v2:AWS-0011=2; contextual-v2:CKV_AWS_18=2; contextual-v2:AWS-0013=1 |
| 3. Serverless REST API | 6 | 5 | 5/6 (83.33%; 43.65–96.99%) | 5/6 (83.33%; 43.65–96.99%) | 5/6 (83.33%; 43.65–96.99%) | 0 | 0 | 0 | 0 | 0 | 51.36704697450023 (n=2) | 0.028285474999999997 (n=2) | none observed / unavailable |
| 4. Private EC2 with SSM | 6 | 2 | 2/6 (33.33%; 9.68–70.00%) | 2/6 (33.33%; 9.68–70.00%) | 2/6 (33.33%; 9.68–70.00%) | 0 | 0 | 0 | 0 | 0 | 94.61185958049987 (n=2) | 0.047689825000000005 (n=2) | none observed / unavailable |
| 5. Private RDS application | 6 | 5 | 5/6 (83.33%; 43.65–96.99%) | 5/6 (83.33%; 43.65–96.99%) | 5/6 (83.33%; 43.65–96.99%) | 0 | 0 | 0 | 0 | 0 | 111.73313298949984 (n=2) | 0.042875125 (n=2) | none observed / unavailable |
| 6. Fargate HTTPS application | 6 | 6 | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0 | 0 | 0 | 0 | 0 | 176.43046247550024 (n=2) | 0.058815549999999994 (n=2) | strict:AWS-0053=6; strict:CKV_AWS_91=5; strict:CKV_AWS_130=2; strict:AWS-0090=1; strict:AWS-0164=1; contextual-v1:AWS-0053=6; contextual-v1:CKV_AWS_91=5; contextual-v1:CKV_AWS_130=2; contextual-v1:AWS-0090=1; contextual-v1:AWS-0164=1; contextual-v2:CKV_AWS_91=5; contextual-v2:CKV_AWS_130=2; contextual-v2:AWS-0090=1; contextual-v2:AWS-0164=1; contextual-v2:CKV_AWS_144=1 |
| 7. Fargate database and cache | 6 | 5 | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0 | 0 | 0 | 0 | 0 | 204.99818267550017 (n=2) | 0.08771332500000001 (n=2) | strict:AWS-0053=6; strict:CKV_AWS_91=6; strict:CKV_AWS_157=2; strict:AWS-0050=1; strict:AWS-0164=1; contextual-v1:CKV_AWS_91=6; contextual-v1:AWS-0053=5; contextual-v1:CKV_AWS_157=2; contextual-v1:AWS-0050=1; contextual-v1:CKV2_AWS_12=1; contextual-v2:CKV_AWS_91=6; contextual-v2:CKV_AWS_157=2; contextual-v2:AWS-0050=1; contextual-v2:AWS-0053=1; contextual-v2:CKV2_AWS_12=1 |
| 8. EKS Helm application | 6 | 2 | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0 | 0 | 0 | 0 | 0 | 297.12687812800027 (n=2) | 0.10063355 (n=2) | strict:AWS-0053=7; strict:CKV_AWS_91=6; strict:CKV2_AWS_12=4; strict:CKV_AWS_130=3; strict:AWS-0164=2; contextual-v1:CKV_AWS_91=6; contextual-v1:AWS-0053=5; contextual-v1:CKV2_AWS_12=4; contextual-v1:CKV_AWS_130=3; contextual-v1:AWS-0164=2; contextual-v2:CKV_AWS_91=6; contextual-v2:CKV2_AWS_12=4; contextual-v2:CKV_AWS_130=3; contextual-v2:AWS-0053=2; contextual-v2:AWS-0164=2 |
| 9. ECS application anchor | 6 | 1 | 1/6 (16.67%; 3.01–56.35%) | 1/6 (16.67%; 3.01–56.35%) | 1/6 (16.67%; 3.01–56.35%) | 0 | 0 | 0 | 0 | 0 | 208.48413451750025 (n=2) | 0.145829975 (n=2) | strict:AWS-0164=6; strict:CKV_AWS_130=6; strict:AWS-0104=4; strict:CKV2_AWS_12=3; strict:AWS-0053=2; contextual-v1:AWS-0164=6; contextual-v1:CKV_AWS_130=6; contextual-v1:AWS-0104=4; contextual-v1:CKV2_AWS_12=3; contextual-v1:AWS-0090=2; contextual-v2:AWS-0164=6; contextual-v2:CKV_AWS_130=6; contextual-v2:AWS-0104=4; contextual-v2:CKV2_AWS_12=3; contextual-v2:AWS-0053=2 |
| 10. EKS microservices anchor | 6 | 2 | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0/6 (0.00%; 0.00–39.03%) | 0 | 0 | 0 | 0 | 0 | 274.79663545649987 (n=2) | 0.1247025 (n=2) | strict:KSV-0125=4; strict:AWS-0039=2; strict:AWS-0053=2; strict:AWS-0090=2; strict:AWS-0104=2; contextual-v1:KSV-0125=4; contextual-v1:AWS-0039=2; contextual-v1:AWS-0053=2; contextual-v1:AWS-0090=2; contextual-v1:AWS-0104=2; contextual-v2:KSV-0125=4; contextual-v2:AWS-0039=2; contextual-v2:AWS-0090=2; contextual-v2:AWS-0104=2; contextual-v2:CKV_AWS_21=2 |

#### Per complexity level

| ID / level | Packages | Valid | Strict; Wilson 95% | Contextual-v1; Wilson 95% | Contextual-v2; Wilson 95% | Missing | Unstarted | Incomplete | Unknown slots | Failed runs | Median s | Median USD | Top blockers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 6 | 6 | 4/6 (66.67%; 30.00–90.32%) | 4/6 (66.67%; 30.00–90.32%) | 4/6 (66.67%; 30.00–90.32%) | 0 | 0 | 0 | 0 | 0 | 158.49294543200006 (n=2) | 0.021506749999999998 (n=2) | strict:AWS-0132=1; strict:CKV_AWS_111=1; strict:CKV_AWS_145=1; strict:CKV_AWS_18=1; contextual-v1:AWS-0132=1; contextual-v1:CKV_AWS_111=1; contextual-v1:CKV_AWS_145=1; contextual-v1:CKV_AWS_18=1; contextual-v2:AWS-0132=1; contextual-v2:CKV_AWS_111=1; contextual-v2:CKV_AWS_145=1; contextual-v2:CKV_AWS_18=1 |
| 2 | 12 | 8 | 7/12 (58.33%; 31.95–80.67%) | 7/12 (58.33%; 31.95–80.67%) | 7/12 (58.33%; 31.95–80.67%) | 0 | 0 | 0 | 0 | 0 | 98.80469372100015 (n=4) | 0.04096985 (n=4) | strict:AWS-0010=2; strict:AWS-0011=2; strict:CKV_AWS_18=2; strict:AWS-0013=1; contextual-v1:AWS-0010=2; contextual-v1:AWS-0011=2; contextual-v1:CKV_AWS_18=2; contextual-v1:AWS-0013=1; contextual-v2:AWS-0010=2; contextual-v2:AWS-0011=2; contextual-v2:CKV_AWS_18=2; contextual-v2:AWS-0013=1 |
| 3 | 12 | 7 | 7/12 (58.33%; 31.95–80.67%) | 7/12 (58.33%; 31.95–80.67%) | 7/12 (58.33%; 31.95–80.67%) | 0 | 0 | 0 | 0 | 0 | 111.1924934064998 (n=4) | 0.047689825000000005 (n=4) | none observed / unavailable |
| 4 | 18 | 13 | 0/18 (0.00%; 0.00–17.59%) | 0/18 (0.00%; 0.00–17.59%) | 0/18 (0.00%; 0.00–17.59%) | 0 | 0 | 0 | 0 | 0 | 204.99818267550017 (n=6) | 0.08771332500000001 (n=6) | strict:AWS-0053=19; strict:CKV_AWS_91=17; strict:CKV_AWS_130=6; strict:CKV2_AWS_12=5; strict:AWS-0164=4; contextual-v1:CKV_AWS_91=17; contextual-v1:AWS-0053=16; contextual-v1:CKV2_AWS_12=5; contextual-v1:CKV_AWS_130=5; contextual-v1:AWS-0164=3; contextual-v2:CKV_AWS_91=17; contextual-v2:CKV2_AWS_12=5; contextual-v2:CKV_AWS_130=5; contextual-v2:AWS-0053=3; contextual-v2:AWS-0164=3 |
| 5 | 12 | 3 | 1/12 (8.33%; 1.49–35.39%) | 1/12 (8.33%; 1.49–35.39%) | 1/12 (8.33%; 1.49–35.39%) | 0 | 0 | 0 | 0 | 0 | 240.23029080950005 (n=4) | 0.1247025 (n=4) | strict:AWS-0104=6; strict:AWS-0164=6; strict:CKV_AWS_130=6; strict:AWS-0053=4; strict:AWS-0090=4; contextual-v1:AWS-0104=6; contextual-v1:AWS-0164=6; contextual-v1:CKV_AWS_130=6; contextual-v1:AWS-0090=4; contextual-v1:CKV_AWS_21=4; contextual-v2:AWS-0104=6; contextual-v2:AWS-0164=6; contextual-v2:CKV_AWS_130=6; contextual-v2:AWS-0090=4; contextual-v2:CKV_AWS_21=4 |

#### Pass rate versus complexity level

| Level | Packages | strict | contextual-v1 | contextual-v2 |
|---|---|---|---|---|
| 1 | 6 | 4/6 (66.67%; 30.00–90.32%) | 4/6 (66.67%; 30.00–90.32%) | 4/6 (66.67%; 30.00–90.32%) |
| 2 | 12 | 7/12 (58.33%; 31.95–80.67%) | 7/12 (58.33%; 31.95–80.67%) | 7/12 (58.33%; 31.95–80.67%) |
| 3 | 12 | 7/12 (58.33%; 31.95–80.67%) | 7/12 (58.33%; 31.95–80.67%) | 7/12 (58.33%; 31.95–80.67%) |
| 4 | 18 | 0/18 (0.00%; 0.00–17.59%) | 0/18 (0.00%; 0.00–17.59%) | 0/18 (0.00%; 0.00–17.59%) |
| 5 | 12 | 1/12 (8.33%; 1.49–35.39%) | 1/12 (8.33%; 1.49–35.39%) | 1/12 (8.33%; 1.49–35.39%) |

#### Anchors versus final sets

| Scenario | Final set | Profile | Unit | Broad | Final | Fisher two-sided p |
|---|---|---|---|---|---|---|
| 2 | final set 1 | strict | package | 2/6 | 6/9 | 0.3146853146853147 |
| 2 | final set 1 | strict | run | 2/2 | 3/3 | 1.0 |
| 2 | final set 1 | contextual-v1 | package | 2/6 | 6/9 | 0.3146853146853147 |
| 2 | final set 1 | contextual-v1 | run | 2/2 | 3/3 | 1.0 |
| 2 | final set 1 | contextual-v2 | package | 2/6 | None/9 | unknown |
| 2 | final set 1 | contextual-v2 | run | 2/2 | None/3 | unknown |
| 2 | final set 2 | strict | package | 2/6 | 7/9 | 0.13566433566433567 |
| 2 | final set 2 | strict | run | 2/2 | 3/3 | 1.0 |
| 2 | final set 2 | contextual-v1 | package | 2/6 | 7/9 | 0.13566433566433567 |
| 2 | final set 2 | contextual-v1 | run | 2/2 | 3/3 | 1.0 |
| 2 | final set 2 | contextual-v2 | package | 2/6 | None/9 | unknown |
| 2 | final set 2 | contextual-v2 | run | 2/2 | None/3 | unknown |
| 2 | final combined | strict | package | 2/6 | 13/18 | 0.1501456209694196 |
| 2 | final combined | strict | run | 2/2 | 6/6 | 1.0 |
| 2 | final combined | contextual-v1 | package | 2/6 | 13/18 | 0.1501456209694196 |
| 2 | final combined | contextual-v1 | run | 2/2 | 6/6 | 1.0 |
| 2 | final combined | contextual-v2 | package | 2/6 | None/18 | unknown |
| 2 | final combined | contextual-v2 | run | 2/2 | None/6 | unknown |
| 9 | final set 1 | strict | package | 1/6 | 1/23 | 0.3768472906403941 |
| 9 | final set 1 | strict | run | 1/2 | 1/8 | 0.37777777777777777 |
| 9 | final set 1 | contextual-v1 | package | 1/6 | 1/23 | 0.3768472906403941 |
| 9 | final set 1 | contextual-v1 | run | 1/2 | 1/8 | 0.37777777777777777 |
| 9 | final set 1 | contextual-v2 | package | 1/6 | None/23 | unknown |
| 9 | final set 1 | contextual-v2 | run | 1/2 | None/8 | unknown |
| 9 | final set 2 | strict | package | 1/6 | 0/24 | 0.2 |
| 9 | final set 2 | strict | run | 1/2 | 0/8 | 0.2 |
| 9 | final set 2 | contextual-v1 | package | 1/6 | 0/24 | 0.2 |
| 9 | final set 2 | contextual-v1 | run | 1/2 | 0/8 | 0.2 |
| 9 | final set 2 | contextual-v2 | package | 1/6 | None/24 | unknown |
| 9 | final set 2 | contextual-v2 | run | 1/2 | None/8 | unknown |
| 9 | final combined | strict | package | 1/6 | 1/47 | 0.2155297532656023 |
| 9 | final combined | strict | run | 1/2 | 1/16 | 0.21568627450980393 |
| 9 | final combined | contextual-v1 | package | 1/6 | 1/47 | 0.2155297532656023 |
| 9 | final combined | contextual-v1 | run | 1/2 | 1/16 | 0.21568627450980393 |
| 9 | final combined | contextual-v2 | package | 1/6 | None/47 | unknown |
| 9 | final combined | contextual-v2 | run | 1/2 | None/16 | unknown |
| 10 | final set 1 | strict | package | 0/6 | 0/8 | 1.0 |
| 10 | final set 1 | strict | run | 0/2 | 0/3 | 1.0 |
| 10 | final set 1 | contextual-v1 | package | 0/6 | 0/8 | 1.0 |
| 10 | final set 1 | contextual-v1 | run | 0/2 | 0/3 | 1.0 |
| 10 | final set 1 | contextual-v2 | package | 0/6 | None/8 | unknown |
| 10 | final set 1 | contextual-v2 | run | 0/2 | None/3 | unknown |
| 10 | final set 2 | strict | package | 0/6 | 1/8 | 1.0 |
| 10 | final set 2 | strict | run | 0/2 | 1/3 | 1.0 |
| 10 | final set 2 | contextual-v1 | package | 0/6 | 1/8 | 1.0 |
| 10 | final set 2 | contextual-v1 | run | 0/2 | 1/3 | 1.0 |
| 10 | final set 2 | contextual-v2 | package | 0/6 | None/8 | unknown |
| 10 | final set 2 | contextual-v2 | run | 0/2 | None/3 | unknown |
| 10 | final combined | strict | package | 0/6 | 1/16 | 1.0 |
| 10 | final combined | strict | run | 0/2 | 1/6 | 1.0 |
| 10 | final combined | contextual-v1 | package | 0/6 | 1/16 | 1.0 |
| 10 | final combined | contextual-v1 | run | 0/2 | 1/6 | 1.0 |
| 10 | final combined | contextual-v2 | package | 0/6 | None/16 | unknown |
| 10 | final combined | contextual-v2 | run | 0/2 | None/6 | unknown |

Schema-only context sizes: {'count': 60, 'median': 4487.0, 'p90': 4490, 'max': 4496}

Schema guidance overflow (omitted types by tier): {'measured_packages': 60, 'overflow_packages': 30, 'unknown_packages': 0, 'omitted_types': {'required': {}, 'conditional_required': {'aws_dynamodb_table': 6, 'aws_ecs_task_definition': 9, 'aws_lb': 6, 'aws_lb_listener': 9, 'aws_ecs_service': 9, 'aws_cloudfront_distribution': 3, 'aws_instance': 3, 'aws_s3_bucket': 3}}}

PR-05 recorded verdict: PASS.

Wilson intervals and Fisher tests are descriptive. Three variants share a plan, so package independence is unrealistic and package-level p-values are optimistic. Run-level sensitivity counts complete runs with at least one passing package, including complete failed runs in the denominator. Repeated prompts, provider conditions, model choices and changed code remain confounders; these comparisons cannot isolate the causal effect of Phase 9i. Historical contextual-v2 remains unavailable. No deployment success is implied.
