# Codex task — Phase 7b: correct run model provenance

You are starting a **fresh session**. First read `AGENTS.md`, the latest
entries of `docs/IMPLEMENTATION_LOG.md`, and D-33 in
`docs/design-deviations.md`. Phases 0–7 are complete. This is a small,
self-contained fix.

## The bug (found in a manual Phase 7 demo)

A run submitted with `{"config": {"provider": "stub"}}`, while `.env` has
`LLM_MODEL=anthropic/claude-sonnet-5`, is stored with
`model = "anthropic/claude-sonnet-5"`. The downloaded readiness file then
says `Model: anthropic/claude-sonnet-5` for a run that used the stub.

**Cause 1:** `RunConfig.resolve()` (`app/domain/run_config.py`) takes the
provider from the request but still inherits `settings.llm_model`. That
model belongs to the configured provider, not the overriding one.

**Cause 2, same family:** `AgentFactory.create_security_agent()`
(`app/agents/factory.py`) applies `SECURITY_FIX_PROVIDER` and
`SECURITY_FIX_MODEL` regardless of the run's provider:
- a stub run records the real fixing model name (wrong provenance);
- if `SECURITY_FIX_PROVIDER` is set, a stub run would make **real, paid**
  fixer calls.

This matters for the thesis: evaluation records and downloads must name the
model that actually produced each package.

## Required behaviour

1. **Model resolution (`RunConfig.resolve`):**
   - request gives `model` → use it;
   - request gives no `provider`, or the same provider as
     `settings.llm_provider` → inherit `settings.llm_model` (unchanged
     behaviour);
   - request overrides to a **different** provider and gives no `model`:
     - `stub` → model `"stub"`;
     - a provider that needs a model → refuse with 400
       `invalid_request`, message "model is required when overriding the
       provider". Never guess a model.
2. **Fixer overrides (`create_security_agent`):**
   - `SECURITY_FIX_PROVIDER`, `SECURITY_FIX_MODEL` and
     `SECURITY_FIX_REASONING_EFFORT` apply only when the run's resolved
     provider equals `settings.llm_provider`. They are the configured
     deployment's fixer, not a global override.
   - A run whose provider is `stub` always uses the stub fixer, with model
     `"stub"`. **A stub run never makes a network call.**
3. **One source of truth.** The model recorded on the run row, in events,
   in the security report's fixing metadata, in results and in the ZIP
   readiness file comes from the same resolution. Check the API submit path
   (`app/api/pipeline.py` currently does `resolved.model or ("stub" if …)`)
   and the evaluation scripts. Remove any duplicate fallback logic.
4. **Historical rows are not rewritten.** Note in the implementation log
   that runs stored before this fix, submitted with a provider override, may
   carry the configured model name. Don't add a migration for this.

## Tests (use requirement markers as before)

- `{"provider": "stub"}` with `LLM_MODEL` set → run row model `stub`;
  results `run.model == "stub"`; the readiness file says `Model: stub`.
- No config → inherits `LLM_PROVIDER` and `LLM_MODEL` (regression).
- Same provider as configured, no model → inherits `LLM_MODEL`.
- Different non-stub provider without `model` → 400, and no run row is
  created.
- `SECURITY_FIX_PROVIDER` / `SECURITY_FIX_MODEL` set, run provider `stub` →
  the fixer adapter is the stub, model `stub`, and no network adapter is
  built (spy on `build_adapter` or the adapter class).
- `SECURITY_FIX_*` set, run uses the configured provider → the fixer uses
  the override (regression for D-33's hybrid setup).
- NFR-01 canary tests still pass.

## Rules

- No installs, no `.env` reads, no real LLM calls, no push.
- One or two commits prefixed `phase7b:`, each with an implementation-log
  entry. Add a short note to D-33 that fixer overrides are scoped to the
  configured provider.
- Finish with `make lint` and `make test`, and report the real counts.
- Out of scope: anything else. In particular, no frontend work.
