# Phase 9e verification — 2026-10-16

Section 0 findings and historical counts are in
[the investigation](phase9e-investigation.md). Most sampled rising Terraform
errors came from security fixes: 48/58 missing-argument diagnostics concern
empty default-security-group rules, and all 28 invalid references concern
flow-log placeholders. Four initial / nine post-security deadline stops are
historical counts with unknown attempted/stopped distinctions. Fourteen original
packages could not initialize; new gates record safe failure categories.

The implementation uses D-45. Readiness, blocking criteria, severities, PR
thresholds, benchmark prompts, model choices and output-token limits are
unchanged. No thesis sources, dependencies or migrations changed. Verification
used an isolated local PostgreSQL 16 container with synthetic credentials,
dotenv-disabled settings, installed tools and the existing read-only mirror.
No real LLM calls, external services, downloads, installs or pushes were used.

## Commands and outcomes

| Command | Actual outcome |
|---|---|
| `make lint` | Ruff / format, strict mypy (113 source files), frontend ESLint / TypeScript passed |
| `make test` | 1302 passed, 0 failed, 0 skipped; 6 performance tests deselected (129.68 s) |
| `make frontend-test` | 100 passed across 15 files |
| `make test-e2e` | 6 passed (1.4 minutes) |
| `make secret-scan` | 0 findings, 0 scan errors (final scan 20261016T205116906423Z) |
| `make provider-schema` | All seven pinned version indexes exported offline |
| `make bench-stub` | Completed: 14 pipeline runs, 42/42 packages ready, 10 downloads; PR-03 failed, PR-01/04/05 passed |

The first full backend run found seven failures (1274 passed). Fixture syntax,
shared-runner assertions and stage-notice counts were updated. A real Retry bug
was fixed: a scanner failure during candidate verification now preserves a
session report and original files. The selected 44 regression tests passed.
Later source-preservation regressions cover mixed JSON rule lists, encoded JSON
flow-log placeholders, comments and complete multiword AWS field names. Failed
initialization cannot create reusable cached validation state. Ambiguous masked
optional-tool failures remain `unknown`, as do masked Terraform failures.

## Measured stub evidence

Final evidence:
[benchmark summary](evals/phase9-bench-stub-20261016T204355321818Z/summary.md),
[quality](evals/phase9-bench-stub-20261016T204355321818Z/quality.json),
[agents.csv](evals/phase9-bench-stub-20261016T204355321818Z/agents.csv),
[verification rehearsal](evals/phase9-bench-stub-20261016T204355321818Z/verification-rehearsal.json).
An earlier complete rehearsal is retained separately at
`evals/phase9-bench-stub-20261016T203756960530Z/`; neither run predicts real quality.
Backend verification ran concurrently with the benchmark; these are local stub
measurements under that load, without threshold adjustments.

| Measurement | Count | Median seconds | p90 seconds | Maximum seconds |
|---|---:|---:|---:|---:|
| PR-01 | 10 | 15.7593 | 19.2627 | 19.5219 |
| PR-03 including isolated baseline | 4 | 34.8426 | 35.2072 | 35.2072 |
| PR-04 ZIP download | 10 | 1.2310 | 1.4618 | 1.5678 |
| Separate scripted-fix iteration verification | 6 | 15.0201 | 31.1578 | 31.1578 |

All 42 generated stub packages had valid gates and passed final readiness.
Production-ready rate: 42/42 (100%) **for these stub packages**. The normal stub
pipeline attempted zero scanner-fix iterations or validation-repair rounds;
its initial/post-security deadline-stop counts are 0/0. Deadline-only rollbacks:
zero with zero attempted fix iterations (rate undefined).

Package-wide initialization totals: 42 runs, 126 reuse events, zero
reinitializations; cumulative init time 4.3980 s and provider validation time
5.1566 s. Generator schema reference: 5689 characters in all 42 packages,
below the 6000-character input cap. No repair/scanner context sizes are inferred
when those calls were absent. Descriptive stage rows in the linked CSV include
actual gate, deterministic, initial/post-security/final validation and final
security-scan time; no new thresholds are introduced. Repair timing rows are
unit/integration-tested even though clean stub packages require none.

The separately labelled scripted-fix rehearsal uses real offline Terraform,
AWS 5.100.0 and 6.68.0, and three concurrent private workspaces. It is excluded
from quality rates and PR thresholds. Verification time includes initialization,
validation and queue waiting. It recorded 3 init runs, 9 reuse events, zero
reinitializations, zero validity-regression rollbacks, zero pre-candidate
deadline stops, zero multiple-cause deadline rollbacks, and **0 deadline-only
rollbacks / 6 attempted fix iterations**. A deadline-only rollback does not
establish that the candidate would have passed verification.

## Injected clocks and budget effects

These test results are separate from historical and stub observations:

- Three 60-second boundary cases: one stop before a candidate, one deadline-only
  rollback after a candidate, and one rollback with both Terraform regression
  and deadline causes. The deadline-only candidate is unverified.
- Pipeline integration tests inject a completed 230-second security stage.
  Both long-stage cases still attempt the post-security round with a fresh
  60 seconds, including the case whose final security scan fails. No
  post-security repair deadline stops occur in those two cases.
- Unit coverage also proves the original initial budget can be expired while
  an independent post-security budget remains available. This does not estimate
  how the historical four/nine stops would change in a real run.

## Next author-run comparison

Keep the 9d provider/endpoint and both model choices:
`openai/gpt-oss-120b:nitro` through the OpenAI-compatible provider. Keep generator
output 16000, attempt 140 s, deadline 150 s, LLM deadline 150 s, JSON schema,
fix attempt 45 s, security deadline 240 s, maximum remediation iterations four
and initial repair rounds two. Use initial repair 120 s, new post-security repair
60 s and schema context cap 16000 characters. See the
[README settings](../README.md#phase-9e-syntax-gates-and-repair-budgets).

Build `make provider-schema` after installing the offline mirror (also a Phase
10 prerequisite). Real quality and deadline-stop changes remain unmeasured.
PR-03 is a measured failure requiring follow-up, with its threshold unchanged.
Chapter 4/6 thesis follow-ups are recorded in design-deviations.md; thesis text
was not edited. No new unresolved specification question was introduced.
