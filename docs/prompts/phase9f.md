# Codex task — Phase 9f: Secure-by-construction and better security fixing

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-40 to D-45),
the latest `docs/IMPLEMENTATION_LOG.md` entries, `docs/phase9e-investigation.md`,
`docs/phase9e-followup-verification.md`, the SecurityAgent loop, the fixer
prompts, `backend/app/validation/` (gate, idioms, schema index/context,
preservation, workspace), the generator prompt, and `backend/scripts/`
(benchmark, seed). Phases 0–9e are complete.

## Why this phase exists

Real benchmark after the 9e loop fix
(`docs/evals/phase9-bench-real-20261017T144629709424Z`, gpt-oss-120b for all
agents): **production-ready 1/40**. Validity no longer breaks because of
security fixes (final failure origins: 56 generated, 7 unknown, 0 security),
but **35/40 packages keep blocking findings**. Of 154 security fix
iterations, 17 were accepted, 61 produced no change, about 76 were rolled
back (new blocking findings or Terraform regression). Top remaining blocking
rules: AWS-0104 (50), CKV_AWS_130 (41), AWS-0164 (40), AWS-0038 (35),
AWS-0028 (30), AWS-0132 (24), CKV_AWS_103/129/161/293 (23 each),
AWS-0176/0177 (22), CKV_AWS_8 (22), CKV_AWS_145 (21), CKV_AWS_91 (20),
AWS-0131, CKV_AWS_18, CKV_AWS_118, CKV_AWS_353 (19 each), AWS-0178 (17).
Generator-side validity errors remain (Unsupported argument 27).

Full results JSON: `.cache/phase9e2-results/` (the author saves it before you
start; read-only, never commit).

## The non-negotiable rule (unchanged)

Raise quality, not the label. Do not change the readiness rule, blocking
criteria, severities, check meanings, the per-iteration validity guard or
the no-new-blocking-finding rule. No benchmark-prompt special cases. Every
automatic change must make the infrastructure more secure and stay valid.

## Rules

No real LLM calls, no `.env` reads, no installs/downloads, no push, no new
dependencies. One commit per numbered section, prefix `phase9f:`,
requirement IDs, implementation-log entries with real test counts. Plan mode
first: report section 0 before code changes.

## 0. Investigate (report first)

From the saved JSON: for each top-20 rule, the affected resource types, what
the fixer attempted, and why it failed (no change, rollback reason). Classify
each rule as (a) attribute-level fix (set/add one argument or nested block on
the flagged resource), (b) needs a new supporting resource (KMS key, log
bucket, WAF…), or (c) context-dependent / design choice. For rolled-back
iterations: how many contained at least one file whose change alone would
have passed all guards (estimate from the saved candidates where possible).

## 0b. Supervisor audit R2 — resource-specific encryption exemption (do first)

The checkpoint-4 audit (`docs/reviews/checkpoint4-audit.md`, R2) reproduced a
security-policy defect: `backend/app/security/policy.py::classify` exempts
CKV_AWS_145 when the substring `AES256` appears anywhere in the package (even
a README comment). Fix it before anything else, because it changes the
benchmark numbers:

- Remove the substring-based exemption. An exemption may apply only when a
  parsed check proves that the **flagged bucket itself** has the encryption
  configuration (same-file or cross-file
  `aws_s3_bucket_server_side_encryption_configuration` whose `bucket`
  references that bucket). Comments, strings, README text and other
  resources never count; unresolvable evidence stays blocking.
- Regressions from R2: README/comment-only text; a second correctly encrypted
  bucket next to an insecure one; cross-file association; absent/unknown
  encryption; a valid resource-specific case. Do not weaken existing
  assertions.
- Report how many findings in `.cache/phase9e2-results/` the old rule
  exempted and how many of those the new rule keeps blocking.
- Check the other variant exemptions in `policy.py` for the same pattern
  (text search instead of a resource-specific check) and report each one;
  fix those with the same approach.

## 1. Deterministic security autofix catalogue (option 1)

- A catalogue of rule → safe attribute-level fix for the class (a) rules,
  covering both Checkov and Trivy IDs of the same control (e.g. RDS deletion
  protection, IAM DB auth, storage encryption, enhanced monitoring /
  performance insights, IMDSv2 `metadata_options`, EBS encryption,
  `map_public_ip_on_launch = false` on non-public subnets, TLS ≥ 1.2
  listener policies, EKS control-plane logging…), only where the fix is a
  secure default with no functional downside you cannot justify.
- Each entry: rule IDs, resource type, exact change, provider-version
  applicability (checked against the schema index), justification, and
  whether it can conflict with the plan (e.g. a subnet the plan marks public
  must not be changed).
- Apply after generation and before each security iteration's LLM fix, only
  to resources the scanners actually flagged; never remove or weaken
  anything; idempotent; logged per rule/resource; covered by the existing
  validity guard and no-new-blocker check.
- Document the catalogue as a table in D-46 (it becomes a thesis appendix).

## 2. Partial acceptance (option 2)

When an iteration's combined candidate fails a guard, do not discard
everything: split the candidate into independent change groups (per file;
for Terraform per top-level block where separable), evaluate groups in a
deterministic order, and keep each group that passes syntax, Terraform
non-regression and no-new-blocking-finding checks against the current
retained baseline. Bound the number of group evaluations per iteration by a
setting (propose a default) inside the existing 60 s iteration and 240 s
stage budgets; record kept/discarded groups and reasons. Reuse workspaces and
cached scans as in 9e.

## 3. Secure by construction (option 3)

Generate a compact per-resource security checklist from the catalogue (and
the most frequent class (b) controls) and add it to the generator prompt for
the resource types the plan needs, within the existing generator schema cap
(adjust the cap only if measured and justified). Do not change output-token
limits.

## 4. Focused fix prompts (option 4)

Group blocking findings by resource and send the fixer at most a bounded
number of resources/findings per call (setting, propose a default), most
severe first, with that resource's schema context and the catalogue's
guidance. Keep the rejection-feedback field from 9e.

## 5. Configurable stronger fixer (option 5)

`SECURITY_FIX_MODEL` already exists. Verify that a different fixer model
(e.g. an Anthropic model via OpenRouter) works end to end with the fixer's
structured output, reasoning settings and timeouts (mocked HTTP only), and
that the benchmark records the fixer model. The author plans a second
benchmark with a faster Anthropic model (Claude Haiku class) as fixer while
keeping gpt-oss for Architect and Generators; make sure the 60 s iteration
ceiling and 45 s fixer attempt timeout are reported per fixer model.
Document how the author runs the comparison; no default change.

## 6. PR-04 seed fix

`seed_benchmark_package` and `make bench-stub` now fail with "Benchmark
prerequisite or fixture preparation failed" even with PostgreSQL running.
Find and fix the cause (likely new required report/package fields since 9e),
with a regression test. Report the real cause.

## 7. Measurement, tests, docs

- Per package: catalogue fixes applied, partial-acceptance groups kept /
  discarded, findings per fixer call, fixer model. Add to the benchmark
  quality summary, plus a "near-miss" table (valid packages with 1, 2–3,
  4+ remaining blocking findings) and per-rule remaining counts.
- Tests for every catalogue entry (both provider versions, idempotence,
  plan-conflict skip), partial acceptance (mixed good/bad groups, budget
  bound, no bad group retained), focused batching, fixer-model switch,
  seed fix, canaries.
- D-46, README, thesis follow-ups (Chapter 4: autofix catalogue and partial
  acceptance; Chapter 6: 9e → 9f comparison).

Finish with `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make secret-scan`, `make provider-schema`, `make bench-stub` (real counts,
including PR-04). Summary in the `AGENTS.md` §10 format, starting with the
section 0 rule classification and the recommended settings for the author's
two real benchmarks (gpt-oss fixer, then a stronger fixer).
