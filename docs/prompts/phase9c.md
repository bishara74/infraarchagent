# Codex task — Phase 9c: Generator output reliability on real runs

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md`, the latest
entries of `docs/IMPLEMENTATION_LOG.md`, and the Generator agent, its prompt
templates, the LLM adapters (OpenRouter path), the JSON output parser and
`backend/scripts/benchmark.py`. Phases 0–9 are complete.

## Why this phase exists

The author ran `make bench-real` (real provider, generation model
`anthropic/claude-sonnet-5`, reasoning off, `json_object` format; fixer
`openai/gpt-oss-120b:nitro`). Result: **FAIL**, with 4 of 8 PR-01 runs failed
or incomplete, a median of 190 s over the 4 completed runs, and a measured
cost of **$4.94** (about $0.90 per run, most of it spent on failed attempts).
The author stopped the run to save credit. The raw results are in the
untracked `docs/evals/phase9-bench-real-*` folder. **Do not delete or change
it.**

What the server log showed per run (`prompt_chars` is the size of the
Architect plan given to the generators):

| Run | prompt_chars | Generator calls |
|---|---|---|
| 1 | 3738 | 4 of 6 attempts invalid JSON, 1 timeout |
| 2 | 5484 | every attempt invalid JSON or timeout |
| 3 | 3311 | all 3 succeeded first time (20–29 s, ≈3k output tokens) |
| 4 | 4488 | 2 invalid, then success on retry |
| 5 | 5497 | every attempt failed |
| 6 | 3331 | all succeeded first time |
| 7 | 4653 | every attempt failed |

The failing attempts log `outcome=invalid_json category=invalid_response
format_reason=multiple_blocks` or `prose_before`, with **10k–19k output
tokens** and 70–138 s per call, or `category=unreachable
exception_class=TimeoutError` at about 150 s. The gpt-oss fixer calls all
succeeded in 1–3 s. The pattern: small plans work; larger plans make Sonnet
write very long answers that drift out of the single-JSON format, and a
retry with the same settings cannot finish inside the timeout.

## Rules

- No real LLM calls, no `.env` reads, no installs or downloads, no push.
- No new Python or npm dependencies.
- Don't change the default models or any agent logic outside the generator
  call path, its parser and the benchmark script.
- One commit per numbered section, prefixed `phase9c:`, each with
  requirement IDs (PR-01, PR-05, FR generator IDs as applicable) and an
  implementation-log entry with real test counts.

## 0. Investigate first (report in the summary before changing code)

1. The exact generator request body sent through the OpenRouter adapter:
   `response_format`, `max_tokens` (or absence), temperature, reasoning
   settings, provider routing options.
2. The output instructions in the generator prompt, and the expected package
   schema (Pydantic model).
3. How the parser decides `multiple_blocks`, `prose_before` and the other
   `format_reason` values, and what it accepts today.
4. The retry policy for generators: attempts, per-call timeout, what the
   retry sends (same prompt, or a correction), and the worst-case total
   time per generator.
5. Whether raw invalid outputs are stored anywhere (DB, events, logs). They
   must not be logged as text; only sizes, token counts and reasons.

## 1. Output budget

- Add a setting `generator_max_output_tokens` (default **8000**, documented
  in `.env.example` with a comment; observed Sonnet speed is ≈140 tokens/s,
  so 8000 tokens ≈ 60 s) and send it as the request's output-token limit.
- A response cut off by the limit (`finish_reason` `length` or the
  provider equivalent) is classified as `invalid_response` with
  `format_reason=truncated`.
- Give the generator prompt an explicit size budget: a focused package,
  only the files the plan needs, short comments, no long README prose, no
  repeating the plan text. Keep the security and validity requirements
  unchanged.

## 2. Enforce the output format

- Add a setting `llm_structured_output` = `json_schema` | `json_object` |
  `off` (default `json_schema`). With `json_schema`, send OpenRouter's
  structured output form (`response_format: {type: "json_schema",
  json_schema: {name, strict: true, schema}}`) with the schema derived from
  the existing package model, and ask OpenRouter to route only to providers
  that support the parameter (`provider.require_parameters: true`).
  If the current schema shape can't be expressed in strict mode (e.g. a
  free-form dict of files), report it and adapt the wire schema (e.g. a list
  of `{path, content}` objects) while keeping the internal model.
- Strengthen the prompt's format sentence: exactly one JSON object, starting
  with `{` and ending with `}`, no markdown fences, no text before or after.
- Safe salvage: if the answer contains text before or after but exactly
  **one** balanced top-level JSON object that passes full schema
  validation, accept it and record `format_reason=salvaged` on the attempt
  (it must be countable in reports). Two or more objects, multiple fenced
  blocks, or a schema-invalid object stay rejected.
- If a provider refuses the structured-output parameter, the existing error
  categories apply (`request_rejected` / `model_unavailable`); the message
  should tell the author to set `LLM_STRUCTURED_OUTPUT=json_object`.

## 3. Retry that can succeed

- A retry after `invalid_response` adds a short correction message naming
  the reason (e.g. "Your previous answer was not a single JSON object;
  answer again with only the JSON object."). Do **not** re-send the invalid
  output (cost).
- Make sure the worst-case total generator time (attempts × timeout) is
  documented, and report how it compares to PR-05's 150 s generator
  threshold. Don't change PR-05; just report.

## 4. Benchmark support for a cheap check

- `benchmark.py pr01`: add `--prompts 0,1,2` (indices into the fixed prompt
  set) so a run can target specific prompts.
- Record per run, from existing event/report data: generator attempt count,
  attempt outcomes by `format_reason` (including `truncated` and
  `salvaged`), and output tokens per attempt where available. Add these to
  `results.csv` and a short table in `summary.md`. Failed runs list their
  reason category.
- `make bench-smoke BUDGET=…`: 3 real PR-01 runs, one per example prompt,
  with the same budget guard. Document it in the README next to
  `bench-real` ("run this first after any generator change").

## 5. Tests

Mocked HTTP only:

- The request body contains the output-token limit and the configured
  `response_format` for each `llm_structured_output` value, plus
  `require_parameters` for `json_schema`.
- `finish_reason=length` → `truncated`.
- Salvage: prose + one valid object → accepted, `salvaged` recorded; two
  objects → rejected; multiple fenced blocks → rejected; one object that
  fails the schema → rejected.
- The retry message contains the reason and not the previous output.
- The wire schema round-trips into the internal package model.
- Benchmark: `--prompts` selection, new CSV columns, and the existing canary
  check over all outputs.

## 6. Evidence and documentation

- Run `make secret-scan`, then commit the untracked
  `docs/evals/phase9-bench-real-*` folder unchanged as evidence of the first
  real attempt (`phase9c: keep first real benchmark attempt`). If the scan
  reports anything in it, stop and report instead.
- D-43: output budget, structured output, safe salvage, and why (with the
  numbers above).
- "Thesis text to update": the first real benchmark attempt failed for
  generator output reliability on larger plans; this finding and its fix
  belong in Chapter 6.

## 7. Out of scope

- Real runs, estimated results, model changes, thesis text, Phase 10.

Finish with `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make secret-scan` and `make bench-stub` (report real counts). Summary in
the `AGENTS.md` §10 format, starting with the section 0 findings.
