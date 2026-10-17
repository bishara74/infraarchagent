# Phase 9f investigation — 2026-10-17

Read-only inputs: `.cache/phase9e2-results/*.json` (14 runs, 40 packages).
Original source JSON is never committed. One package is production ready;
35 have blocking findings. Seven validate: one has no blockers, six have 4+;
none have one or two–three blockers.

154 started fix iterations: 16 accepted, 61 unchanged, 77 rolled back.
Rollbacks: 48 Terraform regressions, 29 new-blocking-finding rejections.
Proposal rejection counts: new_file_exists 47, security_control_removed 27,
invalid_syntax 2. Declared fix intentions below come from file-level summaries;
they are not proof that discarded candidate code implemented those intentions.
N/T/B denotes unchanged / Terraform rollback / new-blocker rollback iterations
whose targeted file included the rule. Counts overlap across rules.

| Rule | Remaining | AWS resource types | Class | Declared attempt | N/T/B |
|---|---:|---|---|---|---|
| AWS-0104 | 50 | security_group, security_group_rule | C | Restrict egress | 38/40/18 |
| CKV_AWS_130 | 41 | subnet | A (private only) | Disable public IPs | 42/41/18 |
| AWS-0164 | 40 | subnet | A (private only) | Disable public IPs | 39/41/18 |
| AWS-0038 | 35 | eks_cluster | A | Control-plane logs | 8/15/5 |
| AWS-0028 | 30 | instance | A | Require IMDSv2 | 24/19/8 |
| AWS-0132 | 24 | s3_bucket, s3_bucket_server_side_encryption_configuration | B | KMS encryption | 37/33/19 |
| CKV_AWS_293 | 23 | db_instance | A | Deletion protection | 37/40/18 |
| CKV_AWS_161 | 23 | db_instance | A (engine dependent) | IAM authentication | 37/40/18 |
| CKV_AWS_129 | 23 | db_instance | A (engine dependent) | Export engine logs | 37/40/18 |
| CKV_AWS_103 | 23 | lb_listener | A/C | TLS policy / HTTPS | 29/29/17 |
| AWS-0176 | 22 | db_instance | A (engine dependent) | IAM authentication | 34/40/18 |
| AWS-0177 | 22 | db_instance | A | Deletion protection | 34/40/18 |
| CKV_AWS_8 | 22 | instance, launch_configuration | A | Encrypt volumes | 23/14/7 |
| CKV_AWS_145 | 21 | s3_bucket | B | KMS encryption | 35/30/16 |
| CKV_AWS_91 | 20 | lb | B | Access-log bucket | 29/29/17 |
| CKV_AWS_118 | 19 | db_instance | B (A with existing role) | Enhanced monitoring | 27/32/12 |
| CKV_AWS_353 | 19 | db_instance | A (engine dependent) | Performance Insights | 27/32/12 |
| CKV_AWS_18 | 19 | s3_bucket | B | Access-log destination | 35/24/14 |
| AWS-0131 | 19 | instance | A | Encrypt block devices | 20/14/7 |
| CKV2_AWS_11 | 17 | vpc | B | Flow logs | 29/26/14 |
| AWS-0178 | 17 | vpc | B | Flow logs | 29/26/14 |

A: attribute/block; B: supporting resources; C: design-dependent. Both rules
tied at position 20 are included. Common Terraform diagnostics across candidate
verification: unsupported argument 50, generic configuration diagnostic 35,
undeclared resource 13, unsupported block 11, undeclared input 7, invalid resource
type 7, missing argument 4, cycle 3, invalid index 1, single-argument block 1.
These are diagnostic occurrences, not distinct iterations.

## Partial acceptance evidence

Nine of the 77 rolled-back iterations retained a separately verified
k8s/workloads.yaml change while Terraform reverted. The other 68 lack discarded
candidate source. Additional salvage potential, especially per Terraform block,
is unknown; do not estimate it from fixer summaries or retained-only diffs.

## Supervisor R2

The current substring policy changes an insecure cost bucket from blocking to
advisory when AES256 is added only to README or a Terraform comment. The seven
other variant exemption entries are explicit rule decisions (CKV_AWS_144 cost /
performance; CKV_AWS_157, 118, 353, 354 and AWS-0133 cost); none searches text.

Saved final advisory samples expose one CKV_AWS_145 exemption but truncate nine
cost-package lists. An isolated offline Checkov CKV_AWS_145 rescan of all 13 final
cost packages found seven findings: three old-rule exemptions, all three with
bucket-specific AES256 evidence; zero of those three become blocking. This is a
final-file rescan, not a reconstruction of every historical scan. Historical
exemption totals beyond saved samples remain unknown.

## Additional observations and approved settings

AWS-0104 is unrestricted egress but currently injects S3 replication schema
context. Full PR-04 calibration succeeds (66 files, 9,989,866 ZIP bytes); in this
shell seed settings fail before database access because four database environment
variables are absent. The author's database-backed failure remains unverified.

Approved defaults: 2 resources / 12 findings per fixer call, at most 6 partial
group evaluations, existing 60 s iteration / 240 s stage / 4 iteration ceilings.
Author comparison overrides: 45 s fix attempts; generator output 16000 tokens,
attempt 140 s, deadline 150 s. Baseline fixer is openai/gpt-oss-120b:nitro,
reasoning low; compare with an author-selected Haiku-class fixer, reasoning off.

Initial read-only checks: policy and seed-file tests, 3 passed, 0 failed.
No full-suite or lint claim is made by this investigation.
