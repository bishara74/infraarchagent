# Codex task — Phase 9e: Syntax gate and schema-grounded repair

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-40 to D-44),
the latest entries of `docs/IMPLEMENTATION_LOG.md`, the Generator, the shared
remediation/repair helper (automatic + engineer Retry), the SecurityAgent
loop and its patch gate, the ValidatorAgent, the offline provider mirror
setup (`install_validators.sh`, mirror location and pinned providers), and
`backend/scripts/benchmark.py`. Phases 0–9d are complete.

## Why this phase exists

Real benchmark after Phase 9d
(`docs/evals/phase9-bench-real-20261015T180417396510Z`, gpt-oss-120b for all
agents, 14 runs): **production-ready 1/40** (baseline 1/36). Phase 9d removed
the targeted classes (undeclared variables 35→11, duplicate declarations 7→0,
empty Helm charts 10→0, ansible-lint 14→0, parse errors 5→2), but
`terraform validate` errors rose: **Missing required argument 22→58,
Unsupported argument 15→32, new Invalid reference 28, Invalid resource type
10, Unsupported block type 10**. The model does not know the AWS provider
schema; the repair prompt only sees the error message. Also: PR-01 median rose
41.6→120.1 s while validator rows in `agents.csv` dropped to ~0.04 s, so
validation and repair time is no longer measured.

The supervisor asked for a **syntax check**. This phase adds (a) a syntax and
validity gate directly after generation and after every patch, and (b)
schema-grounded repair using the real provider schema from the offline mirror.

Full results JSON of the 14 post-9d runs: `.cache/phase9d2-results/`
(read-only; never commit).

## The non-negotiable rule (unchanged)

**Raise quality, not the label.** Do not change the readiness rule, which
findings or checks are blocking, severities, or any check's meaning; do not
special-case benchmark prompts. Never "fix" a validation error by deleting a
security-relevant resource or setting; a repair that removes security
configuration must be rejected (re-scan must show no new blocking finding, as
in 9d).

## Rules

- No real LLM calls, no `.env` reads, no downloads or installs (the provider
  mirror is already installed; use it offline), no push.
- No new dependencies. One commit per numbered section, prefix `phase9e:`,
  requirement IDs and an implementation-log entry with real test counts.
- Plan mode first: report section 0 before changing code.

## 0. Investigate (report before changing code)

Using the saved JSON and the code:

1. Remediation history: validation repair rounds run / accepted / rolled back,
   and rollback reasons (count not reduced, new blocking finding, invalid
   patch, deadline), for the initial and post-security rounds.
2. For the rising `terraform.validate` classes: present in generated files,
   introduced by security fixes, introduced by repair rounds, or previously
   hidden behind earlier parse/declaration errors? Sample real cases.
3. Where validation/repair time goes and why `agents.csv` shows ~0.04 s for
   the validator; which stages are unmeasured.
4. Schema export feasibility, offline: can `terraform providers schema -json`
   run against the installed mirror (e.g. scratch module + mirror/plugin dir,
   no network) for the pinned providers (AWS 5.100.0 and 6.68.0, random,
   kubernetes, helm, tls, null)? Which AWS version do generated packages
   actually resolve to? Raw schema size, and size of a compact per-resource
   summary.
5. Current syntax checks and where they run (Terraform patch gate
   `invalid_structure`, `document.parse`, validator tools), and which file
   types have no early check.

## 1. Offline provider-schema index

- `make provider-schema`: generate, offline from the installed mirror, a
  compact index per provider version: resource and data-source types; for
  each, required arguments, optional arguments, computed-only attributes, and
  nested block types with nesting mode and min/max items. Store it next to the
  mirror (not in git), with a version/hash manifest; document it in the
  README install steps and as a Phase 10 install prerequisite.
- A small library to query it: `resource_schema(type)`, `nearest_types(name)`
  (for invalid resource types), `nearest_arguments(type, name)`, `required_missing(type, given)`.
- The pipeline must work (degraded, logged) if the index is missing.

## 2. Syntax and validity gate after generation

Right after each Generator package (and after the 9d deterministic repairs),
run a fast gate in a temporary directory:

- Parse every file by type: HCL, YAML (multi-document), JSON.
- Terraform: `terraform fmt` applied deterministically (formatting only,
  logged), then `terraform init -backend=false` against the offline mirror
  and `terraform validate` per module.
- Helm: `helm lint` / `helm template`; Ansible: `ansible-playbook
  --syntax-check`; Prometheus rules: `promtool check rules`. Use only tools
  already installed; skip with a recorded reason if one is unavailable.
- On failure: one **schema-grounded** repair inside the generation stage
  (section 3) before the package enters the security loop; if it still fails,
  continue to the 9d validation repair as today. Respect the generator budget
  and record gate time.

## 3. Schema-grounded repair prompts

For every repair (generation-stage, 9d validation repair, post-security
round, engineer Retry, through the shared helper), enrich the failed checks
with authoritative context from the index, capped by a setting
(`SCHEMA_CONTEXT_MAX_CHARS`, propose a default):

- Missing required argument → the resource's required arguments and their
  types.
- Unsupported argument / block type → the allowed arguments and block types,
  plus the nearest valid names.
- Invalid resource type → nearest valid resource types.
- Invalid reference / undeclared resource → the resources, data sources and
  attributes actually declared in that module.
- Also give the Generator a compact schema summary for the resource types it
  is most likely to use? Report whether this fits the prompt budget; implement
  only if it does without breaking the Phase 9c output budget.

## 4. Syntax gate on every patch

Extend the existing Terraform-only patch gate so every fixer patch (security
loop and repair rounds) is parsed for **all** touched file types before it is
applied; a patch that breaks syntax is rejected and recorded, as today for
Terraform.

## 5. Measurement

- `agents.csv` and the PR-05 table must include real durations for:
  deterministic repairs, the syntax/validity gate, each validation repair
  round, final validation and final security scan (descriptive rows; no new
  thresholds).
- Per package: gate outcome and failed checks, schema context size, repair
  outcome by error class, and the origin of each final failed check
  (generated / security fix / repair / unknown).
- Benchmark summary: add these to the quality table, and production-ready
  rate as before.

## 6. Tests and documentation

- Tests with a small fixture schema index (no real mirror needed in unit
  tests) plus one integration test that uses the real mirror when present
  (skipped with reason otherwise): index queries, nearest-name suggestions,
  gate per file type, schema-enriched prompts within the cap, patch-gate
  rejection for YAML/JSON/HCL, timing rows, canaries.
- D-45: syntax gate, schema index and grounded repair (why, order, limits,
  offline guarantee) and the unchanged readiness criteria.
- "Thesis text to update": Chapter 4 (tool-grounded generation and repair),
  Chapter 6 (9d → 9e comparison).

## 7. Out of scope

Real runs, estimated results, model changes, readiness/blocking criteria,
thesis text, Phase 10 packaging (beyond documenting the new install step).

Finish with `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make secret-scan`, `make provider-schema` and `make bench-stub` (real
counts). Summary in the `AGENTS.md` §10 format, starting with the section 0
findings and the recommended `.env` settings for the next real benchmark
(keep the 9d benchmark settings for comparability).
