# Phase 9e investigation (2026-10-16)

Read-only inputs: `.cache/phase9d2-results/*.json` and
`docs/evals/phase9-bench-real-20261015T180417396510Z/`. No source, feedback,
diffs or credentials are copied into this evidence document.

14 runs produced 40 packages: 39 pending review, one production ready (2.50%),
two missing variants. Readiness and all blocking criteria remain unchanged.

| Phase | Completed | Accepted | Rolled back | Deadline stops | Limit markers |
|---|---:|---:|---:|---:|---:|
| before_security | 38 | 7 | 31 | 4 | 0 |
| after_security | 23 | 9 | 14 | 9 | 8 |

Rollback reasons: no improvement 35 (24 initial/11 post-security), new blocking
findings five (initial), invalid patch five (two initial/three post-security).
15 rejected candidates increased failed-check count. Deadline records do not
distinguish started work from a stop before execution; limit markers are not
attempts. Historical attempted-round counts cannot be reconstructed exactly.

136 offline package-stage evaluations reproduced final targeted diagnostics:
58 missing required arguments, 32 unsupported arguments, 28 invalid references,
10 invalid resource types and 10 unsupported block types; no tool-unavailability
skips. Complete intermediate pairs were reconstructed for 28/40 packages.
Origins for the remaining histories and discarded candidates are unknown.

- Generated: aws_db_instance.name; CloudFront origins and
  drop_invalid_header_fields; aws_rds_instance and aws_ec2_instance types.
- Security fixes: 48/58 missing-argument diagnostics concern default security
  groups; empty ingress/egress blocks were added (e.g. 5fc06e4d/security).
  All 28 invalid references concern unescaped flow-log field interpolation in
  7812c7b9/security and aa060f55/cost. Other added invalid configuration includes
  revoke_all_rules, aws_db_instance_log_exports and S3 replication blocks.
- Hidden errors: declaration repair alone exposes the missing
  origin_access_control_origin_type and unsupported CloudFront blocks in
  e3508bbc/security; its LLM repair rounds were rejected.
- No new final diagnostic signatures were observed after post-security repair
  in reconstructed pairs; this is not proof for the incomplete histories.

Validator timing covers prepared-report persistence, not preceding tools:
80 rows, median 0.038457 s. Generation-complete to first validator-running has
median 35.875 s; security-complete to final validator-running median 42.714 s.
Deterministic repair, validation/repair verification and final scanning are
outside those timers. Package intervals overlap and must not be summed into
pipeline wall time. The old repair budget also elapses during security.

All seven pinned versions export offline from scratch modules:

| Provider | Raw schema bytes | Compact index bytes |
|---|---:|---:|
| aws 5.100.0 | 13591718 | 10323113 |
| aws 6.68.0 | 19701628 | 13961639 |
| random 3.9.1 | 23586 | 3913 |
| kubernetes 2.38.0 | 3130041 | 802259 |
| helm 2.17.0 | 22140 | 6013 |
| tls 4.4.1 | 37298 | 5786 |
| null 3.3.2 | 3364 | 499 |

Median compact AWS resource bytes: 634 (v5), 707.5 (v6); deeply nested schemas
can exceed 1 MB. The eight-resource, version-labelled generator summary is
5465 bytes. Initial successful init resolves 15 originals to AWS 5.100.0 and
11 to 6.68.0; 14 cannot initialize. Final files resolve 23/14, with three
unresolved. Never assume one AWS version for every package.

invalid_structure checks paths/layout/size/completeness, not HCL syntax.
document.parse and external tools run later; Helm templates bypass plain YAML
parsing. No shared early per-patch syntax gate exists. ansible-playbook is
installed next to ansible-lint inside pipx, although absent from PATH.

Approved additions: schema-ground ordinary scanner fixes; remove only empty
default-security-group rule blocks and escape AWS flow-log placeholders;
validate each security iteration under its existing 60-second ceiling; use
independent initial 120-second/post-security 60-second repair budgets; retain
private initialized workspaces across iterations. Record initialization reuse,
verification time and deadline-only rollbacks without estimating real gains.

Baseline verification: make lint passed (105 mypy source files, Ruff/format,
frontend ESLint/TypeScript). No full test suite was run for this read-only
investigation. The 136 evaluations and seven exports are tool investigations,
not unit-test counts. No real LLM calls, .env reads, installs or downloads.
