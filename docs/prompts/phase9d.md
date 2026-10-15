# Codex task — Phase 9d: Raise the production-ready rate (validation repair)

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-40 to D-43),
the latest entries of `docs/IMPLEMENTATION_LOG.md`, the readiness rule
(Option C), the SecurityAgent remediation loop, the ValidatorAgent, the fixer
prompts, the generator prompt, and `backend/scripts/benchmark.py`.
Phases 0–9c are complete.

## Why this phase exists

The real benchmark (`docs/evals/phase9-bench-real-20261015T124330508703Z`,
gpt-oss-120b for all agents, 14 runs) passed PR-01 (median 41.6 s) and PR-05,
but only **1 of 36 packages** reached `production_ready`. The readiness gate
worked as designed; the packages themselves are not good enough. Tally over all
36 packages:

- Status: 35 `pending_review`, 1 `production_ready`.
- Review reasons: **35 `validation_failed`**, 30 `unresolved_security_findings`.
- Validation: 35 invalid, 1 valid.
- Security stop reason: 28 `iteration limit`, 2 `no progress`, 6 none.
- Most frequent failed validation checks:
  28 `terraform.validate: Terraform configuration diagnostic`;
  22 `Missing required argument`; 15 `Unsupported argument`;
  14 `ansible-lint.lint: ansible-lint optional lint failed`;
  10 `Reference to undeclared input variable` plus 25 `terraform.var_ref: var.X is not declared`;
  10 `helm.templates: Chart requires templates`;
  9 `Reference to undeclared resource`; 7 `Duplicate variable declaration`;
  7 `grafana.panels: Dashboard requires panels`; 6 `Unsupported block type`;
  5 `document.parse: Document could not be parsed`.
- Most frequent blocking findings left after the last fix iteration:
  19 each of AWS-0086, AWS-0087, AWS-0091, AWS-0093 (S3 public access block),
  15 CKV_AWS_144, 13 CKV_AWS_18, 12 AWS-0052, 12 AWS-0065, 10 KSV-0125,
  9 AWS-0053.
- Generation: 6 of 42 packages missing (`incomplete_package`, required files
  absent even after the second package attempt).

The full results JSON of all 14 runs is in
`.cache/phase9d-results/<run_id>.json` (saved by the author; read-only input,
never commit it).

## The non-negotiable rule

**Raise quality, not the label.** Do not change the readiness rule, which
findings are blocking, severity thresholds, the validator's pass/fail
criteria, or any check's meaning, and do not special-case the benchmark
prompts. Every improvement must make the generated infrastructure itself
better. If you believe a check is misclassified (for example an *optional*
lint that blocks validity), report it with evidence from the design documents
and leave it unchanged; the author decides.

## Rules

- No real LLM calls, no `.env` reads, no installs or downloads, no push.
- No new dependencies. One commit per numbered section, prefixed `phase9d:`,
  with requirement IDs and an implementation-log entry with real test counts.
- Plan mode first: report section 0 before changing code.

## 0. Investigate (report before changing code)

Using the code and the saved results JSON:

1. Is there already any remediation of **validation** failures (the
   `failed_checks_for_remediation` field suggests one)? If so, when does it
   run, how many rounds, with which inputs, and why did it not fix the
   failures above?
2. Pipeline order today: generation → security loop → validation? What
   happens to validation errors introduced by security fixes?
3. Why do the S3 public-access findings (AWS-0086/87/91/93) survive four fix
   iterations? Inspect the final diffs/iterations in the saved JSON: does the
   fixer add `aws_s3_bucket_public_access_block`, for which buckets, and does
   Trivy accept it?
4. For the top validation classes, sample 3–5 real cases each from the JSON
   and classify the cause (wrong AWS provider argument for the mirrored
   provider versions, missing `variables.tf` entries, duplicate declarations,
   empty Helm chart, empty Grafana dashboard, unparsable document, …).
5. Is the 14× `ansible-lint optional lint failed` blocking validity by design?
   Quote the design rule; don't change it.
6. Current security iteration limit and per-iteration time (from
   `agents.csv`), and the PR-01/PR-05 time headroom.

## 1. Deterministic Terraform repairs (no LLM)

Before the security loop, apply safe, deterministic, logged repairs to
Terraform files:

- Declare every referenced but undeclared input variable in `variables.tf`
  (`type` inferred conservatively or omitted, a short description, **no
  default for anything secret-like**).
- Remove exact duplicate variable declarations; leave conflicting duplicates
  for the LLM repair in section 2.
- Record each repair (file, kind, name) in the package report.

Keep the repairs minimal and idempotent. Tests for each repair, including
"no change when nothing is wrong" and secret-like variables getting no
default.

## 2. Validation repair loop

Add a bounded repair step driven by the Validator's failed checks:

- Order: generation → deterministic repairs → **validation repair (up to N
  rounds, setting, default 2)** → security loop → final validation → if the
  security fixes broke validity, **one more validation repair round** →
  final validation **and** final security scan → readiness gate.
- Each round sends the fixer only the failed checks (check ID, message, file,
  line range) and the affected file contents; the fixer returns changed files
  in the existing patch format. Use the existing fixer model/settings.
- Accept a round only if the number of failed validation checks decreases
  **and** the security scan has no new blocking findings; otherwise roll it
  back and stop. Record rounds, before/after counts and outcome.
- Respect the existing deadlines and cancellation; keep each LLM call within
  the fixer's attempt timeout.

## 3. Security loop improvements

- Fix whatever section 0.3 finds (e.g. the fixer prompt or patch format
  losing the public-access-block resources, or findings mapped to the wrong
  resource).
- Make the security iteration limit a setting if it isn't one; propose a new
  default based on the measured per-iteration time and PR-01/PR-05 headroom
  (do not exceed the 60 s per-iteration threshold; report the expected total
  run time).
- Do not reclassify any finding.

## 4. Generator completeness

- Give each generator the exact list of required file paths/types from the
  Architect plan and require every one (non-empty Helm `templates/`,
  Grafana dashboards with panels, parsable documents).
- Require a `variables.tf` declaring every referenced variable, no duplicate
  declarations, and arguments valid for the AWS provider versions available
  in the offline mirror (name them in the prompt).
- Keep the output budget and structured-output schema from Phase 9c.

## 5. Measurement

- Per package, record: deterministic repairs, validation repair rounds and
  before/after failed-check counts, security iterations, final review
  reasons.
- `benchmark.py` summary: add a quality table (status counts, review-reason
  counts, top failed checks, top remaining findings, production-ready rate),
  computed from the results API, like the author's tally above.
- Add a `quality` subcommand that recomputes this table for an existing
  result folder, so the Phase 9 baseline folder can be summarised the same
  way (write into a new folder; never modify the baseline folder).

## 6. Tests and documentation

- Stub/mocked tests for every new path: repair accepted, repair rolled back
  (count not reduced; new security finding), round limit, deadline, final
  re-validation after security fixes, deterministic repairs, metrics, and
  canaries over new outputs.
- D-44: validation repair loop and deterministic repairs (why, order,
  acceptance rule, limits), and the explicit statement that readiness criteria
  were not changed.
- "Thesis text to update": Chapter 4 (Validator → remediation feedback loop),
  Chapter 6 (baseline 1/36 production-ready; after-change result measured by
  the author).

## 7. Out of scope

- Real runs, estimated results, model changes, changing readiness or
  blocking criteria, thesis text, Phase 10.

Finish with `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make secret-scan` and `make bench-stub` (report real counts). Summary in the
`AGENTS.md` §10 format, starting with the section 0 findings and the
recommended settings for the author's next real benchmark.
