# Phase 9m verification

All six requested targets passed. Exact counts, durations, limitations and
verification corrections are in [results.json](results.json), with actual
command logs alongside it. Functional verification used dotenv-disabled
bootstrap, synthetic settings and two separate disposable UTF-8 PostgreSQL 16
clusters with normal owner/app/inspection-role grants. No real inference,
external service, installation, author database or key was used.

| Check | Result |
|---|---|
| make lint | Pass; Ruff/format 40 script + 386 app/test files, mypy 185 sources, frontend ESLint/TypeScript |
| make test | 2,632 passed; 0 failed/skipped; 6 perf deselected |
| make frontend-test | 459 passed in 45 files; 0 failed/skipped; two-CPU affinity, unchanged timeouts |
| make test-e2e | 33 passed; 0 failed/skipped |
| make test-perf | 6 passed; 0 failed/skipped; PR-04 1.060254 seconds |
| make secret-scan | 0 findings; 0 scan errors |

The extended browser rerun adds active Generate/View results and five-target
retry-cap interactions to the same twelve gate scenarios: 12 passed in 54.5s.
The [UI inventory](ui-controls.md) maps controls to unchanged gates and recovery
hints. The [desktop capture](ui-download-reasons.png) uses explicit synthetic
API responses, not a real provider run. Hint geometry is checked at 1280×800;
91 historical tracked captures from the full run were restored.

[Corpus evidence](filter-corpus.json) reports both v1 and v2 for original and
expanded corpora, separately counting structural, independent raw filter,
additional filter and cumulative outcomes. Independent and additional counts
are not additive. [Filter fingerprints](filter-fingerprints.json) preserve exact
configurations/corpora. [Source fingerprints](source-fingerprints.json) record
the baseline and confirm protected spec, readiness, policy, threshold, v1 and
frontend dependency files are unchanged.

The final file-input review's escaped-separator correction is covered by 64
passing focused input/Terraform checks and the final full backend suite. D-61
and the request-path thesis notes retain OS-sandbox and heuristic limitations.
Measured synthetic checks do not establish real-provider lesson improvement or
successful infrastructure deployment. Run `make migrate`, restart the backend,
then repeat the author's manual ECS check outside Codex.
