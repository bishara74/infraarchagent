# One author-run Phase 10e real round

**This next round is the final reported result regardless of outcome.**

Run this only after the final Phase 10e commit and completed offline checks.
Use a quiet machine and keep other uses of the provider key stopped. Supply the
four database URLs, matching master API_KEY in both terminals, persistent
CREDENTIAL_ENCRYPTION_KEY and LLM_API_KEY privately in the author environment.
The bootstrap disables dotenv. No real credentials belong in this document.

From the repository root, apply this environment in **both terminals**:

```bash
export INFRAARCH_TEST_BOOTSTRAP=1
export PYTHONPATH="$PWD/backend/tests/bootstrap:$PWD/backend"
export LLM_PROVIDER=openai LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_MODEL=openai/gpt-oss-120b:nitro LLM_REASONING_EFFORT=low
export LLM_RESPONSE_FORMAT=json_object LLM_STRUCTURED_OUTPUT=json_schema
export SECURITY_FIX_PROVIDER=openai
export SECURITY_FIX_MODEL=openai/gpt-oss-120b:nitro
export SECURITY_FIX_REASONING_EFFORT=low
export GENERATOR_MAX_OUTPUT_TOKENS=16000
export GENERATOR_ATTEMPT_TIMEOUT_SECONDS=140 LLM_DEADLINE_SECONDS=150
export GENERATOR_DEADLINE_SECONDS=150 LLM_MAX_ATTEMPTS=3
export GENERATOR_MAX_PACKAGE_ATTEMPTS=3 FIX_ATTEMPT_TIMEOUT_SECONDS=45
export SECURITY_DEADLINE_SECONDS=240 SECURITY_FIX_MAX_RESOURCES=2
export SECURITY_FIX_MAX_FINDINGS=12 SECURITY_PARTIAL_MAX_GROUPS=6
unset ARCHITECT_MODEL ARCHITECT_THINKING ARCHITECT_PROVIDER_PREFERENCE

git diff --exit-code HEAD -- docs/evals/scenarios/broad-v1.json
sha256sum docs/evals/scenarios/broad-v1.json
```

Terminal 1: restart the backend with the completed code and this environment.

```bash
mkdir -p .cache/broad-benchmark
BROAD_TAG=$(date -u +%Y%m%dT%H%M%SZ)
LOG_FILE="$PWD/.cache/broad-benchmark/phase10e-${BROAD_TAG}-calls.jsonl" \
  make run PORT=8765
```

Terminal 2: execute this **once**, for the registered twenty-run schedule:

```bash
make bench-broad MODE=real BASE_URL=http://127.0.0.1:8765 \
  BUDGET=2 RUNS_PER_SCENARIO=2 MAX_RUNS=20 \
  PROVIDER_PREFERENCE=Cerebras \
  ARCHITECT_MODEL= ARCHITECT_THINKING= ARCHITECT_PROVIDER_PREFERENCE= \
  SMOKE=0 FORCE=0
```

The frozen schedule is scenario IDs 1–10, then 10–1, with at most 60 generated
variants. Architect inherits the server model/reasoning with no explicit provider
preference; Generator/Fixer request Cerebras. The benchmark master-header path
bypasses saved account model preferences and lessons. Check actual served
providers in the resulting telemetry rather than assuming routing.

BUDGET=2 is the minimum remaining-credit reserve, **not a total-spend cap**.
Do not run a real smoke or automatically repeat a partial/stopped round. Retain
the printed output folder and the stopped/not-started slots if the guard stops it.
Keep prompts, policies, thresholds and captured configuration fixed. Commit the
new evidence folder separately after the author-run round; do not alter old
benchmark files. No real invocation of this command was executed by Codex.
