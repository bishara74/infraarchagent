# Codex task — Phase 10c: diagnose and fix the final-round regression

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-56 to D-63),
the latest `docs/IMPLEMENTATION_LOG.md` entries (9m, 10, 10b), and the
committed broad benchmark folders:

- round 1 `docs/evals/phase9-bench-broad-20261020T234203035108Z` (24/60)
- round 2 `docs/evals/phase9-bench-broad-20261021T200436165739Z` (19/60)
- Sonnet experiment `docs/evals/phase9-bench-broad-20261024T233240471733Z` (24/56)
- **final round** `docs/evals/phase9-bench-broad-20261027T015443795826Z` (7/60)

Phases 0–10b are complete. Same scenario file, same models
(`openai/gpt-oss-120b:nitro` for every role), Cerebras served every call.

## Symptoms in the final round

- Checks passed fell to **7/60 (11.67%)**; 3 `scan_error` packages (new).
- `terraform.validate: Invalid multi-line string` **76** times and
  `TERRAFORM_SYNTAX` blocking **78** times — absent from earlier rounds.
- Review reason `plan_conformance_conflict` on **40** packages, while the
  10b audit found only 3 confirmed exposure flips in 998 historical packages.
- Other top failures: unsupported arguments/blocks, Helm undefined template,
  ansible-lint, Grafana panels.

Code changes since the earlier rounds include the 9m duplicate-block repair
and file-input guard (literal decoding), the 10 changes, and the 10b
plan-conformance guard, Fixer prompt v8 and Fixer context.

## Rules

No real LLM calls, no `.env` reads, no installs, no network, no push. Do not
modify committed evidence folders. Profiles, scanner rules, blocking rules,
thresholds and the intent of the 10b guard (planned public exposure must
never be weakened) stay unchanged. **Plan mode first: complete section 1 and
report it before changing any code.** One commit per section, prefix
`phase10c:`, requirement IDs, implementation-log entries with real counts.
Record causes and decisions in a new D-64.

## 1. Diagnosis (report before fixing)

From the committed final-round evidence, per package:

- **Invalid multi-line string:** for each occurrence, find the first stage
  where the offending text appears — Generator original output,
  deterministic repairs (name each repair kind, especially the 9m
  duplicate-block merge), Fixer candidates (prompt v8), validation repair —
  using retained originals, repair records, iteration diffs and hashes.
  Show 3 representative minimal excerpts (no secrets). Check whether any
  code path decodes escapes (e.g. `\n`, `\u…`) and writes the decoded text
  back into files, or re-serialises HCL strings.
- **plan_conformance_conflict (40):** for each, classify: true exposure
  violation, unknown/ambiguous binding rejecting a change, or false positive
  rejecting a provably unrelated fix. Report the rule IDs whose fixes were
  rejected and how many findings stayed open only because of the guard.
  Compare with the 10b replay fixtures.
- **scan_error (3):** cause and stage.
- Compare stage-level counts (generation validity, repairs accepted,
  fixes accepted/rolled back by reason, final blockers) with rounds 1 and 2,
  and attribute the 24→7 drop to causes with numbers. State what remains
  unexplained (model variance cannot be excluded with one round).

## 2. Fixes (only proven causes)

- Fix any repair or guard path that corrupts Terraform strings; files must
  stay byte-identical unless a repair is provably safe, and every rewrite
  must pass a syntax check before acceptance (roll back otherwise).
- Correct the plan-conformance guard so it rejects only changes that can
  affect a planned exposure: provably unrelated fixes must be accepted;
  ambiguous bindings must not block fixes to resources that cannot affect
  the exposure path. Keep fail-closed for changes on the exposure path.
- If Fixer prompt v8 itself causes the strings, fix the prompt or the
  context rendering and disclose the version change (v9).
- Fix the scan_error cause if it is in the code.

## 3. Offline verification

- Regression tests from the real final-round cases (synthetic copies, no
  secrets) for every fixed cause, plus the existing 10b replay fixtures
  (the run 3/4 ALB flips must still be rolled back).
- Replay the deterministic stages (repairs, syntax gates, guard decisions on
  recorded Fixer candidates, scanners, validation) over the final-round
  packages where the recorded data allows it, and report before/after counts
  (invalid multi-line strings, guard conflicts, packages that would no
  longer be blocked by these causes). Do not claim a pass rate: a real
  rerun is needed for that.

## Finish

Run `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make test-perf`, `make secret-scan`, traceability and evidence-index
generation (real counts). Summary in the `AGENTS.md` §10 format, starting
with the diagnosis table and the attributed causes, then the replay
counts, then the exact command for the author's rerun of the final round.
