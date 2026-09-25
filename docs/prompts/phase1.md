# Codex task — Phase 1: LLM adapter layer and timing spike

Read `AGENTS.md`, `docs/design-deviations.md` and `docs/IMPLEMENTATION_LOG.md`
first. The specification is in `docs/spec/`. This task is **Phase 1 only**.
Phase 0 is complete; build on it without changing its behaviour.

## Goal

Build the single way every agent will talk to an LLM:
- an abstract `LLMAdapter`;
- three providers: Anthropic, OpenAI, and a deterministic Stub for tests;
- one shared retry/timeout/JSON wrapper;
- a factory that picks the adapter from configuration;
- a timing spike script that the author runs with a real key to answer OQ-03.

No agent, prompt-engineering, orchestrator or API endpoint work belongs in
this phase.

Relevant spec: NFR-03, FR-I-04, ADR-02, FR-A-04, PR-05, the per-agent timing
paragraph in Section 3.2, and the class diagram (`LLMAdapter {abstract}` with
`AnthropicAdapter`, `OpenAIAdapter` and `StubAdapter`).

## Definition of done

- `make test` and `make lint` pass. No test touches the network or needs a key.
- A deliberately minimal adapter defined inside a test works through the whole
  retry wrapper by implementing only `send_prompt` and `parse_response`
  (NFR-03).
- `make spike` runs end-to-end with `LLM_PROVIDER=stub` and writes a results
  file. The author runs it later with a real key.
- `docs/IMPLEMENTATION_LOG.md`, `docs/design-deviations.md` and `README.md`
  are updated per `AGENTS.md` §8.

Commit after each numbered section, as in Phase 0.

---

## 0. Security rule addition

Add this line to the security rules in `AGENTS.md` §6, in the same commit as
section 1: *"Never open, print, or copy `.env` or any real API key. Real keys
are only used by the author, outside Codex runs."*

Follow it yourself for the whole task. Tests use the existing canary key
only.

## 1. Dependencies

- Add `anthropic` and `openai` (the official SDKs) to runtime dependencies.
- Regenerate `backend/requirements.lock` with the same `pip freeze
  --exclude-editable` method and install through it.
- Nothing else. Tests fake HTTP with `httpx.MockTransport`; `httpx` is
  already installed.

## 2. Configuration additions (`app/core/config.py`)

| Variable | Type | Default |
|---|---|---|
| `LLM_ATTEMPT_TIMEOUT_SECONDS` | float > 0 | 30 |
| `LLM_MAX_ATTEMPTS` | int ≥ 1 | 3 |
| `LLM_DEADLINE_SECONDS` | float > 0 | 150 |
| `LLM_BACKOFF_BASE_SECONDS` | float ≥ 0 | 1.0 |
| `LLM_MAX_OUTPUT_TOKENS` | int ≥ 1 | 16000 |

Add them to `.env.example` and the README table. `LLM_MODEL` stays optional
globally, but it is required when a real adapter is built (see section 5).

## 3. Adapter design (`app/llm/`)

Files: `base.py`, `errors.py`, `anthropic.py`, `openai.py`, `stub.py`,
`factory.py`, `__init__.py`.

### 3.1 The provider contract (`base.py`) — exactly two abstract methods

```python
class LLMAdapter(ABC):
    def __init__(self, model: str, policy: RetryPolicy, *, sleep=asyncio.sleep, clock=time.monotonic): ...

    @abstractmethod
    async def send_prompt(self, prompt: str, *, system: str | None = None,
                          max_output_tokens: int, timeout: float) -> LLMResponse: ...

    @abstractmethod
    def parse_response(self, response: LLMResponse) -> dict[str, Any]: ...

    async def complete_json(self, prompt: str, *, system: str | None = None) -> LLMResult: ...
```

- `LLMResponse` is a small dataclass: `text`, `input_tokens: int | None`,
  `output_tokens: int | None`, `stop_reason: str | None`.
- `LLMResult` carries the parsed `data: dict`, the final `LLMResponse`, the
  `attempts` used, and the total `elapsed_seconds`.
- **`complete_json` is a concrete template method.** It owns all retry,
  timeout, backoff and JSON handling, so a provider class never re-implements
  them. This is how NFR-03's "exactly one adapter class with two methods"
  holds. Record it as D-07. The class diagram shows only the two abstract
  methods; add "add `complete_json` to the class diagram" to "Thesis text to
  update".
- The methods are `async` because the pipeline is asyncio. The diagram's
  signatures are otherwise kept. Mention this in D-07.
- Keep `parse_response` synchronous and pure, so it is easy to unit-test.

### 3.2 Retry policy (`complete_json`), exact semantics

`RetryPolicy` is a frozen dataclass: `attempt_timeout`, `max_attempts`,
`deadline`, `backoff_base`, `max_output_tokens`. It is built from settings.

1. The whole call runs under an overall deadline of `policy.deadline`
   seconds, measured with the injected `clock`.
2. Each attempt calls `send_prompt(..., timeout=t)`, wrapped in
   `asyncio.wait_for` with `t = min(attempt_timeout, time remaining before
   the deadline)`. If there isn't enough time left for a meaningful attempt
   (≤ 0), stop with `LLMDeadlineExceeded`.
3. **Retryable errors:**
   - attempt timeout;
   - `LLMTransientError` (rate limit 429, HTTP 5xx, connection errors);
   - `LLMResponseFormatError` (the response was not valid JSON per
     `parse_response`);
   - a response cut off by the token limit (`stop_reason` meaning
     max-tokens), raised as `LLMResponseFormatError` with reason
     `truncated`.
4. **Non-retryable:** `LLMPermanentError` (auth failure 401/403, bad request
   400, unknown model 404). Raise immediately.
5. **Backoff** before attempt *n* (n ≥ 2) is `backoff_base * 2**(n-2)`, i.e.
   1 s then 2 s with the defaults. Add full jitter from a seedable
   `random.Random`, and never sleep past the deadline.
6. After `max_attempts` failures, raise `LLMRetryExhausted`. It carries the
   attempt count, elapsed time, and the last error's *category* (never its raw
   text).
7. `sleep` and `clock` are injected, so tests run in milliseconds without real
   waiting.

**Error hygiene (NFR-01):** every exception raised out of `app/llm/` is one
of the classes in `errors.py`, with a message you wrote yourself. SDK
exception text, request headers and URLs are never included. The original
exception may be chained (`from`), but the canary test must show the key
appears in no message, `repr` or log line.

**Logging:** at INFO, one line per attempt with provider, model, attempt
number, outcome category, latency, and token counts. Never the prompt, the
response text, or the key. Log prompt sizes in characters only.

### 3.3 `parse_response`, strict JSON (shared helper in `base.py`)

- Accept either the whole text as one JSON **object**, or exactly one fenced
  block ```` ```json ... ``` ```` or ```` ``` ... ``` ```` surrounded only by
  whitespace.
- Reject everything else with `LLMResponseFormatError`: prose before or after
  the JSON, multiple blocks, a top-level array, a scalar, invalid JSON, or an
  empty response.
- Provide it as `extract_json_object(text) -> dict`. The three adapters call
  it from their `parse_response`.

### 3.4 `AnthropicAdapter` and `OpenAIAdapter`

- Use the official async clients: Anthropic Messages API, and OpenAI Chat
  Completions API (as the design says).
- **Construct the SDK clients with their built-in retries disabled
  (`max_retries=0`)**, and pass the per-attempt timeout through. Otherwise
  the SDK's own retries would multiply our attempts and break the timing
  guarantees. Add a test asserting this.
- Accept an optional `http_client` (an `httpx.AsyncClient`) in the
  constructor for tests.
- Map SDK exceptions to our categories:
  - authentication/permission/bad request/not found → `LLMPermanentError`;
  - rate limit, 5xx, connection, timeout → `LLMTransientError` or timeout.
- Read token usage and the stop reason into `LLMResponse`.
- Check the installed SDK versions' actual APIs rather than relying on
  memory. Record the SDK versions in the log entry.

### 3.5 `StubAdapter`

- Constructed with a script: a list of steps. Each step is one of:
  - a response text;
  - an exception to raise;
  - a delay in seconds, combined with a response.
- It records every prompt it receives (the tests in later phases need this,
  e.g. FR-S-09's "prompt contains the feedback").
- It is fully deterministic and needs no key. If the script runs out, it
  raises a clear error.
- It also has a default "echo" mode for `make spike --provider stub`: it
  returns a small valid JSON object, so the spike pipeline can be tested.

### 3.6 Factory (`factory.py`)

`build_adapter(settings, *, provider=None, model=None) -> LLMAdapter`:
- Per-call `provider` and `model` override settings. This is the hook that
  FR-I-04's run configuration uses in later phases.
- For `anthropic` and `openai`:
  - require the key via `settings.require_llm_key()`;
  - require a model (settings or override); otherwise raise a clear
    configuration error naming the missing variable.
- For `stub`: no key or model needed.
- This is the only place that constructs adapters, outside tests.

## 4. Tests (all offline; tag with `req` markers)

**Retry wrapper**, using the Stub or a test adapter, with fake `sleep` and
`clock`:
1. Success on the first attempt; `attempts == 1`.
2. Transient error, then success; `attempts == 2`. The recorded backoff is
   within `[0, 1s]` with jitter, or exactly 1 s with jitter disabled.
3. Attempt timeout (the stub delays longer than `attempt_timeout`), then
   success.
4. Invalid JSON, then valid JSON; it succeeds on attempt 2.
5. A truncated response is retried.
6. Three failures give `LLMRetryExhausted` with `attempts == 3`.
7. A permanent error is raised immediately; `attempts == 1` and no sleep.
8. **Deadline** (`req("FR-A-04","PR-05")`): with defaults (30/3/150) and a
   stub that always times out, the total simulated elapsed time is ≤ 150 s.
   With `deadline=40`, the second attempt's timeout is shortened to what
   remains, and no third attempt starts.
9. **Backoff never sleeps past the deadline.**

**Parsing:** a table of accepted and rejected inputs for
`extract_json_object`.

**NFR-03** (`req("NFR-03","FR-I-04")`): a `MinimalAdapter` defined inside
the test file, implementing only the two abstract methods, completes
`complete_json` successfully through retries.

**Providers**, via `httpx.MockTransport` (no network):
- Anthropic and OpenAI each:
  - send the expected model, max-tokens and prompt fields;
  - parse a realistic success body including token usage;
  - map 401 to permanent, 429 and 500 to transient;
  - map a max-tokens stop reason to truncated.
- Both SDK clients are built with `max_retries=0`.

**Factory:**
- Selection by provider.
- Override precedence.
- Missing key or model errors for real providers.
- Stub works with neither.

**Canary** (`req("NFR-01")`): with the canary key, force a provider 401
whose mocked body and headers contain the key. Assert the key appears in no
exception message, no `repr` and no captured log. Extend the existing canary
test module rather than duplicating its fixtures.

## 5. Timing spike (OQ-03): script only, the author runs it

`backend/scripts/spike_llm_timing.py`, plus `make spike`:

- **Arguments:** `--provider`, `--model`, `--runs N` (default 3), and
  `--mode {full,split,both}` (default `both`).
- **The adapter is built through the factory, but with a spike-only policy:**
  `attempt_timeout=240`, `max_attempts=1`, `deadline=240`. We want to
  *measure* how long a call really takes, not cut it off at 30 s.
- **Workload:** a fixed, realistic deployment plan embedded in the script: a
  three-tier AWS web app with an ALB, 2 app services, RDS PostgreSQL, S3 and
  CloudWatch. The prompt asks for a strict JSON object `{"files": {path:
  content}}`.
  - `full`: ONE call requesting a complete package with all file types the
    design lists (Terraform, Kubernetes, Helm, Nginx, Jenkins, Ansible,
    Prometheus, Grafana).
  - `split`: one call **per file group**, in parallel with
    `asyncio.gather`. Record each group's latency, plus the wall-clock time
    for the whole set.
- **Record per call:** latency, input/output tokens, stop reason, whether the
  JSON parsed, number of files, and total characters.
- **Output:**
  - raw JSON to `docs/spikes/phase1-llm-timing-<provider>-<timestamp>.json`;
  - a short Markdown summary next to it with median and max latency per
    mode, output tokens per second, parse success rate, and a one-line
    verdict for each mode: "fits 30 s" / "does not fit 30 s".
- **Never** write the key, the full prompt or the generated file contents
  into these files. Sizes and counts only.
- Verify it end-to-end with `--provider stub` and include that stub output in
  the commit, as a format example.
- Do **not** run it against a real provider. There is no key in your
  environment, by design.

## 6. Documentation

- **D-07:** `complete_json` template method on the abstract base, async
  methods, and why (NFR-03).
- **CL-03 (retry arithmetic):** Section 3.2 of the requirements says "30s +
  60s + 60s = maximum 150 seconds", which contradicts "30 seconds per attempt
  ... up to 3 attempts". Implemented as: 30 s per attempt, at most 3
  attempts, exponential backoff with jitter (1 s, 2 s), and a hard 150 s
  overall deadline that also shortens the last attempt. Add "fix the
  30s+60s+60s sentence" to "Thesis text to update".
- **OQ-03:** add "Measurement: spike script ready (`make spike`), awaiting a
  run with a real key." Do not resolve it.
- **README:** the new variables, and how to run the spike.
- **Implementation log** entry with real test counts and SDK versions.

## 7. Out of scope

- Agents and their prompts.
- Orchestrator and pipeline.
- API endpoints.
- SSE.
- Scanners.
- Frontend.
- Streaming responses. If the spike shows 30 s cannot hold, streaming or
  splitting is decided afterwards, as a design decision with the author.

Finish with the summary format from `AGENTS.md` §10.
