# Phase 9f verification — 2026-10-17

## Preserved real baseline and read-only investigation

The section 0 [investigation](phase9f-investigation.md) classifies all top-20
positions including the tied rules and records exact saved outcomes. Of 40
packages, one was production ready and 35 retained blockers; 154 iterations were
16 accepted, 61 unchanged and 77 rolled back (48 Terraform regressions, 29 new
blocking findings). Nine already retained a separately verified Kubernetes file;
additional salvage potential is unknown without discarded candidate source.
The 13 final cost-package CKV_AWS_145 rescan found seven findings, three old
exemptions and zero newly blocking among those three resource-proven exemptions.
Historical advisory truncation prevents an exact all-iteration exemption total.

## Implementation and scripted evidence

D-46 records the catalogue, templates, route inference, edit recovery and partial
acceptance. Readiness, severities, blocking criteria and guards remain unchanged.
No Phase 9g exception profile is implemented. New template findings remain
rejected and visible; SSE-S3 destinations follow the author's approved AWS
compatibility clarification. No source JSON, discarded candidate or credential
is copied into benchmark quality evidence.

Four scripted existing-path collisions normalized successfully; three proposals
survived every guard and one introducing a blocker remained rejected. Additional
regressions cover conflicts, missing context, stale content, suppression and
syntax. These counts cannot estimate recovery among the historical 47 rejections.
Mocked gpt-oss and Anthropic-family OpenRouter calls reached factory selection,
JSON validation, reasoning controls, guards and PostgreSQL session reports. The
45-second attempt clipped to 20 seconds when 20 remained. No real model call or
availability/quality claim is made for the synthetic Haiku test identifier.

Four template families validate offline against both AWS 5.100.0 and 6.68.0.
Additional tests preserve existing keys, bucket-key options, supporting-resource
reuse, dependency grouping, guard rejection, budget limits and verified checkpoints.

PR-04's reproduced prerequisite defect was full application Settings demanding
three unrelated migration/test URLs when only the development app URL was needed.
The new minimal loader preflights exported DATABASE_URL. A full-size rejected
synthetic package persists and downloads through real PostgreSQL/HTTP with no
successful scanner/validator claim. The author's original process environment
remains unverified; no dotenv or original credentials were inspected.

## Final commands

| Command | Final result |
|---|---|
| make lint | PASS: Ruff check/format, mypy on 122 app sources, frontend ESLint/TypeScript |
| make test | 1451 passed, 0 failed, 0 skipped; 6 perf deselected (167.51 s) |
| make frontend-test | 100 passed, 15 files |
| make test-e2e | 6 passed (1.5 min) |
| make provider-schema | Seven pinned provider/version indexes exported offline |
| make secret-scan | 0 findings / 0 errors |
| make bench-stub | Completed 14 pipeline runs / 42 ready packages and 10 ZIP downloads; PR-01/04/05 PASS, PR-03 FAIL |

[Secret scan](evals/phase9-secret-scan-20261017T213555936855Z/summary.md)
and [stub benchmark](evals/phase9-bench-stub-20261017T213158569704Z/summary.md)
retain the measured evidence. Reports correctly record the pre-section-7 HEAD
and tracked working-tree changes; the verified source is committed with section 7.
Verification uses an isolated PostgreSQL 16 container, existing app/owner roles,
explicit synthetic test settings and dotenv-disabled bootstrap. No existing
project database or real key is used. No installs/downloads are performed.

An initial full run had 1428 passes and seven legacy fixture/concurrency failures.
Follow-up regressions passed after representing rejected support as actually
invalid, retaining independent-call concurrency, serializing shared context and
restoring sorted result metadata. A subsequent full run passed 1439 tests before
two final malformed-input regressions were added. Final counts below supersede
those intermediate runs.

## Author comparison defaults

Use the same prompts/Architect/Generators for both runs: gpt-oss fixer with low
reasoning, then an author-selected Haiku-class OpenRouter fixer with reasoning
off. Use 45-second attempts, 60-second iterations, 240-second security stages,
four iterations, two resources / twelve findings per call, six group evaluations,
and the baseline generator 16000-token / 140-second attempt / 150-second deadline.
README documents startup/export and comparison commands. Real quality comparison
is author-only and remains outstanding; stub readiness is not real-model quality.

## Quiet-machine stub measurements

These are stub overhead measurements, not real generation/remediation quality.
All 14 runs settled, all 42 variants were generated and ready, with zero missing
variants and zero remaining blockers. Valid-package near misses are zero in all
three buckets. Normal clean packages made zero fixer calls and applied zero
catalogue/template edits; their zero recovery/group counts are measured zeros.
All 42 package profiles record stub / 45 s attempt / 60 s iteration / 240 s stage
and the 2-resource / 12-finding / 6-group limits.

| Measurement | Count | Median seconds | Maximum seconds | Verdict |
|---|---:|---:|---:|---|
| PR-01 API settlement | 10 | 13.1708 | 14.6100 | PASS |
| PR-03, including isolated baseline | 4 | 33.3133 | 33.8181 | FAIL: cohort ratios 2.6226–2.6698x |
| PR-04 complete ZIP download | 10 | 1.0733 | 1.3643 | PASS |
| Separate scripted/offline verification | 6 | 14.3084 | 30.1389 | Descriptive, excluded from quality/PR verdicts |

The seeded rejected archive downloaded as 9,989,867 bytes. No fixture-preparation
error occurred. PR-03's 1.5x threshold and all other thresholds are unchanged.
The scripted rehearsal used three concurrent private workspaces, three init runs,
nine reuses, no reinitializations and zero deadline-only / validity rollbacks.
Do not infer real-model gains or extra historical salvage from this rehearsal.

The implementation uses existing dependencies only. Task-created PostgreSQL and
benchmark server are stopped after verification; existing project services and
untracked user files are left intact. No .env/spec edits, paid calls, installs,
downloads, push or history rewrite occurred.
