# Phase 9i Kubernetes follow-up replay

All results are offline static observations. `checks_passed` means valid and zero blocking findings for that assessment; strict remains the sole official acceptance policy.

## Original generated packages, fresh offline baseline

| Prompt | Packages | Valid | Strict checks_passed | v1 checks_passed | v2 checks_passed |
|---|---:|---:|---:|---:|---:|
| ECS | 47 | 9 | 1 | 1 | 1 |
| EKS | 16 | 1 | 1 | 1 | 1 |
| static | 18 | 13 | 13 | 13 | 13 |

## Previous Phase 9i retained packages, freshly observed

| Prompt | Packages | Valid | Strict checks_passed | v1 checks_passed | v2 checks_passed |
|---|---:|---:|---:|---:|---:|
| ECS | 47 | 29 | 5 | 5 | 5 |
| EKS | 16 | 3 | 2 | 2 | 2 |
| static | 18 | 13 | 13 | 13 | 13 |

## Final retained packages

| Prompt | Packages | Valid | Strict checks_passed | v1 checks_passed | v2 checks_passed |
|---|---:|---:|---:|---:|---:|
| ECS | 47 | 29 | 5 | 5 | 5 |
| EKS | 16 | 3 | 2 | 2 | 2 |
| static | 18 | 13 | 13 | 13 | 13 |

## Per-change outcomes

| Stage | Accepted | Unchanged | Rejected reasons | New retained finding identities |
|---|---:|---:|---|---:|
| independent_pods | 11 | 70 | none | 0 |
| independent_formats | 2 | 66 | new_blocking_findings: 12, no_improvement: 1 | 0 |
| cumulative_equivalents | 31 | 43 | no_improvement: 7 | 0 |
| cumulative_addressing | 17 | 64 | none | 0 |
| cumulative_formats | 2 | 66 | new_blocking_findings: 12, no_improvement: 1 | 0 |
| cumulative_defaults | 15 | 66 | none | 0 |
| cumulative_pods | 10 | 71 | none | 0 |

## Rule count deltas from previous retained packages

| Scope | Rule | Previous | Final | Delta |
|---|---|---:|---:|---:|
| rules | CKV_K8S_40 | 4 | 2 | -2 |
| rules | KSV-0104 | 4 | 0 | -4 |
| rules | KSV-0118 | 4 | 0 | -4 |
| all_rules | CKV_K8S_28 | 6 | 0 | -6 |
| all_rules | CKV_K8S_29 | 4 | 0 | -4 |
| all_rules | CKV_K8S_31 | 4 | 0 | -4 |
| all_rules | CKV_K8S_37 | 6 | 0 | -6 |
| all_rules | CKV_K8S_40 | 4 | 2 | -2 |
| all_rules | KSV-0003 | 6 | 0 | -6 |
| all_rules | KSV-0004 | 6 | 0 | -6 |
| all_rules | KSV-0020 | 10 | 8 | -2 |
| all_rules | KSV-0021 | 26 | 5 | -21 |
| all_rules | KSV-0030 | 4 | 0 | -4 |
| all_rules | KSV-0104 | 4 | 0 | -4 |
| all_rules | KSV-0106 | 6 | 0 | -6 |
| all_rules | KSV-0118 | 4 | 0 | -4 |

## Residuals and limitations

Image values preserve existing identities. Latest/blank tags (CKV_K8S_14/KSV-0013), untrusted registries (KSV-0125) and low ports (KSV-0117) remain blocking wherever observed. No image, registry, digest, Service, probe or application port is invented or changed.

Explicit weak settings, unsupported source bindings, dynamic container structures, ambiguous render mappings and preserved quantities can leave findings. See changes.json for skipped-entry reasons and every stage row for candidate/retained evidence.

Identity, filesystem, capability and resource changes can break startup. Accepted archive records say **runtime compatibility unverified**. No image pull, workload startup, Kubernetes deployment, real LLM inference or real cloud API was used.

All-rule counts include advisory findings. Per-rule tables count scanner occurrences; introduced/removed identity lists use the existing rule/path/resource fingerprints. These are complementary measures.

Unknown scans/validation by stage: {"baseline": [0, 0], "cumulative_addressing": [0, 0], "cumulative_defaults": [0, 0], "cumulative_equivalents": [0, 0], "cumulative_formats": [0, 0], "cumulative_pods": [0, 0], "independent_formats": [0, 0], "independent_pods": [0, 0], "previous_retained": [0, 0]}.

Original snapshots, both final sets and previous Phase 9i evidence remain unchanged. Three missing variants remain missing; they are excluded from the 81-package denominator. Stored strict/v1 assessments match all 81 original packages.
Stored/fresh baseline discrepancy packages: 0; see stored-vs-fresh.json. Stored profiles remain exactly as saved; v2 is not backfilled into historical snapshots.

Historical pinned commit: c3be20c. Byte verification: 648 stage checks across 81 packages. Tool versions, isolation/configuration and evaluator fingerprints are recorded in verification.json and each row.
