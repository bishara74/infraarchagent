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
