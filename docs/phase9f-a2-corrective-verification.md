# Phase 9f A2 corrective verification — 2026-10-18

Requirements: FR-G-02, FR-S-03/04/09, FR-V-03, NFR-01, PR-01/03/04/05.
Design/setting changes: D-46 A2. No source specification, readiness/severity/
blocking rule, migration or privilege change. No real LLM calls, dotenv reads,
installations, downloads, new dependencies or pushes.

## Preserved A2 findings

Author A2 evidence remains unchanged at
`evals/phase9-bench-real-20261018T163731511036Z`; full source JSON remains read-only
under `.cache/phase9f-a2-results/`. The original aggregate PR-05 verdict stays FAIL.

All six missing variants exhausted structural completeness after two successful
structured responses, before syntax recovery: 31c7c780/performance 4.804922 s;
52b11be8/cost 3.442726 s; 8614c9e9/performance 2.966098 s; a92bafec/cost 3.266075 s;
b8f9536f/performance 3.756861 s and security 3.414373 s. No recorded deadline,
regeneration or provider exception caused these failures. Their discarded file
maps and exact layout errors were not saved; those historical details remain unknown.

All five security overruns were in the concurrent PR-03 cohort: e0f47a31/cost/2
68.900529 s; a2ef9d64/security/2 62.703118 s; dc7ec97f/cost/0 61.718622 s;
dc7ec97f/performance/1 61.506421 s; a2ef9d64/performance/0 60.057306 s. The previous
implementation separately bounded work and a publication helper, leaving closing
notices/transitions outside. For e0f47a31/cost, publication ran approximately
52.84–61.17 s, then completion-notice/transition handling continued to 68.90 s.
Individual DB versus scheduling waits cannot be reconstructed from old timestamps,
which precede EventLog lock acquisition. Shutdown sums are not additive wall-clock
phase measurements. An offline 36-pass parse/reference probe over nine packages
blocked a scheduled callback for 2.539 s; this demonstrates cooperative scheduling
limits, not exact historical CPU attribution.

The 31 final builtin variable-reference failures belong to two syntax-repaired
packages: 9a6cfc31/performance (19; original missing comma at main.tf:202) and
dc7ec97f/security (12; missing AMI quote at main.tf:383). Declaration repair skipped
their invalid originals and was not retried after parsing succeeded. All referenced
variables existed in the originals, which had no variable declarations. Regeneration
was unused and partial acceptance did not introduce these references. Line movement
and partial observations incorrectly relabelled 22 origins as security_fix.

Two-sided Fisher exact test for [[3,38],[1,35]]: **p=0.618259407733092**.
Counting missing variants as unsuccessful gives [[3,39],[1,41]],
**p=0.615796519410977**. Neither comparison establishes a detectable difference;
small counts, correlated variants and changed prompts prevent causal attribution.

## Implemented corrections

Generation retries declaration repair after syntax recovery/regeneration and
accepted generation changes. Module content fingerprints replace gate presence
as the completion criterion. New declarations require native syntax checks;
unresolved modules remain blocking. All work shares the original 150-second budget.

GENERATOR_MAX_PACKAGE_ATTEMPTS defaults to **3 instead of 2**, including the initial
attempt; explicit overrides remain authoritative. Prompt v9 sends the missing
types/patterns/concrete suggested paths independently of truncated general feedback.
Per-attempt reports contain only source-free categories/counts and layout evidence.
Allowed alternative paths remain accepted. Two syntax rounds and one regeneration,
models and output-token settings are unchanged. Subsequent author comparisons must
use matched corrected code/prompt/settings; A2 used v8/two attempts.

One absolute iteration window now covers ordinary work, cancellation, restoration,
notices and closing state/event persistence. Five seconds remain reserved. Tool
shutdown and DB/lock waits are clipped to remaining time. Package-local bounded
caches reuse parsed documents/trees and reference/declaration indexes; no parsing
workers are introduced. Variable identities survive line movement and partial
observations; metadata distinguishes first observation from proven introduction.

If mandatory finalization cannot finish, the iteration fails closed. Existing
legal arrows settle the stage, including an interrupted publication after a clean
transition was committed. That fault-recovery tail uses the original remaining
stage allowance and remains visible in elapsed/overrun reporting. No hard real-time
guarantee is claimed for cooperative Python scheduling under external CPU/DB faults.

## Offline replay and workload views

Command:

```sh
cd backend
.venv/bin/python -m scripts.phase9f_a2_replay --output /tmp/phase9f-a2-replay.json
```

Artifact: [A2 replay](evals/phase9f-a2-corrective-replay-20261018.json).
Replay uses the two saved parsable final checkpoints, not new real-model syntax
repairs. It adds **19 + 12 declarations**, reduces **31 variable failures to zero**,
passes native syntax checks and is idempotent. SHA-256 hashes of all fourteen input
JSON files remain unchanged. Readiness was not recomputed.

Additional historical PR-05 views use exactly the existing thresholded observations:

| Workload | Observations | Failures | Verdict |
|---|---:|---:|---|
| Isolated PR-01 | 159 | 0 | PASS |
| Isolated PR-03 baseline | 19 | 0 | PASS |
| Concurrent PR-03 cohort | 57 | 5 | FAIL |

The aggregate calculation, thresholds and event timestamp boundaries are unchanged.
Historical rows without classification remain unknown, and empty additional groups
do not change the aggregate verdict.

## Verification

- `make lint`: Ruff/format, mypy (125 application sources), frontend ESLint/TS PASS.
- `make test`: **1,507 passed, 0 failed, 0 skipped, 6 performance deselected
  (210.11 s)** with the final acceptance-expiry guard included. The preceding
  1,506-test checkpoint and 29 focused acceptance tests also passed.
- `make frontend-test`: 100 tests / 15 files PASS.
- `make test-e2e`: 6 PASS (2.1 min), separate isolated PostgreSQL 16 container.
- `make provider-schema`: all seven pinned versions exported offline.
- `make secret-scan`: **0 findings / 0 scan errors**, working tree and all
  refs/reflogs through source commit d5a1857. Evidence:
  [audit](evals/phase9-secret-scan-20261018T192138796355Z/summary.md).
- `make bench-stub`: completed twice; both actual outcomes are retained below.

The first full-suite attempt was interrupted after failures in legacy continuation
fixtures: terminal scan timings had been attached as fix verification metadata,
and old fake-clock fixtures spent 61 seconds while expecting reserve-time recovery.
Terminal scans now retain separate timing records; work-timeout fixtures spend 56
seconds, while a dedicated hard-expiry fixture keeps 61 seconds and verifies
scan_error with unchanged files. A separate stage-budget fixture stays inside the
iteration deadline while exhausting the stage's remaining work allowance.
The resulting full checkpoint passed **1,502 tests / six performance deselected**
(281.86 s), before the final boundary/expiry regressions.

All PostgreSQL checks use an isolated task-owned Docker PostgreSQL 16 instance,
the repository initialization script and normal owner/app privileges. Stub and
backend verification overlap; reported timings are observed verification overhead,
not an isolated real-model performance claim.

A later 150 ms integration watchdog raced setup while the benchmark and backend
checks shared CPU. Deadline fault tests now expire after an explicit phase-entry
signal, while separate timer tests still exercise real asynchronous cancellation.
A final fault injection also reproduced acceptance after provenance consumed the
remaining budget; a post-observation deadline check rejects that result. No expired
candidate is allowed to advance the retained checkpoint.

## Stub benchmark evidence

The loaded run remains at
[summary](evals/phase9-bench-stub-20261018T185418022034Z/summary.md): 14 pipeline runs,
42/42 ready packages, ten labelled synthetic downloads excluded from quality rates.
PR-01 PASS (median 19.559164 s), PR-03 FAIL (ratios 2.632652–2.873781), PR-05 PASS.
PR-04 FAIL: median 1.606764 s, maximum 2.141344 s; one of ten requests exceeded
its unchanged two-second threshold. This run overlapped backend verification.

After other verification jobs finished, a fresh backend ran the delivered initial
boundary changes. The second full stub run is preserved at
[summary](evals/phase9-bench-stub-20261018T191346950459Z/summary.md): 14 pipeline runs,
42/42 ready packages and ten synthetic downloads, all 9,989,867-byte archives.

- PR-01 PASS: median 13.778885 s, maximum 16.177687 s.
- PR-03 FAIL: cohort ratios 2.798020–2.830299 versus unchanged 1.5x threshold.
- PR-04 PASS: median 1.100812 s, maximum 1.295116 s; zero requests above two seconds.
- PR-05 PASS: isolated PR-01 70/0, isolated PR-03 baseline 7/0, concurrent cohort 21/0
  thresholded observations/failures. The aggregate calculation is unchanged.

Both runs record 16,000 generator output tokens, 140-second attempt timeout,
150-second generator budget, **three package attempts**, 45-second fixer attempts,
60-second iterations, 240-second stages, four iterations, two resources/12 findings
and six partial evaluations. Clean stub packages needed no security fixes; separate
scripted native verification remains descriptive. These are stub measurements,
not a new real-model success rate. The last one-line acceptance-expiry check was
verified separately; it does not execute on the clean-package benchmark path.

No threshold was changed to make either run pass. Both the loaded PR-04 failure
and the subsequent successful measurement remain evidence; the timing difference
alone does not isolate a single scheduling/DB cause. PR-03 remains a measured failure.

Task-owned stub servers and both isolated PostgreSQL containers were stopped and
removed after verification. The existing application PostgreSQL on 5432 remains
available. Only pre-existing untracked workspace files remain outside these commits.
No new open question was added; historical missing evidence and real-model
performance remain unverified. Both author fixer configurations should use matched
corrected source, prompt v9 and the same explicit package-attempt setting.
