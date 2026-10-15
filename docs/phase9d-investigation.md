# Phase 9d investigation (2026-10-15)

Read-only inputs: the 14 restored `.cache/phase9d-results/*.json` API snapshots
and `docs/evals/phase9-bench-real-20261015T124330508703Z/`. Neither is modified.

The 36 generated packages contain 35 pending review and one production ready
(2.78%); six of 42 expected variants are missing. Review reasons: 35 validation
failures and 30 unresolved-security packages. Stops: 28 iteration limit, two
no progress, six clean.

Automatic execution is generation → security → validation. Validation feedback
is currently consumed only on engineer Retry, using its existing per-file fixer,
then rescan and revalidation. Thus automated validation failures have no repair.
Security fixes can introduce invalid configuration that final validation catches.

## S3 evidence

The baseline ran three fix passes and a fourth, terminal scan, not four fixes.
Unique run prefixes identify the restored input files.

| Run / variant | Observed final infrastructure / scan history |
|---|---|
| 166ec6e2 security | logs, nlb_logs and replica use unsupported nested public_access_block blocks; all remain flagged. |
| 7044915b performance | Added alb_logs has public-access flags directly on aws_s3_bucket; all four findings survive. |
| c2e828db security | Website/log buckets and new replicas use direct flags; final patch rejected as invalid_structure. |
| 93fd2237 security | Correct standalone block protects alb_logs; the newly added replica remains unprotected. |
| eb88c7d2 performance | Standalone alb_logs_block clears that bucket's findings; subsequent fixes add unprotected duplicate log_bucket resources. |

The samples support wrong resource syntax and incomplete coverage of introduced
buckets, rather than a systematic mapping or patch-loss fault. Trivy accepts
correctly linked standalone public-access blocks.

## Validation samples

| Class | Real samples and cause |
|---|---|
| Generic Terraform diagnostic | 29e0f372 cost/performance provider objects lack separators; its security package duplicates KMS, replica and IAM resources; ce810609 security duplicates an ALB. Local no-init Terraform diagnostics confirmed separators/duplicates. |
| Missing argument | 166ec6e2 performance empty ECS cluster; 495188d7 cost/performance/security incomplete default-security-group definitions with empty rule blocks. |
| Unsupported argument | 495188d7 performance, 7044915b performance/security, 81d6adb4 performance use unsupported flow-log log_group_name; resource_id also occurs. |
| Undeclared variable | 166ec6e2 performance lb_logs_bucket; 495188d7 performance alb_logs_bucket; 7044915b performance project_name; a4a7a37e performance aws_region. Both original omissions and new security-fix references occur. |
| Undeclared resource | 166ec6e2 performance caller identity; 495188d7 performance/security and 7044915b security availability zones: missing data declarations. |
| Duplicate variable | 81d6adb4 cost aws_region, api_image, prometheus_image, grafana_image: main declarations conflict with defaults in variables.tf; not safe exact duplicates. |
| Unsupported block | 495188d7 cost load_balancer_attributes; 7044915b security revoke_rules; a4a7a37e cost logging; c2e828db cost origins. |
| Parse error | 53ee08fb security HCL semicolons; 93fd2237 cost blocks inside yamlencode object; b8f7496f security two YAML attributes on one line; ce810609 cost malformed dotted assignment. |
| Helm templates | 93fd2237 cost Grafana/Prometheus and security app charts; b8f7496f performance Grafana chart: metadata without templates. |
| Grafana panels | 166ec6e2 performance datasource; 48ce2227 security dashboard API envelope; 7044915b performance/security wrapped dashboards. Nested panels inside an API envelope do not satisfy the provisioning dashboard contract. |
| Ansible lint | Offline reproduction for 166ec6e2 security and 93fd2237 cost/security found major name[play], fqcn[action-core] and no-changed-when findings. |

D-35 explicitly says “any ordinary failed check makes a package invalid” and
“blocker/critical/major/error fail”. Optional means unavailable tooling can skip;
emitted failures still block. No validation or readiness rule is changed.

## Timing and recommendation

100 fix-bearing iterations: median 8.127658 s, p90 12.213808 s, maximum
28.111706 s. 36 terminal scans: median 4.8504565 s, maximum 10.215115 s.
PR-01 median 41.620840 s leaves 258.379160 s headroom; maximum 60.011176 s.
PR-05 passes, with 31.888294 s headroom at the slowest security iteration.
The existing security limit defaults to three and its deadline is 240 s.

Recommend four passes, two initial validation rounds, at most one post-security
round, and 45-second fixer attempts under a 60-second iteration ceiling. The
author must measure new validation-repair timing; no improved quality or total
runtime is claimed. Preserve baseline generator overrides of 16,000 output
tokens and 140-second attempts (repository defaults remain 8,000 and 120).
