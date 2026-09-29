# Codex task — Phase 3: GeneratorAgents

Read `AGENTS.md`, `docs/design-deviations.md` and `docs/IMPLEMENTATION_LOG.md`
first. The specification is in `docs/spec/`. This task is **Phase 3 only**.
Phases 0–2 are complete. Keep their behaviour, except for the small
`complete_json` extension in section 1.

## Goal

Build the three GeneratorAgents:
- an abstract `GeneratorAgent`, with cost, performance and security subclasses
  (the **Strategy pattern** from the class diagram);
- each turns a `DeploymentPlan` into an `IaCPackage` of real files in a fixed
  folder layout;
- a completeness check (FR-G-02);
- directive-compliance checks that are **reported, not enforced**;
- the factory methods;
- an evaluation script that compares models on the same plans.

Relevant spec:
- FR-G-01 to FR-G-07;
- FR-A-05 (generators see only the plan);
- the class diagram (`GeneratorAgent` abstract, three subclasses,
  `optimisation_directive`, `generate(plan)`, `AgentFactory.create_generator`);
- the artifact validation table (the file types).

## Decisions already made by the author (do not revisit)

1. **One LLM call per package.** A generator produces its whole package in one
   response, so names and references stay consistent across files. There are
   no per-file-type calls.
2. **Fixed folder layout.** File types are identified from paths (section 2),
   not by guessing from content.
3. **Directive compliance is reported, not enforced.** A package that misses
   its directive (e.g. the cost variant uses `m5.large`) still proceeds.
   Compliance is checked and reported. Only structural problems (unsafe paths,
   missing plan file types, invalid output) trigger a correction attempt.
4. **Generators are pure,** like the ArchitectAgent: no database, no events,
   no `.env`.
   - Deferred to Phase 4, with the orchestrator: persisting packages (FR-G-07),
     running the three in parallel inside a pipeline run (FR-G-01), and run
     status (FR-G-06).
   - This phase provides the agents, plus a helper that runs them concurrently
     for the evaluation.

## Definition of done

- `make test` and `make lint` pass. No test touches the network.
- `make eval-generators` works end-to-end with `LLM_PROVIDER=stub`.
- Docs are updated per `AGENTS.md` §8.

Commit after each numbered section. Do not read `.env`. Make no real API
calls.

---

## 1. Settings and the `complete_json` extension

**New settings**, added to `.env.example` and the README:

| Variable | Default | Purpose |
|---|---|---|
| `GENERATOR_DEADLINE_SECONDS` | 150 | FR-G-06 budget per generator |
| `GENERATOR_ATTEMPT_TIMEOUT_SECONDS` | 120 | a full package is a long response; the 30 s default is for short calls |
| `GENERATOR_MAX_OUTPUT_TOKENS` | 32000 | packages are ~12K+ output tokens, plus reasoning tokens |
| `GENERATOR_MAX_PACKAGE_ATTEMPTS` | 2 | structural correction attempts |

**Extend `LLMAdapter.complete_json`** with two more optional keyword overrides,
following exactly the pattern of the existing `deadline` override:
- `attempt_timeout: float | None = None`. When given, it replaces
  `policy.attempt_timeout` for that call. It is still capped by the remaining
  deadline.
- `max_output_tokens: int | None = None`. When given, it replaces
  `policy.max_output_tokens` for that call.

`None` keeps today's behaviour. Add tests for both overrides and for `None`.

Record the new timing parameters in a new **CL-06**: the thesis's 30 s
per-attempt figure applies to short calls, and full-package generation uses its
own configurable attempt timeout. Add "PR-05 / per-attempt timing: state the
per-agent timeouts" to "Thesis text to update".

## 2. Package layout (`app/domain/package_layout.py`), pure

Define **one** table mapping each `FileType` to its path rule. The prompt,
the checks and the tests all derive from this table.

| FileType | Required path rule (at least one file matching) |
|---|---|
| terraform | `terraform/**/*.tf` |
| kubernetes | `k8s/**/*.yaml` or `k8s/**/*.yml` |
| helm | `helm/<chart>/Chart.yaml` (plus anything under `helm/<chart>/`) |
| dockerfile | `docker/**/Dockerfile` |
| jenkins | `jenkins/Jenkinsfile` |
| nginx | `nginx/**/*.conf` |
| ansible | `ansible/**/*.yml` or `ansible/**/*.yaml` |
| prometheus | `monitoring/prometheus/**/*.yml` or `.yaml` |
| grafana | `monitoring/grafana/**/*.json` |

**Also allowed:**
- `terraform/**/*.tfvars` and `*.tf.json`;
- files under `helm/<chart>/` (e.g. `values.yaml`, `templates/*.yaml`);
- a single optional top-level `README.md`.

**Functions:**
- `classify_path(path) -> FileType | None`;
- `required_types_missing(files, required: list[FileType]) -> list[FileType]`,
  for FR-G-02;
- `package_structure_errors(files, required) -> list[str]`. It returns
  human-readable, **actionable** messages, all collected together:
  - each missing required type, naming the expected path, e.g. *"missing
    kubernetes files: expected at least one k8s/*.yaml"*;
  - any file outside the layout;
  - any file belonging to a type **not** in the plan (the plan is the
    contract, FR-A-05);
  - empty files;
  - more than 80 files;
  - any file over 200 KB;
  - a total over 2 MB.

  Paths must also pass the existing Phase 0 `validate_file_map`; include its
  errors.

## 3. Generator output schema

The LLM returns `{"files": {path: content}, "notes": str}`:
- `notes` is optional, ≤ 1,000 characters, and holds the generator's design
  notes (useful later in the UI);
- `extra="forbid"`;
- `files` must be a non-empty object of string values.

A valid output becomes an `IaCPackage(variant, files)`. Keep `notes` in the
run info, not in the package.

## 4. `GeneratorAgent` (`app/agents/generators/`), the Strategy pattern

- **`base.py`: the abstract `GeneratorAgent`.**
  - Constructor: `llm_adapter`, `deadline_seconds`, `attempt_timeout`,
    `max_output_tokens`, `max_package_attempts`, `clock`.
  - Abstract members:
    - `variant: Variant`;
    - `optimisation_directive: str`, the variant-specific paragraph.
  - Concrete method `async generate(plan: DeploymentPlan) -> IaCPackage`.
    **It accepts only a `DeploymentPlan`** (FR-A-05): no text argument, and no
    access to the original description.
  - `last_run: GeneratorRunInfo | None`, following the ArchitectRunInfo
    pattern: package attempts, LLM attempts, elapsed seconds, tokens, prompt
    version, the structure-error counts per attempt, notes length, file count
    and total characters. It never contains file contents or prompt text.
- **`cost.py`, `performance.py`, `security.py`:** the concrete subclasses.
  Each defines **only** its `variant` and `optimisation_directive`. Use the
  class names from the class diagram in `docs/spec/`.

**Directives** (write them as clear instructions to the model):
- **cost (FR-G-03):**
  - prefer AWS Free Tier eligible resources and the smallest reasonable sizes
    (e.g. `t3.micro` / `db.t3.micro`);
  - on-demand pricing;
  - single-AZ unless the plan requires otherwise;
  - minimal replicas;
  - avoid NAT gateways where a cheaper design is possible;
  - keep monitoring lightweight.
- **performance (FR-G-04):**
  - larger instance classes;
  - `multi_az = true` for databases;
  - autoscaling (an ASG with scaling policies, and/or a Kubernetes HPA);
  - multiple replicas;
  - caching where the plan has a cache;
  - load balancing across AZs.
- **security (FR-G-05):**
  - least-privilege IAM (no `*` actions or resources);
  - encryption at rest (RDS `storage_encrypted = true`, S3 server-side
    encryption, encrypted EBS) and in transit (TLS/HTTPS listeners);
  - private subnets for everything that isn't public in the plan;
  - no `0.0.0.0/0` ingress except HTTPS on public load balancers;
  - S3 public access blocks;
  - no hardcoded secrets (use variables or a secrets manager);
  - logging enabled.

**Behaviour of `generate`:**
1. Start an `AgentBudget(deadline_seconds)`.
2. Run up to `max_package_attempts` attempts. Each calls:

   ```python
   complete_json(user_prompt, system=system_prompt,
                 deadline=budget.remaining(),
                 attempt_timeout=self.attempt_timeout,
                 max_output_tokens=self.max_output_tokens)
   ```

   Before each call, check `remaining() < 1` and stop with the deadline error
   **without calling** (the Phase 2 lesson). Then validate the output schema
   plus `package_structure_errors(files, plan.file_types)`.
3. If the package is valid, return it immediately. There is no budget re-check
   after validation (the Phase 2 rule).
4. If it is invalid, the next attempt's prompt lists the numbered errors and
   the **paths** of the previous files (not their contents, which are too
   large), and asks for the complete corrected package.

**Errors** (subclasses of `GeneratorError`, with `category`, `variant` and a
plain-English message):
- `GeneratorDeadlineExceeded`;
- `GeneratorIncompletePackage`, for FR-G-02. It carries the missing types and
  the last errors, capped at 10;
- `GeneratorLLMFailure`, with the LLM category only.

## 5. Prompt (`app/agents/prompts/generator.py`)

- `GENERATOR_PROMPT_VERSION = "1"`.
- The system prompt is built from:
  - the shared rules;
  - **the variant's directive**;
  - **the layout table generated from section 2's table**, not typed out
    separately.
- **The rules:**
  - AWS; Terraform is the source of truth for cloud resources;
  - produce files **only** for the plan's `file_types`, with every one of them
    present;
  - use the plan's service and storage names consistently across **all**
    files. For example, a Kubernetes Service name, a Helm value, the Terraform
    RDS identifier and the Nginx upstream must match;
  - complete, deployable content: no `TODO`, no placeholders like `<your-value>`;
    use Terraform variables with sensible defaults instead;
  - never hardcode secrets or credentials;
  - output only one JSON object `{"files": {...}, "notes": "..."}`.
- **The plan is data.** The user prompt embeds the plan as JSON inside
  `<deployment_plan>` tags. Neutralise `<` inside it, exactly as the Architect
  prompt does with the user text: plan strings (purpose, ambiguities)
  ultimately derive from user input.

## 6. Factory

Add to `AgentFactory`:
- `create_generator(variant, run_config=None) -> GeneratorAgent`;
- `create_generators(run_config=None) -> list[GeneratorAgent]`, returning all
  three, in cost, performance, security order.

Both use the run config and the new settings. This is the only place
generators are constructed, outside tests.

## 7. Directive-compliance checks (`app/domain/directive_checks.py`), report only

`check_directive(variant, files) -> list[DirectiveCheck]`, where
`DirectiveCheck` has `name`, `passed: bool` and `detail`. These are **documented
heuristics** over the Terraform/Kubernetes text (regex level, which is enough
for a report):

- **cost:**
  - every `instance_type` / `instance_class` value is micro or small class
    (`t2/t3/t3a/t4g` with `.micro`/`.small`, `db.t3.micro`/`db.t4g.micro` etc.);
  - no `multi_az = true`.
- **performance:**
  - `multi_az = true` is present when the plan has a relational DB;
  - an autoscaling construct exists (`aws_autoscaling_group`,
    `aws_appautoscaling_*`, or a Kubernetes `HorizontalPodAutoscaler`).
- **security:**
  - `storage_encrypted = true` when the plan has RDS;
  - S3 encryption configuration present when there's S3;
  - an S3 public access block is present when there's S3;
  - no `0.0.0.0/0` ingress except on port 443;
  - no IAM statement with `"*"` actions.

Each check states its result and a short reason. **Nothing is rejected.**
FR-G-05's real test (zero HIGH findings) happens in Phase 5 with Checkov. Note
that in the module docstring.

## 8. Tests (offline, with `req` markers)

**Layout** (`req("FR-G-02")`):
- every type classifies correctly;
- nested paths;
- helm requires `Chart.yaml`;
- files outside the layout are rejected;
- an unplanned type is rejected;
- empty file, size and count limits;
- messages name the expected path;
- several errors are reported together.

**Generator agent**, with a scripted stub and a fake clock:
1. A valid package on the first attempt: an `IaCPackage` with the right
   variant; `last_run` is filled, with no file contents in it.
2. A missing file type, then complete. The second prompt contains the missing
   type's error text **and the previous paths, but not the contents**.
3. Incomplete twice: `GeneratorIncompletePackage` with the missing types
   (`req("FR-G-02")`).
4. An unsafe path (`../x`) is treated as a structure error.
5. Budget: an attempt that consumes the budget; the next attempt makes **no
   call** (assert the stub recorded one prompt).
6. The overrides reach the adapter: `attempt_timeout` and `max_output_tokens`
   are passed (assert via a recording test adapter).
7. **`generate` only accepts a `DeploymentPlan`,** and the prompt contains the
   plan JSON and no other user text (`req("FR-A-05")`).
8. **The Strategy pattern**
   (`req("FR-G-01","FR-G-03","FR-G-04","FR-G-05")`):
   - the three subclasses produce **different** system prompts, each
     containing its directive;
   - they share every other rule, byte for byte outside the directive
     section;
   - the subclasses define only `variant` and `optimisation_directive`.
9. The `<` in plan strings is neutralised in the prompt.

**Directive checks**, with small fixed Terraform/K8s snippets per check, for
both pass and fail.

**Factory:**
- `create_generators` returns three agents with distinct variants, in order;
- run-config overrides reach the adapter;
- settings reach the agents.

**Canary** (`req("NFR-01")`): a `GeneratorLLMFailure` from a provider error
containing the canary key doesn't leak it.

## 9. Evaluation script (`backend/scripts/eval_generators.py`, `make eval-generators`)

**Inputs:** two fixed plans stored as fixtures next to the script. Copy them
from the committed prompt-v2 Architect evaluation (the `three_tier` and
`kubernetes_monitoring` plans in the committed `docs/evals/phase2-architect-*`
run with prompt version 2). If you can't find them, write two equivalent valid
plans by hand.

**Arguments:**
- `--models` (a comma-separated list; default: the configured model);
- `--plans` (a comma-separated list; default: both);
- `--mode parallel|sequential` (default `parallel`: the three variants run
  concurrently via `asyncio.gather`);
- `--pause-seconds` (default 0; the pause between generators in sequential
  mode and between plans, for free-tier limits);
- `--save-packages` (a flag: write every generated file under the output
  directory, so the author can inspect real packages).

**Per model × plan × variant, record:**
- success or error category;
- missing types;
- package attempts, LLM attempts, elapsed seconds;
- tokens, file count, total characters;
- **every directive check with PASS/FAIL**;
- the wall-clock time for the three variants together, in parallel mode.

**Output:** `docs/evals/phase3-generators-<timestamp>/`, containing:
- `results.json`;
- `summary.md`, with:
  - one table per plan, with models as column groups;
  - a directive-compliance section;
  - a totals line per model: success rate, compliance rate, median time, total
    tokens;
  - an **estimated cost** per model, from optional `--price-in` and
    `--price-out` per-million arguments, given per model as
    `model=in/out,...`;
- `packages/` when `--save-packages` is set.

Never write the key or the prompts.

**With `--models stub`:**
- use fixture packages (valid, and complete for the fixture plans) loaded into
  the stub adapters **after** building agents through the unchanged factory
  (the Phase 2 pattern);
- include one incomplete-then-complete fixture, so the correction loop is
  visible;
- use fixture content designed so the directive checks show both PASS and
  FAIL.

Commit that stub output as the format example. **No real API calls.**

## 10. Documentation

- **D-12:** the package layout convention and why (decision 2), plus the
  "plan is the contract" rule for unplanned types.
- **D-13:** directive compliance is reported, not enforced (decision 3), with
  the heuristic checks listed.
- **D-14:** one call per package (decision 1), and the reason (cross-file
  consistency).
- **CL-06:** the per-agent timing parameters (section 1).
- **"Thesis text to update", add:**
  - the class diagram's generator members, if their names or types changed;
  - the package layout (Chapter 4 or 5);
  - a note that the FR-G-01, FR-G-06 and FR-G-07 integration tests land in
    Phase 4 with the orchestrator.
- **README:** the new settings, `make eval-generators` with examples
  (sequential mode for rate-limited free tiers; `--models` for comparisons),
  and the tip that OpenRouter's `:nitro` model suffix prefers faster hosts.
- **Implementation log:** entry with real test counts.

## 11. Out of scope

- Orchestrator and pipeline run.
- Database persistence.
- Events and SSE.
- API endpoints.
- Scanners: Checkov and tfsec, and the Terraform/linters.
- SecurityAgent and ValidatorAgent.
- Frontend.
- Real API calls.

Finish with the summary format from `AGENTS.md` §10.
