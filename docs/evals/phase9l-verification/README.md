# Phase 9l verification

This evidence covers local functional verification of human-curated advisory
lessons. No real inference, external provider service, deployment, installation
or dotenv read was used. Tests use real isolated PostgreSQL 16 with migration
and application roles; browser inference uses existing stubs/mocked HTTP.
Backend and browser full suites used separate PostgreSQL instances so their
owner cleanup could not interfere. Existing historical UI evidence is restored
byte-for-byte after browser verification.

Final command results, source fingerprints and evidence hashes are recorded in
[results.json](results.json). The implementation log records intermediate
failures and fixes.
The [thesis notes](../../thesis-notes/phase9l-curated-lessons.md) explain the
design and interpretation; [D-60](../../design-deviations.md#d-60--human-curated-advisory-lessons-and-injection-defense-phase-9l)
records the extension and threat model. [UI evidence](../phase9l-ui/README.md)
contains inspected Chromium screenshots at 1280×800.

| Final command | Result |
|---|---|
| `make test` | 2,466 passed; 0 failed/skipped; 6 performance tests deselected; 750.49s |
| `taskset -c 0,1 make frontend-test` | 435 passed across 43 files; 0 failed/skipped; 93.31s |
| `make test-e2e` | 21 passed; 0 failed/skipped; 8.6m |
| Separate self-approval-exception browser run | 1 passed; 0 failed/skipped; 32.0s |
| `make lint` | Exit 0; mypy 181 sources; Ruff and frontend ESLint/TypeScript pass |
| `make frontend-build` | Exit 0; 184 modules transformed |
| `make secret-scan` | Exit 0; 0 findings; 0 scan errors |

| Requirement boundary | Evidence |
|---|---|
| Named-account ownership, admin privileges, CSRF, default four-eyes, immutable successors/sets and audit rollback | `tests/integration/test_phase9l_governance.py` |
| Separate self-approval confirmation, actor/session/revision/filter/set/policy/expiry binding and wrong-proposer rejection | Governance suite plus `test_phase9l_confirmation_target.py`; browser exception run with policy explicitly false |
| Strict structure, NFKC, invisible/control rejection, fixed vocabulary and server filter | `tests/unit/test_phase9l_lessons.py`, `test_phase9l_corpus.py` and governance approval recheck |
| Unapproved syntax survivors never reach prompts | `test_corpus_survivors_require_human_approval_before_any_hook` |
| Role-only selection, escaped numbering, complete-entry limits and unchanged system messages | Domain renderer tests and corrective/regeneration integration tests |
| No hook/dispatcher/governance query for disabled, unconfigured, empty-role or benchmark adapters; complete serialized body equality | 48 cases in `tests/unit/test_phase9l_wire.py`, using 12 captured pre-integration bodies from revision `29751f1` |
| Immediate disable before later attempts/retries, no wait for in-flight response, sticky after re-enable | Explicit-event synchronized transport tests |
| Actual-use dispatch/telemetry deduplication, retained set/hash/self-approval and archive evidence | `tests/integration/test_phase9l_transport.py`, existing results/download/bundle tests, seed download and browser ZIP/hash checks |
| Scanners/validation/readiness cannot be bypassed by advisory text | Before/after blocker/report/readiness comparison in transport suite; existing full backend security/validation suites |
| Retained deterministic counts and exact decision links, no raw reasons in aggregates | `tests/integration/test_phase9l_insights.py` and admin insights UI/browser tests |
| Proposal → filter → approval → visible run use → disable; keyboard focus and existing desktop geometry | Vitest lesson suites, `phase9l-lessons.spec.ts`, `phase9l-insights.spec.ts`, existing full browser suite |

The 46-case [corpus report](../phase9l-security/corpus.json) contains no raw
payloads: 10 structural rejections and 28 additional filter rejections give
38 cumulative. The independent raw filter rejects 29; this measurement is not
additive. All eight syntax survivors (six benign controls, two semantic
residuals) remain excluded while proposed. Delimiting, output controls and the
kill switch are tested boundaries, not universal semantic attack detectors.

Limitations remain explicit: filters/confusable maps/secret heuristics are
incomplete, approved malicious preferences can influence a model, self-approval
reduces review independence, and dispatch coordination assumes the existing
single-worker server. Output improvement requires separate author-run
evaluation. An extra PR-04 performance probe failed its unchanged two-second
bound (7.89–8.07 seconds); its cause is unestablished. The required functional
backend suite excludes six performance tests by its normal `not perf` marker.
