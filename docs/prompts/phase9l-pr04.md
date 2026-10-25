# Codex task — Phase 9l follow-up: PR-04 archive download timing

Fresh session. Read `AGENTS.md`, the PR-04 requirement, the earlier PR-04
evidence and implementation-log entries, `backend/tests/integration/test_pipeline_download.py`
(`test_ten_megabyte_package_download_under_two_seconds`), the archive/download
code (`backend/app/domain/archive.py`, `backend/app/pipeline/results.py`, the
download API) and `backend/scripts/measure_performance.py`.

## Facts from the author's quiet machine

- HEAD `b6e4185`: the PR-04 test measured 2.149, 2.240, 2.536 and 2.380 s
  (limit 2 s; 7.58 MB archive). The other five `perf` tests pass.
- During Phase 9l verification under load it measured 7.89–8.07 s.
- Earlier PR-04 evidence reported a maximum of about 0.73 s; confirm what that
  measurement was and where it is recorded.
- `make test-perf` stops with "Phase 9 tool failed; check prerequisites" and
  an INCOMPLETE summary without a reason, while
  `scripts.run_verification pytest -m perf` runs.
- A git worktree at `29751f1` (before Phase 9l) printed nothing when the test
  was run with the main checkout's venv.

## Tasks

1. **Baseline comparison.** Measure the PR-04 test at least five times each at
   `29751f1` and at HEAD on the same machine, with nothing else running. Use
   a temporary worktree outside the repository and the existing venv (no
   installs); make the old revision's imports resolve to the worktree. Report
   every time, median and maximum.
2. **Cause.** If HEAD is slower, find the cause (profile the request; compare
   archive construction, queries, provenance/lesson data, hashing,
   compression, event loading). If both revisions are similar, say so and
   explain the difference from the earlier ~0.73 s evidence.
3. **Fix if Phase 9l caused it.** Keep archive contents, hashes, manifest,
   provenance, security and retention behaviour byte-identical (existing
   download/bundle tests must pass). Do not change the 2-second threshold or
   the test's package size. If the slowdown predates 9l, do not tune blindly:
   report the findings and options and stop for the author's decision.
4. **`make test-perf` diagnostics.** Make it report which prerequisite or
   test failed (no secrets), and make it run the same suite that
   `run_verification pytest -m perf` runs.

## Rules

No real LLM calls, no `.env` reads, no installs, no network, no push. Plan
mode first. Commit prefix `phase9l:`, requirement IDs (PR-04, NFR-01),
implementation-log entry with real measurements. Run `make lint`,
`make test`, the perf suite (real times) and `make secret-scan`. Summary in
the `AGENTS.md` §10 format, starting with the measured comparison.
