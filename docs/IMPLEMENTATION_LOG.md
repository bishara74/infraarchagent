# Implementation Log

Chronological record of every implementation change. Newest entry at the top.
This file is the raw material for thesis Chapter 5 (Implementation) and
Chapter 6 (Testing), so be factual and specific. Never delete old entries;
if something was wrong, add a new entry that corrects it.

## Entry template

```markdown
## YYYY-MM-DD — Phase N — <short title>

**Summary:** One or two sentences on what changed and why.

**Requirements addressed:** FR-..., NFR-..., PR-... (or "none — infrastructure").

**Files:** added / changed / removed (paths).

**Decisions:** Any choice made during the task, with the reason. Link to a
deviation ID (D-xx) or open question (OQ-xx) if relevant.

**Tests:** Command run and real result, e.g. `make test` → 42 passed,
0 failed, 1 skipped. List new test files and what they prove.

**Known gaps / follow-ups:** What is intentionally not done yet.
```

---

## 2026-10-18 — Phase 9f A2 — Repair declarations and explain package completeness

**Summary:** Retry declaration repair after syntax recovery using module content
fingerprints. Feed exact missing-type/layout inventories into subsequent package
attempts and raise the configured default from two attempts to three.

**Requirements addressed:** FR-G-02, FR-V-03, FR-S-04, NFR-01, PR-05.

**Files:** domain/package_layout.py, agents/generators/base.py,
agents/prompts/generator.py, core/config.py, pipeline/orchestrator.py,
generation-recovery/config/prompt tests, .env.example, README and D-46.

**Decisions:** D-46 records the explicitly approved default setting change;
overrides remain effective. Prompt v9 adds missing paths/types outside truncated
general feedback. Per-attempt metadata contains categories/counts and layout
patterns/suggested paths, never generated contents. Alternate permitted paths are
still accepted. No-candidate attempts remain explicitly unknown. Regeneration
retains its separate one-replacement limit and aggregate attempt/usage evidence.
All generation still shares 150 seconds; model/output defaults remain unchanged.

**Tests:** Fourteen focused A2 unit tests passed (6.39 s), covering third-attempt
success/exhaustion, two-attempt override, explicit missing feedback despite more
than ten other errors, source canaries, shared-budget exhaustion, cache/context
isolation and provenance. Actual generation integration covers normalization,
syntax round one and regeneration before declaration repair while newly revealed
findings remain blocking. Final combined results follow in the release entry.

**Replay:** Native offline replay of the two saved parsable A2 final checkpoints
adds 19 and 12 variable declarations, reducing all 31 variable-reference failures
to zero, with native syntax and idempotence passing. Original syntax-invalid input
repair skips remain reproduced. No real model replay or new readiness rate is
claimed; discarded completeness-candidate details remain historically unknown.

**Known gaps / follow-ups:** A2 used prompt v8 and two attempts. Subsequent author
fixer comparisons must use matched corrected code/prompt/settings. The third-attempt
scripted success is not an extrapolated recovery of the six missing real variants.

## 2026-10-18 — Phase 9f A2 — Complete iteration deadlines and cached indexes

**Summary:** Enclose automated and review iteration work/finalization in one
absolute deadline. Cache content-keyed documents/trees and reference/declaration
indexes per package, and preserve line-independent variable-reference provenance.

**Requirements addressed:** FR-S-03, FR-S-04, FR-S-09, FR-V-03, NFR-01, PR-05.

**Files:** core/deadlines.py, db/session.py, events/log.py, pipeline/state.py,
scanners/runner.py, agents/security/agent.py, security/acceptance.py,
validation/documents.py, references.py, repairs.py, workspace.py and PostgreSQL
deadline/continuation/security regressions.

**Decisions:** D-46 A2. Work retains a five-second finalization reserve; shutdown,
workspace locking, DB/statement/advisory-lock waits, notices and closing state/
event writes share remaining time. No parsing workers. Expired finalization fails
closed through legal arrows, including interrupted publication of an already
committed clean transition. Any stage-fault settlement uses the original remaining
stage allowance and stays visible as fault-recovery time/actual overrun. Partial
observations preserve variable identity; first observation is distinct from proof
of introduction. Terminal scans retain timing metadata without pretending a fix
verification occurred.

**Tests:** Full backend checkpoint: 1,502 passed / 0 failed / 0 skipped / 6 perf
deselected (281.86 s). Five final PostgreSQL deadline tests passed (8.01 s), including
advisory-lock cancellation, restoration/notice/closing-write stalls, and durable
clean-event interruption failing closed. Final combined release checks follow.
Old continuation fixtures now expire work at 56 seconds while retaining reserve;
the separate 61-second hard-expiry fixture verifies scan_error and unchanged files.

**Known gaps / follow-ups:** Cooperative timers cannot guarantee hard real-time
scheduling under external CPU/DB failure. Such overruns remain failures in PR-05;
no thresholds, benchmark timestamp boundaries or readiness rules are changed.

## 2026-10-18 — Phase 9f corrective — Final history audit and cleanup

**Summary:** Record the post-implementation secret scan and close task-owned test
services. All fourteen benchmark-A JSON input hashes still match replay evidence.

**Requirements addressed:** NFR-01, PR-05.

**Files:** this log, phase9f-corrective-verification.md and
evals/phase9-secret-scan-20261018T150931250888Z/.

**Decisions:** D-46 remains the corrective design record; no new open question.
The audit covers the working tree and all refs/reflogs through implementation/
evidence commit 26ed06a. This final commit contains documentation/audit output only.

**Tests:** make secret-scan PASS: 0 findings / 0 scan errors. Final lint and
backend/frontend/E2E/schema/stub results are recorded in the preceding entry.
Task-owned Docker containers were removed and the fallback PostgreSQL stopped;
the original application PostgreSQL on 5432 still accepts connections.

**Known gaps / follow-ups:** Real author benchmarks were not run. PR-03 remains
FAIL in the stub evidence; model comparisons require matched corrected commits.

## 2026-10-18 — Phase 9f corrective — Offline replay, reports and verification

**Summary:** Preserve benchmark-A evidence and report deterministic syntax recovery
separately from scripted repair/regeneration. Project allowlisted recovery/timing
metadata and document the concrete syntax, provenance, deadline and scan failure
investigation with file/line evidence.

**Requirements addressed:** FR-G-02, FR-S-03, FR-S-04, FR-S-09, FR-V-03, NFR-01,
PR-01, PR-03, PR-04, PR-05.

**Files:** scripts/phase9c_metrics.py, phase9e_metrics.py, phase9f_metrics.py,
phase9f_syntax_replay.py, test_phase9f_metrics.py, README, D-46 and Chapter 4/6
follow-ups, phase9f-corrective-verification.md, dated replay/Helm JSON and stub/
secret-scan evidence directories.

**Decisions:** D-46. All 20 final Terraform syntax findings existed in original
generation. One retained variable deletion was a separate dependency defect.
Duplicate/unstable observations and incomplete native baselines explain unknown
origins. PR-05's two security overruns were 65.530602 and 60.375424 seconds;
the first reached no fixer/partial evaluation. Helm path mapping caused the sole
scan_error before templates. Historical exact timing remains unknown. No cached
JSON, original benchmark evidence, readiness rules or source specifications changed.

**Tests:** Final make lint PASS (Ruff/format, mypy 124 application sources,
frontend ESLint/TS). make test against isolated Docker PostgreSQL 16: 1,481 passed /
0 failed / 0 skipped / 6 performance deselected (199.43 s). Six final targeted
Helm/report checks also passed (2.29 s), including three Helm cases added after
full-suite collection. make frontend-test: 100 passed / 15 files. make test-e2e:
6 passed (1.6 min), Docker PostgreSQL with repository initialization/normal roles.
make provider-schema: all seven pinned versions exported offline. make secret-scan
previous working-tree run: 0 findings / 0 errors; post-commit scan follows.
No dotenv reads, real model calls, dependencies, installs, downloads or pushes.

**Replay:** 11 affected original files/packages: 3 deterministic recoveries,
7 additional scripted syntax repairs and 1 scripted regeneration. Native
diagnostics 24 -> 21 -> 0; all 14 input JSON hashes unchanged. Scripted results
are test oracles, not real-model reliability or an updated readiness rate.
Native Checkov preserved 107/107 findings, including all 21 mapped Helm findings.

**Benchmark:** make bench-stub completed 14 pipeline runs / 42 ready generated
packages and 10 separately labelled synthetic PR-04 downloads. PR-01 PASS, median
14.703493 s / maximum 18.832189 s; PR-04 PASS, median 1.415957 s / max 1.695589 s;
PR-05 PASS at unchanged limits. PR-03 FAIL, ratios 2.444690–2.458220 against 1.5x.
Benchmark overlapped verification; stub timings do not establish model performance.
The first launch stopped at authentication preflight; its evidence is retained.

**Known gaps / follow-ups:** Docker/5432 temporarily disappeared after a session
pause; installed local PostgreSQL supplied an isolated fallback, then recovered
Docker supported the final checks on task-owned port 55441. The application
container was untouched. Both author fixer configurations should run on the
corrected commit/prompt v8 to isolate fixer differences from benchmark A's v7.
Real Haiku/corrected benchmarks remain author work. No new open question or
Phase 9g exception behavior is introduced.

## 2026-10-18 — Phase 9f corrective — Checkov Helm source mapping

**Summary:** Resolve rendered chart-name paths through validated chart metadata
to exact source files. Preserve every finding and distinguish path failures from
malformed scanner JSON.

**Requirements addressed:** FR-S-03, FR-V-03, NFR-01.

**Files:** scanners/checkov_parser.py, scan.py, test_phase9f_helm_locations.py.

**Decisions:** D-46. Map only Helm framework reports with one exact validated
chart-root/name match; reject traversal and ambiguous nested mappings. Do not
claim rendered line numbers as source locations. Scan errors now distinguish
path_mapping from invalid_json rather than dropping or weakening findings.

**Tests:** Four focused tests passed (0.25 s): exact source mapping, traversal,
ambiguous nested charts and separate malformed-JSON/path failure categories.
Native offline replay of benchmark-A 1c3abc8d/security produced valid JSON and
preserved all 107 reported findings, including all 21 previously unmappable Helm
findings; source hashes and counts are recorded in the final evidence artifact.

**Known gaps / follow-ups:** No source line claims are made for rendered findings.
The original scan failure preceded templates; it was not template-introduced.

## 2026-10-18 — Phase 9f corrective — Retention and iteration finalization

**Summary:** Reject syntax-breaking candidates even when diagnostic counts or
scanner fingerprints match, protect declarations referenced by unchanged files,
and bound iteration work/publication within the existing security limits.

**Requirements addressed:** FR-S-03, FR-S-04, FR-S-09, FR-V-03, NFR-01, PR-05.

**Files:** security/acceptance.py and partial.py, agents/security/agent.py,
scanners/runner.py, test_phase9f_acceptance_followup.py and integration
test_phase9f_deadlines.py.

**Decisions:** D-46. Native cached syntax checks precede every candidate retention.
Builtin references and module-wide unchanged consumers prevent dependency deletion.
Retained provenance names catalogue/template/fixer/partial actions. Security work
gets 55 of the existing 60 seconds, leaving bounded restoration/publication time;
tool cancellation is measured with a shorter cleanup bound. Template records
interrupted by deadlines become explicit rejections. EventLog batches notices;
full action details remain in package metadata. Limits remain 45/60/240 seconds,
four iterations, two resources/12 findings and six partial evaluations.

**Tests:** Five acceptance/publication follow-ups passed (2.18 s), covering
unchanged variable consumers, equal-count syntax replacement and bounded security
and generation publication. The full backend run before the final two generation
cases passed 1,479 tests. A PostgreSQL deadline regression retains verified TLS,
finalizes the interrupted KMS template and stays within the 60-second workload.
Final combined results follow in the concluding entry.

**Known gaps / follow-ups:** Benchmark A's exact publication/cleanup breakdown is
historically unavailable; its two measured overruns are not retroactively filled
in. Real-model performance remains author verification.

## 2026-10-18 — Phase 9f corrective — Native generation syntax recovery

**Summary:** Establish native syntax checks before accepting Terraform edits and
recover provisional generation with whitespace-only normalization, two syntax-only
fixer rounds and one diagnostic-fed regeneration. Share the original generator
deadline through publication, retaining model/output limits and blocking rules.

**Requirements addressed:** FR-G-02, FR-S-03, FR-V-03, FR-V-04, NFR-01, PR-05.

**Files:** agents/generation_syntax.py, generators/base.py, generator/security-fix
prompts, security/fix.py and generation.py, validation/syntax.py, gate.py and
workspace.py, agents/validation_repair.py and validator.py, domain/validation.py,
pipeline/orchestrator.py, security/terraform.py, corrective unit/generation
integration tests and existing generator/event fixtures.

**Decisions:** D-46. Native Terraform rejects compact blocks accepted by Python
HCL; lexer normalization inserts only newlines and verifies token equivalence.
Scope/control checks constrain model repairs. Generation stays provisional until
parsing succeeds; newly exposed findings remain blocking. Record source-free
recovery paths, redacted diagnostic feedback, usage and attempt totals. Deduplicate
observations and preserve unique source anchors across line movement. The complete
generation workflow has an outer deadline, with five seconds reserved for
finalization; timeout recovery follows existing legal status transitions.

**Tests:** make test completed 1,479 passed / 0 failed / 0 skipped / 6 performance
deselected (213.81 s) before the final outer-publication follow-up. Its two added
deadline cases pass within the five-test acceptance follow-up. Native checks,
normalization/token/idempotence, two rejected/accepted rounds, regeneration limits,
scope, redaction, clocks and newly revealed blockers are covered. Final combined
verification is recorded in the concluding corrective entry.

**Known gaps / follow-ups:** No real model success rate is measured. Native tools
must be available; unavailable verification fails closed. The preserved benchmark
A used prompt v7; corrected generation uses v8, requiring matched author runs.

## 2026-10-17 — Phase 9f section 7 — Quality measurement and final verification

**Summary:** Add allowlisted per-package catalogue/template/group/recovery/call/model
metrics, final-validity near misses, effective benchmark security limits and
complete offline/full-stack evidence. Preserve introduced blockers and unknowns.

**Requirements addressed:** FR-S-02, FR-S-03, FR-S-04, FR-S-09, FR-G-02, FR-V-03,
NFR-01, PR-01, PR-03, PR-04, PR-05.

**Files:** phase9f_metrics.py, phase9d_quality.py, generator_settings.py, final
security guard/checkpoint reporting fixes, automatic/offline-template/metrics and
legacy regression fixtures, README, D-46/thesis follow-ups, phase9f-verification.md,
new dated stub/secret-scan evidence directories and this log.

**Decisions:** D-46. Reports exclude source/diffs/model summaries and retain
historical missing metrics as unknown. Unstarted calls do not claim sent findings.
Verified checkpoint diffs/proposal metrics survive cancellation. Provider changes
stay with their module dependencies; malformed resource/policy shapes skip safely.
Legacy regression fixtures use genuinely invalid supporting declarations, preserving
rejection assertions while allowing independent valid groups. Shared context is
serialized; independent modules remain concurrent and result metadata stays sorted.
No defaults/models/severities/readiness/thresholds or dependencies are weakened.

**Tests:** Final make lint PASS (Ruff/format, mypy 122 sources, frontend ESLint/TS).
make test: 1451 passed / 0 failed / 0 skipped / 6 perf deselected (167.51 s).
make frontend-test: 100 passed / 15 files. make test-e2e: 6 passed (1.5 min).
make provider-schema: all 7 pinned versions exported offline. make secret-scan:
0 findings / 0 errors. The first full run's 1428 passes / 7 failures and corrected
fixture/concurrency assumptions are documented in phase9f-verification.md.
Scripted collision corpus: 4 normalized / 3 retained / 1 new-blocker rejection.
Mocked model switching and 45 -> 20 s timeout clipping pass; no real calls.

**Benchmark:** make bench-stub completed 14 pipeline runs / 42 generated and ready
packages plus 10 ZIP downloads. PR-01 median 13.1708 s; PR-04 median 1.0733 s,
maximum 1.3643 s (9,989,867-byte ZIP); PR-01/04/05 PASS. PR-03 FAIL, unchanged
1.5x threshold, measured cohort ratios 2.6226–2.6698x. Clean packages made zero fix
calls; their zero catalogue/template/recovery counts are not quality gains. Separate
six-attempt scripted real-offline verification: median 14.3084 s, max 30.1389 s,
3 init runs / 9 reuses / 0 reinitializations and zero deadline-only/regression
rollbacks. Evidence: phase9-bench-stub-20261017T213158569704Z and
phase9-secret-scan-20261017T213555936855Z.

**Known gaps / follow-ups:** Author-run gpt-oss then stronger-fixer real comparison
remains; historical 1/40 readiness and unreconstructable discarded candidates are
unchanged evidence. Template-introduced blockers remain rejected; no Phase 9g
profile is implemented. PR-03 remains a measured failure. Original author seed
environment remains unverified; only the reproduced exported-settings defect and
isolated full-stack fix are claimed. No new open questions beyond these explicit
limits; no source specification was edited.


## 2026-10-17 — Phase 9f section 6 — Minimal PR-04 seed configuration

**Summary:** Seed with only a development app URL, preflight before pipeline
submissions, and verify the full-size rejected synthetic ZIP through PostgreSQL/HTTP.

**Requirements addressed:** PR-04, FR-S-10, NFR-01.

**Files:** db/session.py, seed_benchmark_package.py, run_phase9_benchmarks.py,
unit seed settings and integration seed HTTP tests, README, D-46 and this log.

**Decisions:** The reproducible prerequisite defect was full Settings requiring
three unrelated migration/test URLs even when a valid app URL was available;
PostgreSQL running alone is insufficient. SeedSettings reads only exported
DATABASE_URL and never dotenv. Public commands still refuse test DB/owner role.
No new required package/report fields, migration or privilege changes were needed.

**Tests:** Seed configuration, calibration, schedule/preflight and full-size
PostgreSQL/HTTP tests: 10 passed / 0 failed. The downloaded rejected ZIP is under
10 MB with unavailable scan/validation explicitly labelled. The initial test
module basename collision was corrected by naming the integration file uniquely.

**Known gaps / follow-ups:** The author's original process environment cannot be
reconstructed without prohibited dotenv access; no claim is made about it. Final
bench-stub verification follows section 7 on a separate isolated database.


## 2026-10-17 — Phase 9f section 5 — Alternate fixer end-to-end verification

**Summary:** Persist effective fixer timing/batching limits and verify gpt-oss
and an Anthropic-family OpenRouter fixer through mocked HTTP and stored reports.

**Requirements addressed:** FR-S-02, FR-S-04, FR-S-09, NFR-01, PR-05.

**Files:** security agent session metadata, integration/test_phase9f_fixer_model.py,
README, D-46 and this log.

**Decisions:** Existing adapter/model defaults retained. Author override 45 s;
60 s iteration / 240 s stage retained; model-specific reasoning and JSON format
reach the request. Haiku test identifier is synthetic, not a provider availability
claim. Author chooses the actual model for a separately executed comparison.

**Tests:** Model HTTP/report integration plus factory tests: 16 passed / 0 failed.
Both requests clip to 20 s when only 20 s remains. No real LLM calls or keys.

**Known gaps / follow-ups:** No real latency/quality comparison is claimed; final
benchmark projection of this metadata follows section 7.


## 2026-10-17 — Phase 9f section 3 — Secure generator checklist

**Summary:** Select resource schemas and security/support requirements from the
plan while keeping the existing generator context and output-token budgets.

**Requirements addressed:** FR-G-02, FR-S-02, FR-V-03, NFR-01, PR-05.

**Files:** security/generation.py, generator prompt/base, schema context,
orchestrator metadata, domain validation report, generation tests, README/D-46/log.

**Decisions:** D-46; input <=6000 characters (4500 schemas / 1500 checklist),
explicit truncation and checklist length, prompt version 7. No model/default
output-budget change or benchmark-specific matching.

**Tests:** Secure generation, generator prompt/agent and schema context:
30 passed / 0 failed. Focused Ruff passed. Final full lint/suites follow section 7.

**Known gaps / follow-ups:** Prompt guidance is not proof of generated security;
all scans and acceptance guards remain authoritative.


## 2026-10-17 — Phase 9f section 4 — Focused calls and existing-file recovery

**Summary:** Bound resource/findings input, rotate equal-severity targets, supply
existing paths/content and normalize valid existing-path creations into edits.

**Requirements addressed:** FR-S-02, FR-S-03, FR-S-04, FR-S-09, NFR-01, PR-05.

**Files:** fixer/prompt/feedback, shared merge, security agent, focus helper,
settings, schema context, recovery and iteration tests, README, D-46, this log.

**Decisions:** D-46; 2 resources / 12 findings per call, optional backward-compatible
edits, per-file stale-base checks and existing three-additional-path bound.
Preserve candidate failure counts separately from retained counts and capture
regression-plus-deadline evidence before aborting. AWS-0104 schema alias corrected.

**Tests:** Focus/recovery, fixer, legacy iteration/lifecycle, schema context and
security-agent integration: 63 passed / 0 failed. Scripted collisions: 4 normalized,
3 retained, 1 guard-rejected. Focused Ruff/mypy passed. Unit exploration exposed
legacy fixed-length verifier mocks; they now repeat their final scenario result
and assert the added independent group evaluation rather than exhausting early.

**Known gaps / follow-ups:** Historical 47-rejection recovery remains unknown.
Secure generation and full benchmark/reporting verification follow.


## 2026-10-17 — Phase 9f section 2 — Bounded partial acceptance

**Summary:** Keep independently verified files/blocks from failed combined
candidates, group changed dependencies and preserve verified checkpoints on
cancellation. Reuse cached checks/scans and existing private workspaces.

**Requirements addressed:** FR-S-03, FR-S-04, FR-S-09, FR-V-03, PR-05, NFR-01.

**Files:** security/partial.py, acceptance.py, security agent, settings, partial
unit and recorded-loop integration tests, README, D-46 and this log.

**Decisions:** D-46; six evaluations per iteration, clipped to existing budgets.
Recorded LLM-only scanner sequences isolate automatic candidates without changing
assertions. Review retries retain forced rescan. Verification errors use existing
state arrows rather than attempting remediating -> scan_error directly.

**Tests:** Partial acceptance plus security-agent integration: 24 passed / 0
failed (real isolated PostgreSQL). Focused Ruff and mypy passed. Interim failures
identified fixture rescan sequencing and unchanged review rescans; both corrected.

**Known gaps / follow-ups:** Full suite and focused/model/reporting additions
follow. Tests use synthetic clocks and mocked scanner outcomes, not real LLMs.


## 2026-10-17 — Phase 9f section 1b — Supporting-resource templates

**Summary:** Add linked KMS, access logging, encrypted VPC flow logs and RDS
monitoring support with schema checks, reuse, safe skips and introduced findings.

**Requirements addressed:** FR-S-02, FR-S-03, FR-S-04, FR-V-03, NFR-01.

**Files:** security/templates.py, terraform.py, security agent, template tests,
design-deviations.md, this log.

**Decisions:** D-46; approved SSE-S3 access-log destination due to AWS delivery
constraints. All new blockers still reject templates; no exception profile or
recursive logging. Existing keys and bucket-key options are preserved.

**Tests:** Template tests: 20 passed / 0 failed. Eight offline Terraform checks
(four template families x two AWS versions) had zero failed/skipped checks;
AWS v6 KMS/flow templates emitted provider deprecation warnings only. Focused
Ruff and mypy passed before the final combined section verification.

**Known gaps / follow-ups:** No AWS deployment or real model calls. Supporting
resources can introduce blockers and remain rejected until separately reviewed.


## 2026-10-17 — Phase 9f section 1 — Schema-checked security catalogue

**Summary:** Add twelve scanner-targeted controls, source-preserving Terraform
edits, route-derived subnet intent and guard verification before LLM fixing.

**Requirements addressed:** FR-S-02, FR-S-03, FR-V-03, NFR-01.

**Files:** security/catalogue.py, terraform.py, acceptance.py, security agent,
catalogue/policy tests, design-deviations.md, this log.

**Decisions:** D-46 appendix records rules, edits and conflicts. Public subnet
intent is preserved; unresolved routes/engines/expressions skip. Automatic
changes must pass syntax, preservation, validity and no-new-blocker checks.

**Tests:** Catalogue and policy: 62 passed / 0 failed; focused Ruff passed.
Initial mypy found a local list annotation, corrected before the section commit.
An attempted multiline fixture-line formatting change caused three temporary
policy failures; the valid single-line header was restored before 62 passes.

**Known gaps / follow-ups:** Supporting resources and partial acceptance follow
in separate sections. Full-stack verification follows section 7.


## 2026-10-17 — Phase 9f section 0b — Resource-specific encryption evidence

**Summary:** Remove the package-wide AES256 substring exemption and require a
unique parsed configuration for the exact flagged bucket, including cross-file
and Terraform JSON associations. Unknown/conflicting evidence remains blocking.

**Requirements addressed:** FR-S-02, NFR-01.

**Files:** security/encryption.py, security/policy.py, policy unit tests,
integration security policy-version assertion, design-deviations.md, this log.

**Decisions:** D-46; policy version 3. Seven other variant entries contain no text
search and retain their existing explicit policy decisions. Positive assertions
are preserved using a genuine associated-encryption fixture.

**Tests:** Policy regressions: 12 passed / 0 failed. Initial focused Ruff check found
one E501 fixture line; corrected in section 1 before final verification.
Full lint and suites run after remaining sections.

**Known gaps / follow-ups:** No new real benchmark. Final-file offline rescan
shows no old exemption becoming blocking; synthetic counterexamples remain fixed.


## 2026-10-17 — Phase 9f section 0 — Saved-evidence investigation

**Summary:** Record rule classification, exact iteration outcomes, R2 rescan and
partial-acceptance evidence without copying source or discarded candidates.

**Requirements addressed:** FR-S-02, FR-S-03, FR-S-04, NFR-01.

**Files:** docs/phase9f-investigation.md, docs/IMPLEMENTATION_LOG.md.

**Decisions:** Approved plan; no policy or readiness changes in this section.
Unknown historical exemption and additional salvage totals remain unknown.

**Tests:** Investigation checks: 3 passed / 0 failed (policy and seed-file tests).
Offline Checkov rescan: 13 cost packages, 7 CKV_AWS_145 findings, 3 resource-proven
old exemptions, 0 of those 3 newly blocking. Full suites deferred to implementation.

**Known gaps / follow-ups:** Implement R2 first; author database failure is not
reproduced. Discarded candidate source was not saved.


## 2026-10-17 — Phase 9e follow-up — Correct nested security evidence reporting

**Summary:** Use a shared canonical security-session iteration reader for context
and rollback summaries, with legacy fallback and no duplicate aliases. Preserve
original real-run evidence and publish a separate sanitized historical audit.

**Requirements addressed:** FR-S-03, FR-S-09, FR-V-04, NFR-01, PR-01, PR-03,
PR-04, PR-05.

**Files:** domain/review.py, scripts/phase9d_quality.py, unit follow-up reporting/
feedback tests, phase9e-followup-verification.md, dated sanitized audit, stub and
secret-scan evidence. D-45 and README were updated in the preceding loop commit.

**Decisions:** Positive, zero and missing context measurements remain distinct;
file categories and safe degraded reasons survive compact round trips. Historical
reasons stay unknown. Saved JSON proves grounding was present (52 proposals,
44 positive; run 12a0fcfb… lengths 11689 and 15452 exactly regenerate); the old
zero summary read top-level iterations instead of nested sessions. The stopping
condition originated in Phase 5 commit 91633dc on 1 October; Phase 9e rollback/
baseline reuse in 5584316 exposed it. All 14 raw evidence hashes remain unchanged.
Original readiness totals stay 1/40, with two missing variants.

**Tests:** Final make lint passed; make test 1322 passed / 6 perf deselected
(435.31 s), make frontend-test 100 passed / 15 files, make test-e2e 6 passed
(3.9 min). make provider-schema exported seven versions offline. make secret-scan
reported 0 findings / 0 errors. New tests cover canonical/legacy session reading,
missing measurements, compact round trips, unchanged readiness and safe bounded
feedback. Earlier legacy assertions and Docker-only setup errors are documented
in the verification report; final checks have no test failures.

**Benchmark:** make bench-stub completed 14 pipeline runs / 42 generated packages,
42 valid gates and 42 ready, plus ten ZIP measurements. PR-01/05 pass; PR-03/04
fail unchanged thresholds under concurrent verification load. The separate
scripted real-offline-Terraform rehearsal measured six iteration verifications:
median 14.8905 s, p90/max 31.4790 s, including initialization/queue waiting;
three init runs / nine reuses / zero reinitializations; zero validity rollbacks;
0 deadline-only rollbacks / 6 attempts, zero pre-candidate and multiple-cause
stops. Normal clean stub packages attempted zero fixes, with 42 init runs /
126 reuses and initial/post-security deadline stops 0/0. Historical four/nine
stops and injected-clock outcomes are reported separately.

**Known gaps / follow-ups:** PR-03 concurrency and PR-04 latency remain measured
failures. No new real benchmark, readiness change or quality prediction. Author
comparison and Chapter 4/6 follow-ups remain; no new specification ambiguity.

## 2026-10-17 — Phase 9e follow-up — Continue bounded security attempts

**Summary:** Remove the repeated-fingerprint terminal shortcut so rejected,
unchanged and rolled-back candidates can use the remaining attempt allowance.
Retain validity comparison, selective Terraform rollback, security-control
protection and no-new-blocker checks; send bounded previous-attempt feedback.

**Requirements addressed:** FR-S-03, FR-S-04, FR-S-05, FR-S-09, FR-V-03,
NFR-01, PR-05.

**Files:** security agent/fixer/new feedback helper, security-fix prompt v4,
remediation metadata, continuation and scanner-loop grounding integration tests,
existing security/schema tests, README and D-45/CL-01.

**Decisions:** D-45 records the approved policy. Started attempts consume the
allowance; terminal scans and baseline-only deadline stops do not. Discard
unverified timed-out candidates and continue only within the 60-second iteration,
240-second stage and configured attempt limits. Retained sources and verified
mixed-file changes are the next baseline. Separate redacted rejection feedback
is capped at 4,000 characters, labels candidate diagnostics and keeps engineer
feedback separate. Existing version-correct schema grounding and caps remain;
proposal metadata now records safe context reasons.

**Tests:** make lint passed (Ruff/format, mypy 114 source files, frontend lint).
Final make test: 1322 passed, 0 failed, 0 skipped, 6 perf deselected, 435.31 s.
make frontend-test: 100 passed / 15 files. make test-e2e: 6 passed, 3.9 min.
The 12-case continuation matrix covers regression, repeated findings, rejected
patches, four-attempt exhaustion, clean exit, mixed edits, deadline continuation,
stage exhaustion and three Retry variants. Two real FixAgent loop cases prove
AWS 5/6 fixture schemas survive rollback and reach the next prompt. Additional
schema tests cover malformed input and missing indexes; feedback canaries and
caps remain enforced. The independent unit run passed 1121 tests in 177.72 s.

**Known gaps / follow-ups:** No real benchmark was run; stub measurements cannot
predict real quality. The final verification report records the separate audit,
all command outcomes and measured benchmark/deadline counts. No dependencies,
installs, downloads, dotenv reads, migrations, thesis edits or pushes.

## 2026-10-16 — Phase 9e section 6 — Verify offline gates, budgets and evidence

**Summary:** Complete lifecycle, cancellation, source-preservation, masked-origin,
clock-boundary, independent-budget and safe reporting regressions. Record full
verification and two complete stub rehearsals with unchanged thresholds.

**Requirements addressed:** FR-G-02, FR-G-06, FR-S-03, FR-S-07, FR-S-09,
FR-V-03, FR-V-04, FR-V-05, NFR-01, PR-01, PR-03, PR-04, PR-05.

**Files:** README; D-45; phase9e-verification.md; lifecycle/gate/measurement/quality
and integration regressions; security agent/fixer, validator/domain/orchestrator,
workspace/idiom/initialization guards; strict quality summaries; new dated stub
and secret-scan evidence. Thesis sources were not edited.

**Decisions:** D-45 documents ordering, limits, offline prerequisites and private
workspace cleanup. Final reports include package-wide initialization totals and
actual generator context size. Masked optional-tool origins stay unknown. JSON
repairs preserve unrelated escapes and nonempty rule source; HCL repairs leave
comments and expressions intact. Failed init never populates validation cache.
Retry scanner verification failures now retain durable session evidence.
No dependencies, downloads, installs, real LLM calls, dotenv reads or pushes.

**Tests:** Final make lint passed (Ruff/format, mypy 113 source files, frontend
ESLint/TypeScript). make test: 1302 passed, 0 failed, 0 skipped, 6 perf deselected,
129.68 s. make frontend-test: 100 passed / 15 files. make test-e2e: 6 passed,
1.4 min. make secret-scan: 0 findings, 0 errors. make provider-schema: seven
pinned versions exported offline. Focused new regressions: 58 passed. The first
full run had seven failures / 1274 passes; the Retry persistence bug and old
fixture/event/runner assumptions were corrected, then selected regressions and
full reruns passed. No readiness assertions were weakened.

**Benchmark:** Final make bench-stub completed 14 pipeline runs / 42 packages,
42 valid gates and 42 production ready; ten ZIP measurements. PR-01/04/05 pass;
PR-03 fails its existing concurrency ratio. Backend verification ran concurrently.
Package totals: 42 init runs, 126 reuse events, zero reinitializations. Generator
schema context 5689 characters. Separate scripted-fix/real-offline-Terraform
rehearsal: six verification intervals, median 15.0201 s, p90/max 31.1578 s;
3 init runs, 9 reuse events, no reinitializations or validity regressions,
0 deadline-only rollbacks / 6 attempted fix iterations. The clean pipeline has
zero fix attempts and zero initial/post-security deadline stops; this is distinct
from the historical four/nine. Injected clocks cover one pre-candidate stop,
one deadline-only rollback and one multiple-cause rollback; two 230-second-stage
integration cases still get a full 60-second post-security repair budget.
See docs/phase9e-verification.md and dated evidence for full measured tables.

**Known gaps / follow-ups:** Real quality/deadline improvements remain unmeasured.
PR-03 remains a measured failure; no threshold, model or label was changed.
Chapter 4/6 and author-run comparison follow-ups are documented. No new open
specification question was introduced.

## 2026-10-16 — Phase 9e section 5 — Measure validation and iteration verification

**Summary:** Publish actual stage durations through EventLog; export strict,
source-free benchmark rows, gate/context/repair outcomes and conservative final
failure origins. Distinguish validator persistence from prepared validation.

**Requirements addressed:** FR-V-03, FR-V-04, FR-S-09, NFR-01, PR-05.

**Files:** validation/{measurement,workspace,terraform,documents}.py; agents
security/repair/validator; orchestrator; domain reports; benchmark/quality scripts;
new phase9e_metrics.py and phase9e_rehearsal.py; measurement/history tests.

**Decisions:** Initialization and validation timings include concurrency waiting;
unknown/hidden error origins remain unknown. Stub packages are clean, so their
zero fix iterations are reported separately from a labelled three-workspace,
real-offline-Terraform/scripted-fix load rehearsal. Neither rehearsal rows nor new
descriptive timings alter quality rates or thresholds (D-45). Cache reuse also
requires matching current initialization state after rollback. Helm JSON
Go templates are checked after rendering, like YAML Go templates.

**Tests:** Focused measurement/gate/iteration/benchmark/repair/security suite:
82 passed, 0 failed, 0 skipped. Ruff checks and formatting passed; strict mypy
113 source files passed. Canary allowlists, historical unknown origins,
deadline-only/multiple-cause counts and fixture-runner reuse are covered.

**Known gaps / follow-ups:** Full verification and measured real-tool stub
rehearsal results follow in section 6. No real-run improvements are predicted.

## 2026-10-16 — Phase 9e section 4 — Reject broken patches and iteration regressions

**Summary:** Parse touched/merged documents, render affected charts, preserve
security controls and verify Terraform before/after security fix iterations.
Roll back Terraform regressions including added files; verify retained YAML.

**Requirements addressed:** FR-S-03, FR-S-07, FR-S-09, FR-V-03, NFR-01, PR-05.

**Files:** security/{agent,fix,verification}.py; validation/{gate,preservation,
terraform,workspace}.py; factory/remediation; pipeline/review.py; iteration tests;
recorded security/automatic-repair fixture corrections; this log.

**Decisions:** One shared bounded tool runner and private workspaces. Cache
complete checks only for identical package/mirror inputs; never cache tool
unavailability. The 60-second iteration encloses verification; distinguish
candidate rollback at deadline from a stop before a candidate. Retry keeps one
workspace through final validation. Existing scanner recordings now inject their
schema verifier; new regressions explicitly script schema counts (D-45).

**Tests:** Iteration/fixer/repair/real-PostgreSQL security regressions: 49 passed,
0 failed, 0 skipped. Strict mypy: 112 source files passed. Fixtures now use valid
HCL comments instead of bare original text, declare their Kubernetes type, and
use a remaining subset of original fingerprints. History comparisons normalize
new default metadata fields. No readiness assertion or check meaning weakened.

**Known gaps / follow-ups:** Per-stage measurement and benchmark tables follow
in section 5; comprehensive deadline/canary/workspace regressions in section 6.

## 2026-10-16 — Phase 9e section 3 — Ground scanner fixes and repair prompts

**Summary:** Supply exact-version resource/data schemas to every shared fixer
entry point, including scanner-only calls; add bounded generator references and
explicit provider/default-security-group/flow-log/replication idioms.

**Requirements addressed:** FR-G-02, FR-S-03, FR-S-09, FR-V-03, NFR-01.

**Files:** validation/schema_context.py; agents/{factory,remediation,security/fix,
prompts/*}.py; schema-context tests; prompt version assertion; Makefile; this log.

**Decisions:** Initialized versions outrank constraint selection; non-HashiCorp
sources never receive HashiCorp schemas. File-linked failures prioritize target
schemas and nested blocks. Context includes symbol/attribute names, never values;
complete JSON entries fit the 16000-character cap. Generator input is capped at
6000 characters without changing output limits. Missing indexes log/degrade (D-45).

**Tests:** Schema/context/fixer/generator regressions: 52 passed, 0 failed,
0 skipped. Strict mypy: 110 source files passed. Ruff passed. make provider-schema:
seven versioned exports successful, no downloads; AWS index sizes 10323113 and
13961639 bytes. Earlier prompt-version assertion updated from v5 to v6.

**Known gaps / follow-ups:** Patch/iteration guards and benchmark measurements
follow in sections 4–5. No real quality gain is inferred from stub tests.

## 2026-10-16 — Phase 9e section 2 — Gate generation in reusable workspaces

**Summary:** Add all-type parsing, formatting and installed-tool generation
checks, a bounded generation repair, private reusable module initialization,
safe init categories, two targeted idiom repairs and a fresh post-security budget.

**Requirements addressed:** FR-G-02, FR-G-06, FR-V-03, FR-V-04, NFR-01, PR-05.

**Files:** validation/{workspace,gate,idioms,engine,terraform,documents}.py;
pipeline/orchestrator.py; remediation/repair protocol; runner; domain/config;
unit/test_phase9e_gate.py; .env.example; README; this log.

**Decisions:** Gate metadata is separate from final readiness; original files
are redacted before audit persistence. Ordinary source changes reuse init;
provider/module dependency changes invalidate it. Existing declaration repairs
remain generation-only; exactly two new source-preserving rewrites (D-45).

**Tests:** Gate/workspace/idiom/validator/repair regression command: 63 passed,
0 failed, 0 skipped. Strict mypy: 109 source files passed. Earlier standalone
mypy from repository root lacked backend plugin configuration; running from
backend resolves the unrelated Settings call-argument diagnostics.

**Known gaps / follow-ups:** Prompt schema context, per-patch enforcement and
iteration regression checking follow in sections 3–4. Full acceptance follows.

## 2026-10-16 — Phase 9e section 1 — Export offline provider schema indexes

**Summary:** Add compact hash-verified indexes for every pinned version and
version-bound resource/data queries, required-member checks and name suggestions.

**Requirements addressed:** FR-V-03, NFR-01.

**Files:** validation/provider_schema.py; scripts/provider_schema.py; schema
unit/offline integration tests; Makefile; .gitignore; README; D-45; this log.

**Decisions:** Offline scratch HOME/provider-installation config; no network
fallback. Index absence/corruption safely degrades. Descriptions are removed,
recursive types/blocks retained; optional+computed stays writable (D-45).

**Tests:** Schema unit and real-mirror integration: 9 passed, 0 failed,
0 skipped. Ruff/format and strict mypy verification recorded below/final.

**Known gaps / follow-ups:** Prompt integration/workspace gates follow in
sections 2–4. Schema structure cannot describe every conditional provider rule.

## 2026-10-16 — Phase 9e section 0 — Investigate syntax, repair and timing

**Summary:** Record approved read-only findings, offline schema feasibility,
error-origin samples and measurement gaps before implementation.

**Requirements addressed:** FR-V-03, FR-V-04, NFR-01, PR-05.

**Files:** docs/phase9e-investigation.md; this log.

**Decisions:** Preserve unknown provenance; distinguish deadline/limit markers
from completed rounds. Author approved schema grounding for scanner fixes,
two narrow deterministic repairs, iteration rollback, fresh post-security
budget and private initialized workspace reuse. D-45 follows in implementation.

**Tests:** Baseline make lint PASS (105 mypy source files; Ruff/format and
frontend ESLint/TypeScript). Investigation: 136 offline stage evaluations,
0 unavailable-tool skips; seven provider-schema exports successful. No unit
or full-suite tests run in section 0; these are not test-suite counts.

**Known gaps / follow-ups:** 12 incomplete intermediate package histories;
no real-run prediction or provider calls. Sections 1–6 implement and verify.

## 2026-10-15 — Phase 9d section 6 — Verify feedback, safety and quality evidence

**Summary:** Finish failure/cancellation/canary and real-database regressions;
retain compact baseline and stub measurement evidence; document author settings
and Chapter 4/6 follow-ups without changing readiness or validator criteria.

**Requirements addressed:** FR-G-02, FR-S-03, FR-S-07, FR-S-09, FR-V-01,
FR-V-03, FR-V-04, NFR-01, PR-01, PR-03, PR-04, PR-05.

**Files:** final verification and stub/secret-scan evidence; pipeline
orchestrator/review; security/validation repair persistence; narrow domain
verification arrows; repair/canary/row-panel/scope-guard tests; recorded scanner
and recursive canary fixtures; README.md; D-44/thesis follow-ups; this log.

**Decisions:** Final candidate files and validation results commit together
before security confirmation; scan failure cannot produce readiness. Preserve
repair history through engineer Retry. Review-demo bypass is stub-only. Keep
all finding classifications and validator meanings. Exact next-benchmark lines
and defaults are in README and the verification summary. No new open question.

**Tests:** make lint PASS (105 mypy files; Ruff/format/frontend lint/TypeScript).
make test: 1244 passed, 0 failed, 0 skipped, 6 perf deselected. make frontend-test:
100 passed / 0 failed. make test-e2e: 6 passed / 0 failed. Final make secret-scan:
0 findings / 0 errors ([evidence](evals/phase9-secret-scan-20261015T154529168973Z/summary.md)).
make bench-stub: 14 successful pipelines
and 10 downloads; PR-01 median 14.229337s PASS, PR-03 ratios 2.571282–2.616546
FAIL, PR-04 maximum 1.321749s PASS, PR-05 PASS. Overall stub benchmark FAIL
is preserved. Backend/browser runs used isolated PostgreSQL and were rerun
serially after an interrupted overlapping attempt. Final acceptance includes
new round/call deadlines, rollback, candidate redaction, final scan failures,
Retry history, provider-scoped demo bypass and nested Grafana row panels.
Exact deduplication preserves a newline in an otherwise emptied file so later
fix proposals still satisfy the existing non-empty-file guard.

**Known gaps / follow-ups:** Real production-ready rate and total run time
remain author-only. Stub readiness is not real quality evidence. PR-03 overhead
still fails and is not hidden or optimized outside this phase. Original
baseline/spec remain unchanged; no real keys/calls, installs or downloads.

## 2026-10-15 — Phase 9d section 5 — Measure quality with compact safe inputs

**Summary:** Add status/review/check/finding tables to benchmark summaries and
an offline quality command. Save only explicit allowlisted metadata, never
source/diffs/feedback. Recompute the original baseline into a separate folder.

**Requirements addressed:** FR-V-04, NFR-01, PR-01, PR-05.

**Files:** scripts/{phase9d_quality,benchmark,run_phase9_benchmarks}.py;
unit/{test_quality_metrics,test_phase9_benchmark}.py;
docs/evals/phase9d-baseline-quality-20261015/; README.md; D-44; this log.

**Decisions:** Run/variant association lives in filenames. Generated-package rate
is separate from six missing variants. Historical absent snapshots are unknown.
Existing canary assertions now recursively inspect every new evidence file.

**Tests:** Quality and benchmark regression command: 19 passed, 0 failed,
0 skipped. Real offline baseline command reproduces 1/36 (2.78%), 35 validation
failures, 30 unresolved-security packages and all supplied top-check/rule counts.
make lint passes including strict mypy (105 files), frontend eslint/TypeScript.

**Known gaps / follow-ups:** Full backend/browser acceptance is section 6;
no real provider calls or estimated post-change outcomes.

## 2026-10-15 — Phase 9d section 4 — Require complete valid generator artifacts

**Summary:** Generator prompt v5 renders concrete plan-specific file paths from
shared layout rules and reuses provider/S3/Ansible/Grafana correctness guidance.

**Requirements addressed:** FR-G-02, FR-V-01, FR-V-03, NFR-01.

**Files:** agents/prompts/generator.py; unit/test_generator_prompt.py; D-44; this log.

**Decisions:** Preserve structured-output schema and output/attempt defaults.
The Architect schema stays unchanged. Plain dashboard JSON is required without
changing the Grafana validator; wrappers are not provisioning dashboards.

**Tests:** Generator prompt/generation/Phase 9c regression command: 39 passed,
0 failed, 0 skipped. Concrete checklist paths classify under existing layout.

**Known gaps / follow-ups:** Author-only real quality measurement remains pending.

## 2026-10-15 — Phase 9d section 3 — Correct S3 guidance and bound iterations

**Summary:** Teach the shared fixer standalone public-access resources and
provider-compatible repairs, covering new log/replica buckets and preserving
existing resources. Raise the existing iteration default to four and cap each
automated iteration at 60 seconds within the 240-second stage budget.

**Requirements addressed:** FR-S-03, FR-S-05, FR-V-03, PR-05.

**Files:** agents/prompts/{quality,security_fix}.py; agents/security/agent.py;
core/config.py; .env.example; unit/{test_quality_guidance,test_config}.py;
integration/test_security_agent.py; D-44; this log.

**Decisions:** Fixer attempt default stays 90, clipped to iteration time;
recommend 45 for the author. No model, readiness or finding reclassification.
Measured baseline iterations were median 8.13s/max 28.11s; added validation
work and the new total runtime remain unmeasured.

**Tests:** Guidance/config/security/concurrency command: 50 passed, 0 failed,
0 skipped. Injected-clock deadline regression preserves files and iteration count.

**Known gaps / follow-ups:** Real quality/runtime measurements are author-only.

## 2026-10-15 — Phase 9d section 2 — Share remediation and repair validation

**Summary:** Reuse Retry's fixer, prompt and patch-merging code for bounded
atomic validation rounds, then verify the exact final files with both tools.
Preserve original files, typed repair history and existing engineer-Retry policy.

**Requirements addressed:** FR-S-07, FR-S-09, FR-V-01, FR-V-03, FR-V-04, NFR-01.

**Files:** agents/{remediation,validation_repair,validator,security/*,prompts/security_fix}.py;
pipeline/orchestrator.py; domain/{states,validation}.py; core/config.py;
db/repositories/packages.py; new repair unit/integration tests; pipeline API
recorded-scanner fixture; README.md; .env.example; D-44; this log.

**Decisions:** Default two initial rounds plus one after security changes;
share the 120-second repair budget. Automatic acceptance requires fewer failed
checks and no new blocking fingerprints; Retry's acceptance stays unchanged.
Review demo intentionally retains manual repair. Final scan errors cannot pass.

**Tests:** Retry/security/concurrency/recovery regression command: 67 passed,
0 failed, 0 skipped. Automatic repair/validator command: 22 passed, 0 failed,
0 skipped. Strict mypy on app passed (104 files). Earlier fixture exhaustion
was corrected by provisioning enough recorded replies for new final scans.

**Known gaps / follow-ups:** Security guidance, iteration bounds and quality
aggregation follow. Full acceptance remains section 6.

## 2026-10-15 — Phase 9d section 1 — Repair Terraform declarations

**Summary:** Add source-preserving, per-module missing-variable and allowlisted
data-source repairs and exact variable deduplication; expose optional data
reference indexing without changing ordinary validator checks.

**Requirements addressed:** FR-V-01, FR-V-03, NFR-01.

**Files:** app/validation/{repairs,documents}.py; unit/test_terraform_repairs.py;
design-deviations.md D-44; this log.

**Decisions:** No variable defaults; secret names are sensitive. Existing JSON
and HCL declarations count. Unparsable modules and conflicting duplicates stay.

**Tests:** New repair tests: 5 passed, 0 failed, 0 skipped after correcting
idempotence for data declarations. Full acceptance follows section 6.

**Known gaps / follow-ups:** Pipeline/report wiring belongs to section 2.

## 2026-10-15 — Phase 9d section 0 — Investigate baseline quality

**Summary:** Record the approved investigation, real failure samples, S3 fix
histories and timing headroom before implementation.

**Requirements addressed:** FR-S-03, FR-S-09, FR-V-01, FR-V-03, PR-01, PR-05.

**Files:** docs/phase9d-investigation.md; this log.

**Decisions:** No readiness or validation changes. Three baseline fix passes;
recommend four, with bounded validation repair and fair generator overrides.

**Tests:** Read-only snapshot aggregation and offline Terraform/Ansible diagnostics;
implementation suites not run for this documentation section. No pass counts claimed.

**Known gaps / follow-ups:** New quality and timing require an author benchmark.

## 2026-10-14 — Phase 9c evidence integrity correction — Preserve stored bytes

**Summary:** Post-commit blob verification found Git had normalized CRLF endings
in four original benchmark CSVs, although all working-copy hashes stayed intact.
Disable text normalization for the exact original evidence directory and restore
its original bytes to the index. Add a corrective commit instead of rewriting
history; this is the sole additional commit beyond the six numbered sections.

**Requirements addressed:** PR-01, PR-05, NFR-01.

**Files:** .gitattributes; the four original CSV Git blobs (working files unchanged);
this log. No runtime source changed.

**Decisions:** Byte preservation includes committed blobs, not only working
copies. The original folder's 13 SHA-256 hashes must match both index and working
tree before committing. Git's no-history-rewrite instruction remains in force.

**Tests:** Full acceptance remains 1217 backend passed/6 perf deselected,
100 frontend passed, 6 E2E passed, lint clean, 14 successful stub pipelines and
10 downloads (PR-03 FAIL preserved). Manual blob-integrity verification found
four line-ending mismatches and verifies all 13 original index/working hashes
after correction. Fresh make secret-scan: 0 findings/0 errors, report
phase9-secret-scan-20261014T121937053671Z, before this corrective commit.

**Known gaps / follow-ups:** No code retest needed for attributes/evidence-only
changes. Real post-change measurements remain author-only.

## 2026-10-14 — Phase 9c section 6 — Keep first real attempt and final evidence

**Summary:** Preserve all 13 files of the author's first real benchmark unchanged,
retain the free post-change rehearsal/secret-scan evidence, and record the actual
acceptance results and Chapter 6 follow-ups without running a paid provider.

**Requirements addressed:** PR-01, PR-03, PR-04, PR-05, FR-G-02, FR-G-06, NFR-01.

**Files:** docs/evals/phase9-bench-real-20261014T101701420278Z/ (unchanged);
docs/evals/phase9-bench-stub-20261014T121247036453Z/;
docs/evals/phase9-secret-scan-20261014T120847350989Z/ and final scan evidence;
docs/design-deviations.md; this log. README/.env.example recommendations and
commands were updated in sections 1–4.

**Section 0 / confirmed findings:** the old OpenRouter body sent
max_completion_tokens=32,000, json_object, reasoning disabled, no explicit
temperature or provider routing. Prompt v3 had compactness guidance but no actual
budget; GeneratorOutput used a free-form file map with optional capped notes.
The old parser counted four backticks anywhere as multiple_blocks, potentially
rejecting valid string content; raw invalid outputs were not stored, so individual
historical false positives cannot be established. Adapter retries repeated the
same prompt; package retries supplied only errors/paths, not previous content.
The author confirms attempt=150, generator=270 and duplicate completion values
150 then 270; synthetic installed-loader checks prove last assignment wins,
and a shared-clock mock reproduces 150 then 120-second calls ending at 270.
General attempt=60/output=16,000 fallbacks were overridden; an unset generator
output now selects 8,000. Settings/authentication guidance is in README and D-43.

**Final actual acceptance:**
- make lint: passed Ruff/format (200 app/test files; 11 evaluation scripts),
  mypy (101 app sources), ESLint and both strict TypeScript projects.
- make test: 1217 passed, 0 failed, 0 skipped; 6 perf deselected (125.84s).
  The first full run's 1214 passed/2 failed exposed generator options leaking
  into generic adapter calls; the corrected scope and regression passed rerun.
- make frontend-test: 100 passed, 0 failed, 0 skipped; 15 files (10.20s).
- make test-e2e: 6 passed, 0 failed, 0 skipped (1.3m).
- make secret-scan: 0 findings, 0 scan errors in the initial and final scans;
  final report phase9-secret-scan-20261014T121615100543Z, checked before the evidence commit.
- make bench-stub executed once: 14 pipelines all success and 10 complete ZIP
  downloads. PR-01 median 6.696361s PASS; PR-03 ratios 2.212720–2.241065 FAIL
  versus 1.5; PR-04 maximum 1.314243s PASS; recorded PR-05 thresholds PASS.
  Three recorded generator attempts per run, all first-attempt success. Effective
  server configuration captured as output=8,000, structured=json_schema,
  attempt=120, completion/generator=150, adapter/package attempts=3/2. Mode is
  stub, provider cost zero; this is overhead rehearsal, not real LLM performance.
- git diff --check passed. All 13 original evidence hashes matched the pre-edit
  snapshot; no original bytes were modified.

**Decisions:** Extend existing D-43 and timing/JSON clarifications, with no new
open question. Retain valid late packages and report their configured-budget
flag/overrun without changing PR-05. Keep the original failed real outcome and
both unknown historical settings/attempt fields in those unchanged artifacts;
author-confirmed historical settings are recorded separately here. Official
OpenRouter docs confirm max_completion_tokens semantics and required-parameter
strict routing; client-side schema validation remains authoritative.

**Known gaps / follow-ups:** Stub PR-03 still fails; runtime optimisation is
outside this phase. Post-change real reliability/cost are unmeasured. Recommend
the author use 8,000 output tokens, attempt=90, generator/completion=150, one dotenv
assignment per key, matching server/client API_KEY, restart, then bench-smoke.
No real LLM calls, .env reads/edits, installations/downloads, dependencies, model
changes, pushes, specification edits or Phase 10 work occurred. Verification used
an isolated postgres:16 container from an existing image with ordinary roles and
synthetic credentials; the backend/container were removed after rehearsal. The
author's database/container state and untracked REVISION.txt are untouched.

## 2026-10-14 — Phase 9c section 5 — Verify generator and reporting behavior

**Summary:** Add real PostgreSQL regressions proving valid late packages remain
stored and failed attempt metrics reach EventLog/SSE without raw output. Complete
mocked deadline/fallback/duplicate-key and generic-adapter compatibility coverage.

**Requirements addressed:** PR-01, PR-05, FR-G-02, FR-G-06, FR-G-07, NFR-01, NFR-03.

**Files:** backend/tests/integration/test_phase9c_events.py;
tests/unit/test_phase9c_generator.py; app/agents/generators/base.py;
app/llm/{base,openai}.py; this log.

**Decisions:** Keep output validation and strict request options scoped to generator
calls using an async context, so generic spike/evaluation calls through the same
adapter keep their original contract. The first full run exposed this regression
in two existing tests; fix it rather than weakening those tests. Log actual retry
prompt sizes, never response contents. Other agents keep their original options.

**Tests:** New PostgreSQL persistence/canary cases: 2 passed, 0 failed, 0 skipped
(6.76s). Focused compatibility/generator/parser/provider suite: 178 passed,
0 failed, 0 skipped (3.49s). First full make test: 1214 passed, 2 failed,
6 perf deselected (135.84s); final rerun after the scope correction: 1217 passed,
0 failed, 0 skipped, 6 perf deselected (125.84s). make lint passed Ruff/format
(200 app/test files; 11 scripts), mypy (101 sources), ESLint and both TS projects.
make frontend-test: 100 passed, 0 failed, 0 skipped across 15 files (10.20s).
Initial make secret-scan: 0 findings/0 errors (phase9-secret-scan-20261014T120847350989Z).
Browser acceptance, the one free stub rehearsal and final scan follow section 6.

**Known gaps / follow-ups:** Real post-change reliability and spending remain
author-only measurements; no estimated performance claim is made.

## 2026-10-14 — Phase 9c section 4 — Authenticate settings and expose attempt evidence

**Summary:** Add a strictly key-protected generator settings endpoint, capture
server-effective numeric/mode evidence, report all generator attempts/failures/
overruns, and support selected prompts plus a three-example guarded smoke check.

**Requirements addressed:** PR-01, PR-05, FR-G-02, FR-G-06, NFR-01.

**Files:** backend/app/{api/{benchmark,deps},core/generator_settings,main,
pipeline/{orchestrator,state}}.py; scripts/{benchmark,phase9c_metrics,
run_phase9_benchmarks}.py; tests/unit/test_phase9c_benchmark.py;
tests/integration/test_phase9c_settings.py; Makefile; .env.example; README.md;
docs/design-deviations.md; this log.

**Decisions:** D-43. Health is unchanged. Missing/wrong/unconfigured API keys
receive generic 401 responses; clients cannot substitute local defaults for
server metadata. Benchmarks now require matching server/client API keys, including
stub rehearsals. Existing EventLog/state paths persist terminal metrics for both
success and failure; generation policy/stage classification is unchanged. CSV
nested metrics are JSON, unknown historical values remain unknown. PR-05 compares
150 seconds while configured-budget overrun flags remain separately descriptive.

**Tests:** Selection/report/authenticated-metadata/coordinator units: 27 passed,
0 failed, 0 skipped (1.64s). Real PostgreSQL settings/orchestrator/HTTP harness:
15 passed, 0 failed, 0 skipped (15.59s). make lint passed Ruff/format, mypy
(101 sources), ESLint and both strict TypeScript projects. New tests cover API
key cases, no settings on health, actual server overrides, prompt order, all
report outputs/canaries and smoke schedule. An initial missing type annotation
and long report strings were corrected before the passing lint run.

**Known gaps / follow-ups:** Section 5 adds late/failing persistence regressions
and runs full required acceptance. Real smoke is author-only, never run by Codex.

## 2026-10-14 — Phase 9c section 3 — Correct retries and audit shared deadlines

**Summary:** Add safe format correction messages and per-attempt records,
cancel in-flight calls at the shared budget, and retain valid late packages
with explicit deadline flags/overrun seconds. Invalid late packages cannot retry.

**Requirements addressed:** PR-01, PR-05, FR-G-02, FR-G-06, NFR-01.

**Files:** backend/app/llm/{base,errors}.py; agents/generators/base.py;
tests/unit/test_phase9c_generator.py; README.md; design-deviations.md; this log.

**Decisions:** D-43. Author-confirmed 270-second generator/completion settings
explain the original ceiling; synthetic duplicate-key parsing confirms last
assignment wins. General 60-second and 16,000-token fallbacks are overridden
by generator-specific arguments. Retain paid-for valid late validation per the
author's explicit instruction, recording the overrun instead of hiding it.

**Tests:** Focused mocked provider/parser/generator/error suite: 194 passed,
0 failed, 0 skipped (3.58s). Slow HTTP cancellation uses an event-blocked mock
and a 1.1-second budget; final-validation tests use a shared injected clock.
External cancellation, no late retry, reason-only correction and failed token
records are verified. Full acceptance follows section 5.

**Known gaps / follow-ups:** Event persistence and reports follow section 4.
No real provider call, dotenv read or default timeout change.

## 2026-10-14 — Phase 9c section 2 — Enforce and validate generator output

**Summary:** Add generator-only structured modes, a closed file-list wire schema,
whole-object-first parsing and schema-validated salvage with safe reason codes.

**Requirements addressed:** PR-01, PR-05, FR-G-02, NFR-01, NFR-03.

**Files:** backend/app/{core/config,agents/factory,agents/generators/{base,schema},
agents/prompts/generator,llm/{base,openai,json_output}}.py; tests/unit/
{test_generators,test_phase9c_generator}.py; .env.example; README.md;
docs/design-deviations.md; this log.

**Decisions:** D-43. Free-form dictionary keys cannot form a closed strict wire
schema; adapt only the request/response boundary. Preserve other agents' request
settings and native Anthropic wire format. Whole valid JSON always wins over
markdown heuristics; historical multiple_blocks false positives are possible
but not individually provable. Reject invalid schema before safe salvage.

**Tests:** Focused generator/parser/provider/config suite: 191 passed, 0 failed,
0 skipped (1.97s). Ruff passed; mypy results follow final acceptance. New mocked
HTTP tests cover all modes and 8,000-token limits, routing/reasoning merge,
truncation, salvage, internal fences, multiple objects/blocks, wire round-trip,
duplicate paths and safe structured-refusal advice.

**Known gaps / follow-ups:** Retry correction and attempt/event metrics follow
section 3. No paid evaluation or .env access.

## 2026-10-14 — Phase 9c section 1 — Bound full-package output

**Summary:** Change the existing generator output default from 32,000 to 8,000
and give prompt v4 the actual configured size budget. Keep all security,
validity and optimisation guidance.

**Requirements addressed:** PR-01, PR-05, FR-G-02, FR-G-06.

**Files:** backend/app/core/config.py; agents/generators/base.py;
agents/prompts/generator.py; tests/unit/test_config.py and
test_generator_prompt.py; .env.example; README.md; design-deviations.md; this log.

**Decisions:** Section 0 investigation completed before edits. The adapter already
sends max_completion_tokens and classifies provider length as truncated; reuse
those paths. D-43 records the observed failure and budget rationale. The author's
unset GENERATOR_MAX_OUTPUT_TOKENS will pick up 8,000; the general 16,000 fallback
cannot override an explicitly supplied generator limit.

**Tests:** Focused config/prompt/generator/provider unit suite: 113 passed, 0 failed, 0 skipped (1.77s). Initial verification helper forced a stub fixer and caused one default-setting assertion failure; corrected the helper environment before rerunning..
Full required acceptance checks follow section 5; no real provider call.

**Known gaps / follow-ups:** Structured format, parser repair, retry telemetry,
strictly authenticated settings and benchmark reports follow sections 2–5.

## 2026-10-13 — Phase 9 section 8 — Audit scope and retain final measured evidence

**Summary:** Complete all sections 0–8, retain raw verification/rehearsal reports,
and document the actual stub PR-03 failure without altering runtime performance.

**Requirements addressed:** PR-01 through PR-05, NFR-01, NFR-03, FR-A-04,
FR-G-06, FR-S-02; traceability reports every specification ID.

**Files:** final reports under docs/evals/phase9-{backend-perf,pr02,bench-stub,
traceability,secret-scan}-*; backend/app/llm/{errors,base,openai,anthropic}.py;
backend/app/agents/security/agent.py; backend/scripts/{benchmark,
run_phase9_benchmarks,phase9_common}.py; backend/tests/unit/
{test_phase9_provider_errors,test_phase9_benchmark,test_phase9_traceability}.py;
backend/tests/integration/test_phase9_provider_surfaces.py; README.md;
docs/design-deviations.md; this log.

**Final audit corrections:** Clear original provider exception contexts, retain
original JSON decoder class names and actual HTTP status for malformed responses,
validate success-body shapes before SDK attribute access, and keep untrusted token
values out of logs. Success logs now say category=success. Failed security fixes
emit their fixed safe notice. New canaries verify quota/permission/authentication
messages across results, SSE, logs and PostgreSQL rows. Reject dotenv reference
paths before reading; redact native-provider configured secrets in metadata;
version probes use secret-free environments and temporary working directories.
Record tracked dirty state with the Git parent reference so pre-commit evidence
is explicit. Capture failed generation statuses from retained events/results and
distinguish partial usage deltas from final per-run costs. These corrections remain
within approved error/evaluation scope; no agent policy, prompt or UI redesign.

**Tests / actual final output:**
- make lint: passed Ruff/format (10 new evaluation scripts; 193 app/test files),
  mypy (98 app sources), ESLint and both strict TypeScript projects.
- make test: 1180 passed, 0 failed, 0 skipped; 6 perf deselected (116.22s).
  Earlier complete runs passed 1173 and 1178 before final audit coverage additions.
- make frontend-test: 100 passed, 0 failed, 0 skipped; 15 files (5.25s).
- make test-e2e: 6 passed, 0 failed, 0 skipped (1.2m).
- make test-perf: 6 passed, 0 failed, 0 skipped (JUnit recorded), with
  operator-confirmed quiet-machine status explicitly unknown.
- make test-ui-perf: 1 passed, 0 failed, 0 skipped; 32 live PR-02 samples,
  min 22ms, max 188ms, median 68.5ms. These are stub verification samples.
- make traceability: 59 requirements, no collection failures/invalid annotations;
  nine uncovered IDs: NFR-02, NFR-04, UC-01 through UC-07. Annotation coverage does
  not prove semantic coverage. Final report: phase9-traceability-20261013T185112881628Z.
- make secret-scan: zero findings, zero scan errors across working tree and full
  refs/reflogs history. Final report: phase9-secret-scan-20261013T185541011173Z.
- make bench-stub executed once: 14 pipelines all success, 10 ZIP requests all
  complete; PR-01 median 5.470856s (PASS), PR-03 isolated-baseline ratios
  2.755901–2.780750 (FAIL versus 1.5), PR-04 median 0.942928s/max 1.361918s
  (PASS), recorded PR-05 thresholds PASS. Synthetic source 13,177,789 bytes,
  calibrated ZIP 9,989,867 bytes. Mode stub; no provider spending. Report:
  phase9-bench-stub-20261013T182956518992Z. The command's successful exit means
  measurements completed; the report preserves the failed performance criterion.
- git diff --check passed; specification, dependency manifests/locks and applied
  migrations are untouched. Existing untracked REVISION.txt is untouched.

**Decisions:** D-42/D-43 completed; no new open question. Preserve initial scanner
trial reports with an explicit superseded-trial note, rather than presenting their
placeholder/parser false positives as operational credential findings. Verification
used a separate postgres:16 container from the existing local image, ordinary
roles/grants and synthetic passwords. Author database/container state was untouched.
Temporary backend stopped after rehearsal; isolated verification container removed.

**Known gaps / follow-ups:** Stub PR-03 fails on this environment with actual
local scanners/validation; runtime optimization is outside Phase 9. Real provider
PR-01/03/05, costs and quiet-machine final thesis evidence remain author-only.
NFR-04 clean-Ubuntu deployment remains Phase 10; NFR-02 and UC annotation gaps are
explicit. Static validation does not prove deployability. No real LLM call, .env
read, installation/download, push, history rewrite or Phase 10 work occurred.
Next: author-run guarded real measurements, then Phase 9b report generation.


## 2026-10-13 — Phase 9 section 7 — Document evaluation and thesis follow-ups

**Summary:** Consolidate the Phase 9 author workflow, D-42/D-43 methods/limits and
collected thesis-update notes without editing the specification or thesis prose.

**Requirements addressed:** NFR-01, NFR-04, PR-01 through PR-05.

**Files:** docs/design-deviations.md and docs/IMPLEMENTATION_LOG.md. README's
complete operator instructions were updated alongside sections 2–6.

**Decisions:** Preserve historical evidence and all requirement IDs. Stub results
are rehearsals, real measurements are author-only, and clean-Ubuntu deployment is
Phase 10. No new open question: existing OQ-03/OQ-06 remain author measurements.

**Tests:** Documentation checked against implemented CLI/Make targets and tests.
Most recent make lint passed Ruff/format, mypy (98 app sources), ESLint and both
TS projects. Most recent focused coordinator/budget/observer suite: 29 passed,
0 failed, 0 skipped (0.15s); frontend 100 passed in 15 files. Required final full
suites, traceability/scanning and one stub rehearsal are next, not claimed here.

**Known gaps / follow-ups:** Final audit/evidence and actual counts in section 8.
No spec, dependency, migration, generator prompt, scanner policy or UI edits.


## 2026-10-13 — Phase 9 section 6 — Coordinate guarded author benchmarks

**Summary:** Add bench-stub/bench-real orchestration, one shared cost guard,
per-measurement reports and a once-only first-real-run affordability advisory.

**Requirements addressed:** PR-01, PR-03, PR-04, PR-05, NFR-01.

**Files:** backend/scripts/run_phase9_benchmarks.py; scripts/benchmark.py and
phase9_common.py; backend/tests/unit/test_phase9_commands.py and
test_phase9_benchmark.py; Makefile; README.md; docs/design-deviations.md (D-43);
this log. Shared evidence directories now start with an INCOMPLETE summary.

**Decisions:** Export Make parameters to the process environment rather than
interpolating credentials/configuration into shell commands. Keep 14 planned
pipeline runs (10 PR-01, one baseline, one indivisible three-run cohort).
Projection uses first measured cost and never mutates/overrides the real guard.
Actual submitted/settled UTC times supplement monotonic durations. Native
Anthropic does not inherit OpenAI-compatible key-info endpoint configuration.

**Tests:** 29 coordinator/budget/observer tests passed, 0 failed, 0 skipped
(0.15s), including primary-versus-secondary verdicts, once-only safe advisory,
and a later measured cost increase overruling the projected count. make lint
passed Ruff/format, mypy (98 sources), ESLint and strict TS. Earlier frontend
acceptance remains 100 passed. No author real-mode command was executed.

**Known gaps / follow-ups:** Whole stub rehearsal and full verification follow
section 8. Real measurements and quiet-machine claims remain author-owned.


## 2026-10-13 — Phase 9 section 5 — Capture quiet-machine timing evidence

**Summary:** Wrap existing backend/frontend timing suites in timestamped Phase 9
raw reports and preserve live PR-02 samples before threshold assertions.

**Requirements addressed:** PR-02, NFR-01; existing backend perf requirements.

**Files:** backend/scripts/measure_performance.py; backend/tests/unit/
test_phase9_performance.py; frontend/e2e/{pr02.spec.ts,support/perfEvidence.ts};
frontend/playwright.config.ts; frontend/src/test/perfEvidence.test.ts;
Makefile; README.md; this log.

**Decisions:** Keep original timing thresholds/event correlation and default
perf exclusions. New wrappers use exported settings with no dotenv and isolated
verification children. make test-perf relies on pytest's existing test-database
migration fixture rather than a normally dotenv-loading Make prerequisite.
No UI component/style change or new spec deviation. Frontend skill applied.

**Tests:** Backend wrapper tests: 3 passed, 0 failed, 0 skipped (0.06s).
Frontend: 100 passed, 0 failed, 0 skipped across 15 files (4.32s); initial run
had 98 passing original tests and one failing new suite due to filesystem mock
interop, corrected. make lint passed Ruff/format, mypy (98 sources), ESLint and
both TS projects. Real browser/timing-wrapper execution follows final acceptance.

**Known gaps / follow-ups:** Quiet-machine status is operator-confirmed, never
inferred. Existing tool/mirror/browser prerequisites remain; no installation,
LLM call or dotenv read occurred.


## 2026-10-13 — Phase 9 section 4 — Seed a synthetic download fixture

**Summary:** Seed a reproducible near-10 MB ZIP through normal repositories,
valid state transitions and EventLog; label it rejected and explicitly synthetic.

**Requirements addressed:** PR-04, FR-UI-06, NFR-01.

**Files:** backend/scripts/seed_benchmark_package.py; backend/tests/unit/
test_phase9_seed_files.py; backend/tests/integration/test_phase9_seed.py;
Makefile; README.md; docs/design-deviations.md (D-43); this log.

**Decisions:** CLI accepts only the dev infraarch database/app role; injected
helpers let integration tests use the real test database. Compression calibration
measures the archive, not source bytes. No scanner, validation engine or LLM runs;
state events explicitly identify the synthetic fixture. No schema/grant changes.

**Tests:** Final seeding/content/HTTP checks: 3 passed, 0 failed, 0 skipped
(5.97s). Initial 2 failed/1 passed exposed last-chunk truncation in calibration;
fixed before the passing run. make lint passed Ruff/format, mypy (98 sources),
ESLint and strict TS. Small test fixtures prove ZIP sizing/content and label/event
provenance; the full-size rehearsal follows section 8.

**Known gaps / follow-ups:** Synthetic files are deliberately outside generator
size limits and are not deployable infrastructure. The dev CLI is exercised by
bench-stub once; tests write only to the isolated test database.


## 2026-10-13 — Phase 9 section 3 — Measure HTTP settlement and guarded budgets

**Summary:** Add PR-01/03/04 HTTP observation, per-agent/security-iteration timing,
same-prompt secondary references, safe CSV/JSON reports and measured-credit guards.

**Requirements addressed:** PR-01, PR-03, PR-05, NFR-01.

**Files:** backend/scripts/benchmark.py and phase9_budget.py; docs/phase9-prompts.json;
backend/app/api/health.py; backend/tests/integration/{test_health,
test_phase9_benchmark_http}.py; backend/tests/unit/{test_phase9_budget,
test_phase9_benchmark}.py; Makefile; README.md; docs/design-deviations.md (D-43);
this log. Budget helpers are isolated in a phase9 module for direct offline tests.

**Decisions:** D-43. Actual package transitions are emitted by the orchestrator,
so security iteration correlation uses variant/status rather than agent name.
Retain missing metrics as unknown. Health exposes actual runner_capacity without
new settings or migrations. OpenRouter key-info probes never retain response text
or key identifiers. Real commands read exported settings with dotenv disabled.

**Tests:** 26 focused unit and real-PostgreSQL HTTP integration checks passed,
0 failed, 0 skipped (7.24s). Tests cover guard thresholds/caps, unknown/malformed
credit, cost resets, offline fake key-info, zero/unknown affordability projections,
EOF replay with active snapshots, security iteration events, secondary references,
and a complete public-API stub baseline/cohort. make lint passed Ruff/format,
mypy (98 sources), ESLint and both strict TS projects. No real LLM/provider call.

**Known gaps / follow-ups:** Real-provider measurements remain author-only;
per-request cohort costs and absent Architect token metrics cannot be attributed.
Download fixture creation and coordinated author commands follow sections 4–6.


## 2026-10-13 — Phase 9 section 2 — Scan working-tree and historical secrets

**Summary:** Add an offline standard-library credential scanner with safe
location-only findings, exact allowlists and pre-read dotenv/cache exclusions.

**Requirements addressed:** NFR-01.

**Files:** backend/scripts/secret_scan.py; docs/secret-scan-allowlist.json;
backend/tests/unit/test_phase9_secret_scan.py; Makefile; README.md;
docs/design-deviations.md (D-42); this log; timestamped clean scan evidence.

**Decisions:** D-42 records heuristic/binary/commit-message/exclusion limits.
Full refs/reflogs trees detect deleted/renamed keys; blob caching avoids duplicate
reads. Initial runs found documentation placeholders and an empty-assignment
newline parsing bug, not operational credentials. Restrict assignment whitespace
to horizontal space and allowlist the two exact documented README placeholders.
No matched value was printed. Preserve initial raw trial reports until final audit.

**Tests:** Scanner tests: 8 passed, 0 failed, 0 skipped (0.09s), including earlier
commits, renames, untracked files, exclusions/symlinks, every pattern and exact
allowlisting. Final make secret-scan passed: zero findings, zero read/history
errors. make lint passed Ruff/format, mypy (98 sources), ESLint and both TS projects.

**Known gaps / follow-ups:** An absence of findings is not proof of no secrets;
D-42 documents excluded/unsupported surfaces. Benchmark tooling follows section 3.


## 2026-10-13 — Phase 9 section 1 — Collect requirement traceability

**Summary:** Collect pytest markers and Vitest/Playwright titles without running
fixtures, servers or test bodies; report exact thesis TC mappings and gaps.

**Requirements addressed:** none — evaluation infrastructure for all 59 IDs.

**Files:** backend/scripts/{phase9_common,phase9_report,pytest_traceability,
traceability}.py; docs/traceability-map.json; backend/tests/unit/
test_phase9_traceability.py; Makefile; this log; generated Phase 9 traceability
CSV-free JSON/Markdown/environment evidence under docs/evals/.

**Decisions:** Collection-only evidence is not a passing-test claim. TC groups
are many-to-many and reproduce the thesis matrix exactly. Missing mappings stay
unassigned. Perf Playwright titles are collected explicitly. No new deviation.

**Tests:** Focused extraction, real inherited/parameter-marker collection,
report and statistics checks: 8 passed, 0 failed, 0 skipped (0.47s). make lint
passed Ruff, formatting, mypy (98 app sources), ESLint and both TS projects.
make traceability passed: 59 IDs, zero invalid annotations/collection failures;
10 uncovered: NFR-02, NFR-04, PR-01, UC-01 through UC-07. Section 0's final
focused suite was 204 passed in 2.29s (correcting the earlier time-only entry).

**Known gaps / follow-ups:** Coverage counts describe annotations, not semantic
coverage; no tests added merely to fill gaps. Section 3 adds benchmark behaviors.


## 2026-10-13 — Phase 9 section 0 — Classify provider failures safely

**Summary:** Add eight provider-error categories, fixed public sentences and
safe category/HTTP-status/original-class diagnostics across SDK and agent failures.

**Requirements addressed:** NFR-01, NFR-03, FR-A-04, FR-S-02.

**Files:** backend/app/llm/{errors,base,openai,anthropic}.py;
backend/app/agents/{architect,generators/base,security/fix}.py;
backend/app/core/logging.py; backend/tests/unit/{test_phase9_provider_errors,
test_llm_base,test_eval_architect,test_security_fix}.py; this log;
docs/design-deviations.md (D-43).

**Decisions:** D-43. Preserve retry/deadline policy; retain only safe diagnostics,
not SDK exceptions. Existing successful-result schemas are unchanged. Suppress
provider transport logs. Use an isolated existing-image PostgreSQL container,
ordinary app/owner roles and explicitly dotenv-disabled verification settings.

**Tests:** make lint passed Ruff/format (183 files), mypy (98 sources), ESLint
and both TS projects. Initial focused suite: 192 passed, 1 failed due to the old
fix-reason expectation; corrected. Initial make test: 1115 passed, 1 failed,
6 perf deselected; its old evaluator category assertion was corrected. Final
focused suite: 204 passed, 0 failed, 0 skipped (2.42s). No real provider call, dotenv read or installation.

**Known gaps / follow-ups:** Full final suite repeats in section 8; tool building
follows section 1. No database migration or UI behavior change.


## 2026-10-13 — Phase 8c follow-up to item 2 — Settle approve/reject SSE provenance

**Summary:** Commit the late item 2 correction that resumes the closed SSE stream
after successful approve/reject decisions, recovering their label-origin events.
The author explicitly chose a separate follow-up commit; the seven existing
Phase 8c item commits are preserved without rebase or history rewriting. This
entry resolves the pending commit-packaging notes in the item 7 entry below.

**Requirements addressed:** FR-UI-07, FR-P-04.

**Files:** frontend/src/components/ReviewPanel.tsx;
frontend/src/screens/PackageScreen.tsx; frontend/src/screens/screens.test.tsx;
docs/design-deviations.md (D-37 clarification); docs/IMPLEMENTATION_LOG.md.

**What E2E caught:** Item 2's new archive/display-origin checks failed for both
approve and reject (initial suite: 4 passed, 2 failed). The automated run was
terminal and its pending-review stream had already settled closed. Those actions
refreshed results but did not restart SSE, so Download ZIP became available while
screen 4 displayed "unavailable (transition event not recorded)" instead of
"engineer decision". The backend had recorded the event; the browser had never
replayed it. Retry passed because its existing callback already reopened SSE.

**Why item 2 tests missed it:** readinessOrigin.test.ts supplied complete,
preloaded recorded event histories; review.test.tsx supplied origin strings as
props. Screen tests mocked the stream/results hooks and swapped pending/repaired
snapshots instead of executing an approve/reject action after a real stream
close. They proved origin selection and presentation with available events,
but did not prove decision-event delivery through the closed-stream lifecycle.

**Decisions / regression:** Successful approve/reject invokes onDecision, wired
to the existing stream.reconnect callback, before refreshing results. The store
resumes using its retained event cursor. Only retries invoke reopenRetry and
set the retry latch. Parameterized screen regressions start with state=closed,
exercise Approve and Reject → Confirm reject, assert the exact review request,
one reconnect, refreshed results and no retry latch. Dialog methods are stubbed
per instance solely for jsdom; native browser flows remain covered by E2E.
No endpoint/schema/setup change, new dependency, spec deviation or open question.
README needs no change for this follow-up.

**Tests:** Removing the decision-reconnect wiring temporarily made both new
regressions fail with an explicit reconnect-call assertion: 2 expected failures,
14 skipped (4.02s); source was restored in a finally path. Final ordinary checks:
make lint passed Ruff/format (182 files), mypy (98 sources), ESLint and both
strict TS projects; make test: 1088 passed, 0 failed, 0 skipped, 6 perf deselected
(139.68s); make frontend-test: 98 passed, 0 failed, 0 skipped in 14 files (8.72s).
The first lint attempt caught an unsupported test-only ByRoleOptions property;
it was removed before the passing final run. The corrected production code was
already verified by make test-e2e: 6 passed, 0 failed, 0 skipped (1.2m), including
both real decision-event origin assertions; it is unchanged since that run.
E2E was not repeated solely for the added Reject unit-regression case.
git diff --check passes.

**Known gaps / follow-ups:** No functional work remains after these checks and
the approved follow-up commit. No dotenv opened/printed/copied/modified, install,
real LLM call, push or change to pre-existing untracked REVISION.txt.

## 2026-10-13 — Phase 8c item 7 — Correct operator guidance and verify the polish

**Summary:** Correct the standing scanner names and make run's single-worker,
no-reload behavior. Cross-check current README commands and finish verification
of all seven polish items, leaving historical evaluation reports intact.

**Requirements addressed:** FR-UI-01..07, FR-P-04, FR-S-09, FR-S-10, NFR-01;
operator documentation consistency.

**Files:** AGENTS.md; README.md; backend/tests/unit/test_make_commands.py;
docs/IMPLEMENTATION_LOG.md. A late item 2 acceptance correction also updates
frontend/src/{components/ReviewPanel.tsx,screens/PackageScreen.tsx,
screens/screens.test.tsx} and docs/design-deviations.md (D-37).

**Decisions:** AGENTS names Checkov/Trivy and describes one FastAPI worker;
README explicitly says no automatic reload and documents the custom port/proxy.
The documentation regression checks actual scanner TOOLS plus operator guidance,
alongside the exact Make dry-run command. Existing Phase 8 verification counts
in README are historical evidence, explicitly labelled as such. No spec edit,
new deviation or open question; D-37/D-40 presentation clarifications are kept.

Final E2E found that approve/reject refreshed results but left the already-closed
SSE stream closed, so the new origin display lacked the decision event. Resume
SSE after those accepted actions, without setting the retry-only latch. A screen
regression and real approve/reject archive/display assertions prove recovery.
The verified correction is in the working tree; packaging it into item 2 or a
separate follow-up commit requires the author's choice under AGENTS section 9.

**Tests:** All required commands ran through ordinary Make invocations:

- `make lint`: passed Ruff, format (182 files), mypy (98 sources), ESLint and
  both strict TypeScript projects, including after the late frontend correction.
- `make test`: 1088 passed, 0 failed, 0 skipped, 6 perf deselected (112.32s).
  Backend source did not change after this run.
- Final `make frontend-test`: 97 passed, 0 failed, 0 skipped in 14 files (6.66s).
- Initial `make test-e2e`: 4 passed, 2 failed (4.2m), both from missing engineer
  decision events on screen 4. With accepted-decision SSE recovery: 6 passed,
  0 failed, 0 skipped (1.2m), including identical UI/ZIP origin assertions.
- `make frontend-build`: passed (142 modules; final build 241ms).
- Earlier focused backend archive/history checks and three prompt, expected
  reconnect mutation failures are recorded in the item entries above.

Manual global playwright-cli verification used installed Chromium, temporary
cache/profile/output paths and a persistent shell after default cache writes
failed. No installation was performed. A temporary localhost-only server served
the four untouched thesis PDFs for actual browser-rendered comparison. The built
FastAPI UI ran on PORT=8765 with dotenv-disabled stub/review test-role settings.
Input, progress, comparison and package screens match the fixed layout/tokens;
real events showed 3 clean and 2 valid / 1 invalid. The manual pending → feedback
retry → ready flow showed exactly one badge beside Download ZIP, no header badge,
and the correct automatic-after-engineer-retry origin. Pending/ready screens at
1440px and 1024px were inspected; no horizontal overflow, no application console
errors/warnings. Screenshots were temporary inspection artifacts, not fake data
or committed historical evidence. A manual Chromium ZIP download completed;
its readiness origin and repaired Terraform content were verified. Temporary
servers/browser were stopped and repository screenshot artifacts removed.
Final git diff --check passes.

**Known gaps / follow-ups:** Windows/PowerShell and Firefox execution are not
available here; custom-port runtime was verified on Linux/Chromium. The UI @perf
and backend perf suites were outside this prompt. The last SSE correction awaits
commit-packaging authorization; all code and verification are complete. No
dotenv opened/printed/copied/modified by the agent, installs, real LLM calls,
push, later-phase work or changes to pre-existing untracked REVISION.txt.

## 2026-10-13 — Phase 8c item 6 — Make the operator backend port configurable

**Summary:** Add PORT (default 8000) to make run and a process-environment
INFRAARCH_BACKEND_URL override for Vite's API proxy, with its existing default.

**Requirements addressed:** FR-UI-01; local tooling infrastructure.

**Files:** Makefile; frontend/vite.config.ts; frontend/playwright.config.ts;
frontend/src/test/tooling.test.ts; backend/tests/unit/test_make_commands.py
(added); README.md; docs/design-deviations.md (D-40); docs/IMPLEMENTATION_LOG.md.

**Decisions:** Document make run PORT=8765, changed FastAPI UI/API URLs and the
unchanged Vite browser URL. Include PowerShell proxy configuration. Vite keeps
envDir=false. E2E pins its existing 8000/5173 defaults so an operator's proxy
environment cannot route browser acceptance to another application. No new
dependency, schema, endpoint, spec deviation or open question.

**Tests:** Make dry-run default/override: 2 passed, 0 failed, 0 skipped (0.06s).
Frontend: 96 passed, 0 failed, 0 skipped in 14 files (4.74s); frontend lint and
strict TS pass. Proxy integration now exercises the configured environment
target against an ephemeral real HTTP backend instead of replacing target in
the test; a separate case proves default 8000 and dotenv-disabled config.

**Known gaps / follow-ups:** Actual custom-port startup and final suites follow
item 7. Windows itself is unavailable; PowerShell syntax is documented.

## 2026-10-13 — Phase 8c item 5 — Bound reconnect regression clients

**Summary:** EOF, cursor, sequence replay and network-backoff tests use finite
response lists, explicit open-count/final-state assertions and two-second bounds.

**Requirements addressed:** FR-P-04, FR-UI-02; verification infrastructure.

**Files:** frontend/src/api/sse.test.ts; docs/IMPLEMENTATION_LOG.md.

**Decisions:** Exhausting the fake response budget aborts its controller before
throwing, so streamRun's network-error handler cannot spin forever. Six opens
must end paused for unchanged EOF; ordered/recovery streams must end closed.
No production SSE behavior, spec deviation or open question changed.

**Tests:** Frontend lint/strict TS pass; full frontend suite: 95 passed, 0 failed,
0 skipped in 14 files (4.84s). Three temporary production mutations separately
removed the EOF cap, seq de-duplication and cursor advance. Each produced the
explicit six-opens assertion (7 actual calls), with 1 expected failed/18 skipped
in 975ms, 1.05s and 982ms respectively. Production source was restored in a
finally path; restored focused SSE suite passes all 19 tests. No worker hang.

**Known gaps / follow-ups:** Full Make checks follow item 7.

## 2026-10-13 — Phase 8c item 4 — Delay download Blob URL cleanup

**Summary:** Keep the download URL alive for one second after the synthetic
anchor click so browsers can start saving the response reliably.

**Requirements addressed:** FR-UI-06.

**Files:** frontend/src/api/client.ts and client.test.ts;
docs/IMPLEMENTATION_LOG.md.

**Decisions:** Schedule revocation in the existing finally path before removing
the temporary link. Both successful and throwing clicks schedule cleanup; the
link is removed immediately. No dependency, spec deviation or open question.

**Tests:** Frontend: 95 passed, 0 failed, 0 skipped in 14 files; frontend lint
and strict TypeScript pass. Fake-timer assertions prove no revocation at 999ms
and exactly one revocation at 1000ms for both click outcomes. Full Make checks
and real browser download verification follow item 7.

**Known gaps / follow-ups:** Firefox-specific execution is not requested; the
existing real-browser acceptance suite uses Chromium.

## 2026-10-13 — Phase 8c item 3 — Show one package readiness badge

**Summary:** Remove the duplicate readiness/status badge from screen 4's header
and place the single readiness badge beside Download ZIP in the action panel.

**Requirements addressed:** FR-UI-06, FR-UI-07.

**Files:** frontend/src/screens/PackageScreen.tsx and screens.test.tsx;
frontend/src/components/ReviewPanel.tsx; docs/design-deviations.md (D-40
presentation clarification); docs/IMPLEMENTATION_LOG.md.

**Decisions:** Reuse the existing action-row spacing, native download button,
status badge and muted provenance text. Pending review keeps its explicit
heading, reasons and engineer controls; accepted retries hide stale labels.
No new deviation or open question.

**Tests:** Frontend: 94 passed, 0 failed, 0 skipped in 14 files (4.71s).
Regression asserts exactly one badge, adjacency to download, a clean header
and clear pending review. Frontend lint/strict TS pass after removing a
test-only unsupported ByRoleOptions property. Full Make checks follow item 7.

**Known gaps / follow-ups:** Real browser layout verification follows item 7.

## 2026-10-13 — Phase 8c item 2 — Retain readiness provenance after review retries

**Summary:** ZIP readiness documents and screen 4 distinguish automatic labels,
automatic labels after engineer-requested retries, and approve/reject decisions.

**Requirements addressed:** FR-UI-06, FR-UI-07, FR-S-09, FR-S-10.

**Files:** backend/app/domain/archive.py; backend/app/db/repositories/results.py;
backend/app/pipeline/results.py; backend/tests/unit/test_archive.py;
backend/tests/integration/test_pipeline_download.py;
frontend/src/lib/readinessOrigin.ts and readinessOrigin.test.ts;
frontend/src/screens/PackageScreen.tsx; frontend/src/components/ReviewPanel.tsx
and review.test.tsx; frontend/e2e/{review-flow.spec.ts,support/flow.ts};
docs/design-deviations.md (D-37 clarification); docs/IMPLEMENTATION_LOG.md.

**Decisions:** Select review retries strictly before the label event, scoped to
run/variant; explicit label decisions win. Missing label events remain unavailable.
Frontend reads existing SSE history, rendering provenance beside the label in
the action panel. Reuse current muted typography and panel tokens. No new schema,
endpoint, database field, spec deviation or open question. E2E asserts identical
archive/display origin for retry, approve and reject.

**Tests:** Archive/download focused checks: 18 passed, 1 perf deselected; extended
download history checks: 9 passed, 1 perf deselected. Frontend: 93 passed,
0 failed, 0 skipped in 14 files; ESLint/strict TypeScript and backend Ruff pass.
Full suites and real-browser provenance checks follow item 7.

**Known gaps / follow-ups:** D-19's separately committed missing-event limitation
remains; provenance is derived only from retained event evidence.

## 2026-10-13 — Phase 8c item 1 — Preserve mixed stage outcomes

**Summary:** SecurityAgent and ValidatorAgent summaries count recorded outcomes
per variant instead of displaying the last completion's message.

**Requirements addressed:** FR-UI-02, FR-P-04, FR-V-05.

**Files:** frontend/src/lib/runReducer.ts and runReducer.test.ts;
docs/design-deviations.md (D-40 clarification); docs/IMPLEMENTATION_LOG.md.

**Decisions:** Use package transition statuses from SSE, retaining outcomes
across agent notices and clearing a variant's prior result when its next attempt
starts. Preserve stage badges, sequence correlation and the fixed visual tokens.
No new deviation or open question; no invented counts or API changes.

**Tests:** Frontend suite: 86 passed, 0 failed, 0 skipped (13 files, 5.13s).
Four mixed-outcome cases cover invalid/exhausted/error before the last success
and replacement after retries. Frontend ESLint/strict TypeScript pass after
correcting a test-only unused final increment. Full Make checks follow item 7.

**Known gaps / follow-ups:** Browser verification follows the remaining polish.

## 2026-10-13 — Phase 8b — Scope the verification bootstrap to explicit test children

**Summary:** Fix plain-shell `make test` failing before pytest because the Phase 8
Makefile disabled dotenv in its `migrate-test` prerequisite. Guard the bootstrap
with explicit opt-in and launch verification with configured test URLs, stub
defaults and empty LLM/API keys, while restoring normal operator settings.

**Requirements addressed:** NFR-01; verification infrastructure regression.

**Files:** Makefile; backend/scripts/run_verification.py (added);
backend/tests/bootstrap/sitecustomize.py;
backend/tests/unit/test_test_bootstrap.py;
backend/tests/unit/test_run_verification.py (added);
backend/tests/unit/test_eval_validation.py;
backend/tests/unit/test_scanner_timeout.py;
backend/tests/unit/test_trivy_scanners.py;
backend/tests/unit/test_validation_terraform.py;
frontend/playwright.config.ts; README.md; docs/design-deviations.md;
docs/IMPLEMENTATION_LOG.md.

**Decisions / confirmed cause:** The Makefile exported bootstrap PYTHONPATH for
`test test-perf migrate-test`; Make also inherited the stub/empty-value exports
from test targets into prerequisites. The unguarded sitecustomize disabled
Settings.model_config.env_file before Alembic instantiated settings. A fresh
subprocess with synthetic environment values reproduced dotenv_disabled=True
and exactly the four missing database fields, without reading the real dotenv.
Phase 8's explicitly exported test URLs masked this ordinary-shell failure.

The proposed venv-contamination hypothesis is ruled out here: plain venv Python
from both repository root and backend imported /usr/lib/python3.12/sitecustomize.py.
`python -m site` reported user-site disabled; the user site directory is absent.
All venv/user-site .pth/sitecustomize.py/usercustomize.py candidates were checked:
only the ordinary editable-install .pth exists, with no bootstrap reference.
No activation script or pyvenv.cfg references bootstrap/PYTHONPATH. Pytest's
pythonpath is only `.`; conftest's internal Alembic inherits its parent environment.
The E2E webServer and four isolated Python harnesses intentionally opt in now.
No venv file was modified; no cleanup command is needed.

INFRAARCH_TEST_BOOTSTRAP=1 is required before importing settings or mutating
environment in the bootstrap. Normal Make migrations, including test
prerequisites, receive no test overrides. The parent launcher uses the existing
get_settings() source behavior; only configured test database credentials are
forwarded, with ordinary URLs also mapped to test URLs. LLM/API credentials are
cleared and the child is executed with scoped PYTHONPATH/flag. No hardcoded URL,
runtime settings-source change, installed dependency, role/grant change or
later-phase feature. D-40 is corrected; D-41 is unchanged. No new deviation or
open question. README documents the parent/child distinction and direct E2E use.

**Tests:** Initial bootstrap regression: 2 failed, 2 passed, demonstrating the
unguarded startup bug. An intermediate focused run had 10 failed, 20 passed,
4 deselected because the new Make probe used multiline --eval syntax and the
temporary-file guard referenced argv after replacement; both test harnesses
were corrected. Bootstrap/launcher focused checks then passed 18 tests; two
command-usage checks and a subprocess secret-redaction check were subsequently
added, with all 8 launcher tests passing. Ordinary `make up` reported PostgreSQL
healthy. All required Make commands ran in the ordinary shell without exported
database URLs, bootstrap flag or PYTHONPATH overrides:

- `make lint`: passed Ruff, format (181 files), mypy (98 sources), ESLint and
  both strict TypeScript projects. Supplemental Ruff check/format also passed
  for the new launcher, which is outside Make's existing app/tests lint scope.
- Initial `make test`: 1076 passed, 0 failed, 0 skipped, 6 deselected (183.70s),
  before collection included the last subprocess canary regression. Final
  `make test`: 1077 passed, 0 failed, 0 skipped, 6 deselected (158.48s).
- `make test-perf`: 6 passed, 0 failed, 0 skipped, 1077 deselected (27.62s).
- `make frontend-test`: 82 passed, 0 failed, 0 skipped, 13 files (15.75s).
- `make test-e2e`: 6 passed, 0 failed, 0 skipped (2.1m); fresh test-role backend
  migration/startup, real scanner/mirror prerequisites, and all browser flows
  passed. The separately selected UI @perf test was outside the requested run.
- `git diff --check`: passed. Final venv-wide startup-file enumeration again
  found only the editable-install .pth, no sitecustomize.py/usercustomize.py.

The 20 new regression cases cover inactive/explicitly active startup, temporary
dotenv database loading, normal Make environments and prerequisite inheritance,
child-only test database selection, credential isolation, pytest/E2E execution,
command usage, and secret-free configuration failures (including fresh processes).

**Known gaps / follow-ups:** No production migration, server or real-provider
evaluation was executed; normal command environment/loader behavior is covered
by nine fresh-process Make probes and synthetic dotenv tests. The real root
dotenv was never opened, printed, copied or modified by the agent; normal
operator commands and the parent launcher may load it through existing settings
as required. No installs, real LLM calls, push, spec edits or changes to the
pre-existing untracked REVISION.txt.

## 2026-10-13 — Phase 8 section 9 — Audit completed scope and protected files

**Summary:** Finish the documentation-only audit of sections 0–9, approved backend
exceptions, dependency/manifest checkpoint, commit order and actual verification.
Phase 8 is complete; no later-phase runtime work is included.

**Requirements addressed:** FR-UI-01..07, FR-P-04, UC-08, PR-02, NFR-01; scope audit.

**Files:** docs/evals/phase8-ui-20261012T204423Z/scope-audit.md;
docs/IMPLEMENTATION_LOG.md. Documentation only.

**Decisions:** Read-only diffs/AST checks show unchanged pipeline API route
signatures, database/models/repositories/applied migrations, domain state rules
and docs/spec. The only results-schema delta is required retry_in_progress.
All 22 manifest pins match installed lock entries and the publish-date record;
lock unchanged since section 1. REVISION.txt remains untracked and untouched.
The approved cancellation fix is confined to read/cleanup shields, with required
red/green, short-bound cancellation and same-pool full-pipeline evidence (D-40).
No accounts/history/mobile/i18n/UI library/framework/fonts/new pipeline endpoint,
extra install, dotenv read, real LLM call, push or history rewrite. No new open
question. Section commits/logs follow 0 → 1 → 5 → 2 → 3 → 4 → 6 → 7 → 8 → 9.

**Tests:** Documentation only; no rerun of unchanged code. Latest actual results:
make lint/build passed; pytest 1057 default passed, 6 perf deselected; perf 6
passed, 1057 deselected; Vitest 82 passed; default E2E 6 passed; final @perf 1
passed. PR-02 saved 32 live samples: max 663ms, median 165.5ms. Cancellation suite
10 passed after original 3 failures/2 passes. Read-only dependency/lock/route/
protected-file audits and git diff --check pass. Visual evidence links all four
real screens and 1024px checks. Earlier failures remain documented.

**Known gaps / follow-ups:** Phase 9 final performance measurements are out of
scope. Collected thesis wording awaits author edits; docs/spec remains unchanged.



## 2026-10-13 — Phase 8 section 8 — Document the completed frontend and thesis updates

**Summary:** Update project status/setup and the exact results field list; collect
thesis changes for counts, annotation sources, validation tabs, Node/stack versions
and PR-02 methodology. Preserve all approved direct pins and UTC publish dates
alongside the completed visual/test evidence.

**Requirements addressed:** FR-UI-01..07, FR-P-04, UC-08, PR-02, NFR-01.

**Files:** README.md; docs/design-deviations.md; docs/IMPLEMENTATION_LOG.md;
docs/evals/phase8-ui-20261012T204423Z/dependency-pins.md.

**Decisions:** D-39/D-40/D-41 describe implemented behavior; D-36 explicitly marks
the Phase 8 fetch client implemented, and D-33 already records unconditional stub
models. D-40 retains the sole results-schema addition and approved cancellation
scope exception. Node thesis wording is “Node.js 22.22 or later (developed on Node
24 LTS)”; operational minimum stays 22.22.2. Comparison counts and file-linked
annotations use retained evidence, never invented scores/rules. PR-02 uses live
UTC-event-to-DOM sequence correlation, including multiple observer mutations,
with historical replay excluded. docs/spec remains unchanged.

**Tests:** Documentation cross-checked against package.json/package-lock.json,
results schema, test commands and saved PR-02 JSON. No runtime change since section
7: make lint/build passed; Vitest 82 passed; pytest default 1057 passed (6 perf
deselected), perf 6 passed (1057 deselected); Playwright default 6 passed, final
perf 1 passed; 32 PR-02 samples, max 663ms and median 165.5ms. No tests rerun solely
for prose. git diff --check passes.

**Known gaps / follow-ups:** Section 9 scope audit follows. Thesis sources are
collected for author edits, not modified. Final performance evaluation is Phase 9.



## 2026-10-13 — Phase 8 section 7 — Verify thesis layouts and repair SSE disconnect cleanup

**Summary:** Compare all four real screens with the mockup PDFs through global
playwright-cli; save final 1440×900 and 1024px evidence. Fix layout/timing details,
shared stream ownership and accepted-retry presentation. Repair a backend bug
found by Phase 8 browser reload under an explicitly approved scope exception.

**Requirements addressed:** FR-UI-01..07, FR-P-04, UC-08, PR-02, NFR-01.

**Files:** frontend/src/components/{StageCard,LiveLog,FileTree,ReportPanel,ReviewPanel};
screens/{ProgressScreen,ComparisonScreen,PackageScreen}; hooks/useRunStream;
lib/{runReducer,runStreamStore,fileTree} and tests; screen/review tests;
styles/global.css, index.html, public/favicon.svg; playwright.config.ts,
e2e/support/testDatabase.ts and its unit tests; backend/app/api/pipeline.py,
backend/tests/integration/test_pipeline_sse.py; .interface-design/system.md;
docs/evals/phase8-ui-20261012T204423Z/, docs/design-deviations.md and this log.

**Decisions:** D-40 records the backend cause and author-approved exception.
StreamingResponse's level-triggered disconnect cancellation interrupted database
reads/session cleanup, allowing a closed asyncpg connection to reach another
pipeline borrower. Shield only replay/close-check reads and cleanup, never yields
or live/keep-alive waits. A resource-lease microtask transfers frontend stream
ownership across navigation/StrictMode without delaying accepted event commits;
an accepted-retry latch prevents stale snapshots restoring review controls.
Directory rows derive only from returned paths. Generator states follow the
horizontal mockup layout; compact log fits the full viewport. Stage activity
uses the union of timestamp intervals, excluding review gaps and concurrent
double counting. Reuse Intl.DateTimeFormat; fix singular fix-count copy. E2E
accepts the exact test database and ordinary app/owner roles, never URL substrings.

**Tests:** Required red run on unchanged backend: 3 cancellation tests failed,
2 cancellation-bound tests passed (12.37s). With the fix: all 10 SSE tests passed
(14.83s); strengthened 60-second keep-alive watchdog suite: 10 passed (31.13s).
Every canceled-read case verifies no checked-out connection and a complete
successful three-package stub pipeline on the same pool. make test: 1057 passed,
0 failed, 0 skipped, 6 deselected (196.01s). make test-perf: 6 passed, 0 failed,
0 skipped, 1057 deselected (30.38s). Initial concurrent-load perf attempt had
5 passed/1 PR-04 timing failure (2.412591s > 2s); isolated reruns passed without
weakening thresholds. Final make lint passes Ruff/format (180 files), mypy
(98 sources), ESLint and both strict TS projects; frontend build passes.
Vitest: 82 passed, 0 failed, 0 skipped in 13 files (13.59s). Default Playwright:
6 passed (2.4m); final @perf: 1 passed (28.6s), 32 live samples, max 663ms,
median 165.5ms. Earlier PR-02 max/median: 1134/275.5ms failed; 949/305ms and
726/242.5ms passed. No latency threshold changed. Earlier active-reload attempts
failed from the diagnosed backend bug; final reload and full flow pass.
Manual repair preserves baseline/run history; downloaded ZIP content and readiness
document verified. All four 1024px layouts checked; built FastAPI SPA renders
under CSP with 0 console errors/warnings. Screenshots use real stub/API data.

**Known gaps / follow-ups:** Final performance measurements remain Phase 9.
Section 8 documentation and section 9 documentation-only audit follow. No new
endpoint, migration or dependency; no further install, dotenv read, real model
call, spec edit, push or change to untracked REVISION.txt.




## 2026-10-12 — Phase 8 section 6 — Add acceptance checks and dotenv-disabled verification

**Summary:** Add real-backend Playwright flows for retry/approve/reject, complete
labelled ZIP content, reload/submission guard, key reentry and keyboard review.
Add the separately selected PR-02 observer and permanent Python verification
bootstrap. Harden protocol validation, snapshot ordering and long-text display.

**Requirements addressed:** FR-UI-01..07, FR-P-04, UC-08, NFR-01, PR-02.

**Files:** frontend/playwright.config.ts; frontend/e2e/*.spec.ts and
support/flow.ts/prerequisites.ts; src/api/sse.ts/contract tests;
src/lib/runStreamStore.ts and reducer/presentation tests; App.tsx;
components/{RunNotice,LiveLog,StageCard,StatusBadge,WindowedRows.test,review.test};
styles/global.css; backend/tests/bootstrap/sitecustomize.py and its unit test;
unit scanner/validator/evaluator subprocess tests; Makefile, README.md,
docs/design-deviations.md and this log.

**Decisions:** Every E2E submission explicitly requests stub. Fresh servers have
stub/review defaults and a test-only API key, with one backend process/worker.
Reuse is disabled because existing health data cannot verify provider/scenario
configuration. Real scanner/Terraform/provider-mirror requirements are checked,
not weakened. Python dotenv is disabled before settings instantiate, including
migration and isolated subprocesses. Explicit test URLs supply omitted ordinary
URLs; Make test targets force stub/empty-key defaults while canary tests retain
in-process overrides. PR-02 reconstructs every sequence mutation in a callback
using subsequent oldValue records, excludes historical reload replay, and writes
max/median/samples to test-results/pr02.json. No API polling or event batching.

**Tests:** Vitest 69 passed, 0 failed, 0 skipped in 14.56s. make lint passed Ruff,
format (180 files), mypy (98 sources), ESLint and strict TypeScript projects;
frontend build passed. Playwright discovery: 6 default, 1 @perf, selected correctly.
Actual default E2E: 6 failed at browser launch; @perf: 1 failed at browser launch.
Both commands started the configured backend/Vite and passed tool/mirror/DB
prerequisites, but no browser test body ran: installed Chromium is missing
libnspr4/libnss3/libnssutil3/libsmime3/libasound. No latency samples were produced.
Final make test: 1052 passed, 0 failed, 0 skipped, 6 deselected in 279.90s.
make test-perf: 6 passed, 0 failed, 0 skipped, 1052 deselected in 31.40s. Initial bootstrap
regression: 1051 passed, 1 failed, 6 deselected in 307.09s, due solely to the old
module-cache assertion; evaluator import guard and bootstrap focused checks then
passed (2 tests), and explicit-test-URL bootstrap check passed (1 test). One
component typing loop exceeded the default 5s test timeout under concurrent load;
replace it with direct input for its request-body assertion, then 69 tests pass.

**Known gaps / follow-ups:** Browser E2E, PR-02 latencies, manual flow and screenshots
remain unverified until the author supplies Chromium system libraries. No browser
or package installation, dotenv read, real LLM call, push or migration. Section 7
visual work and subsequent documentation/audit completion remain pending.


## 2026-10-12 — Phase 8 section 4 — Serve optional frontend build from FastAPI

**Summary:** Mount local assets and register the SPA fallback after existing routes.
Missing dist keeps API-only behavior. Apply CSP/nosniff/no-referrer only to UI
responses, with secure path resolution and missing-asset handling.

**Requirements addressed:** FR-UI-01, FR-UI-03, FR-UI-04, NFR-01.

**Files:** backend/app/api/frontend.py, backend/app/main.py;
backend/tests/unit/test_frontend_serving.py and test_app.py;
backend/tests/integration/test_canary.py and test_pipeline_auth.py; README.md, docs/design-deviations.md,
and this log.

**Decisions:** D-40 records serving and the internal temporary-dist override.
The fallback declines /api at routing time for every HTTP method, preserving
unknown API 404 responses. Tests that add synthetic failure routes explicitly
use absent dist so developer builds cannot intercept their canary assertions.

**Tests:** Serving-focused suite: 19 passed in 1.09s; app/serving initial focused
suite: 19 passed in 20.35s. make lint passed Ruff/format (178 files), mypy
(98 sources), ESLint and both TypeScript projects. Frontend unchanged since
62 passing unit/component tests. Full regression before both synthetic-route overrides: 1046 passed, 2 failed,
6 deselected in 245.06s. Both failures were SPA interception of synthetic test
routes, corrected with missing-dist overrides. A focused rerun was started while
a helper signature edit was incomplete (28 passed, 5 failed); corrected and
rerun: 33 passed, 0 failed in 19.62s. The next full regression also covers the
permanent test bootstrap.

**Known gaps / follow-ups:** Browser acceptance still needs the author's system
libraries. No install, dotenv read, real LLM call, migration or dependency change.


## 2026-10-12 — Phase 8 section 3 — Build four thesis screens and review controls

**Summary:** Implement input, progress, comparison and package routes with native
controls and the fixed design tokens. Add URL-backed variant/file selection,
windowed logs/diffs/file lists, report tabs, authenticated recovery and review.

**Requirements addressed:** FR-UI-01..07, FR-P-04, PR-02, UC-08, NFR-01.

**Files:** frontend/src/screens/, components/, constants/; src/lib/diff.ts,
reportView.ts, reviewReasons.ts and presentation.test.ts; App.tsx/App.test.tsx,
src/styles/global.css, src/test/setup.ts; docs/design-deviations.md and this log.

**Decisions:** D-39 documents real blocking counts and evidence-linked annotation.
Validation-only fixes do not invent security rule IDs. sessionStorage guards
submissions across reload, real code-point counting matches backend limits, empty
config fields are omitted and incomplete input reaches server validation. Retry
202 explicitly reopens the stream. Native dialog confirms rejection; report tabs
support arrows/Home/End, controls have names and untrusted content is text.

**Tests:** Frontend lint and build passed; Vitest 62 passed, 0 failed, 0 skipped.
make lint passed Ruff/format (176 files), mypy (97 sources) and frontend checks.
Most recent make test: 1032 passed, 6 deselected (section 2, backend unchanged).
Tests cover loading/errors/empty results, active submission/reload guard, config,
missing variants, file selections, safe rendering, report status distinction,
review/download exclusivity, five-file picker, in-flight exclusion and API-key
reentry. Initial run had 57 passing tests, one focus failure and one Node setup
failure, corrected before the passing suite.

**Known gaps / follow-ups:** CLI browser launch was attempted with the author's
Chromium 1.63.0; it cannot launch because libnspr4/libnss3/libnssutil3/libsmime3/
libasound are missing in this environment, verified outside the sandbox as well.
The author was asked to install system prerequisites; no package/browser/install
scripts were run. Visual and E2E checks remain for sections 6–7. Serving follows.


## 2026-10-12 — Phase 8 section 2 — Implement results contract and resumable streaming

**Summary:** Add the sole approved results field retry_in_progress, derived directly
from the persisted retry marker. Implement typed authenticated API access, safe
errors and downloads, UTF-8 SSE framing, immediate reducer updates, shared streams,
resume/backoff, EOF snapshot settlement and disposal guards.

**Requirements addressed:** FR-P-04, FR-UI-02, FR-UI-07, PR-02, NFR-01.

**Files:** backend/app/api/schemas.py, backend/app/pipeline/results.py,
backend/tests/integration/test_pipeline_results.py and test_pipeline_demo_scenario.py;
frontend/src/api/, src/hooks/, src/lib/, src/test/fixtures/;
frontend/e2e/support/recordFixtures.ts; docs/design-deviations.md and this log.

**Decisions:** D-40 implements the required boolean without a migration or timestamp
exposure; D-36 marks fetch SSE implemented. Record actual stub/review responses
and SSE using installed offline scanners and Terraform, including pending/repaired
history. Normal EOF closes only after the exact approved snapshot predicate. Five
EOF reconnect attempts without a unique event precede manual recovery; failed
snapshots cannot settle. Resume advances only after accepted events. Disposed
stores abort readers/waits and ignore stale snapshots.

**Tests:** make lint passed Ruff/format (176 files), mypy (97 sources), ESLint and
both strict TypeScript projects. make frontend-test: 36 passed, 0 failed, 0 skipped
in 8.06s. make test: 1032 passed, 0 failed, 0 skipped, 6 deselected in
259.63s. Coverage
includes framing/chunk boundaries, marker-only activity, duplicates/gaps, resume,
EOF cap/reset, errors, cancellation, shared consumers, stale runs, every recorded
event kind, contract fields, header auth/401, review bodies and Blob cleanup.

**Known gaps / follow-ups:** Screens, serving and browser acceptance follow in
sections 3, 4 and 6. No additional installation, dotenv read or real LLM call.

## 2026-10-12 — Phase 8 section 5 — Add deterministic validation-review scenario

**Summary:** Add clean/review pipeline demo selection, security-only built-in
validation failure and a dedicated fixer returning the real FixOutput shape.
Review retry follows existing persistence, scan and validation paths.

**Requirements addressed:** FR-I-04, FR-V-01, FR-S-08, FR-S-09, FR-UI-07, NFR-01.

**Files:** backend/app/core/config.py, backend/app/pipeline/demo_stub.py,
backend/app/agents/factory.py, backend/app/main.py, .env.example,
backend/tests/unit/test_config.py, backend/tests/unit/test_pipeline_demo_stub.py,
backend/tests/integration/test_pipeline_demo_scenario.py, README.md,
docs/design-deviations.md and docs/IMPLEMENTATION_LOG.md.

**Decisions:** D-41 records terraform.local_ref at terraform/main.tf:4 and
nonce-delimited fix targeting. Ordinary evaluation/spike stubs and clean demo
files remain unchanged. Real runs, including real runs with a stub fixer, ignore
the scenario. Startup warns for a real default provider. No state-rule, scanner
policy, schema, dependency or migration change. Failure detection needs only
built-ins; complete readiness retains existing offline-tool prerequisites.

**Tests:** make test: 1029 passed, 0 failed, 0 skipped, 6 deselected in 242.70s.
make lint passed Ruff/format (176 files), mypy (97 sources) and frontend lint.
make frontend-test: 3 passed, 0 failed, 0 skipped in 6.36s. Initial focused
checks: 52 passed, 3 failed due to a test-only missing RetryPolicy constructor
configuration; corrected before the passing full suite. Integration proves
retry readiness, unchanged other variants/run, preserved baselines and audit
sessions; unit tests cover both scenarios, all variants, failure-linked repairs,
feedback isolation, settings validation and non-stub isolation. Test database
uses the existing dotenv-disabled bootstrap and normal PostgreSQL roles/grants.

**Known gaps / follow-ups:** Real-tool/demo browser verification follows with
contract fixture capture and E2E. No dotenv read, real LLM call, install, push or
browser download. No new open question. Section 2 is next.

---

## 2026-10-12 — Phase 8 section 1 — Install and scaffold the pinned frontend

**Summary:** After explicit manifest confirmation, perform the one approved
npm install and commit its lockfile. Add the minimal React shell, strict
TypeScript projects, flat ESLint, Vitest, Vite API proxy, fixed design tokens
and root Make targets. Update the standing stack line and setup documentation.

**Requirements addressed:** NFR-01; otherwise infrastructure preparing the
Phase 8 UI, with no pipeline screen behavior claimed yet.

**Files:** added frontend/package.json, frontend/package-lock.json,
frontend/index.html, frontend/vite.config.ts, frontend/tsconfig.json,
frontend/tsconfig.node.json, frontend/eslint.config.mjs,
frontend/src/main.tsx, frontend/src/App.tsx, frontend/src/App.test.tsx,
frontend/src/styles/tokens.css, frontend/src/styles/global.css,
frontend/src/test/setup.ts and frontend/src/test/tooling.test.ts;
removed frontend/.gitkeep; changed AGENTS.md, .gitignore, Makefile, README.md,
docs/design-deviations.md and docs/IMPLEMENTATION_LOG.md.

**Decisions:** D-40 records the approved stack, Node requirement, TypeScript
compatibility exception, two additional dev dependencies and the remaining
delivery/stream contract. No new open question. Use Node 24.21.0 LTS and npm
11.19.0, with package engines >=22.22.2. Keep the heading-only shell honest;
pipeline screens remain section 3. Vite envDir=false disables dotenv loading;
the /api proxy uses loopback port 8000. Keep color-scheme: dark in external CSS
to support section 4's self-only CSP. Copy all existing colour/token values
and system fonts. Subsequent installs use npm ci --ignore-scripts. The planned
retry_in_progress schema addition is recorded in D-40 but deferred to section 2.

**Installed exact versions:** runtime react 19.3.0, react-dom 19.3.0,
react-router 8.4.0, diff 9.0.0. Development @eslint/js 10.0.1,
@playwright/test 1.63.0, @testing-library/dom 10.4.2,
@testing-library/jest-dom 7.0.1, @testing-library/react 16.3.3,
@testing-library/user-event 14.6.7, @types/node 24.19.0, @types/react 19.3.0,
@types/react-dom 19.3.0, @vitejs/plugin-react 6.1.1, eslint 10.11.0,
eslint-plugin-react-hooks 7.1.1, globals 17.12.0, jsdom 30.1.1,
typescript 6.0.3, typescript-eslint 8.71.0, vite 8.3.1, vitest 5.0.2.
All 22 direct versions match the confirmed manifest and lockfile. diff ships
types; @types/diff was not installed. The transitive graph is locked separately.

**Tests:** The single npm install --save-exact --ignore-scripts added 241
packages and audited 242, reporting zero vulnerabilities. No installation
script was enabled to repair tooling. npm ls --depth=0 confirms every pin;
the local Vite and Playwright executables report 8.3.1 and 1.63.0.
make frontend-test: 3 passed, 0 failed, 0 skipped across 2 files in 8.37s.
Tests prove the app landmark/title, keyboard-reachable skip link, and real
local dev-server proxy preservation of path, query, method, API-key header
and request body. make frontend-build passed, including both strict tsc
projects, transforming 17 modules with Vite in 1.36s. make lint passed backend
Ruff/format (175 files), mypy (97 source files), frontend ESLint and both tsc
checks. make test: 1015 passed, 0 failed, 0 skipped, 6 deselected in 239.51s.
Backend tests use the existing temporary dotenv-disabled bootstrap, isolated
PostgreSQL 16.14 from the existing image and normal roles/migrations/grants.
Make target dry-runs and git diff --check passed. Performance tests were not
rerun: section 0 recorded 6 passed. No Playwright browser/E2E test was run.

**Known gaps / follow-ups:** No .env read, real LLM call, push or browser
download. The author installs Chromium using the pinned local Playwright
before the later browser/E2E sections. API/SSE, pipeline screens, FastAPI
serving, E2E configuration, PR-02 timings and visual screenshots remain
pending. Next in the approved order is section 5, the deterministic review
scenario. Untracked REVISION.txt remains untouched.

---

## 2026-10-12 — Phase 8 section 0 — Normalize stub provenance and separate timing checks

**Summary:** Resolve model `stub` for every stub provider, including configured
and explicit real model names. Separate the existing wall-clock assertions
into a `perf` suite while keeping structural concurrency, download and process
cleanup coverage in the default suite.

**Requirements addressed:** FR-I-04, FR-G-01, FR-P-04, FR-UI-06, FR-S-01,
FR-S-02, FR-V-05, NFR-01, PR-03, PR-04.

**Files:** changed Makefile, README.md, backend/pyproject.toml,
backend/app/domain/run_config.py,
backend/tests/unit/test_run_config.py,
backend/tests/unit/test_llm_factory.py,
backend/tests/unit/test_agent_factory.py,
backend/tests/unit/test_eval_architect.py,
backend/tests/unit/test_scanner_timeout.py,
backend/tests/integration/test_pipeline_api.py,
backend/tests/integration/test_pipeline_download.py,
docs/design-deviations.md and docs/IMPLEMENTATION_LOG.md.

**Decisions:** Extend D-33; historical rows remain unchanged and real-provider
model overrides still reach the agents. Both generated and fixing stub adapters
use the centralized domain resolution. `make test` excludes `perf` and
`make test-perf` selects it. Three blocked Architect calls prove overlap before
an explicit release, without sleeps or relative timing. The default 10 MB ZIP
test checks every generated name and file content plus readiness metadata.
Scanner/validator structural tests retain deadlines, descendant termination
and temporary-directory cleanup; only the eight-second performance assertion
moves to `perf`. The outer deadlock watchdog is 30 seconds. Timing thresholds
are unchanged; final measurements remain Phase 9 work on a quiet machine.

**Tests:** Focused default checks: 90 passed, 0 failed, 0 skipped, 6 deselected
in 43.54s, before adding two real-provider override spy cases. Final `make test`:
1015 passed, 0 failed, 0 skipped, 6 deselected in 201.36s. `make test-perf`:
6 passed, 0 failed, 0 skipped, 1015 deselected in 29.21s; one existing
`record_property` warning from requesting xunit2 JUnit output. `make lint`:
Ruff check and format passed (175 files); mypy passed (97 source files).
`git diff --check` passed. Verification used the existing temporary
dotenv-disabled bootstrap and an isolated PostgreSQL 16.14 container from the
already available postgres:16 image, with the ordinary initialization script,
migrations, roles and grants. No dependency installation was performed.

**Known gaps / follow-ups:** Paid-model behavior was not exercised. No `.env`
read, real LLM call, push, migration edit or historical-row rewrite. No new open
question. Section 1 next writes only the approved pinned package.json and pauses
for the author's explicit confirmation before installation or further setup.
The results `retry_in_progress` field belongs to section 2; the AGENTS.md stack
update belongs to the remainder of section 1. Frontend checks, PR-02 measurement
and visual screenshots have not started. Untracked REVISION.txt remains untouched.

---

## 2026-10-10 — Phase 7b — Correct provider-scoped model provenance

**Summary:** Centralize model selection in RunConfig.resolve so a stub provider
override records `stub`, while a different real provider requires an explicit
model. Scope deployment fixer overrides to the configured provider, and force
stub runs to use a stub fixer with model `stub` without building network adapters.

**Requirements addressed:** FR-I-04, FR-S-02, FR-UI-06, NFR-01.

**Files:** backend/app/domain/run_config.py, backend/app/llm/factory.py,
backend/app/agents/factory.py, backend/app/api/pipeline.py,
backend/app/pipeline/demo_stub.py, backend/scripts/eval_architect.py,
backend/scripts/eval_generators.py, backend/scripts/eval_security.py,
backend/tests/unit/test_run_config.py, backend/tests/unit/test_llm_factory.py,
backend/tests/unit/test_agent_factory.py,
backend/tests/unit/test_eval_architect.py,
backend/tests/unit/test_eval_generators.py,
backend/tests/unit/test_eval_security.py,
backend/tests/integration/test_pipeline_api.py, README.md,
docs/design-deviations.md, docs/IMPLEMENTATION_LOG.md.

**Decisions:** Extend D-33 to document provider-scoped fixer settings and the
FR-I-04 exception to inheriting model defaults across providers. Keep normal
and same-provider inheritance, including explicit model selections. Resolve
the unconfigured stub default once in the domain; the API and adapter factory
consume that resolution. Preserve the resolved generation model when wrapping
adapters with the pipeline demo stub. Fixing metadata comes from the actual
fixer adapter; security evaluations use reported metadata and leave a missing
historical fixing model unknown instead of guessing from current settings.
Results and ZIP readiness already consume the persisted run model and require
no fallback. No migration or historical-row rewrite.

**Tests:** `make test`: 997 passed, 3 failed, 0 skipped in 532.46s. All 29 new
Phase 7b regressions and the NFR-01 secret canary tests passed. Added provider/default/explicit-model
resolution coverage, exact 400/no-row rejection, adapter spies forbidding
network construction for stub runs, hybrid and non-configured-provider fixer
regressions, full stub row/results/report/readiness checks, and evaluation
provenance checks. Initial focused run: 78 passed, 1 failed, 0 skipped; the
existing PR-03 wall-clock concurrency assertion exceeded its threshold.
Focused security evaluation and unchanged PR-03 rerun: 10 passed, 0 failed,
0 skipped in 45.67s. After correcting a mypy annotation, `make lint` passed
Ruff/format (175 files) and mypy (97 source files); the three edited evaluation
scripts also passed explicit Ruff/format checks.
The full-suite failures are unchanged timing assertions:
`test_three_runs_overlap_and_keep_events_isolated` (6.374948s parallel versus
3.821117s solo, exceeding 1.5x),
`test_ten_megabyte_package_download_under_two_seconds` (2.963147s), and
`test_timeout_kills_forked_stdout_owner[validator]` (the harness's elapsed-time
assertion, after the validation deadline result passed). An isolated extraction
of the pre-change HEAD, using the same existing dependencies and test database,
ran those three tests: 2 passed, 1 failed, 0 skipped in 64.35s; PR-04 also
failed there at 3.967157s. The PR-03 and validator cases fluctuate between runs.
No unrelated timing thresholds or scanner/validator behavior were changed.

**Known gaps / follow-ups:** Runs stored before this fix, submitted with a
provider override, may carry the configured deployment model name; they are
intentionally not rewritten. Manual paid-model behavior was not exercised.
The full test suite is not green in this environment due to the three timing
assertions above; investigate performance separately from this provenance fix.
No installs, dotenv reads, real LLM calls, push, or frontend changes. Tests use
the existing dotenv-disabled bootstrap and an isolated PostgreSQL 16 container
from the already available image. Untracked REVISION.txt and the existing ZIP
remain untouched. Re-run the manual demo with a new stub submission.

---

## 2026-10-10 — Phase 7 section 7 — Audit final Phase 7 scope and evidence

**Summary:** Complete the final scope audit and record the implementation outcome for all prompt sections 0–7. No further code changes.

**Requirements addressed:** FR-UI-06, FR-UI-07, FR-S-08, FR-S-09, FR-S-10, NFR-01, PR-04.

**Files:** docs/IMPLEMENTATION_LOG.md.

**Decisions:** Sections 0–4 implement the Helm follow-ups, results, review/recovery, ZIP and authentication; section 5 adds acceptance coverage; section 6 documents the contract and thesis changes; section 7 audits scope. No frontend, accounts/sessions, security-policy, unrelated prompts/checks, retention or run-classification work. No dependency/spec/applied-migration edits. The extra factory/ValidatorAgent/orchestrator/EventLog integration paths beyond the initial inventory only provide the approved persistence redaction; fix-order tests protect existing automated behavior. Deployment plan comes from latest plan_created payload; startup selects review_retry_started_at IS NOT NULL independently of run status. D-36/D-37/D-38 documented, OQ-09 resolved, OQ-01 remains deferred.

**Tests:** Final make test: 971 passed, 0 failed, 0 skipped in 91.96s. Final make lint: Ruff and format passed (175 files); mypy passed (97 source files). Explicit watcher Ruff, format and py_compile passed. Full ASGI PR-04: 0.626244s for 10,000,000 source bytes. git diff --check passed. AST comparisons confirm classify_run, readiness_after_validation and delete_expired unchanged.

**Known gaps / follow-ups:** Phase 9 still needs the curl-based PR-04 measurement; static validation does not prove deployability (D-35). A missing terminal event yields fixed unavailable label time/provenance (D-19). Apply migration 0003 before starting the backend. No installs, dotenv reads, real LLM calls, push or history rewrite occurred. REVISION.txt remains untouched and untracked. Eight section commits complete Phase 7; Phase 8 frontend is the suggested next implementation step.

---

## 2026-10-10 — Phase 7 section 6 — Document review APIs and thesis updates

**Summary:** Document all endpoint examples, exact results fields, optional header authentication, fetch-based SSE, migration-before-startup, timestamp recovery, deterministic label provenance and compression. Retain make sweep documentation.

**Requirements addressed:** FR-UI-06, FR-UI-07, FR-S-08, FR-S-09, FR-S-10, NFR-01, PR-04.

**Files:** README.md, docs/IMPLEMENTATION_LOG.md, docs/design-deviations.md.

**Decisions:** D-36/D-37/D-38 and OQ-09 resolved. OQ-01 explicitly defers 410, keeping 404. Thesis notes include ERD: new column review_retry_started_at, review targets/422 codes, terminal-run gating, review-only state arrows, X-API-Key and readiness files. Correction to the section 1 generic Files entry: backend/app/api/pipeline.py, backend/app/api/schemas.py, backend/app/core/safety.py, backend/app/db/repositories/results.py, backend/app/domain/review.py, backend/app/pipeline/results.py, backend/tests/integration/test_pipeline_results.py, backend/tests/unit/test_review.py, docs/IMPLEMENTATION_LOG.md and docs/design-deviations.md.

**Tests:** No code changes in this section. Verified documentation against final implementation/OpenAPI tests; final make test was 971 passed, 0 failed, 0 skipped in 91.96s, and make lint passed. Final PR-04: 0.626244s for the full ASGI 10 MB response. git diff --check passed.

**Known gaps / follow-ups:** Remaining Phase 7 acceptance/documentation follows. No installs, dotenv reads or real LLM calls; no push.

---

## 2026-10-10 — Phase 7 section 5 — Complete Phase 7 acceptance checks

**Summary:** Extend deterministic acceptance coverage for shared variant capacity, shutdown/launch settlement, retry exhaustion, scan automatic retry, canonical redacted reports, strict OpenAPI fields, migration upgrade/downgrade with existing rows and archive collision fallbacks.

**Requirements addressed:** FR-S-02, FR-S-08, FR-S-09, FR-S-10, FR-UI-06, FR-UI-07, FR-P-04, NFR-01, PR-03, PR-04.

**Files:** backend/app/agents/security/agent.py, backend/app/agents/validator.py, backend/app/api/pipeline.py, backend/tests/integration/test_pipeline_auth.py, backend/tests/integration/test_pipeline_results.py, backend/tests/integration/test_pipeline_review.py, backend/tests/integration/test_pipeline_sse.py, backend/tests/integration/test_review_recovery.py, backend/tests/unit/test_archive.py, backend/tests/unit/test_migration_parity.py, backend/tests/unit/test_security_concurrency.py, docs/IMPLEMENTATION_LOG.md.

**Decisions:** Preserve ordinary automated sorted fix calls while review starts use category order. Sanitize reports before persistence, then restore canonical ordering so redaction cannot cause an otherwise valid report to abort. Migration subprocesses inherit the dotenv-disabled bootstrap and explicit app/owner test URLs; the Phase 6b connection guard remains unchanged. Prior full runs passed 967 and 968 tests before the last coverage additions.

**Tests:** Final dotenv-disabled make test: 971 passed, 0 failed, 0 skipped in 91.96s. make lint: Ruff/format passed (175 files); mypy passed (97 source files). Explicit watcher Ruff, format and py_compile passed. Focused final edge checks: 20 passed in 13.73s; ordering/retry checks: 7 passed in 6.64s. Final PR-04 full ASGI response: 0.626244s for 10,000,000 persisted source bytes (JUnit property 0.6262435829994502), excluding fixture preparation. Verification used PYTHONPATH=/tmp/phase6b-test-bootstrap:$PWD/backend and JUnit reporting; no dotenv loading.

**Known gaps / follow-ups:** Remaining Phase 7 acceptance/documentation follows. No installs, dotenv reads or real LLM calls; no push.

---

## 2026-10-10 — Phase 7 section 4 — Protect pipeline endpoints and public data

**Summary:** Add optional shared API-key authentication, dual-key redaction, safe errors and authenticated watcher requests. Sanitize event/report/file persistence and output without changing traceback rendering or validation checks.

**Requirements addressed:** NFR-01, FR-P-04, FR-UI-06, FR-S-08, FR-S-09.

**Files:** .env.example, README.md, backend/app/agents/factory.py, backend/app/agents/security/agent.py, backend/app/agents/validator.py, backend/app/api/deps.py, backend/app/api/pipeline.py, backend/app/core/config.py, backend/app/core/errors.py, backend/app/core/logging.py, backend/app/core/safety.py, backend/app/events/log.py, backend/app/main.py, backend/app/pipeline/orchestrator.py, backend/app/pipeline/results.py, backend/scripts/run_pipeline.py, backend/tests/integration/test_pipeline_auth.py, backend/tests/integration/test_pipeline_review.py, backend/tests/integration/test_run_pipeline_watcher.py, backend/tests/unit/test_app.py, backend/tests/unit/test_config.py, backend/tests/unit/test_logging.py, docs/IMPLEMENTATION_LOG.md, docs/design-deviations.md.

**Decisions:** D-36 records the open-when-unset static header and fetch-based SSE. EventLog receives optional configured safety without changing locks or ordering; ValidatorAgent sanitizes the report before saving, leaving checks intact. Logs preserve paths and tracebacks; only operator logs retain correlation IDs.

**Tests:** Focused authentication, canary, watcher, validation, event, API and unit checks: 81 passed, 0 failed, 0 skipped in 20.66s. make lint passed (175 formatted files, 97 mypy files). Initial test-only Unicode-header fixture failed in httpx before requests; corrected to an ASCII HTTP header canary and reran successfully.

**Known gaps / follow-ups:** Remaining Phase 7 acceptance/documentation follows. No installs, dotenv reads or real LLM calls; no push.

---

## 2026-10-10 — Phase 7 section 3 — Download deterministic labelled archives

**Summary:** Add pure ZIP/readiness rendering and persisted-file downloads with event-derived label time/provenance and safe path validation.

**Requirements addressed:** FR-UI-06, FR-S-10, PR-04, NFR-01.

**Files:** backend/app/api/pipeline.py, backend/app/db/repositories/results.py, backend/app/domain/archive.py, backend/app/pipeline/results.py, backend/tests/integration/test_pipeline_download.py, backend/tests/unit/test_archive.py, docs/IMPLEMENTATION_LOG.md, docs/design-deviations.md.

**Decisions:** ZIP_DEFLATED level 6, fixed ZIP metadata, sorted entries; Labelled at replaces download time. D-37 documents deterministic collision fallback; missing events show unavailable.

**Tests:** Archive/download tests: 12 passed, 0 failed, 0 skipped in 8.57s. PR-04 full ASGI response: 0.632408s for 10,000,000 source bytes and 7,580,697 ZIP bytes. make lint passed (174 format files, 97 mypy files).

**Known gaps / follow-ups:** Remaining Phase 7 acceptance/documentation follows. No installs, dotenv reads or real LLM calls; no push.

---

## 2026-10-10 — Phase 7 section 2 — Add locked review decisions and recoverable retries

**Summary:** Add migration 0003, atomic review acceptance, shared bounded retry tasks, existing SecurityAgent/ValidatorAgent integration and marker-aware SSE/recovery.

**Requirements addressed:** FR-S-08, FR-S-09, FR-S-10, FR-UI-07, FR-P-04, NFR-01, PR-03.

**Files:** README.md, backend/app/agents/security/agent.py, backend/app/api/pipeline.py, backend/app/api/schemas.py, backend/app/db/migrations/versions/0003_review_retry_started_at.py, backend/app/db/models.py, backend/app/db/repositories/packages.py, backend/app/domain/states.py, backend/app/main.py, backend/app/pipeline/review.py, backend/app/pipeline/runner.py, backend/app/pipeline/state.py, backend/tests/integration/test_pipeline_review.py, backend/tests/integration/test_pipeline_sse.py, backend/tests/integration/test_review_recovery.py, backend/tests/unit/test_migration_parity.py, backend/tests/unit/test_pipeline_runner.py, backend/tests/unit/test_states.py, docs/IMPLEMENTATION_LOG.md, docs/design-deviations.md.

**Decisions:** D-37/D-38; marker is the nullable timestamp column, set/cleared with status. Automated failure rules/run recovery unchanged. Scanner failure persists audit evidence before review abort.

**Tests:** Review/agent/validator/SSE subset: 62 passed in 19.22s. State/recovery subset: 29 passed in 17.38s. Runner/full retry stream subset: 5 passed in 6.92s. Migration/privilege subset: 5 passed in 0.97s. All subsets: 0 failed, 0 skipped. make lint passed (171 format files, 96 mypy files).

**Known gaps / follow-ups:** Remaining Phase 7 acceptance/documentation follows. No installs, dotenv reads or real LLM calls; no push.

---

## 2026-10-10 — Phase 7 section 1 — Expose current results snapshots

**Summary:** Add strict results schemas, ordered package/failure lists, shared derived fields and a single SELECT including the persisted architect plan.

**Requirements addressed:** FR-G-07, FR-UI-06, FR-UI-07, FR-S-07, FR-S-09.

**Files:** Phase 7 section 1 changes listed in this commit; app, tests and documentation paths are recorded by Git.

**Decisions:** Plan comes from plan_created payload; no plan column. Failed generation rows are missing_variants only. Reviews require terminal runs.

**Tests:** Focused results/domain tests: 80 passed, 0 failed, 0 skipped in 7.88s. make lint passed Ruff/format (166 files) and mypy (94 files). An initial fixture duplicated terraform in its plan; corrected before the passing run.

**Known gaps / follow-ups:** Remaining Phase 7 acceptance/documentation follows. No installs, dotenv reads or real LLM calls; no push.

---

## 2026-10-10 — Phase 7 section 0 — Resolve Helm release namespaces

**Summary:** Treat omitted Helm namespaces as dynamic release namespaces, protect raw-manifest precedence with port regressions, and format the pipeline watcher.

**Requirements addressed:** FR-V-01, FR-V-04.

**Files:** backend/app/validation/references.py, backend/tests/unit/test_validation_references.py, backend/scripts/run_pipeline.py, docs/design-deviations.md, docs/IMPLEMENTATION_LOG.md.

**Decisions:** D-35 clarifies release-namespace warnings and raw declaration precedence. No validator policy changes beyond the approved follow-ups.

**Tests:** Focused reference tests: 55 passed, 0 failed, 0 skipped in 2.15s. make lint passed Ruff, formatting (159 files), and mypy (89 source files).

**Known gaps / follow-ups:** Remaining Phase 7 sections follow. No installs, dotenv reads or real LLM calls.

---

## 2026-10-09 — Phase 6b item 5 — Refresh offline validation evaluation and final verification

**Summary:** Run make eval-validation on the twelve original packages, retain the previous report, commit a new timestamped JSON/Markdown report with a per-package comparison, and update README and D-35 with measured results.

**Requirements addressed:** FR-V-01, FR-V-03, FR-V-04, FR-V-05, NFR-01.

**Files:** README.md, docs/design-deviations.md, docs/evals/phase6-validation-20261009T211526321570Z/comparison.md, docs/evals/phase6-validation-20261009T211526321570Z/results.json, docs/evals/phase6-validation-20261009T211526321570Z/summary.md; docs/IMPLEMENTATION_LOG.md records this item.

**Decisions:** The new report is docs/evals/phase6-validation-20261009T211526321570Z. All twelve source hashes and tool versions match the old report. No downloads, installs, dotenv reads, database access or LLM calls occurred during evaluation. Sonnet monitoring performance retains a genuine default-versus-monitoring namespace mismatch. The Sonnet three-tier security diagnostic is Cycle, a genuine security-group dependency cycle; without a range it is anchored to terraform/alb.tf:1 (the package has no main.tf). No additional spec deviation or open question was introduced.

**Tests:** make eval-validation succeeded: 4 valid, 8 invalid, 0 error, versus 2 valid, 10 invalid, 0 error previously. All gpt-oss packages remain invalid; Sonnet monitoring cost/security and three-tier cost/performance are valid. Both known syntax failures remain confirmed. gpt-oss three-tier cost reference failures fell from 19 duplicates to one local.common_tags finding at main.tf:18. Final make test: 802 passed, 0 failed, 0 skipped in 85.14s. The initial full run had 801 passed and 1 failed because the temporary bootstrap overwrote the retention CLI subprocess test URL; corrected the bootstrap to preserve explicit child overrides, then verified retention separately (1 passed in 1.80s) and reran the full suite. make lint passed Ruff/format (159 app/test files) and mypy (89 app files); explicit Ruff checks for all backend scripts passed. Real-Terraform stub pipeline success and mixed partial_success tests passed. Existing mirror remains 391,710,515 bytes (373.56 MiB), with unchanged provider versions.

**Known gaps / follow-ups:** An additional optional script formatting check flagged pre-existing formatting in backend/scripts/run_pipeline.py; the file was left outside these review fixes. Static validation still does not detect the documented Aurora-without-instances gap. No push; untracked REVISION.txt and the old evaluation remain untouched.

---

## 2026-10-09 — Phase 6b item 4 — Deduplicate and locate Terraform references

**Summary:** Retain Terraform reference positions from the shared HCL parse tree and JSON interpolation values, emit one finding per file and identifier, and include the reference in declaration/output messages.

**Requirements addressed:** FR-V-01, FR-V-04, NFR-01.

**Files:** backend/app/validation/documents.py, backend/app/validation/references.py, backend/tests/unit/test_validation_references.py, backend/tests/unit/test_validation_terraform.py, docs/design-deviations.md; docs/IMPLEMENTATION_LOG.md records this item.

**Decisions:** Parse HCL once, retaining original identifier positions before serialization; ignore comments, ordinary quoted strings and escaped interpolations. Module declaration references are deduplicated by module name; inspectable output references are deduplicated by full module/output name. Updated D-35 to distinguish exact reference positions from other source-line fallbacks.

**Tests:** Focused reference/structure/engine/Terraform tests: 131 passed, 0 failed, 0 skipped (4.14s). make lint passed Ruff, formatting and mypy (89 source files). Added repeated-reference tests for all three families across files, JSON interpolation positions, exact identifier boundaries, local-module outputs, and shared-parser reuse.

**Known gaps / follow-ups:** Full-suite verification and the twelve-package evaluation follow in item 5; original package files are untouched.

---

## 2026-10-09 — Phase 6b item 3 — Isolate security evaluator integration writes to the test database

**Summary:** Map app and migration settings to test URLs in the evaluator test; assert both role URLs at its engine boundary and reject any integration non-test DBAPI connection via a shared fixture.

**Requirements addressed:** NFR-01, FR-S-09, FR-V-05.

**Files:** backend/tests/database_safety.py, backend/tests/integration/conftest.py, backend/tests/integration/test_validator_agent.py, backend/tests/unit/test_database_isolation.py, docs/design-deviations.md; docs/IMPLEMENTATION_LOG.md records this item.

**Decisions:** D-35 records explicit test URL mapping and preconnection guard. Safety assertions never print credentials. Verification bootstrap disables dotenv and uses distinct unavailable dev and real test URLs, including migration subprocesses; the normal test roles/grants are unchanged.

**Tests:** Isolation/ValidatorAgent tests against real PostgreSQL: 18 passed, 0 failed, 0 skipped in 11.12 s. Unit tests reject each unsafe app/migration/test URL; integration guard proves a forbidden database cannot reach DBAPI connect. make lint passed Ruff/format (159 app/test files) and mypy (89 app files).

**Known gaps / follow-ups:** The guard is test-only and does not change application connection behavior. Final full-suite verification follows item 5.

---

## 2026-10-09 — Phase 6b item 2 — Preserve actionable Terraform diagnostic titles and locations

**Summary:** Reproduce the Sonnet security diagnostic offline; canonicalize the safe Cycle title, preserve ranges for unknown titles and attach unlocated diagnostics to Terraform root files for remediation.

**Requirements addressed:** FR-V-03, FR-V-04, NFR-01.

**Files:** backend/app/validation/terraform.py, backend/tests/fixtures/validation/README.md, backend/tests/fixtures/validation/terraform/sonnet_security_cycle.json, backend/tests/unit/test_validation_terraform.py, docs/design-deviations.md; docs/IMPLEMENTATION_LOG.md records this item.

**Decisions:** D-35 records fallback file/line semantics. Real summary: Cycle followed by aws_security_group.alb, aws_security_group.app and aws_security_group.rds. Init exited 0, validate exited 1: this is a genuine configuration dependency cycle, not our validation setup. The committed recording contains no source excerpt or detail.

**Tests:** Terraform/report tests: 62 passed, 0 failed, 0 skipped in 3.90 s, including mirror-backed and namespace executions. make lint passed Ruff, formatting and mypy on 89 app files. Range-with-unknown-title and range-less fallback tests prove every available diagnostic becomes a safe remediation target.

**Known gaps / follow-ups:** Global diagnostics have no actual source line; fallback line 1 is a remediation anchor. The original invalid source package is preserved. Updated twelve-package evaluation follows item 5.

---

## 2026-10-09 — Phase 6b item 1 — Resolve Kubernetes references to literal Helm resources

**Summary:** Index literal Helm template identities as resolution targets, with warnings for templated identities/ports and preserved missing-resource failures. Keep Helm templates outside Kubernetes structural/source-reference checks.

**Requirements addressed:** FR-V-01, FR-V-04.

**Files:** backend/app/validation/documents.py, backend/app/validation/references.py, backend/tests/unit/test_validation_references.py, docs/design-deviations.md; docs/IMPLEMENTATION_LOG.md records this item.

**Decisions:** Extend D-35 with safe YAML projection without Go execution; require explicit literal kind/name/namespace for template targets. Dynamic identities warn only for the referenced kind; literal port mismatches fail.

**Tests:** An earlier focused run exposed two incorrect fixture assumptions (91 passed, 2 failed); corrected focused reference/structure/engine tests: 93 passed, 0 failed, 0 skipped in 1.96 s. make lint passed Ruff, formatting and mypy on 89 app files. Regression tests use all three original Sonnet monitoring layouts, remove Grafana to prove genuine failure, and cover templated identities, namespace/port mismatches and other reference families.

**Known gaps / follow-ups:** The original Sonnet performance Ingress uses default namespace while its Grafana Service is literal namespace monitoring: that genuine failure remains. Security templates use dynamic identities and warn. Static projection cannot render Helm includes or compute expressions; optional Helm lint retains that coverage. Final full-suite verification follows item 5.

---

## 2026-10-09 — Phase 6 section 10 — Finalize Phase 6 documentation and verification

**Summary:** Finalize D-33–D-35, superseded placeholder history, thesis-update notes, setup/settings/tool/mirror/evaluation documentation and measured acceptance evidence.

**Requirements addressed:** FR-V-01, FR-V-02, FR-V-03, FR-V-04, FR-V-05, FR-S-09, NFR-01, FR-P-04.

**Files:** README.md, docs/design-deviations.md; new files are included in the section commit.

**Decisions:** D-35 completed; D-26 superseded; D-20 identified as historical security placeholder. OQ-10 records static naming applicability. Keep the artifact table and Appendix A updates in notes; do not edit docs/spec. No phase-7 endpoint work, installs, dotenv reads or real LLM calls.

**Tests:** Final make lint: Ruff check passed, 156 app/test files formatted, mypy passed on 89 source files. Explicit script/capture Ruff checks and format checks passed (9 files). Final PYTHONPATH temporary-dotenv-bootstrap make test ran migrations and the plain pytest entry point against real PostgreSQL with normal roles/grants: 766 passed, 0 failed, 0 skipped in 78.06 s. All 43 scanners-marked tests ran; collection recorded 43/766 (723 deselected). Real Terraform stub success and partial_success tests passed. Git diff --check passed; spec, applied migrations, installer and REVISION.txt were preserved. Mirror remeasure: 391,710,515 bytes (373.56 MiB), seven signed provider archives. Offline evaluation: 2 valid, 10 invalid, 0 error, both known syntax failures confirmed, twelve source hashes unchanged.

**Known gaps / follow-ups:** Static naming limits remain OQ-10. Aurora without instances is undetected; validation does not prove cloud deployability. Remote modules stay unavailable offline. Paid cache experiments and Phase 7 review/results/download endpoints are out of scope.

---

## 2026-10-09 — Phase 6 section 9 — Offline validation evaluation of twelve original packages

**Summary:** Add make eval-validation and a database/LLM-independent evaluator; commit full reports with immutable input hashes, categories, warnings, skips, durations and versions.

**Requirements addressed:** FR-V-01, FR-V-02, FR-V-03, FR-V-04, NFR-01.

**Files:** Makefile, README.md, backend/scripts/eval_validation.py, backend/tests/unit/test_eval_validation.py, docs/design-deviations.md, docs/evals/phase6-validation-20261009T175917789637Z/results.json, docs/evals/phase6-validation-20261009T175917789637Z/summary.md; new files are included in the section commit.

**Decisions:** D-35: measure original inputs unchanged; record the Aurora-without-instances semantic gap without adding deployment checks.

**Tests:** Evaluator tests: 8 passed, 0 failed, 0 skipped in 2.62 s. make lint passed Ruff, format and mypy (89 source files); explicit evaluator/script Ruff checks passed. make eval-validation succeeded: 2 valid, 10 invalid, 0 error; all gpt-oss variants invalid, Sonnet three-tier cost/performance valid, remaining Sonnet variants invalid. Both known gpt-oss syntax failures confirmed at main.tf:172 and ecs.tf:24. Recomputed hashes confirmed all twelve source packages unchanged.

**Known gaps / follow-ups:** One remote Terraform module could not be fetched offline and is a recorded skip; ordinary failures still make that package invalid. Static validation does not detect Aurora clusters lacking instances. Final full-suite verification is section 10.

---

## 2026-10-09 — Phase 6 section 8 — Acceptance coverage and recorded-output normalization

**Summary:** Complete real Terraform stub success and mixed outcomes, PostgreSQL row-lock evidence, forked validator deadline cleanup, cache metric propagation and recorded linter normalization.

**Requirements addressed:** FR-V-01, FR-V-02, FR-V-03, FR-V-04, FR-V-05, FR-S-09, NFR-01, FR-P-04.

**Files:** backend/app/llm/anthropic.py, backend/app/llm/errors.py, backend/app/llm/openai.py, backend/app/validation/structure.py, backend/pyproject.toml, backend/scripts/normalize_security_fixture.py, backend/tests/integration/test_validator_agent.py, backend/tests/unit/test_architect.py, backend/tests/unit/test_eval_security.py, backend/tests/unit/test_generators.py, backend/tests/unit/test_llm_providers.py, backend/tests/unit/test_scanner_timeout.py, backend/tests/unit/test_security_fix.py, backend/tests/unit/test_terraform_parser.py, backend/tests/unit/test_validation_engine.py, backend/tests/unit/test_validation_structure.py, backend/tests/unit/test_validation_terraform.py, docs/design-deviations.md; new files are included in the section commit.

**Decisions:** D-34/D-35: inspect wire cache metrics before SDK coercion; extend scanners marker to validators, with explicit prerequisite skips.

**Tests:** Focused acceptance command: 249 passed, 0 failed, 0 skipped in 22.38 s; final report/retry/evaluator checks after cache assertions: 19 passed, 0 failed, 0 skipped in 8.27 s. make lint passed Ruff, format and mypy (89 source files); final explicit Ruff check passed. Both real Terraform stub outcomes were observed: success (three ready) and partial_success (two ready). Network namespace valid/invalid tests and descendant cleanup ran without skips.

**Known gaps / follow-ups:** Evaluation and final full-suite counts follow in sections 9–10.

---

## 2026-10-09 — Phase 6 section 7 — ValidatorAgent, durable reports and real pipeline wiring

**Summary:** Add the database-independent validation engine with shared parsing, three-command concurrency bounds, stage deadlines and cancellation cleanup; persist reports through a row-locked repository method before outcome events; replace the placeholder in startup and the security evaluator.

**Requirements addressed:** FR-V-01, FR-V-03, FR-V-04, FR-V-05, FR-S-09, NFR-01.

**Files:** .env.example, README.md, backend/app/agents/factory.py, backend/app/agents/validator.py, backend/app/core/config.py, backend/app/db/repositories/packages.py, backend/app/domain/validation.py, backend/app/main.py, backend/app/pipeline/stages.py, backend/app/scanners/runner.py, backend/app/validation/engine.py, backend/app/validation/linters.py, backend/app/validation/terraform.py, backend/scripts/eval_security.py, backend/tests/integration/test_pipeline_api.py, backend/tests/integration/test_run_pipeline_watcher.py, backend/tests/integration/test_validation_placeholder.py, backend/tests/integration/test_validator_agent.py, backend/tests/unit/test_agent_factory.py, backend/tests/unit/test_config.py, backend/tests/unit/test_validation_engine.py, backend/tests/unit/test_validation_report.py, docs/design-deviations.md; new files are included in the section commit.

**Decisions:** D-35 records deadlines, cleanup, safe file inputs and persistence ordering; D-26 is superseded and D-20 clarified as historical security unavailability. JSONB arrays canonicalize to immutable report tuples. Existing Option C and remediation service interfaces remain. The evaluator reloads persisted remediated files; unsafe or uninspectable Terraform file functions never launch validation.

**Tests:** make lint passed (Ruff/format, mypy 89 app files); explicit security-evaluator Ruff passed. Plain make test with dotenv disabled and real PostgreSQL: 724 passed, 0 failed, 0 skipped in 69.84 s. Focused integration/factory/report verification: 46 passed. An earlier full run had 720 passed and one obsolete watcher expectation, corrected before the passing run. Stub pipeline reached success with real validation logic; a prior full run also demonstrated success using installed Terraform.

**Known gaps / follow-ups:** Further acceptance/normalizer/descendant tests follow in section 8. Twelve-package evaluation and final documentation remain pending.

---

## 2026-10-09 — Phase 6 section 6 — Optional local linter adapters and recordings

**Summary:** Add pluggable target discovery, offline commands, safe parsers and real recordings for Helm, hadolint, ansible-lint and promtool, with validated locations and optional-skip semantics. Add the 60-second tool timeout setting and isolate Ansible configuration.

**Requirements addressed:** FR-V-04, NFR-01.

**Files:** .env.example, README.md, backend/app/core/config.py, backend/app/scanners/runner.py, backend/app/validation/linters.py, backend/tests/fixtures/validation/README.md, backend/tests/fixtures/validation/capture_linters.py, backend/tests/fixtures/validation/linters/ansible-lint.json, backend/tests/fixtures/validation/linters/hadolint.json, backend/tests/fixtures/validation/linters/helm.json, backend/tests/fixtures/validation/linters/promtool.json, backend/tests/unit/test_validation_linters.py, docs/design-deviations.md; new files are included in the section commit.

**Decisions:** D-35 records exact installed versions, Code Climate severity/location mappings and no-raw-output reporting. Missing executables skip not_installed; crashes/timeouts/unusable output skip tool_error. Unsafe file-reading inputs and dynamic Ansible lookups are refused before launch. No installation/download occurred.

**Tests:** make lint passed (Ruff/format, mypy 87 app files). Combined linter/tool/descendant-timeout regression: 51 passed in 7.42 s, 0 skipped, including four actual clean linter executions. Initial focused linter set: 34 passed before canary/unsafe-input cases were added.

**Known gaps / follow-ups:** Engine concurrency, stage deadlines, persistence, retry and orchestrator success tests follow in sections 7–8.

---

## 2026-10-09 — Phase 6 section 5 — Static naming consistency warnings

**Summary:** Collect named entities across Terraform, Kubernetes, Helm, Ansible, Nginx and Prometheus; normalize names, apply token boundaries and documented suffixes, and warn on unknown or absent expected application entities.

**Requirements addressed:** FR-V-02, FR-V-04.

**Files:** backend/app/validation/naming.py, backend/tests/unit/test_validation_naming.py, docs/design-deviations.md; new files are included in the section commit.

**Decisions:** D-35 records warning-only naming semantics, conservative artifact applicability and infrastructure exclusions. Literal Helm release names are collected; symbolic release names are not inferred. OQ-10 records the absence of explicit deployment-role metadata without changing the plan schema.

**Tests:** make lint passed (Ruff/format, mypy 86 app files). Naming tests: 13 passed in 1.15 s, including both-file Terraform/Ansible mismatches, token boundaries, workload exclusions, storage and literal-release handling.

**Known gaps / follow-ups:** Static comparison cannot infer dynamic names, all Helm workload identities or deployment roles. Optional linters and pipeline wiring follow.

---

## 2026-10-09 — Phase 6 section 4 — Cross-file references and module scopes

**Summary:** Add deterministic checks for all specified Terraform, Kubernetes, Helm, Ansible and Prometheus references, including local-module outputs, namespace-scoped resources and safe package-contained paths/globs. Terraform preflight now accepts the shared parser index.

**Requirements addressed:** FR-V-01, FR-V-03, FR-V-04, NFR-01.

**Files:** backend/app/validation/references.py, backend/app/validation/terraform.py, backend/tests/unit/test_validation_references.py, backend/tests/unit/test_validation_terraform.py, docs/design-deviations.md; new files are included in the section commit.

**Decisions:** D-35 documents exact reference scope, missing-Secret warnings, remote Helm dependency and Values warnings, symbolic inventory host patterns and one finding per Prometheus rule reference. Literal strings and comments do not create Terraform/Helm references.

**Tests:** make lint passed (Ruff/format, mypy 85 app files). Combined reference/Terraform/structure tests: 85 passed in 7.50 s, including real Terraform and network namespace checks. Final reference-only verification: 29 passed. The full-suite clock flake was corrected in section 3; full regression will run after integration.

**Known gaps / follow-ups:** Conservative static analysis does not infer dynamic references or fetch remote dependencies. Naming, optional linters and pipeline persistence remain pending.

---

## 2026-10-09 — Phase 6 section 3 — Shared parsing and structural validation

**Summary:** Declare the exact installed parser dependencies and add a shared parsed document index with YAML positions, deterministic HCL line fallback, and built-in checks for every supported artifact type. Implement the approved Nginx resolution rule.

**Requirements addressed:** FR-V-01, FR-V-03, FR-V-04, NFR-01, PR-05.

**Files:** README.md, backend/app/validation/documents.py, backend/app/validation/structure.py, backend/pyproject.toml, backend/requirements.lock, backend/tests/unit/test_llm_base.py, backend/tests/unit/test_validation_structure.py, docs/design-deviations.md; new files are included in the section commit.

**Decisions:** D-35 records the installed library versions, parser positioning limits, supporting-file distinctions and exact Nginx resolution semantics. No installation or version changes to existing dependencies. Narrow mypy import exceptions cover PyYAML absent stubs rather than installing another package.

**Tests:** make lint passed (Ruff/format, mypy 84 app files). Structural tests: 32 passed. Full plain make test: 613 passed, 1 failed, 0 skipped in 154.26 s; the sole failure was an existing five-microsecond real-clock assumption. Replacing it with the established fake clock preserved exact timeout assertions; focused LLM/structure regression then passed 95 tests in 3.74 s. Full suite will be rerun after integration.

**Known gaps / follow-ups:** Reference/naming checks and real ValidatorAgent wiring still pending. Full-suite post-fix verification deferred to integration/final verification.

---

## 2026-10-09 — Phase 6 section 2 — Offline provider mirror and Terraform validation

**Summary:** Extend the shared subprocess runner with explicit commands and safe version probes; provision exact pinned providers once; capture real schema diagnostics; add offline initialization, module preflight, diagnostic parsing and health metadata.

**Requirements addressed:** FR-V-01, FR-V-03, FR-V-04, NFR-01.

**Files:** .gitignore, Makefile, README.md, backend/app/api/health.py, backend/app/main.py, backend/app/scanners/runner.py, backend/app/validation/__init__.py, backend/app/validation/terraform.py, backend/app/validation/tools.py, backend/scripts/mirror_providers.py, backend/tests/fixtures/validation/README.md, backend/tests/fixtures/validation/capture_terraform.py, backend/tests/fixtures/validation/terraform/invalid_argument.init.txt, backend/tests/fixtures/validation/terraform/invalid_argument.json, backend/tests/fixtures/validation/terraform/invalid_argument.main.tf, backend/tests/fixtures/validation/terraform/invalid_resource.init.txt, backend/tests/fixtures/validation/terraform/invalid_resource.json, backend/tests/fixtures/validation/terraform/invalid_resource.main.tf, backend/tests/fixtures/validation/terraform/providers.tf, backend/tests/fixtures/validation/terraform/syntax.init.txt, backend/tests/fixtures/validation/terraform/syntax.json, backend/tests/fixtures/validation/terraform/syntax.main.tf, backend/tests/fixtures/validation/terraform/valid.init.txt, backend/tests/fixtures/validation/terraform/valid.json, backend/tests/fixtures/validation/terraform/valid.main.tf, backend/tests/integration/test_health.py, backend/tests/unit/test_mirror_providers.py, backend/tests/unit/test_terraform_parser.py, backend/tests/unit/test_validation_terraform.py, backend/tests/unit/test_validation_tools.py, docs/design-deviations.md, tools/terraform-providers/.terraform.lock.hcl, tools/terraform-providers/README.md, tools/terraform-providers/aws5/.terraform.lock.hcl, tools/terraform-providers/aws5/providers.tf, tools/terraform-providers/providers.tf; new files are included in the section commit.

**Decisions:** D-35 records offline initialization and skip semantics. The single make providers invocation succeeded, authenticated all seven packages, and produced a 391,710,515-byte mirror (373.56 MiB), with lock hashes recorded locally. No other install/download occurred. Validate still runs after malformed init; reports omit source snippets and diagnostic details.

**Tests:** make lint passed (Ruff/format, mypy 82 app files); explicit mirror-script Ruff passed. Plain make test with dotenv disabled and real PostgreSQL: 582 passed, 0 failed, 0 skipped in 63.00 s. Focused Terraform/health tests: 24 passed, including real mirror validation and network-namespace execution. Existing scanner regression subset: 38 passed, 25 deselected.

**Known gaps / follow-ups:** Reusable shared parsing, structural/reference/naming checks, optional linters and stage wiring follow. D-35 remains in progress.

---

## 2026-10-09 — Phase 6 section 1 — Validation report contract and outcomes

**Summary:** Add strict immutable validation checks and reports, centralized outcome/status mapping, deterministic ordering and lossless remediation targets with bounded nonfailure sampling.

**Requirements addressed:** FR-V-03, FR-V-04, FR-V-05, NFR-01.

**Files:** docs/design-deviations.md; new files are included in the section commit.

**Decisions:** D-35 records outcome precedence and sampling. Reports carry required-Terraform and abort metadata for consistent persisted outcomes. No schema migration or stage wiring yet.

**Tests:** make lint passed: Ruff checks/format and mypy on 79 app files. Plain make test against real PostgreSQL with dotenv disabled: 550 passed, 0 failed, 0 skipped in 62.52 s; 29 new report cases included. Earlier focused report run: 22 passed before seven schema cases were added.

**Known gaps / follow-ups:** Provider validation, analysers, persistence and pipeline wiring follow in sections 2–8.

---

## 2026-10-09 — Phase 6 section 0 — Hybrid model decision and cache measurement

**Summary:** Record D-33/D-34 and add opt-in Anthropic system cache markers plus optional cached-input token metrics through adapters, attempt logs, agents and evaluation reports.

**Requirements addressed:** NFR-01, NFR-03, PR-05.

**Files:** .env.example, README.md, backend/app/agents/architect.py, backend/app/agents/generators/base.py, backend/app/agents/security/agent.py, backend/app/agents/security/fix.py, backend/app/core/config.py, backend/app/llm/anthropic.py, backend/app/llm/base.py, backend/app/llm/errors.py, backend/app/llm/factory.py, backend/app/llm/openai.py, backend/app/pipeline/orchestrator.py, backend/scripts/eval_architect.py, backend/scripts/eval_generators.py, backend/scripts/eval_security.py, backend/scripts/spike_llm_timing.py, backend/tests/unit/test_config.py, backend/tests/unit/test_llm_base.py, backend/tests/unit/test_llm_factory.py, backend/tests/unit/test_llm_providers.py, docs/design-deviations.md; new files are included in the section commit.

**Decisions:** Caching defaults off. Preserve explicit zero and absent metrics as None. Native Anthropic requests remain unchanged. The historical 10/20 rejected-fix baseline is attributed to the author rather than reconstructed.

**Tests:** make lint passed (Ruff and mypy, 78 app source files); explicit Ruff checks and formatting passed for four changed scripts. Plain make test with dotenv disabled and normal PostgreSQL roles: 521 passed, 0 failed, 0 skipped in 79.18 s. Earlier compatibility failures were fixed before the passing run.

**Known gaps / follow-ups:** No paid cache experiment or LLM call. Validator implementation follows in sections 1–10.

---

## 2026-10-01 — Phase 5b section 5 — Tool provenance and thesis documentation

**Summary:** Documented current scanning, offline/coverage limits, syntax gate,
Helm support, whole-process-group termination and exact reproducible installs.
Preserved historical entries and annotated their supersession. Moved D-31/D-32
into the deviations section and updated collected thesis changes.

**Requirements addressed:** FR-S-01, FR-S-02, FR-S-04, FR-G-05, NFR-01, NFR-04.

**Files:** changed `README.md`, `docs/design-deviations.md`, this log.

**Decisions:** D-31 records the author's confirmed installation output
`trivy_0.69.3_Linux-64bit.tar.gz: OK`; it does not claim independently repeated
checksum verification or incident research. README reproduces the task's exact
Trivy install snippet and pins `pipx install "checkov==3.3.21"`; no install was
performed in this task. D-32 records the upstream interleaved-drain file/lines,
matching PyPI wheel SHA-256, supported parallelization values, measured fixture
and package timings, and negative regression evidence. D-22/D-25/D-27/D-28,
CL-07, historical names and Appendix A/FR-S-01/NFR-04 notes are updated.

**Tests:** Final implementation `make test` → **507 passed, 0 failed, 0 skipped**
(30 scanner-marked tests, including namespace and all real Terraform probes).
`make lint` passed Ruff check, 132 formatted files and mypy 78 source files;
changed scripts pass explicit Ruff checks/format. Documentation-only changes
were checked with `git diff --check`. The final 12-package scan-only evaluation
has 0 errors, 0 timeouts and 1 remote-module advisory. Blocking counts agree
with the preceding scan; elapsed times/metadata differ as expected.

**Known gaps / follow-ups:** Docker is unavailable in this WSL session; database
tests used an isolated PostgreSQL 16 cluster with ordinary roles/migrations and
no extra grants. A temporary bootstrap disabled dotenv loading. The Trivy
checksum confirmation and incident provenance are author-supplied. Runtime
proxies do not enforce kernel isolation; remote module contents and unrecognized
syntax diagnostics remain coverage limits. No new open question or dependency;
Phase 6 semantic validation remains out of scope. No real LLM call, `.env` read,
API/frontend/schema change, tool upgrade, push or history rewrite.

---

## 2026-10-01 — Phase 5b section 4 — Scan-only comparison on all committed packages

**Summary:** Ran `make eval-security EVAL_ARGS="--scan-only"` on all 12 default
Phase 3 packages. Committed the report under `docs/evals/phase5b-security-20261001T191131076470Z/`.
Evaluation now exposes safe file/line/module coverage advisory records explicitly,
with no source URLs, and aggregates them; its regression test verifies this.

**Requirements addressed:** FR-S-01, FR-S-04, FR-G-05, NFR-01.

**Files:** added evaluation `results.json`/`summary.md`; changed evaluation
script/test and this log. The existing untracked Phase 5 evaluation is preserved.

**Comparison:** baseline `phase5-security-20261001T060220849316Z`:

| Model / package | Blocking old → new | Checkov H/C old = new | tfsec H/C old | Trivy H/C new | Terraform H/C new | Combined H/C old → new |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-oss / kubernetes_monitoring / cost | 30 → 46 | 10 | 1 | 6 | 1 | 11 → 17 |
| gpt-oss / kubernetes_monitoring / performance | 38 → 54 | 8 | 8 | 14 | 0 | 16 → 22 |
| gpt-oss / kubernetes_monitoring / security | 66 → 94 | 10 | 9 | 18 | 0 | 19 → 28 |
| gpt-oss / three_tier / cost | 35 → 31 | 6 | 12 | 9 | 0 | 18 → 15 |
| gpt-oss / three_tier / performance | 11 → 25 | 4 | 1 | 12 | 1 | 5 → 17 |
| gpt-oss / three_tier / security | 31 → 27 | 2 | 12 | 9 | 0 | 14 → 11 |
| Sonnet / kubernetes_monitoring / cost | 37 → 65 | 9 | 9 | 21 | 0 | 18 → 30 |
| Sonnet / kubernetes_monitoring / performance | 40 → 67 | 8 | 10 | 21 | 0 | 18 → 29 |
| Sonnet / kubernetes_monitoring / security | 28 → 54 | 7 | 10 | 20 | 0 | 17 → 27 |
| Sonnet / three_tier / cost | 31 → 28 | 5 | 10 | 8 | 0 | 15 → 13 |
| Sonnet / three_tier / performance | 34 → 30 | 5 | 12 | 9 | 0 | 17 → 14 |
| Sonnet / three_tier / security | 21 → 16 | 4 | 8 | 4 | 0 | 12 → 8 |

All 12 scans completed with zero scanner errors and zero timeouts. One external
module advisory is recorded: gpt-oss three_tier/performance, module.vpc at
`terraform/main.tf:8` (a registry source). Its downloaded contents were unavailable
but local findings were retained; all other module sources are local. Checkov counts are
identical per package. Mean blocking counts changed from 35.17 to 46.17 for
gpt-oss and 31.83 to 43.33 for Sonnet. All packages still have blocking findings;
FR-G-05 still fails for both models. HIGH/CRITICAL totals: gpt-oss Checkov 40
unchanged, old tfsec 43 versus new Trivy 68 plus Terraform 2; Sonnet Checkov 38
unchanged, old tfsec 59 versus new Trivy 83 plus Terraform 0.

Both gpt-oss syntax findings remain: kubernetes_monitoring/cost at
`terraform/main.tf:172` (Invalid single-argument block definition) and
three_tier/performance at `terraform/ecs.tf:24` (Extraneous label for locals).
The old tfsec syntax count is replaced by Terraform, not added to Trivy.

Large increases occur in monitoring packages (+16/+16/+28 for gpt-oss,
+28/+27/+26 for Sonnet) and the syntax-limited gpt-oss three-tier performance
package (+14). Likely causes are additional Kubernetes and Helm coverage,
including Kubernetes findings despite failed Terraform parsing. A direct Trivy
probe of Sonnet monitoring/cost confirms both rendered Helm workloads, with
13 findings and three HIGH/CRITICAL findings each; gpt-oss monitoring/cost
still has no Terraform findings but scans both Kubernetes deployments. Trivy
can also omit unrenderable templates; built-in Helm support is not universal
chart validation. Three-tier reductions of 3–5 findings are consistent with
rule/severity differences in the pinned embedded library; Checkov's severity
policy did not change. No remediation quality or timing speedup is inferred.

**Tests:** After the coverage-record addition, `make lint` passed (132 format
checks, mypy 78 files), explicit script Ruff check passed, and `make test`
→ **507 passed, 0 failed, 0 skipped in 60.75 s** (30 scanner tests, none skipped).
The final 12-package evaluation has no DB connection, dotenv read or LLM calls.

**Known gaps / follow-ups:** No fix evaluation was run. Full semantic validation
remains Phase 6; syntax-limited Terraform findings are incomplete security
coverage. Raw JSON timestamps/IDs and elapsed times are not deterministic.

---

## 2026-10-01 — Phase 5b section 3 — Recorded and isolated scanner verification

**Summary:** Added focused parser, syntax, module-coverage, compatibility and
real-tool tests, plus seven recorded SecurityAgent loop scenarios. Confirmed
three-tool concurrency using a synchronization barrier, without timing guesses.

**Requirements addressed:** FR-S-01, FR-S-02, FR-S-03, FR-S-05, FR-S-07,
FR-S-09, FR-G-05, NFR-01, NFR-04.

**Files:** added `tests/unit/test_{trivy_parser,terraform_parser,external_modules,
security_reports,trivy_scanners}.py`; extended scanner/agent tests and scanner
marker; added Helm/remote-module/single-argument-block inputs and real recordings;
changed Trivy parser to reject malformed empty objects, module lexer to tolerate
invalid quoted input, evaluation output prefix, fixture README/deviations/log.

**Decisions:** D-31/D-32. Every allowlisted diagnostic has a recorded real probe
and real Terraform reproduction; providers/modules/references/types/schema
errors and valid uninitialized configurations remain finding-free. Trivy AVDID
precedence, emitted IDs, paths/lines/severity, empty/malformed/non-FAIL output,
variant exemptions and legacy report attribution are checked. Namespace scans
include ordinary and remote-module packages, run twice with fresh cache, and
retain local findings. Debug evidence shows exactly 563 embedded checks; the
one expected ERROR is the successful missing-cache fallback, not a download.
All three subprocesses/version probes exclude secret canaries and inherited
scanner settings. Historical tfsec findings survive a database-backed review
retry, and previous report sessions remain unchanged.

**Tests:** `make lint` passed (132 formatted files, mypy 78 source files).
Explicit Ruff check/format for both changed scripts passed. Final `make test`
→ **507 passed, 0 failed, 0 skipped in 57.85 s**; **30 scanner-marked tests
passed, 0 skipped**, including real tools and network namespaces. Earlier
negative timeout verification remains 3 expected failures against old logic.
The installed Checkov file hash was rechecked and still matches the verified
PyPI wheel hash documented in D-32.

**Known gaps / follow-ups:** Runtime proxies are not kernel network isolation.
The syntax allowlist intentionally excludes uncertain diagnostics; full semantic
validation remains Phase 6. No tool install/upgrade, dependency or LLM call.

---

## 2026-10-01 — Phase 5b section 2 — Trivy and filtered Terraform syntax gate

**Summary:** Replaced active tfsec scanning with concurrent Checkov, Trivy
0.69.3 and Terraform validate without init. Added strict Trivy location/FAIL
parsing, demonstrated syntax allowlist, remote-module coverage advisories,
policy 2, per-tool report counts, version/health updates and portable recordings.

**Requirements addressed:** FR-S-01, FR-S-02, FR-S-03, FR-G-05, NFR-01, NFR-04.

**Files:** added `app/scanners/{trivy_parser,terraform_parser,external_modules}.py`,
`app/security/reports.py`, Trivy/Terraform JSON recordings, diagnostic corpus and
three syntax fixture packages; changed runner/scanner, domain Violation,
SecurityAgent/policy, evaluation/normalization scripts, existing tests, fixture
README, repository README/deviations; removed tfsec parser and three recordings.

**Decisions:** D-31. Trivy silently misses malformed HCL; fmt also misses an
extraneous locals label, so filtered validate diagnostics preserve remediation.
All requested summaries were triggered with installed Terraform 1.16.4. Native
HCL duplicates say Attribute redefined; JSON duplicates have distinct summaries.
Unsupported block type uses language context to exclude resource/provider schema
errors. Version probes and scanners use refusal proxies and fresh temp state.
`tool=tfsec` remains accepted only for historical report/review retry decoding.
Checkov map/thresholds and FR-G-05 pass measure are unchanged.

**Tests:** `make lint` passed (127 formatted files, mypy 78 files).
`make test` → **414 passed, 0 failed, 0 skipped**, including real installed-tool
vulnerable/fixed and syntax checks. Real captures use only installed binaries;
no tools were installed/upgraded and no LLM calls were made.

**Known gaps / follow-ups:** Section 3 adds comprehensive corpus, network
namespace, parser/policy, and compatibility tests. Runtime proxies do not provide
kernel isolation. External module contents remain unavailable.

---

## 2026-10-01 — Phase 5b section 1 — Bounded scanner process groups

**Summary:** Scanners start in separate sessions; timeout and cancellation kill
all group members and bound pipe cleanup to five seconds. Evaluation prints
per-package/per-attempt progress and retains recovered timeouts; adds
`--packages-limit N`.

**Requirements addressed:** FR-S-01, FR-S-07, NFR-01, NFR-04.

**Files:** scanner runner/orchestration, SecurityAgent iteration propagation,
evaluation script, scanner timeout/evaluation/agent tests, README, deviations.

**Decisions:** D-32. Checkov supports `CHECKOV_PARALLELIZATION_TYPE=none`.
The published interleaved-drain implementation matches its PyPI 3.3.21 wheel.

**Tests:** `make lint` passed (124 formatted files; mypy 75 source files).
`make test` → **414 passed, 0 failed, 0 skipped**. Three isolated forked-child
regressions (timeout, cancellation, full scanner retry/temp cleanup) pass;
the same tests against the original runner fail (3 failures, watchdog expiry).
Docker is unavailable; tests used an isolated local PostgreSQL 16 cluster with
the ordinary migrations/roles and no extra privileges. A temporary bootstrap
disabled dotenv loading, without reading `.env`.

**Known gaps / follow-ups:** Trivy migration and full evaluation follow in
sections 2–5. Single measurements show no consistent Checkov speed advantage.

---

## 2026-10-01 — Phase 5 follow-up — Fix diagnostics and model-aware evaluation

**Summary:** Replaced generic fix rejection labels with safe schema paths and
JSON/path categories, kept file content and new files strict while accepting
imperfect descriptive metadata, expanded remediation summaries, and added
optional SecurityAgent-only model selection.

**Requirements addressed:** FR-S-02, FR-S-03, FR-S-04, FR-G-05, NFR-01.

**Files:** changed `backend/app/agents/security/{fix,agent}.py`,
`backend/app/agents/factory.py`, `backend/app/llm/factory.py`,
`backend/app/core/config.py`, `backend/app/db/repositories/packages.py`,
`backend/scripts/eval_security.py`, unit and integration tests,
`.env.example`, `README.md`, `docs/design-deviations.md`, and this log.

**Decisions:** D-29 records safe rejection categories and lenient
descriptive `fixes` metadata; D-30 records per-agent fixing model selection.
Pydantic diagnostics use only known field names and error types; they never
copy response values. The selected fixer is stored per report session and
at the report root. Evaluation reports generator and fixer independently,
prices tokens by fixer, and includes scan-error packages in the remediation
table without claiming they received fix calls. Cost is null when that
fixer's input or output rate is unavailable.

**Tests:** `make lint` passed Ruff check, Ruff format check (123 files), and
mypy (75 source files). Ruff check and format passed for the evaluation
script. `make test` passed with **410 passed, 0 failed, 0 skipped**. New tests
cover safe reasons for missing code and invalid JSON, truncated summaries,
dropped malformed metadata, strict new-file values, persisted rejection
reasons, fixer override and fallback, persisted fixer identity, remediation
stop reasons, reason counts, per-fixer aggregates, and fixer-priced cost.

**Known gaps / follow-ups:** The author reported gpt-oss reducing blocking
findings from 402 to 53 across 12 packages and Sonnet receiving 10 rejected
fixes across two packages; these real runs were not repeated because that
would make real LLM calls. The two existing untracked evaluation directories
were left untouched. New remediation summary behavior is verified with
recorded test data, not a new paid evaluation.

---

## 2026-10-01 — Phase 5 follow-up — Portable fixtures and Terraform syntax findings

**Summary:** Normalized recorded scanner paths to a fixed placeholder so
tests run from any checkout. tfsec HCL parse diagnostics now become file-linked
CRITICAL `TERRAFORM_SYNTAX` findings; the fix loop can repair and rescan them
instead of ending in `scan_error`.

**Requirements addressed:** FR-S-01, FR-S-02, FR-S-03, FR-S-04, FR-G-05,
NFR-01.

**Files:** added `backend/scripts/normalize_security_fixture.py`,
`backend/tests/fixtures/security/{syntax_error/,tfsec-syntax-error.txt}`,
and `docs/evals/phase5-security-20261001T060220849316Z/`; normalized four
recorded JSON fixtures; changed the scanner parser and loop report,
`backend/scripts/eval_security.py`, scanner/agent/evaluation tests, fixture
README, repository README, design deviations, and this log.

**Decisions:** D-27 records the portable fixture marker and capture script;
D-28 records syntax-limited scans and the `TERRAFORM_SYNTAX` classification.
CL-07 now notes that Checkov 3.3.21 reported zero parsing errors for the
invalid `locals "x" { a = 1 }` fixture. The temporary scanner directory is
stripped from the finding, and other tfsec failures still retry before
`scan_error`. Scan-only evaluation constructs offline settings without
loading `.env` or connecting to PostgreSQL.

**Tests:** `make lint` passed Ruff check, Ruff format check (123 files), and
mypy (75 source files). Ruff check and format passed for both evaluation and
fixture scripts. `make test` passed with **402 passed, 0 failed, 0 skipped**.
New tests copy recordings to another directory, parse recorded and real tfsec
syntax errors, verify a fix pass and full rescan, confirm unparseable output
still retries, and check syntax-limited evaluation output. The real Checkov
test observed zero parsing errors on the invalid Terraform fixture.
`make eval-security EVAL_ARGS='--scan-only'` scanned all 12 saved packages;
the two affected gpt-oss packages now show `TERRAFORM_SYNTAX` findings with
relative files and lines 172 and 24, rather than `tfsec:invalid_json`.

**Known gaps / follow-ups:** A syntax-limited scan has no other tfsec findings
until the syntax is repaired and rescanned. No real LLM call or remediation
evaluation was run.

---

## 2026-10-01 — Phase 5 — Security scanning, remediation, and audit

**Summary:** Added offline Checkov and tfsec scans, severity classification,
parallel per-file LLM fix proposals with suppression and package validation,
bounded remediation and retry sessions, immutable generated-file baselines,
and cumulative diffs. A reached validation placeholder now moves scanned
packages through `validation_error` to `pending_review`.

**Requirements addressed:** FR-S-01–07, FR-S-09, FR-G-05, NFR-01, CL-01.

**Files:** added `backend/app/security/`, `backend/app/scanners/`,
`backend/app/agents/security/`, `backend/app/agents/prompts/security_fix.py`,
Alembic revision `0002_original_files`, security fixtures and tests,
`backend/scripts/eval_security.py`, and
`docs/evals/phase5-security-20261001T051255463643Z/`; changed domain
models/enums, package repository, agent factory, pipeline stages and
orchestrator, app wiring, settings, health, `Makefile`, `.env.example`,
`README.md`, `docs/design-deviations.md`, and this log.

**Decisions:** D-22–D-26 record advisory findings, bounded reports, retry
audit, suppression rejection, subprocess isolation, and the temporary
validation outcome. CL-07 records installed scanner behavior. OQ-09 defers
feedback-only file targeting to Phase 7. FR-G-05 uses only the Checkov
HIGH/CRITICAL first-scan count; tfsec and combined counts are diagnostics.
Counts are null when no valid first scan exists. The combined per-package
count sums both tools' records, including equivalent findings. The report's
top-level `final` mirrors the latest session for direct access.

**Tests:** `make lint` passed Ruff check, Ruff format check (123 files), and
mypy (75 source files). Ruff check and format also passed for the evaluation
script. `make test` passed with **397 passed, 0 failed, 0 skipped**, including
real Checkov/tfsec fixture scans. New tests cover parser shapes and retries,
policy, prompt and fix validation, concurrent fixes, loop outcomes and time
budget, first-scan counts, diff and session persistence, canary redaction,
validation transitions, and orchestrator settlement. Scan-only evaluation
completed for 12 committed generator packages. After `make migrate` applied
the new column to the development database, `LLM_PROVIDER=stub make run` plus
`make run-pipeline TEXT="Deploy a small AWS web service"` ended
`partial_success`, with all three packages in `pending_review`; no real LLM
call was made.

**Known gaps / follow-ups:** The committed evaluation marks two gpt-oss
Terraform packages that tfsec cannot parse; their Checkov counts remain
available, while tfsec and combined counts are unavailable. Helm is absent
locally. Scanner flags and a restricted subprocess environment avoid network
dependencies, but kernel-enforced network isolation was unavailable. The
optional `--remediate` evaluation mode was not run because it makes real LLM
calls. Real validation, review/results APIs, and UI remain for Phases 6–8.

---

## 2026-10-01 — Phase 4 follow-up — Stream closure and core failure guards

**Summary:** Added integration tests for SSE closure after a terminal run with
an active remediation retry, and for unexpected orchestrator failures settling
the run without exposing exception text in persisted or streamed data.

**Requirements addressed:** FR-P-03, FR-P-04, FR-S-09, NFR-01.

**Files:** changed `backend/tests/integration/test_pipeline_sse.py`,
`backend/tests/integration/test_pipeline_orchestrator.py`, and this log.

**Decisions:** The stream test uses a 0.01-second keep-alive setting and
two-second timeouts on every read, so premature closure or a stalled stream
fails promptly. No design deviation or new open question was introduced.

**Tests:** `make test` passed with **374 passed, 0 failed, 0 skipped**.
`make lint` passed Ruff check, Ruff format check (100 files), and mypy
(61 source files). Replacing the active-package condition in `_can_close`
with `True` made the stream test fail before the keep-alive. Removing the
generic exception handler's `_fail_unexpected` call made the core failure
test fail because the persisted run remained `running`. Both mutations were
restored before the full checks.

**Known gaps / follow-ups:** None from this test-only follow-up.

---

## 2026-10-01 — Phase 4 — Pipeline orchestration and live progress

**Summary:** Added the asynchronous pipeline API, Architect-to-parallel-generator
barrier, durable state/event writing, bounded in-memory SSE broker, recovery,
and command-line watcher. The production security placeholder leaves generated
packages in `scan_error`, so Phase 4 runs truthfully settle as `failed`.

**Requirements addressed:** FR-I-01--04, FR-A-04, FR-G-01, FR-G-06--07,
FR-P-01--04, PR-02, PR-03, UC-01, UC-02, NFR-01.

**Files:** added `backend/app/events/{kinds,broker}.py`,
`backend/app/pipeline/{state,stages,demo_stub,orchestrator,runner}.py`,
`backend/app/api/pipeline.py`, `backend/scripts/run_pipeline.py`, and Phase 4
unit and integration tests; changed the LLM parser and OpenAI adapter,
repositories, state machine, app wiring, settings, `Makefile`, `.env.example`,
`README.md`, and `docs/design-deviations.md`.

**Decisions:** D-17--D-21 record the evaluation model, SSE format, launch
failure edge, unavailable security stage, and capacity limit. OQ-01 now has a
durable `package_generated` variant record; OQ-04 is enforced by one Uvicorn
worker; OQ-08 implements safe format diagnostics and optional JSON mode.
The deterministic pipeline demo is an explicit factory opt-in, preserving all
Phase 1--3 stub consumers. State commits before the event transaction, so a
hard crash in that window can leave a missing event. The spec's `failed = 0
packages` wording is recorded for correction to `0 usable packages`.

**Tests:** `make lint` passed Ruff check, Ruff format check (100 files), and
mypy (61 source files). `make test` passed with **372 passed, 0 failed, 0
skipped**. New tests cover API rejection and persistence, the generator
barrier, success and partial outcomes with fake stages, placeholder failure,
startup recovery, cancellation, canary redaction, broker isolation and
overflow, replay/live overlap, keep-alives, concurrency, and stub regression.
With `LLM_PROVIDER=stub`, `make run` and `make run-pipeline TEXT="Deploy a small
AWS web service"` produced a full stream ending `failed`, with all
three packages in `scan_error`. No real LLM API call was made.

**Known gaps / follow-ups:** Real scanning and remediation (Phase 5), real
validation (Phase 6), results/review/download APIs (Phase 7), and frontend
(Phase 8) remain. A database outage or hard crash cannot be settled until
recovery; an event missing from the state/event commit window cannot be
reconstructed by replay.

---

## 2026-09-30 — Phase 2 follow-up — Architect evaluation placement checks

**Summary:** Corrected the architect evaluator's three-tier relational
database check so a database represented in `storage` no longer causes a
false FAIL. The object storage, CDN, and queue checks now recognize their
schema-compatible service and storage placements too.

**Requirements addressed:** FR-A-01, FR-A-02.

**Files:** changed `backend/scripts/eval_architect.py`,
`backend/tests/unit/test_eval_architect.py`,
`docs/design-deviations.md`, and this log.

**Decisions:** The report calls the check `relational database`. It passes
for an RDS/Aurora-labelled service or a storage entry whose kind is
`relational_db`; an RDS label on storage of another kind does not suffice.
D-10 records that the evaluation accepts equivalent placements allowed by
the plan schema. These are advisory evaluation checks, not plan validation.

**Tests:** `make test` passed with 331 passed, 0 failed, 0 skipped.
`make lint` passed Ruff check, Ruff format check (84 files), and mypy
(52 source files). Added positive and negative examples for both placements
and asserted the renamed check in the saved stub report. No real provider
calls were made.

**Known gaps / follow-ups:** These soft checks detect named components; they
do not establish deployability or service compatibility. Existing untracked
evaluation reports were left untouched.

---

## 2026-09-30 — Phase 3 follow-up — Configurable reasoning effort

**Summary:** Added optional `LLM_REASONING_EFFORT` control for
OpenAI-compatible requests and recorded its configured value in each LLM
attempt log. Unset leaves request bodies unchanged.

**Requirements addressed:** PR-05, NFR-01.

**Files:** changed `backend/app/core/config.py`, `backend/app/llm/base.py`,
`backend/app/llm/openai.py`, `backend/app/llm/anthropic.py`,
`backend/app/llm/stub.py`, `backend/app/llm/factory.py`, their configuration,
factory, adapter, and log tests, `.env.example`, `README.md`,
`docs/design-deviations.md`, and this log.

**Decisions:** D-16 maps `off` to OpenRouter's
`reasoning: {enabled: false}` and `low`/`medium`/`high` to
`reasoning: {effort: <value>}` in SDK `extra_body`. Anthropic does not send
the setting; it only records it in the common attempt log. The default logs
`reasoning_effort=unset`. OQ-07's request mechanism is resolved, while the
quality effect remains an evaluation question.

**Tests:** `make test` passed with 326 passed, 0 failed, 0 skipped.
`make lint` passed Ruff check, Ruff format check (84 files), and mypy
(52 source files). Mock transport tests assert absence when unset and exact
request shapes for all configured values, plus Anthropic's unchanged body.
No real provider calls were made.

**Known gaps / follow-ups:** Provider/model support and any quality benefit
must be assessed in evaluation; the adapters do not discover supported
reasoning levels per model.

---

## 2026-09-30 — Phase 3 follow-up — Generator prompt v3 autoscaling

**Summary:** Advanced the generator prompt to version 3 and replaced the
performance directive's Kubernetes-only HPA sentence with per-service
autoscaling guidance for Kubernetes Deployments, ECS services, and EC2 Auto
Scaling groups.

**Requirements addressed:** FR-G-04.

**Files:** changed `backend/app/agents/prompts/generator.py`,
`backend/app/agents/generators/performance.py`,
`backend/tests/unit/test_generator_prompt.py`,
`docs/design-deviations.md`, and this log.

**Decisions:** D-14 records the directive expansion. The shared prompt rules
and generation algorithm remain the same; only the performance strategy text
and prompt version changed.

**Tests:** `make test` passed with 312 passed, 0 failed, 0 skipped. `make lint`
passed Ruff check, Ruff format check (84 files), and mypy (52 source files).
The prompt test asserts the complete new instruction and confirms all three
system prompts are byte-identical after replacing the marked directives.
No real provider calls were made.

**Known gaps / follow-ups:** The prompt directs generation but does not
establish that generated autoscaling resources deploy correctly; later
validation and evaluation must assess the packages.

---

## 2026-09-30 — Phase 3 follow-up — Evaluation logging, prompt, and Aurora check

**Summary:** Fixed the LLM attempt log separator, recorded optional
OpenRouter serving and reasoning diagnostics, shortened the generator's
prompt-v2 output guidance, required Kubernetes HPAs in the performance
directive, and corrected the Aurora multi-AZ report after the first real
model comparison.

**Requirements addressed:** PR-05, NFR-01, FR-G-04.

**Files:** changed `backend/app/llm/base.py`,
`backend/app/llm/openai.py`, `backend/app/agents/prompts/generator.py`,
`backend/app/domain/directive_checks.py`, their unit tests,
`docs/design-deviations.md`, and this log.

**Decisions:** D-13 now recognizes an Aurora cluster with multiple instance
declarations or multiple distinct explicit availability zones. The check
remains a text heuristic and does not resolve Terraform references or prove
placement. D-14 records the compact prompt-v2 guidance and the performance
HPA instruction. Serving diagnostics are optional and never required for a
successful response. Attempt log fields are complete `key=value` tokens
joined with single spaces.

**Tests:** Before the first three commits, `make lint` passed each time and
`make test` reported 304, 307, and 307 passed respectively. Before the
Aurora commit, `make lint` passed Ruff check, Ruff format check (84 files),
and mypy (52 source files); `make test` reported 312 passed, 0 failed,
0 skipped. New tests parse every attempt outcome, exercise OpenRouter mock
transport with and without optional fields, compare directive-neutralized
prompts, and cover Aurora pass and fail cases. No real provider calls were
made.

**Known gaps / follow-ups:** The Aurora result remains an advisory heuristic;
subsequent validation and scanning must establish package validity and
deployed behaviour. The untracked report from the first real evaluation was
left outside these commits.

---

## 2026-09-30 — Phase 3 — Generator agents and offline evaluation

**Summary:** Added a shared full-package generation template, three
optimisation strategies, deterministic path completeness, report-only
directive checks, factory methods, and a stub-first model comparison
evaluator. One package response keeps cross-file names together; structural
defects can request one complete correction.

**Requirements addressed:** FR-A-05, FR-G-02--05, partial FR-G-01 and
FR-G-06, PR-05, NFR-01. Pipeline concurrency, status, and FR-G-07
persistence remain Phase 4 work.

**Files:** added `app/domain/package_layout.py` and `directive_checks.py`,
`app/agents/generators/*`, `app/agents/prompts/generator.py`,
`scripts/eval_generators.py` and its committed plan/package fixtures, new
unit tests, and a stub report under `docs/evals/phase3-generators-*`;
changed `app/core/config.py`, `app/llm/base.py`, `app/agents/factory.py`,
existing tests, `.env.example`, `Makefile`, `README.md`, and
`docs/design-deviations.md`.

**Decisions:** D-12 fixes package paths and treats the plan's file-type list
as the contract. D-13 reports directive heuristics without rejecting a
package. D-14 requests one whole package per attempt. D-15 combines the
Template Method generation algorithm with directive-based Strategy
subclasses. CL-06 gives full-package LLM attempts a configurable 120-second
limit inside a 150-second agent budget. Generator notes remain in
`GeneratorRunInfo` and the evaluation report; Phase 4 will persist them in
the package-generated event payload. File limits use decimal UTF-8 bytes
(200,000 per file and 2,000,000 per package).

**Tests:** `make lint` passed: Ruff check, Ruff format check (84 app/test
files), and mypy (52 source files). The offline unit suite passed with
270 passed, 0 failed, 0 skipped. The provider canary subset passed with
2 passed, 0 failed, 1 deselected. The stub `make eval-generators` command
with `--models stub --no-env-file --price-in stub=1 --price-out stub=2`
completed with six successful package cases and one visible correction;
the report contains PASS and FAIL directive findings. `make test` stopped
before pytest at Alembic migration because PostgreSQL refused the connection
at 127.0.0.1:5432. `make up` failed because Docker is unavailable in this
WSL distro.

**Known gaps / follow-ups:** The full PostgreSQL-backed test suite needs
Docker Desktop WSL integration or another PostgreSQL 16 instance. The stub
report verifies workflow and format, not real-provider quality, deployability,
or FR-G-05's Checkov first-scan criterion. Phase 4 owns the pipeline
integration and persistence tests for FR-G-01, FR-G-06, and FR-G-07.

---

## 2026-09-27 — Phase 1/2 follow-up — Rate-limit hints and architect corrections

**Summary:** LLM adapters now fall back from an unusable `retry-after` to
the larger parseable token or request reset duration and log only the
parsed wait and recognized header names. Architect prompt version 2
clarifies the roles of services, storage and file types; plan validation
now gives specific corrections when dependencies name storage or tools.

**Requirements addressed:** FR-A-01, FR-A-02, FR-A-04, PR-05, NFR-01.

**Files:** changed `backend/app/llm/errors.py`, `base.py`, `anthropic.py`,
`openai.py`, `backend/app/agents/prompts/architect.py`,
`backend/app/domain/plan.py`, their unit tests, the committed offline
stub report under `docs/evals/`, and `docs/design-deviations.md` (D-09,
D-11).

**Decisions:** D-09 now accepts finite nonnegative numeric seconds and
durations such as `7.66s`, `1m2.5s`, and `250ms`. A valid `retry-after`
takes precedence; otherwise the larger valid reset hint wins. The
existing deadline cap is unchanged. Per-attempt logs show the parsed
wait and fixed header names, never header values. D-11 records prompt
version 2 and actionable dependency-reference feedback. The stub report
was refreshed with explicit settings and `.env` loading disabled.

**Tests:** Before each of the three commits, `make lint` passed: Ruff
check, Ruff format check (69 app/test files), and mypy (43 source files).
`make test` was attempted before each commit but stopped at the Alembic
migration because PostgreSQL refused the connection at 127.0.0.1:5432;
pytest did not start. `make up` failed because Docker is unavailable in
this WSL distro, and the Windows Docker executable could not connect.
The offline unit suite passed after each code change: 214 tests after
the rate-limit change and 218 after prompt v2. Tests cover all requested
duration formats, precedence, invalid values, header-name-only logs,
deadline clipping, the revised prompt, and both actionable messages.
No real API call was made.

**Known gaps / follow-ups:** The full database-backed test suite needs
PostgreSQL or Docker Desktop WSL integration restored. The author's real
Groq run informed these changes but was not repeated in this task.

---

## 2026-09-27 — Phase 2 follow-up — Evaluation failure details

**Summary:** The ArchitectAgent now retains up to ten validation messages
per plan attempt for evaluation. The ArchitectAgent evaluator writes those
messages to its Markdown summary and per-case JSON, and records a safe LLM
failure category when applicable. The CLI configures redacted INFO logging
to show adapter attempt metrics on stderr.

**Requirements addressed:** FR-A-01, FR-A-04, NFR-01.

**Files:** changed `backend/app/agents/architect.py`,
`backend/scripts/eval_architect.py`, their unit tests, the committed stub
report under `docs/evals/`, `README.md`, and `docs/design-deviations.md`
(D-11).

**Decisions:** `ArchitectRunInfo.validation_errors_by_attempt` contains
only validation messages, capped at ten per attempt; the existing count
retains the full number. Every case now has a JSON report, including
failures, with the validated plan nested under `plan`. The evaluator writes
`ArchitectLLMFailure.llm_category` when present. CLI logging uses the
existing `configure_logging` redacting setup at INFO level; it logs metrics
without prompts or raw responses.

**Tests:** `make test` → 222 passed, 0 failed, 0 skipped. `make lint` →
Ruff check passed, Ruff format check passed (69 app/test files), mypy passed
(43 source files). Stub tests verify diagnostic error text in Markdown and
JSON, the ten-message cap, LLM failure category, CLI logger setup, stderr
attempt metrics, and canary redaction. The stub format example was refreshed
with explicit settings and `.env` loading disabled. No network call was made.

**Known gaps / follow-ups:** Real-provider output was not evaluated in this
task. The stored plan is validated JSON; raw provider responses and prompts
remain excluded from reports.

---

## 2026-09-27 — Phase 2 follow-up — Broader intent gate and no-call deadline test

**Summary:** Widened the deterministic infrastructure-intent gate to accept
realistic descriptions that omit product-specific cloud terms. Added a
deadline regression test that checks the stub receives no second prompt
when fewer than one second remains after an invalid first plan.

**Requirements addressed:** FR-I-02, FR-A-04, PR-05.

**Files:** changed `backend/app/domain/input_rules.py`,
`backend/tests/unit/test_input_rules.py`,
`backend/tests/unit/test_architect.py`, and
`docs/design-deviations.md` (CL-04).

**Decisions:** Single-word terms accept optional whole-word suffixes `s`,
`es`, `ing`, and `ed`. Added terms for stores, online platforms, serving,
scheduled jobs, applications, and WebSockets while keeping the list at 100
terms. CL-04 now states that this coarse gate favours false accepts over
false rejects. The budget test uses a fake clock: the first invalid plan
consumes 149.5 of 150 seconds, leaving too little time to start another call.

**Tests:** `make test` → 218 passed, 0 failed, 0 skipped. `make lint` →
Ruff check passed, Ruff format check passed (69 app/test files), mypy passed
(43 source files). The new tables cover 14 accepted descriptions, six
rejected descriptions, and all four suffixes; existing intent tests still
pass. With the pre-call `remaining < 1` guard temporarily removed, the new
budget test failed as intended because the stub recorded two prompts;
after restoring the guard, it passed with exactly one prompt. No network
call was made.

**Known gaps / follow-ups:** The word list is intentionally lenient and
can accept text that merely mentions an infrastructure term. No HTTP
mapping or real-provider evaluation was added in this follow-up.

---

## 2026-09-27 — Phase 2 — Input rules and ArchitectAgent

**Summary:** Added deterministic input validation, per-run configuration,
a strict AWS deployment plan, schema-derived prompts, an agent-wide budget,
the ArchitectAgent and factory, and a sequential evaluation runner. The
offline stub report covers five cases and an invalid-then-valid correction.

**Requirements addressed:** FR-I-01, FR-I-02, FR-I-04, FR-A-01,
FR-A-02, FR-A-03, FR-A-04, partial preparation for FR-A-05, PR-05,
NFR-01, NFR-03, UC-01.

**Files:** added `backend/app/domain/input_rules.py`, `run_config.py`,
`plan.py`, `backend/app/agents/*`, `backend/scripts/eval_architect.py`,
eight new unit test modules, and the stub report under `docs/evals/`;
changed `backend/app/domain/models.py`, `app/core/config.py`,
`app/llm/base.py`, `app/llm/stub.py`, existing unit and canary tests,
`.env.example`, `Makefile`, `README.md`, and `docs/design-deviations.md`.

**Decisions:** D-10 makes the plan strict and limits compact UTF-8 JSON to
32,768 bytes; D-11 records the versioned schema-derived correction prompt.
CL-04 sets validation order to controls, length, then intent. CL-05 replaces
the nine-character `a web app` example with `build a web app`. OQ-05 is
resolved by passing the agent's remaining budget into each call, where the
Phase 1 policy may impose a shorter deadline. A valid call result is returned
after validation without a second budget check. The evaluation loads fixture
scripts into the factory-created stub adapter through its public method;
the fixtures remain outside `app/`.

**Tests:** `make test` → 193 passed, 0 failed, 0 skipped. `make lint` →
Ruff check passed, Ruff format check passed (69 app/test files), mypy passed
(43 source files). `make eval-architect EVAL_ARGS='--provider stub'` produced
five passing case reports and a passing correction diagnostic. New tests
cover input boundaries and precedence, schema and graph failures, prompt
tag neutralization, shared deadlines and near-deadline success, correction
feedback, factory overrides, post-construction stub scripting, and report
format. No network call was made.

**Known gaps / follow-ups:** HTTP 400/422 mapping, run persistence and
`plan_created` events, generators, and real-provider evaluation belong to
later phases. On a permanent LLM failure after possible internal retries,
the Phase 1 error does not expose the exact transport attempt count;
`ArchitectRunInfo.total_llm_attempts` is `None` rather than an invented
number. The schema requires an `ambiguities` field, but the completeness of
an LLM's ambiguity notes remains a semantic evaluation question. OQ-03 and
OQ-06 remain open pending the author's provider choice and measurements.

---

## 2026-09-26 — Phase 1 follow-up — Rate-limit retry and real timing result

**Summary:** Both LLM adapters now carry parsed `retry-after` seconds on
HTTP 429 into the shared retry wrapper. Recorded the author's real Groq
timing spike and the free-tier throughput limit it exposed.

**Requirements addressed:** FR-A-04, PR-05, NFR-01.

**Files:** changed `backend/app/llm/errors.py`, `base.py`, `anthropic.py`,
and `openai.py`; changed `backend/tests/unit/test_llm_base.py` and
`test_llm_providers.py`; changed `docs/design-deviations.md`; added the
metrics-only real-provider JSON and Markdown files under `docs/spikes/`.

**Decisions:** D-09 respects a finite nonnegative `retry-after` value in
seconds on 429, taking the greater of that delay and jittered backoff.
If the delay consumes the remaining call budget, the wrapper raises
`LLMDeadlineExceeded` without sleeping. Invalid or missing headers fall back
to ordinary backoff; raw header text is neither retained nor logged. OQ-03
records the 2026-09-26 Groq free-tier spike: one full call finished in
24.6 s with 11,660 output tokens, while all nine split calls were rate
limited. OQ-06 defers evaluation-provider throughput choice.

**Tests:** Before the first commit, `make test` → 137 passed, 0 failed,
0 skipped; `make lint` → Ruff check passed, Ruff format check passed
(52 app/test files), mypy passed (34 source files). Deterministic
`httpx2.MockTransport` tests cover both providers' 429 headers, a 20-second
delay before success, deadline rejection without sleep, and fallback for
missing or invalid headers. Both commands were rerun before the second
commit with the same results.

**Known gaps / follow-ups:** The real spike is one measurement on Groq's
free tier. OQ-03 remains open until the evaluation provider is selected;
OQ-06 requires enough token throughput for parallel generation. No real API
call was made by Codex.

---

## 2026-09-26 — Phase 1 follow-up — OpenAI-compatible base URL

**Summary:** Added optional `LLM_BASE_URL` so the existing OpenAI adapter can
send Chat Completions requests to a compatible endpoint without a new
provider class. The unset value keeps the SDK's default endpoint.

**Requirements addressed:** FR-I-04, NFR-03.

**Files:** changed `backend/app/core/config.py`,
`backend/app/llm/factory.py`, `backend/app/llm/openai.py`,
`backend/tests/unit/test_config.py`, `backend/tests/unit/test_llm_factory.py`,
`.env.example`, `README.md`, and `docs/design-deviations.md`.

**Decisions:** D-08 documents this endpoint override. Empty
`LLM_BASE_URL` is treated as unset, matching the optional model and key
settings. Only `OpenAIAdapter` receives the override. The README Groq
example uses the endpoint and model documented by Groq; no real key was
used.

**Tests:** `make test` → 121 passed, 0 failed, 0 skipped. `make lint` → Ruff
check passed, Ruff format check passed (52 app/test files), mypy passed
(34 source files). New tests verify the optional setting and the final SDK
request URL through `httpx2.MockTransport`, both with and without an
override.

**Known gaps / follow-ups:** No real OpenAI-compatible provider was called;
OQ-03 still awaits the author's timing measurement with a real key.

---

## 2026-09-25 — Phase 1 — LLM adapters and timing spike

**Summary:** Added the provider-independent async JSON completion wrapper,
Anthropic/OpenAI/Stub adapters, configuration factory, offline provider and
retry tests, and a timing spike with full/split and truncation reporting.
No agent or pipeline behavior was added.

**Requirements addressed:** NFR-01, NFR-03, FR-I-04; partial timing evidence
for FR-A-04 and PR-05 at the single-call boundary.

**Files:** added `backend/app/llm/*`, `backend/scripts/*`, four Phase 1 unit
test modules, and a stub JSON/Markdown pair under `docs/spikes/`; changed
`AGENTS.md`, `backend/pyproject.toml`, `backend/requirements.lock`,
`backend/app/core/config.py`, `backend/tests/unit/test_config.py`,
`backend/tests/integration/test_canary.py`, `.env.example`, `Makefile`,
`README.md`, and `docs/design-deviations.md`.

**Decisions:** D-07 adds concrete `complete_json` while keeping exactly two
abstract provider methods. The installed SDKs are Anthropic 1.8.0 and OpenAI
3.19.2; both use `httpx2` custom transports, so `httpx2` is an explicit
runtime dependency for adapter type signatures and offline mocks. Phase 0's
`httpx` remains installed and unaliased. OpenAI 3.19.2 has Chat Completions,
so no Responses API deviation was needed. Anthropic Messages sends no
`temperature`, `top_p`, or `top_k`. CL-03 resolves contradictory retry
arithmetic. The spike includes Dockerfile, missing from the prompt's workload
list but present in the spec. OQ-03 awaits a real-provider measurement; OQ-05
defers the end-to-end agent deadline to Phase 2. The spike's
`--max-output-tokens` defaults to the configured 16000 and its verdict fails
when calls truncate.

**Tests:** `make install` succeeded with the regenerated lock. `make spike`
with `LLM_PROVIDER=stub` produced the committed format example (3 full calls
and 27 split calls). `make test` → 118 passed, 0 failed, 0 skipped. `make lint`
→ Ruff check passed, Ruff format check passed (52 app/test files), mypy passed
(34 source files). New tests in `test_llm_base.py`, `test_llm_providers.py`,
`test_llm_factory.py`, and `test_spike_llm_timing.py` cover retries, deadlines,
strict parsing, both SDK status and transport-error mappings with
`httpx2.MockTransport`, factory
selection, spike output, and truncation. The existing canary module now tests
both SDKs with a canary in mocked 401 headers and bodies.

**Known gaps / follow-ups:** The stub example is only a format check; the
author must run the spike with a real key to assess OQ-03. The 150-second
wrapper deadline applies to one `complete_json` call; Phase 2 must design
the stage-wide agent budget (OQ-05). No real API call was made.

---

## 2026-09-25 — Phase 0 — Harden concurrency and privilege tests, pin dependencies

**Summary:** Made the event prefix test sensitive to loss of the PostgreSQL
advisory lock, required the exact insufficient-privilege SQLSTATE in denied
operation tests, pinned installed dependencies, and made the PostgreSQL init
script executable.

**Requirements addressed:** FR-P-04, NFR-01.

**Files:** changed `backend/tests/integration/test_events.py`,
`backend/tests/integration/test_privileges.py`, `Makefile`, `README.md`, and
`docker/postgres/init/01-roles-and-databases.sh` (mode 100755); added
`backend/requirements.lock`.

**Decisions:** The three prefix-test writers share a seeded random generator
(`23`) and hold each inserted event for up to 5 ms before commit. The
`TRUNCATE` check covering `pipeline_runs` names all three tables so a foreign
key cannot explain its failure; each denied statement must yield SQLSTATE
`42501`. `make install` uses the frozen versions as pip constraints.

**Tests:** With the advisory-lock query temporarily changed to `SELECT 1`,
the prefix test failed on 3 of 3 runs; after restoration, it passed on 3 of
3 runs. `make install` succeeded with the constraints file. `make test` →
63 passed, 0 failed, 0 skipped. `make lint` → Ruff check passed, Ruff format
check passed (41 files), mypy passed (27 source files).

**Known gaps / follow-ups:** None for this review fix. No new specification
deviation or open question was introduced.

---

## 2026-09-25 — Phase 0 — Foundations implemented

**Summary:** Built the Python backend foundation, PostgreSQL schema and
least-privilege roles, durable event log, retention command, and health API.
No agent, LLM, SSE, download, or frontend feature is present yet.

**Requirements addressed:** FR-S-03, FR-S-05, FR-S-07, FR-S-09, FR-V-05,
FR-G-07, FR-P-04, FR-UI-06, NFR-01.

**Sections and files:**
1. Repository layout: added backend package directories and frontend
   placeholder; extended `.gitignore` while retaining its existing entries.
2. Dependencies: added `backend/pyproject.toml` with only approved packages.
3. Database setup: added `docker-compose.yml`, the PostgreSQL init script,
   `.env.example`, and `Makefile`.
4. Configuration: added `app/core/config.py` and its unit tests.
5. Logging: added `app/core/logging.py` and redaction tests.
6. Errors and health: added the app factory, safe error handler, health route,
   and resource accessor with unit tests.
7. Domain: added enums, transition tables, remediation-budget decision,
   path rules, value objects, and corresponding unit tests.
8. Database: added Alembic configuration and initial migration, SQLAlchemy
   models and repositories, test fixtures, migration-parity and PostgreSQL
   integration tests, including a two-session stale-state transition check.
9. Events: added `EventLog`, publisher types, app-owned instance, and
   concurrency, replay, publication, and singleton tests.
10. Retention: added `app/cli.py` and integration coverage for dry-run and
    package-only deletion.
11. Acceptance: added real-database health and secret-canary tests and ran
    the full suite.
12. Documentation: updated this log, `README.md`, and
    `docs/design-deviations.md`.

**Decisions:** D-01 to D-06 and CL-01 are implemented as described in the
deviation log. CL-02 resolves FR-S-07 sequencing: stop remediation, validate,
then enter review. Application code uses one EventLog instance per process;
database ordering still holds across independent writers. App-role identity
insertion succeeded without a sequence grant, so none was added. Run status
is classified at automated completion and remains terminal during review.

**Tests:** `make test` → 63 passed, 0 failed, 0 skipped; `make lint` → Ruff
check passed, Ruff format check passed (41 files), mypy passed (27 source
files). `make install`, `make migrate`, and `make migrate-test` succeeded.
`make run` served `/api/health` with HTTP 200, `database: ok`, and
`llm_configured: false`. `make sweep` completed with 0 packages deleted.

**Known gaps / follow-ups:** The Phase 0 boundary excludes agent logic,
real LLM calls, SSE, review/download endpoints, ZIP writing, and frontend
code. OQ-01, OQ-03, and OQ-04 remain for their later phases.

---

## 2026-09-25 — Phase 0 (setup) — Repository initialised

**Summary:** Repository created with specification (`docs/spec/`), agent
instructions (`AGENTS.md`), this log, and the design-deviation log seeded with
decisions agreed during design review. The spec includes the redrawn
diagrams (package states, run states, sequence, ERD, class diagram), which
now agree with the chapter text.

**Requirements addressed:** none — infrastructure.

**Files:** added `AGENTS.md`, `docs/IMPLEMENTATION_LOG.md`,
`docs/design-deviations.md`, `docs/spec/*`.

**Decisions:** See D-01 to D-06, CL-01 and OQ-01 to OQ-04 in
`docs/design-deviations.md`. OQ-02 is resolved by Option C. D-01 to D-03,
D-05 and D-06 are already part of the thesis design.

**Tests:** none yet.

**Known gaps / follow-ups:** Phase 0 implementation.
