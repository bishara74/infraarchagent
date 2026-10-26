# Specification TC identifiers → executable evidence

The seven group IDs below come from the Chapter 3 matrix; they are not pytest
node IDs. Requirement annotations are collected independently across pytest,
Vitest and Playwright by `backend/scripts/traceability.py`. Collection establishes
linkage, not passing execution or requirement satisfaction. Current execution
counts are recorded in `IMPLEMENTATION_LOG.md` and Phase 10 verification logs.

| Specification TC | Real tests (representative, not an exhaustive count) | Evidence / qualification |
|---|---|---|
| TC-pipeline-01 | `backend/tests/integration/test_pipeline_orchestrator.py::test_barrier_blocks_security_until_every_generator_resolves` (success and failed last generator); `test_pipeline_api.py::test_architect_invocation_sees_committed_run`; `test_pipeline_sse.py` | Real PostgreSQL and explicit synchronization; stub stages. `docs/evals/phase10-verification/section3-tests.txt`. |
| TC-security-01 | `backend/tests/integration/test_security_agent.py::test_two_fix_passes_and_three_first_scan_counts`; `test_phase9e_continuation.py`; `backend/tests/unit/test_security_diff.py` | Recorded scans and scripted fixes establish deterministic behavior; actual scan evidence: `docs/evals/phase5b-security-20261001T191131076470Z/`. D-22/D-31 qualify literal spec scanning. |
| TC-ui-01 | `frontend/src/components/progress.test.tsx`; `DiffView.test.tsx`; `frontend/src/screens/screens.test.tsx`; `frontend/e2e/review-flow.spec.ts`; `phase10-review.spec.ts` | Progress/SSE, missing variants, diff, passed/failed validation and settled review. Browser is Chromium; Windows Chrome/Firefox/Edge clean-deployment matrix remains manual. |
| TC-generator-01 | `backend/tests/unit/test_generators.py`; `test_directive_checks.py`; generator barrier test above | Directives are preferences, not guaranteed output properties (D-13). Actual original-package directive and first-scan measurements are in the Phase 10 alignment report. |
| TC-perf-01 | `backend/tests/integration/test_phase9_benchmark_http.py`; `test_security_agent.py::test_iteration_deadline_preserves_unmodified_files`; `backend/scripts/benchmark.py` | Real matched sets: `docs/evals/phase9-bench-real-20261020T010134093069Z/` and `phase9-bench-real-20261020T013911945957Z/`; PR-03 remains not met. Local stub/performance checks cannot replace real-provider PR-01/05 evidence. |
| TC-adapter-01 | `backend/tests/unit/test_llm_base.py`; `test_llm_factory.py`; `test_llm_providers.py`; `test_architect.py`; `test_generators.py` | Stub adapters and mocked provider transports; no real credentials or inference. D-07 documents the shared adapter template method. |
| TC-review-01 | `backend/tests/integration/test_pipeline_review.py`; `test_pipeline_review.py`; `test_phase9g_labels.py`; `frontend/e2e/review-flow.spec.ts`; `phase10-review.spec.ts` | Approve/reject/retry, preserved evidence, labelled downloads and hidden settled controls. D-47 replaces production-ready claims with honest labels. |

Some test modules above contain several node IDs. The generated report lists the
full actual node IDs; use that report to locate individual cases and their
requirement markers. Do not infer a missing test from an outdated filename in a
historical report.

## Agent replacement (NFR-02)

`test_pipeline_orchestrator.py::test_agent_contract_replacement_without_peer_or_orchestrator_changes`
has six cases: Architect, Cost Generator, Performance Generator, Security Generator,
Security stage and Validator. Each replaces only the selected implementation at
the existing factory/stage seam, exercises dispatch, persistence and settlement,
and leaves peer/orchestrator source unchanged. Architect exposes
`parse_input`/`generate_plan`; generators expose `generate(plan)`; stages expose
`run(context, variant, package)`.

This proves the ordinary dispatch seams. Concrete-class recovery checks,
`generator.last_run` and private `_last_run` telemetry mutations remain coupled.
NFR-02 is **partly met**, not unrestricted replaceability; see D-55. No broad
orchestrator refactor is included.

## Reproduction

```bash
make traceability TRACEABILITY_ARGS='--output-dir ../docs/evals/phase10-traceability-new'
```

The destination must be fresh. The collector does not execute test bodies or
load dotenv. Frontend unit/component tests carry requirement/use-case IDs in
their titles; Playwright carries them in test/parent titles; pytest uses `req`
markers. NFR-04 links to kit checks only and remains unverified without the
author's deployment evidence. [The evidence index](evals/EVIDENCE.md) separates
status from annotations.
