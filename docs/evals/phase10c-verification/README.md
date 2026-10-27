# Phase 10c sections 2–3 — regression verification

The guard fixes and explicit refused-file finding are committed in `ce205ea`.
The [accepted diagnosis](../phase10c-diagnosis/README.md) is frozen. The
[offline replay](../phase10c-replay/README.md) records before/after deterministic
observations without a new model trajectory or pass-rate claim.

Tests used the existing dotenv-disabled bootstrap, stub providers, synthetic
credentials and a disposable native UTF-8 PostgreSQL 16 database on loopback
port 55444. Existing owner/app/inspection roles, migrations and application
privileges were preserved. Browser tests used isolated loopback ports 18144 and
15144. No installs, external services, real model calls or real credential reads
were performed. The native replay used existing offline tools and provider
mirrors; runtime versions and source hashes are in its manifest.

## Completed checks

| Command | Result | Evidence |
|---|---|---|
| `make lint` | Exit 0; Ruff/format, mypy 189 sources, ESLint and both TypeScript configurations | [log](make-lint.txt) |
| `make test` | 2,791 passed, 0 failed/skipped; 6 performance tests deselected; 634.61s | [log](make-test.txt) |
| `make frontend-test` | 467 passed, 0 failed/skipped; 46 files | [log](make-frontend-test.txt) |
| `make test-e2e` | 35 passed, 0 failed/skipped; 9.3m | [log](make-test-e2e.txt) |
| `make test-perf` | 6 passed, 0 failed/skipped; 2,791 deselected; 24.36s | [log](make-test-perf.txt), [measurements](performance/results.json) |
| `make secret-scan` | Exit 0; 0 findings, 0 scan errors; working tree and all refs/reflogs | [report](secret-scan/summary.md), [log](make-secret-scan.txt) |
| Traceability generation | 59 requirement IDs; 0 uncovered, 0 invalid annotations, 0 collection failures | [report](../phase10c-traceability/traceability.md) |
| Evidence-index generation | 45 met, 12 partly met, 1 not met, 1 unverified | [log](evidence-index.txt) |

The full backend suite includes the three historical run-3/run-4 ALB candidate
rollbacks through the real database loop, exposure-path and ambiguity
regressions, refused-read process-boundary checks, the pending-review integration,
and ten exact-diff/input-scope replay tests. No exposure flip is allowed, no
dynamic file read is executed, and no readiness or blocking threshold changes.
The pending-review integration preserves source bytes and the critical finding,
retains the validation error and keeps download unavailable.

All 5,996 protected tracked evidence/specification files retain their exact
pre-verification bytes; see [hash audit](historical-preservation.json). Browser
tests refreshed captures into this folder and preserved all 192 protected
historical browser files; see [browser audit](browser-history-preservation.json).
The generated canonical evidence index was byte-identical. New browser output
is under [ui/](ui/). Raw snapshots, caches and task database files are uncommitted.

Section-2 focused checks and the initial synthetic database-role setup correction
are recorded in D-64 and the implementation log. Two early stdlib-only operator
wrappers used system Python, whose bootstrap emitted a missing-pydantic warning;
the verification children used the repository virtualenv and completed
successfully. The replay and all application verification use that virtualenv.

Performance tests ran after replay and browser/backend suites stopped, without
other task workloads. The measured 10 MB package download took 0.87565s under
the unchanged two-second threshold. The make wrapper's fresh performance output
was relocated into `performance/`; its original destination remains in the
console log. No historical performance directory was modified.
The fresh secret-scan directory was likewise relocated into `secret-scan/`;
dotenv and cache paths were pruned before retrieval under the existing rules.

## Author's real-round rerun

Keep the scenario file and captured model/configuration fixed. In both author
terminals, with database URLs, master API key, encryption key and provider
credentials already supplied privately, use the existing README configuration:

```bash
export INFRAARCH_TEST_BOOTSTRAP=1
export PYTHONPATH="$PWD/backend/tests/bootstrap:$PWD/backend"
export LLM_PROVIDER=openai LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_MODEL=openai/gpt-oss-120b:nitro LLM_REASONING_EFFORT=low
export SECURITY_FIX_PROVIDER=openai
export SECURITY_FIX_MODEL=openai/gpt-oss-120b:nitro
export SECURITY_FIX_REASONING_EFFORT=low
export LLM_STRUCTURED_OUTPUT=json_schema GENERATOR_MAX_OUTPUT_TOKENS=16000
export GENERATOR_ATTEMPT_TIMEOUT_SECONDS=140 LLM_DEADLINE_SECONDS=150
export GENERATOR_DEADLINE_SECONDS=150 LLM_MAX_ATTEMPTS=3
export GENERATOR_MAX_PACKAGE_ATTEMPTS=3 FIX_ATTEMPT_TIMEOUT_SECONDS=45
export SECURITY_DEADLINE_SECONDS=240 SECURITY_FIX_MAX_RESOURCES=2
export SECURITY_FIX_MAX_FINDINGS=12 SECURITY_PARTIAL_MAX_GROUPS=6
```

Restart the backend on the fixed code/configuration in terminal 1:

```bash
make run PORT=8000
```

Then run this exact final-round schedule in terminal 2:

```bash
make bench-broad MODE=real BASE_URL=http://127.0.0.1:8000 \
  BUDGET=2 RUNS_PER_SCENARIO=2 MAX_RUNS=20 \
  PROVIDER_PREFERENCE=Cerebras \
  ARCHITECT_MODEL= ARCHITECT_THINKING= ARCHITECT_PROVIDER_PREFERENCE= \
  SMOKE=0 FORCE=0
```

This selects the same 20-slot forward/reverse schedule over the frozen ten
scenarios. Architect inherits the server model/reasoning without an explicit
provider preference; Generator/Fixer request Cerebras. Confirm actual served
providers from the new telemetry. `BUDGET=2` is the documented minimum credit
reserve, **not a total-spend cap**; the frozen final metadata does not establish
the original reserve setting. This author-only real command was not executed.
