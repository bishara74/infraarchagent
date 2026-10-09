# Codex task — Phase 6: ValidatorAgent

You are starting a **fresh session**. First read:
- `AGENTS.md`;
- `docs/design-deviations.md`;
- `docs/IMPLEMENTATION_LOG.md`, especially the Phase 4, 5 and 5b entries;
- the spec in `docs/spec/`: FR-V-01 to FR-V-05, the artifact validation table
  in Chapter 3, Option C (D-06), and the package state diagram.

Phases 0–5b are complete. This task is **Phase 6 only**.

## Goal

Replace `UnavailableValidationStage` with the real **ValidatorAgent**. Per
package, after security remediation, it:
1. runs **`terraform validate` against real provider schemas**, from an offline
   provider mirror (FR-V-03);
2. runs **deterministic cross-file reference checks** (FR-V-01);
3. runs **deterministic name-consistency checks** (FR-V-02);
4. runs **built-in structural checks for every file type**, plus **external
   linters where installed**;
5. produces a report of passed, failed, warning and skipped checks, **each
   failure linked to a file and line** (FR-V-04, and the Phase 5 retry
   contract);
6. moves the package `validating → valid | invalid | validation_error`.

The orchestrator then applies Option C: a clean scan plus `valid` gives
`production_ready`; everything else gives `pending_review`. **After this
phase, runs can end `success`.**

## Decisions already made by the author (do not revisit)

1. **A local Terraform provider mirror.**
   - Providers are downloaded **once** into a project-local mirror by `make
     providers`.
   - Validation runs `terraform init -backend=false -input=false
     -plugin-dir=<mirror>` **offline**, then `terraform validate -json`.
   - A provider version not in the mirror, or a remote module that can't be
     fetched offline, makes the Terraform check **skipped, with the reason**,
     never passed.
2. **Tiered, pluggable linters.**
   - **Built-in, dependency-free checks run for every file.**
   - **External linters run only if installed:** `helm lint`, `hadolint`,
     `ansible-lint`, `promtool check config`. The author installed them with
     the committed `tools/install_validators.sh`; record the exact versions
     the health check reports.
   - **A missing linter means "skipped (not installed)",** never a pass.
   - **Out of scope, with documented reasons:**
     - the Jenkins `pipeline-model-converter` API, which needs a running
       Jenkins server;
     - `nginx -t`, which needs the nginx binary and resolves upstream
       hostnames, so it fails offline;
     - `grafana-cli`, which needs a Grafana installation;
     - `kubectl --dry-run`, which needs a cluster or kubeconfig.
   - Those file types get the built-in checks only.
3. **Deterministic analysers** for cross-file references and naming. No LLM
   calls in validation.

## Rules

- Running Terraform and the installed linters locally **is allowed**.
- **Running `make providers` once is allowed.** It downloads the providers
  from the official Terraform registry; Terraform verifies their signatures.
- **No other downloads or installs.**
- No real LLM calls.
- Do not read `.env`.
- Commit after each numbered section.
- Do not push.
- Use the existing `ProcessToolRunner` for every external tool: process-group
  timeout, minimal environment, black-hole proxy, `CHECKPOINT_DISABLE=1`, and
  `TF_DATA_DIR` in a temp dir.
- `make test` must pass with the **plain** `pytest` entry point (the 5b
  lesson; `pythonpath = ["."]` is already configured).

---

## 0. Recorded decisions and prompt-caching measurement (small; do first)

**a) D-33, hybrid model configuration.** Record the author's decision:
- **Claude Sonnet 5 (reasoning off) generates; gpt-oss-120b:nitro (reasoning
  low) fixes**, via `SECURITY_FIX_MODEL`.
- **Evidence:** the committed `docs/evals/phase5b-security-*` remediation runs:
  - the gpt-oss fixer: 537 → 34 blocking findings (93.7%), 4/12 packages
    clean, ~25 s and ~1¢ per package;
  - Sonnet as the fixer on the same 2 packages: 44 → 3, but ~3–4× slower and
    ~25× more expensive;
  - after the lenient-metadata fix, Sonnet had 0 rejected fixes (previously
    10/20).
- **Also record:** MEDIUM stays blocking (the policy is confirmed by
  measurement).

**b) Prompt-caching measurement (the mechanism only; off by default).**
- **Record cached input tokens** (`prompt_tokens_details.cached_tokens` or the
  provider's equivalent) in `LLMResponse`, the attempt log line
  (`cached_input_tokens=`), the reports and the evaluations, when present.
- **Add an optional setting, `LLM_PROMPT_CACHE`** (`off` by default, or
  `system`). When it's `system` and the model is an Anthropic model reached
  through the OpenAI-compatible adapter, send the system message as a content
  part carrying OpenRouter's cache marker. Check OpenRouter's current
  prompt-caching documentation for the exact shape.
- **Tests:** the marker is present or absent per the setting; cached tokens are
  parsed when present and `None` when absent.
- **Record it as D-34:** off by default, because run costs are dominated by
  output tokens. Its intended use is a later evaluation of richer cached
  prompts.

## 1. The validation report model (`app/domain/validation.py`)

**`ValidationCheck`:**
- `check_id`, a stable name, e.g. `terraform.validate`,
  `k8s.configmap_ref`;
- `category`: `terraform`, `reference`, `naming`, `structure` or `lint`;
- `tool`: `terraform`, `builtin`, `helm`, `hadolint`, `ansible-lint` or
  `promtool`;
- `status`: `passed`, `failed`, `warning` or `skipped`;
- `file_path` (package-relative, validated) and `line_start` / `line_end`,
  where known;
- `message`, kept short and safe: no raw tool output beyond the bounded
  diagnostic text;
- `skip_reason`.

**`ValidationReport`:**
- `report_version` and the tool versions;
- `checks`, bounded and with counts if truncated;
- **`summary`:** `{passed, failed, warnings, skipped, result}`, where `result`
  is `valid`, `invalid` or `error` (FR-V-04);
- `failed_checks_for_remediation`: every failed check **with its
  `file_path`**, plus lines where known. This is the Phase 5 retry contract.
  A failed check that can't name a file is recorded, but excluded from this
  list.

**The outcome rule, in exactly one place:**
- any `failed` check → `invalid`;
- the **Terraform check skipped or crashed**, while the plan includes
  `terraform` → `validation_error`. This is a required check that couldn't
  run, so the engineer decides;
- otherwise → `valid`;
- warnings and skipped **optional** checks never change the result.

## 2. Provider mirror and `terraform validate` (FR-V-03)

- **`make providers`:**
  - reads `tools/terraform-providers/providers.tf`, which pins **exact
    versions** of the providers the generated packages need;
  - runs `terraform providers mirror` into `.cache/terraform-providers/`
    (gitignored);
  - also writes `.terraform.lock.hcl`-style hashes for the record.
- **Which providers to mirror:** derive the set from the committed Phase 3
  packages' `required_providers` blocks and resource prefixes. At least:
  - `hashicorp/aws`: the latest **5.x and 6.x** releases, because generated
    code uses either;
  - `hashicorp/random`;
  - `hashicorp/tls`;
  - `hashicorp/null`;
  - `hashicorp/kubernetes`;
  - `hashicorp/helm`.

  Record the list and the reasons.
- **Run `make providers` once, and report the mirror size.**
- **The validator:**
  1. copies `terraform/` to a temp dir;
  2. runs `init -backend=false -input=false -plugin-dir=<mirror>`, with
     `-get=true` only for **local** module paths (remote modules must not be
     fetched; the black-hole proxy guarantees that);
  3. then runs `validate -json`;
  4. parses the diagnostics into checks: errors → `failed`, warnings →
     `warning`, each with its file and line.
- **The skip reasons, distinguished and tested:**
  - `provider_version_not_in_mirror`;
  - `remote_module_not_available_offline`;
  - `mirror_missing` (`make providers` not run).
- **`/api/health`** reports the validators' availability and versions, and
  whether the mirror is present.

## 3. Built-in structural checks (every file type)

- **Terraform:** covered by section 2. If Terraform is unavailable,
  `terraform.validate` is skipped.
- **Kubernetes YAML:**
  - every document parses;
  - every document has `apiVersion`, `kind` and `metadata.name`;
  - workload kinds have `spec.template.spec.containers[*].name` and `image`;
  - no duplicate `kind` + name.
- **Helm:**
  - `Chart.yaml` parses, and has `apiVersion`, `name` and `version`;
  - `values.yaml` parses;
  - templates exist.
- **Dockerfile:** has a `FROM`, and every instruction is a known keyword.
- **Jenkinsfile:**
  - braces are balanced;
  - it has a `pipeline {` block, with `agent` and `stages`;
  - every `stage` has `steps`.
- **Ansible:**
  - YAML parses;
  - each playbook is a list of plays with `hosts`;
  - each task has a module key.
- **Nginx:**
  - braces are balanced;
  - there is at least one `server` block;
  - every `proxy_pass` to a named upstream refers to a defined `upstream`, or
    to a hostname recorded as external.
- **Prometheus:**
  - YAML parses;
  - `scrape_configs` is a list;
  - each entry has `job_name`;
  - `rule_files` exist in the package.
- **Grafana:**
  - JSON parses;
  - it has `panels` (FR table: "missing panels" must fail);
  - each panel has a `type`.

**New runtime dependencies,** pinned in `pyproject.toml` and regenerated in
`requirements.lock`: `PyYAML` and `python-hcl2`. Nothing else.

## 4. Cross-file reference checks (FR-V-01): errors unless stated

**Terraform:**
- local `module` sources exist in the package;
- every `var.X` used is declared;
- every `module.X.Y` and `local.X` used is declared.

**Kubernetes:**
- `configMapRef`, `configMapKeyRef` and `volumes[].configMap` name a
  ConfigMap defined in the package;
- `secretRef` and `secretKeyRef` naming a missing Secret are a **warning**,
  because secrets are often created out-of-band, as several generated
  packages state;
- a Service selector matches some workload's pod-template labels;
- an Ingress backend names an existing Service and port;
- an HPA `scaleTargetRef` names an existing workload;
- a PVC `claimName` is defined.

**Helm:**
- `Chart.yaml` dependencies are vendored under `charts/`, or are marked
  **remote** (a warning, "not validated offline");
- `.Values.x.y` paths used in templates exist in `values.yaml` (a warning,
  since defaults may be intended).

**Ansible:**
- playbook `hosts` groups exist in the inventory, if an inventory is present;
- referenced roles exist.

**Prometheus:** referenced `rule_files` exist.

Every check carries a file and line, using the YAML/HCL parser position or a
fallback line search.

## 5. Name consistency (FR-V-02)

- **Collect named entities per artefact type:**
  - the Kubernetes Deployment, StatefulSet and Service names;
  - the Helm chart and release names;
  - the Ansible host groups;
  - the Nginx upstream names;
  - the Prometheus job names and static target hostnames;
  - the Terraform resource name attributes and tags that embed plan service
    names.
- **Normalise them:** lowercase; `-`, `_` and `.` are treated as equivalent.
- **Compare against the plan's service and storage names.** Flag:
  - **an entity that refers to a service-like name that doesn't exist in the
    plan, or in the other artefacts.** For example, Ansible targets
    `web-servers` while Terraform names `app-service-1`;
  - **a plan service that is absent from an artefact type that should
    contain it.** For example, `kubernetes` is in the plan, but no workload
    matches the plan's compute service.
- **Naming findings are `warning`s, not failures.** That satisfies FR-V-02's
  "flags" without making packages `invalid` on fuzzy matches. Record that
  choice as a clarification, with this reasoning.
- **Keep the rules simple and explainable,** and document each one.

## 6. External linters (pluggable)

| Linter | Runs on | Result mapping |
|---|---|---|
| `helm lint <chart>` | each `helm/<chart>/` | `[ERROR]` lines → `failed`; `[WARNING]`/`[INFO]` → `warning` |
| `hadolint --format json` | each Dockerfile | `error` → `failed`; `warning`/`info`/`style` → `warning` |
| `ansible-lint --offline -f json` | `ansible/` | per its JSON severity; never let it install collections or roles |
| `promtool check config` | `monitoring/prometheus/*.yml` | non-zero exit with a parse error → `failed` |

- **Every linter:**
  - runs through `ProcessToolRunner` in the scan's temp copy, with the
    minimal environment and the black-hole proxy;
  - has a per-linter timeout (`VALIDATOR_TOOL_TIMEOUT_SECONDS`, default 60);
  - ends in one of three ways:
    - **not installed** → `skipped (not_installed)`;
    - **crash or timeout** → `skipped (tool_error)`, recorded and never a pass;
    - **otherwise** → mapped per the table above.
- **Linters are optional checks:** their crash or skip never causes
  `validation_error`. Only Terraform is required (section 1).
- **Record each linter's version** in the report.

## 7. The ValidatorAgent and wiring

- **`ValidatorAgent` implements the Phase 4 `ValidationStage` protocol.**
  - It receives the **remediated** files (the 5b fix ensures this).
  - It runs the checks for one package concurrently, bounded by
    `VALIDATOR_MAX_PARALLEL_TOOLS` (default 3).
  - It writes `validation_report` through a new
    `PackageRepository.save_validation_results(...)`, in one transaction.
  - It emits `agent_state` events for `validator`, the package transitions,
    and one `stage_notice` with the summary counts. No file contents in
    events.
  - It returns `valid`, `invalid` or `validation_error`.
- **`VALIDATION_DEADLINE_SECONDS`** (default 120): if exceeded, the outcome is
  `validation_error`, recorded with its reason.
- **`create_app` uses the real `ValidatorAgent`.** Delete
  `UnavailableValidationStage`, and update D-20 and D-26 (superseded).
- **The Phase 5 retry path:** a `pending_review` package with failed
  validation checks, retried through `remediate_from_review`, receives
  `failed_checks_for_remediation` (file-linked). Test that end to end at the
  service level, with recorded tools and a stub fixer.

## 8. Tests (with `req` markers)

**Recorded runs (most tests).** Capture real outputs once, normalise their
paths with the existing fixture normaliser, and keep the tests
path-independent:
- `terraform validate -json`, from a mirror-initialised fixture;
- `helm lint`;
- `hadolint`;
- `ansible-lint`;
- `promtool`.

**FR-V-01:**
- a broken local Terraform module reference is flagged with its file and
  line;
- the missing ConfigMap, Service-selector, Ingress-backend and HPA-target
  cases;
- a missing Secret is a **warning**.

**FR-V-02:** a Terraform vs Ansible name mismatch is flagged as a warning,
naming both files.

**FR-V-03:**
- an invalid resource type and a wrong argument name are reported **from real
  `terraform validate` output**, with file and line;
- the three skip reasons;
- **`validation_error` when the Terraform check is skipped** and Terraform is
  in the plan.

**FR-V-04:**
- the report structure;
- the summary counts;
- the `failed_checks_for_remediation` contents;
- persisted to `generated_packages.validation_report`.

**FR-V-05 / Option C:**
- a clean scan plus `valid` → `production_ready`;
- a clean scan plus `invalid` → `pending_review`;
- `scan_exhausted` plus `valid` → `pending_review`.

**The full stub pipeline:**
- a run whose packages are valid and clean ends **`success`** (prepare demo or
  fixture packages that pass);
- a mixed run ends `partial_success`.

**Built-in structural checks,** with one pass and one fail case per file type,
including Grafana with no `panels`, a Dockerfile with no `FROM`, and an Nginx
block with no `server`.

**Linters:**
- each pluggable linter's skipped path (not installed);
- the tool-error path;
- the mapping of each result.

**Real tools** (the `scanners` marker; skip if the tools or the mirror are
missing): `terraform validate` against the mirror on a valid fixture and an
invalid one, **with network disabled** (use the 5b namespace approach where
available).

**Canary:** the validator subprocess environments and reports contain no
secrets.

## 9. Evaluation (`make eval-validation`)

- **Validate the 12 committed Phase 3 packages,** as generated, with local
  tools only.
- **Report per package:**
  - the result (valid/invalid/error);
  - the failed checks per category;
  - the warnings;
  - the skipped checks and their reasons;
  - the duration.
- **Expected and to be confirmed:** the two gpt-oss packages with syntax
  errors fail `terraform.validate`.
- **Note honestly** that the earlier finding (an Aurora cluster with no
  instances) is a semantic gap that none of these checks detects.
- **Commit the report** under `docs/evals/phase6-validation-<timestamp>/`.

## 10. Documentation

- **D-33** (hybrid models) and **D-34** (prompt-caching measurement), both
  from section 0.
- **D-35, the validator design:**
  - the tiers;
  - the provider mirror;
  - the skip semantics;
  - the outcome rule;
  - the external linters, with their versions;
  - **the out-of-scope validators, with their reasons;**
  - naming findings as warnings.
- **"Thesis text to update", add:**
  - the artifact validation table, revised: built-in checks for Kubernetes,
    Nginx, Jenkins and Grafana, the Jenkins API, `nginx -t`, `grafana-cli`
    and `kubectl` out of scope, `promtool`, `hadolint`, `helm lint` and
    `ansible-lint` kept;
  - FR-V-02's warning semantics;
  - FR-V-03's offline mirror;
  - the Appendix A versions of `helm`, `hadolint`, `promtool`, `ansible-lint`
    and the provider list.
- **README:**
  - `make providers` (run once; needs network);
  - `tools/install_validators.sh`;
  - the new settings;
  - `make eval-validation`;
  - that runs can now end `success`.
- **Implementation log:** entry with real test counts, including the scanner
  tests run or skipped.

## 11. Out of scope

- The review, results and download endpoints (Phase 7).
- Frontend.
- Changes to the security policy or fix loop.
- Installing tools.
- LLM-based validation.

Finish with the summary format from `AGENTS.md` §10, and state explicitly:
- the mirrored provider versions and the mirror size;
- the installed linter versions;
- the eval's valid/invalid/error counts;
- whether a stub run ended `success`.
