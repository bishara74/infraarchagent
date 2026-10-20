# Codex task — Phase 9b: Final evaluation report and traceability

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-40 to D-54),
the latest `docs/IMPLEMENTATION_LOG.md` entries, `docs/spec/` (requirements,
use cases UC-01–UC-07, NFR list, PR thresholds), `backend/scripts/benchmark.py`
and its `quality` subcommand, `docs/phase9-runtime-attribution.md`,
`docs/notes/phase9b-todo.md`, and every `docs/evals/phase9-bench-*` folder.
Phases 0–9h are complete. **No more quality optimisation in this phase.**

## Why this phase exists

The measurements are finished. This phase turns them into one reproducible,
honest evaluation for Chapter 6 of the thesis, closes the requirement
traceability gaps, and records the known performance gaps with evidence.

Final real result (author-run, gpt-oss-120b for all roles, effort low):
- Set 1 `docs/evals/phase9-bench-real-<~20261020T01…>`: 7/40 checks passed.
- Set 2 `docs/evals/phase9-bench-real-<~20261020T…>` (newest): 8/41.
- Combined 15/81 = 18.5 %; Wilson 95 % CI 11.6–28.3 %; two-sided Fisher exact
  p = 0.021 vs the baseline 1/36. PR-01 PASS both sets (median 162.4 s /
  164.3 s, threshold 300 s), PR-05 PASS, PR-03 FAIL (cohort ≈1.7–2.1×).
Verify every number yourself from the folders; report any disagreement.

## Rules

No real LLM calls, no `.env` reads, no installs/downloads, no new
dependencies (implement Wilson and Fisher exact in pure Python with
`math.comb`; test against known values), no push. Never modify existing
evidence folders; write new output folders only. `.cache/` is read-only and
never committed. One commit per numbered section, prefix `phase9b:`,
requirement IDs, implementation-log entries with real test counts. Plan mode
first: report section 0 before code changes. Readiness, blocking criteria and
thresholds stay unchanged.

## 0. Investigate (report first)

- Inventory every real benchmark folder: date, commit, models/efforts,
  prompt version, number of complete runs, stop cause (complete, provider
  `usage_limit`, incomplete), packages, checks-passed, missing variants,
  PR-01/03/04/05 verdicts, measured cost. Identify which folders are
  comparable (same prompts and settings) and which are not.
- Which UC-01–UC-07 and NFR IDs (especially NFR-02) have no linked test,
  and what NFR-02 actually requires per `docs/spec/`.
- What the existing `quality` subcommand already computes, so the report
  reuses it instead of duplicating logic.

## 1. Reproducible final report

- A `make eval-report` target / script that reads only committed evidence
  folders and writes `docs/evals/phase9-final-report/`:
  `report.md` plus machine-readable `rates.csv`, `blockers.csv`,
  `timings.csv`, `costs.csv`, and an input manifest with folder names and
  file hashes.
- Main table, one row per benchmark (baseline → 9d → 9e → 9e2 → 9f A → A2 →
  A3 → B → final set 1 → final set 2 → final combined): what changed in that
  phase (one line), runs complete/planned, packages, checks-passed strict and
  contextual-v1, Wilson 95 % CI, missing variants, PR-01 median, PR-03 and
  PR-05 verdicts, cost. Mark incomplete sets (A3, B: stopped by HTTP 402)
  clearly; never pool non-comparable sets silently.
- Statistical comparison: final combined vs baseline and vs A3 (Fisher exact,
  two-sided), set 1 vs set 2 (reproducibility). State the test, the
  assumption (independent packages; three variants per run share a plan, so
  note the clustering caveat), and that p-values are descriptive.
- Final-set analysis: review-reason counts, top failed validation checks,
  top remaining blocking rules (strict and contextual), near-miss table,
  template and catalogue outcomes, fixer acceptance (A3 12/140 vs final),
  and the strict vs contextual explanation (why contextual equals strict:
  plan-to-resource mapping missing, D-48).
- Timing: PR-01 per set, stage medians, runtime attribution summary (D-54),
  PR-05 isolated vs concurrent views.

## 2. Requirement traceability

- Tag the E2E/integration tests that exercise UC-01–UC-07 with the existing
  requirement marker mechanism; add a test only where a use case has none.
- Add the missing NFR-02 check according to its spec text (report if it
  cannot be checked automatically and document a manual verification step).
- Generate `docs/evals/phase9-final-report/traceability.md`: every
  requirement ID → linked tests (and evidence folder for PR-*), with any
  remaining gaps stated explicitly.

## 3. Performance gaps, documented with evidence (no threshold changes)

- **PR-03:** explain the failure with evidence (CPU-bound local tools on the
  i5-1135G7/8 GB WSL2 machine; cohort ratios from the final sets; isolated vs
  PR-01-prompt-median methods). Draft, for the author to agree with the
  supervisor, a revised target statement and the measurement it would need —
  as text only.
- **PR-04:** (from `docs/notes/phase9b-todo.md`) measure, offline with stub
  data, the download latency with and without the per-request session check
  to see whether 9g/9h auth adds latency; fix only if a clear, guard-
  preserving cause is found; otherwise document.

## 4. Small tooling fixes

- `results.csv` holds fields > 128 KB (runtime telemetry): keep the CSV
  compact (move large telemetry to `results.json` or a separate file) and
  make every reader robust; update docs and tests. Historical folders stay
  as they are; readers must still handle them.

## 5. Thesis material

`docs/thesis-notes/chapter6-evaluation.md`: ready-to-adapt text and tables
for Chapter 6 (setup, method, results, statistics, threats to validity:
single machine, one model family, 14 prompts × 2 sets, clustering, provider
variability, stub vs real) and a "findings for discussion" list: Sonnet too
slow, Haiku prose-before-JSON (fixer schema missing until 9g), the fixer
acceptance jump 12/140 → 47/49, Trivy Terraform-JSON false positives, the
AWS access-log-target vs KMS rule conflict, remaining validity errors
(Unsupported argument), context-dependent rules that need plan-to-resource
mapping. Cite evidence folders and D-numbers; no invented numbers.

## 6. Finish

D-55 (evaluation method and statistics), README section "Reproducing the
evaluation". Run `make lint`, `make test`, `make frontend-test`,
`make test-e2e`, `make secret-scan`, `make eval-report` (real counts).
Summary in the `AGENTS.md` §10 format, starting with the section 0 inventory
and any numbers that differ from this prompt.
