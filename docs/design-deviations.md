# Design Deviations and Open Questions

Every place where the implementation differs from the thesis specification
(`docs/spec/`), and every unresolved ambiguity. This file feeds the
"Design deviations" section of thesis Chapter 5.

Status values:
- **In thesis:** the decision was made during design review and is now part
  of the thesis design (text and diagrams). No difference remains, but
  Chapter 5 may still describe it as a design refinement.
- **Accepted:** implemented; the thesis does not yet describe it.
- **Proposed:** awaiting the author's confirmation.
- **Superseded:** replaced by a later entry.

---

## Deviations

### D-01 — `agent_events.seq` ordering column (In thesis)
- **Spec:** `agent_events` has UUID `event_id` and `timestamp`; SSE replays
  history from the database.
- **Implementation:** add `seq BIGINT GENERATED ALWAYS AS IDENTITY (CACHE 1)`,
  unique, with an index on `(run_id, seq)`. `event_id` stays the primary key.
- **Reason:** UUIDs are not orderable and timestamps can tie. SSE reconnection
  (`Last-Event-ID`) needs a monotonic value to resume from.
- **Guarantee and its conditions:** An identity value is assigned at insert
  time, before commit, so on its own `seq` does not guarantee that commit
  order equals `seq` order. The guarantee holds because every writer goes
  through `EventLog.append()`, which takes
  `pg_advisory_xact_lock(<run id>)` before inserting and publishes to the
  in-memory broker only after commit. Per run, therefore, commit order equals
  `seq` order. Across runs, `seq` values interleave, so one run's `seq`
  values have gaps; nothing may assume they are consecutive.
- **Publish order:** `seq` order is guaranteed per `EventLog` instance, not
  merely by running in one process. The application constructs exactly one
  instance in `create_app()` and exposes it through one accessor; tests may
  construct additional instances to verify database ordering. In Phase 4,
  SSE subscribers will skip live events with `seq` at or below the last sent.
  Out-of-order publication from multiple app instances in one process could
  therefore silently drop an event for a subscriber.
- **In thesis:** ERD (`seq` column note) and sequence diagram (EventLog
  note).
- **Assumption:** single application process (the in-memory broker already
  requires it). The advisory lock keeps database ordering correct even with
  several writers; live publish ordering relies on using one `EventLog`
  instance in that process.
- **Implemented in Phase 0:** identity sequence with `CACHE 1`, advisory-lock
  append, ordered replay, and app-owned singleton access.

### D-02 — `TIMESTAMPTZ` instead of `TIMESTAMP` (In thesis)
- **Spec:** ERD uses `TIMESTAMP`.
- **Implementation:** all time columns are `TIMESTAMPTZ`; the application
  writes timezone-aware UTC values.
- **Reason:** unambiguous durations for PR-01 and the retention cutoff.
- **In thesis:** ERD.
- **Implemented in Phase 0:** application UTC timestamps and `TIMESTAMPTZ`
  columns.

### D-03 — Retention enforcement and foreign keys (In thesis)
- **Spec:** "Generated package data older than 30 days is eligible for
  deletion. `pipeline_runs` and `agent_events` rows are retained indefinitely
  for audit purposes."
- **Implementation:**
  - The retention sweep deletes only from `generated_packages`, by
    `created_at`, which is indexed. It never touches runs or events.
    **The retention policy is enforced by this sweep.**
  - Foreign keys from both child tables use `ON DELETE RESTRICT`. This is
    protection only: it blocks deleting a run that still has child rows, but
    a run with no events or packages could still be deleted by a privileged
    role, so RESTRICT alone does not guarantee retention.
  - Database-level prohibition: the application role `infraarch_app` has no
    DELETE privilege on `pipeline_runs` and no UPDATE or DELETE on
    `agent_events` (append-only audit log). See D-04.
- **In thesis:** ERD (RESTRICT on both relationships, `created_at` index
  note, retention note). Section 4.2 text still describes retention only as
  "eligible for deletion"; see the list at the end.
- **Implemented in Phase 0:** package-only sweep, retention index, RESTRICT
  foreign keys, and app-role prohibitions.

### D-04 — Two database roles (Accepted; privileges in thesis)
- **Spec:** not specified.
- **Implementation:** `infraarch_owner` owns the schema and runs migrations;
  `infraarch_app` is used at runtime with least-privilege grants:
  - `pipeline_runs`: SELECT, INSERT, UPDATE
  - `agent_events`: SELECT, INSERT
  - `generated_packages`: SELECT, INSERT, UPDATE, DELETE
- **Reason:** enforces D-03 in the database and limits damage from bugs.
- **In thesis:** the privilege consequences are noted on the ERD. The
  two-role setup itself (owner for migrations, app role at runtime) is an
  implementation detail for Chapter 5.
- **Implemented in Phase 0:** both roles, databases, and versioned table
  grants. App-role insertion into the identity column succeeded without
  sequence `USAGE`, so no sequence grant was added.

### D-05 — `files` JSONB shape and path validation (In thesis)
- **Spec:** `files JSONB`, `IaCPackage.files: dict`.
- **Implementation:** a map of relative POSIX path → file content. Paths are
  validated when an `IaCPackage` is constructed and again by the ZIP writer:
  relative only; no leading `/`, drive letters, backslashes, NUL bytes,
  `..`, `.` or empty segments; restricted character set; at most 255
  characters and 8 levels; no case-insensitive duplicates.
- **Reason:** prevents path traversal (e.g. `../`) when writing ZIPs or
  scanning files on disk.
- **In thesis:** class diagram (`IaCPackage.files: dict[str, str]` note).
- **Implemented in Phase 0:** path validation in `IaCPackage` and the package
  repository. The ZIP writer repeats validation in Phase 7.

### D-06 — Package outcomes after validation: Option C (In thesis)
- **Spec conflict (original):** the package state diagram showed
  `validation_error → production_ready` (unvalidated code labelled
  production-ready), while FR-UI-06, FR-V-05 and the run-state table treated
  `invalid` and `validation_error` as final, downloadable states. That let a
  package be delivered without an engineer decision, even with unresolved
  security violations. Both readings contradicted the human-in-the-loop
  principle (Section 3.1).
- **Decision (Option C):** a package becomes `production_ready`
  automatically only if its scan was clean AND validation passed. Every
  other outcome that produces a package (`scan_exhausted`, `invalid`,
  `validation_error`) goes to `pending_review`.
  - `invalid` and `validation_error` are intermediate states, recorded as
    events and shown as review reasons.
  - Final labels are only `production_ready` and `not_production_ready`, and
    only those are downloadable.
  - A retry's fix prompt includes the engineer's feedback and any failed
    validation checks (Phase 5).
- **Where in code:** `app/domain/states.py` (transition table,
  `readiness_after_validation`, `review_reasons`, `is_downloadable`).
- **In thesis:** text (FR-S-07, FR-S-09, FR-V-05, FR-UI-06, UC-08,
  run-state table, Chapter 4) and diagrams (package states, run states,
  sequence diagram 5/5a, class diagram `SecurityAgent.remediate`).
- **Implemented in Phase 0:** transition and readiness rules, review reasons,
  and downloadability predicate; agent and review flows follow later.

### D-07 — Async LLM template method and SDK transport (Accepted)
- **Spec:** the class diagram shows `LLMAdapter` with two provider methods;
  ADR-02 names `send_prompt` and `parse_response`.
- **Implementation:** `send_prompt` is async, `parse_response` is synchronous,
  and the concrete `complete_json` template method owns retry, timeout,
  backoff, and strict JSON handling. A new provider still implements only
  the two abstract methods (NFR-03).
- **Prompt correction:** Anthropic 1.8.0 and OpenAI 3.19.2 use `httpx2` for
  custom SDK clients. Provider tests therefore inject `httpx2.AsyncClient`
  with `httpx2.MockTransport`, rather than the prompt's `httpx` equivalents.
  Phase 0 FastAPI tests continue using `httpx` without global aliasing.
- **Reason:** the pipeline is asyncio-based and the installed SDK transport
  types reject or do not natively type-check with legacy `httpx` clients.
  The shared template keeps the retry policy out of provider classes.
- **Implemented in Phase 1:** adapter contract, shared wrapper, both real
  providers, stub, factory, and offline tests.

### D-08 — OpenAI-compatible base URL (Accepted)
- **Spec:** ADR-02 names Anthropic and OpenAI as the supported LLM APIs;
  endpoint configuration is not specified.
- **Implementation:** optional `LLM_BASE_URL` is passed by the factory only
  to `OpenAIAdapter`, which supplies it to `AsyncOpenAI` when set. The default
  remains the SDK's OpenAI endpoint. Compatible services use
  `LLM_PROVIDER=openai` and their own model and key; no provider class or
  enum value is added.
- **Reason:** an OpenAI-compatible Chat Completions endpoint can use the
  existing adapter contract and retry policy.
- **Implemented in Phase 1 follow-up:** setting, factory and SDK wiring,
  mocked request-URL tests, and a README Groq example.

### D-09 — Respect provider rate-limit retry delay (Accepted)
- **Spec:** LLM calls retry transient failures with exponential backoff;
  provider-directed rate-limit delays are not specified.
- **Implementation:** on HTTP 429, both adapters prefer a finite,
  nonnegative `retry-after` value, including numeric seconds and duration
  strings. If it is absent or invalid, they take the largest parseable
  `x-ratelimit-reset-tokens` or `x-ratelimit-reset-requests` duration
  (`ms`, `s`, or `m` plus `s`). The shared wrapper waits for the greater of
  this value and jittered backoff, within the remaining call deadline. A
  delay that leaves no time for another attempt raises
  `LLMDeadlineExceeded` without sleeping. With no valid hint, ordinary
  backoff applies.
- **Reason:** retrying before the provider's stated limit expires wastes an
  attempt and can repeat the rate limit. Only the parsed wait and names of
  recognized rate-limit headers reach the shared error and attempt log;
  raw header values are never logged.
- **Implemented in Phase 1 follow-ups:** both SDK mappings, shared retry
  policy, duration fallback and safe header-name logging, with deterministic
  `httpx2.MockTransport` tests.

### D-10 — Strict deployment plan (Accepted)
- **Spec:** FR-A-01--03 require a structured plan, named IaC file types, and
  recorded ambiguities; the class diagram leaves field types open.
- **Implementation:** replace Phase 0's permissive placeholder with frozen
  Pydantic models that forbid extra fields. The AWS plan names services,
  dependencies, network, storage, file types, and ambiguities. It checks
  references, uniqueness, cycles, Terraform inclusion, and a 32,768-byte
  compact UTF-8 JSON limit. The previous `app.domain.models` import remains.
- **Reason:** generator input must be internally consistent and small enough
  for a later event payload; validation errors must be actionable for retry.
- **Implemented in Phase 2:** plan model, error collector, and offline tests.
- **Evaluation clarification:** the soft infrastructure checks accept
  schema-equivalent placements. A relational database is either a service
  labelled RDS/Aurora or `storage.kind = relational_db`; object storage is
  either `storage.kind = object_storage` or an S3-labelled entry. CDN and queue
  checks inspect `aws_service` in both services and storage. The Phase 2
  evaluation prompt's phrase "RDS-like service" is narrower than the schema.

### D-11 — Schema-derived ArchitectAgent correction prompt (Accepted)
- **Spec:** FR-A-01--04 require a JSON plan, ambiguity notes, and failure
  handling, but do not define prompt construction or correction feedback.
- **Implementation:** the versioned system prompt embeds the model's JSON
  schema and treats tagged user text as data. A failed plan attempt supplies
  numbered validation errors and at most 8,000 characters of prior output
  to the next attempt. Neither prompts nor responses are logged.
- **Reason:** the schema and prompt stay aligned, and a correction targets
  concrete plan defects without persisting untrusted text.
- **Implemented in Phase 2:** prompt builder and ArchitectAgent tests.
- **Prompt v2 follow-up:** explicitly separates services, storage attachments,
  and deployment tools, and tells the model to verify every service reference
  before responding. Validation feedback identifies storage names and file
  types used as dependency endpoints and gives the corrective action.
- **Evaluation follow-up:** reports include at most ten validation messages
  per failed plan attempt and the safe LLM failure category. They omit
  prompts, raw responses, and credentials; console attempt metrics pass
  through the existing redacting logger.

### D-12 — Fixed package layout (Accepted)
- **Spec:** FR-G-02 requires each planned file type but does not specify paths.
- **Implementation:** one FileType-to-path table defines where every generated
  file may live and which path proves completeness. The optional root README
  is exempt from the plan's type list; unplanned types are rejected.
- **Reason:** explicit paths make completeness deterministic and let the
  generator prompt, validator, and tests share one convention.
- **Implemented in Phase 3:** `app/domain/package_layout.py`.

### D-13 — Directive compliance is a report (Accepted)
- **Spec:** FR-G-03--05 set preferences and FR-G-05 proposes a Checkov-based
  first-scan test, but the generator-stage rejection policy is unspecified.
- **Implementation:** cost size and AZ, performance multi-AZ and autoscaling,
  and security RDS/S3 encryption, S3 public access, ingress port, and IAM
  action checks are regex-level reports. They never reject a structurally
  valid package. The check receives the plan for conditional DB/S3 checks.
- **Reason:** text heuristics cannot establish actual compliance; Phase 5
  scanner findings provide the substantive security result.
- **Implemented in Phase 3:** `app/domain/directive_checks.py`.
- **Aurora heuristic correction (2026-09-30):** the performance multi-AZ
  report originally looked only for `multi_az = true`, which falsely failed
  Aurora clusters. It now also passes when an `aws_rds_cluster` has more than
  one declared `aws_rds_cluster_instance`, or lists more than one distinct
  `availability_zones` value. This remains a text heuristic: it does not
  resolve Terraform expressions, verify that instances reference the same
  cluster, or prove actual placement across zones.

### D-14 — One LLM response per package attempt (Accepted)
- **Spec:** FR-G-02 requires a complete package but does not specify call
  granularity.
- **Implementation:** each package attempt requests every planned file type
  in one LLM response. A failed structure check may trigger one complete
  replacement response.
- **Reason:** names and references across files are more likely to stay
  consistent when generated together.
- **Implemented in Phase 3:** the shared GeneratorAgent template.
- **Prompt v2 follow-up:** instruct generators to keep files compact after a
  real evaluation encountered an upstream 8,192-token output cap. The
  performance directive also calls for an HPA per application Deployment
  when Kubernetes is in the plan.
- **Prompt v3 follow-up:** generalise the performance directive's per-service
  autoscaling instruction to Kubernetes Deployments, ECS services, and EC2
  Auto Scaling groups. The shared generator algorithm is unchanged.

### D-15 — Template Method plus Strategy for generators (Accepted)
- **Spec:** Chapter 4 and the class diagram show each concrete generator
  overriding `generate()`; ADR-06 also describes a runtime directive.
- **Implementation:** the abstract base fixes the budget, LLM call,
  validation, and correction algorithm (Template Method). Each concrete
  subclass supplies only `variant` and `optimisation_directive` (Strategy).
- **Reason:** all variants must enforce identical safety and completeness
  behavior; only their optimisation guidance varies.
- **Implemented in Phase 3:** the three named GeneratorAgent subclasses.

### D-16 — Optional reasoning effort for OpenAI-compatible requests (Accepted)
- **Spec:** the thesis does not define a request-level reasoning control for
  the generator evaluation.
- **Implementation:** `LLM_REASONING_EFFORT` is unset by default. The
  OpenAI-compatible adapter then omits `reasoning`; `off` sends
  `reasoning: {enabled: false}` and `low`, `medium`, or `high` send
  `reasoning: {effort: <value>}` through the SDK's `extra_body`. Every attempt
  logs the configured value or `unset`. The Anthropic adapter records the
  setting but does not change its request.
- **Reason:** [OpenRouter's unified reasoning parameter](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
  permits controlled comparisons while leaving existing calls unchanged by
  default. Providers and models may differ in support.
- **Evaluation:** OQ-07's configuration mechanism is resolved; its effect on
  generation quality is measured in the evaluation, not assumed here.

### D-17 — Default evaluation model (Accepted)
- **Decision:** use `anthropic/claude-sonnet-5` through OpenRouter's
  OpenAI-compatible endpoint with `LLM_REASONING_EFFORT=off` for the thesis
  evaluation. The runtime default remains `stub`.
- **Evidence:** committed evaluations under `docs/evals/` found 5/5 Architect
  plans valid on the first attempt and 6/6 generator packages with 100%
  heuristic compliance, about 72 seconds median per package and about $0.65
  for six packages. With reasoning enabled, only 3/6 packages completed due
  to truncation and deadlines. `openai/gpt-oss-120b:nitro` completed 6/6 at
  about 3 seconds and two cents, with 87.5–93.8% compliance; it remains the
  fast, low-cost configuration. `qwen/qwen3-coder` completed 3/6 and was too
  slow for the budget.

### D-18 — SSE message format (Accepted)
- **Implementation:** frames use `id: <seq>`, `event: <kind>`, and JSON data
  with `seq`, `kind`, `agent`, `status`, `previous_status`, `message`, `variant`,
  `timestamp`, and `payload`. `payload.kind` is persisted through `EventLog`;
  package events include `payload.variant` and never file contents.

### D-19 — Failed launch edge (Accepted)
- **Implementation:** permit `created → failed` for a persisted run that
  cannot start or is found at startup. Terminal run states remain frozen.
  State and event commits are separate transactions; a hard crash between
  them can leave a missing event even though the state is correct.

### D-20 — Unavailable security stage (Removed in Phase 5)
- **History:** Phase 4 moved generated packages through `scanning` to
  `scan_error` with an explicit unavailable notice. Phase 5 replaces that
  placeholder with Checkov, tfsec, and the remediation loop.

### D-21 — Bounded in-process runner (Accepted)
- **Implementation:** `MAX_CONCURRENT_RUNS` defaults to five. Capacity is
  reserved before persistence; a full runner returns HTTP 429 without a run
  row. This caps resource use while meeting PR-03's three-run requirement.

### D-22 — Blocking severity policy and first-scan measures (Accepted)
- **Spec difference:** FR-S-02 says to remediate every violation. Phase 5
  remediates CRITICAL, HIGH, and MEDIUM findings. LOW findings, unknown
  Checkov IDs, and narrow variant exemptions remain visible but advisory.
  This avoids costly fixes for checks that lack a defensible severity or
  contradict the cost/performance directive. Security-variant checks are
  never exempted.
- **Checkov severity source:** the local `CHECKOV_SEVERITY` table covers
  common AWS, Kubernetes, and Dockerfile checks. Assignments use Checkov
  3.3.21 check descriptions (`checkov --list`) and tfsec v1.28.14 severity
  for comparable Terraform rules. Free Checkov does not supply severity in
  offline JSON; unknown IDs are `UNKNOWN` and advisory.
- **Exemptions:** cost may omit cross-region S3 replication, RDS multi-AZ,
  Performance Insights, and enhanced monitoring; performance may omit
  cross-region S3 replication. Cost may treat Checkov's KMS-by-default S3
  check as advisory only when the package contains SSE-AES256. The finding
  remains in the report with its reason.
- **FR-G-05:** the security variant passes only with zero Checkov HIGH or
  CRITICAL records on its first scan. The report also stores tfsec's count
  and their sum; equivalent findings reported by both tools count twice in
  that combined diagnostic, while each tool's count stays separate.
- **Report bound:** every blocking finding is retained, but advisory samples
  and embedded diffs are capped with omitted counts. This narrows FR-S-04's
  literal "full scan report" wording to a bounded, auditable report.

### D-23 — Per-file fixes and retry audit baseline (Accepted)
- **Implementation:** one LLM call handles all blocking findings for an
  affected file; file calls run concurrently. Untouched file strings remain
  byte-identical. A response can add at most three planned-layout files.
  Conflicting new-file proposals are rejected in deterministic path order.
- **Audit:** `generated_packages.original_files` is written on the first
  security-result save and never overwritten. A new migration adds the
  nullable JSONB column without changing grants. `remediation_diff` always
  compares this baseline to current files. The JSON report holds automated
  and review-retry sessions; a retry appends a session, resets the current
  iteration count, and includes its own diff. Only the latest ten sessions
  remain in the bounded report; `omitted_session_count` records older ones.
  `security_report.final` mirrors the latest session's `final` for direct
  access to the current outcome and first-scan counts.
- **Phase 6 contract:** each failed validation check supplied for a review
  retry names its package-relative file and, when known, its lines. A
  validation-only retry then targets those files and carries feedback and
  failed checks in each applicable file prompt.

### D-24 — Reject new suppression annotations (Accepted)
- **Implementation:** the fix validator compares case-insensitive Checkov,
  tfsec, Trivy, Bridgecrew, and `#nosec` suppression comments in the old
  and proposed content. Any newly introduced annotation rejects that file
  response; new files must contain none. The original file and finding
  remain for the rescan and report.

### D-25 — Scanner subprocess environment (Accepted)
- **Implementation:** Checkov and tfsec run without a shell under a timeout,
  with only PATH, fresh HOME/TMPDIR, and LANG. Database URLs, LLM credentials,
  cloud credentials, and inherited scanner configuration are excluded.
  Checkov uses `--skip-download --skip-results-upload`; tfsec uses
  `--no-module-downloads`. These flags and the offline test show that these
  inputs do not require network access; they are not OS-level network
  isolation (`unshare -n` is unavailable on this machine).

### D-26 — Reached validation placeholder (Accepted, temporary)
- **Implementation:** Phase 5's real scan reaches the Phase 6 placeholder.
  It records `scan_clean|scan_exhausted → validating → validation_error`
  and a stage notice, then the existing readiness rule sends the package to
  `pending_review`. Stub pipeline runs therefore end `partial_success`,
  never `production_ready`, until real validation arrives in Phase 6.

### D-27 — Portable recorded scanner fixtures (Accepted)
- **Implementation:** recorded Checkov and tfsec JSON uses the fixed
  `/__RECORDED_ROOT__` marker in place of the capture machine's absolute
  package root. The test runner replaces it with each temporary scan root;
  a capture script normalizes new recordings and rejects captures without
  that root. This keeps scanner-path validation independent of checkout
  location while preserving the original relative file references.

### D-28 — Terraform parser failures as blocking findings (Accepted)
- **Implementation:** a tfsec HCL parse diagnostic with a package file,
  line, and parser message becomes a CRITICAL `TERRAFORM_SYNTAX` finding.
  Its scan is marked `syntax_limited`: tfsec produced no other findings, so
  a fix pass must repair syntax before a full rescan. The path is constrained
  to the package file map and the temporary root is never reported. Other
  malformed output, missing binaries, and timeouts still follow the scan
  retry and `scan_error` path. The evaluation includes the syntax finding
  and counts it once under tfsec, leaving FR-G-05's Checkov measure intact.

## Clarifications (spec is silent; the diagrams decide)

### CL-01 — Where the iteration limit is checked
- **Spec:** the text says only that the loop "exits with unresolved
  violations". The package state diagram draws `remediating →
  scan_exhausted` ("iteration limit reached with violations remaining") and
  has no `scanning → scan_exhausted` edge.
- **Implementation:** `scanning → remediating | scan_clean | scan_error`;
  `remediating → scanning | scan_exhausted`. When a scan finds violations,
  the package enters `remediating`. There, if the iteration budget is used
  up, it moves to `scan_exhausted` without applying a fix; otherwise it
  applies a fix pass, increments `iteration_count` and returns to
  `scanning`. `iteration_count` therefore counts completed fix passes, and
  it never exceeds `max_iterations`.
- **Implemented in Phase 0:** pure remediation-budget decision and transition
  tests; actual fix application follows in the SecurityAgent phase.

### CL-02 — Validation follows exhausted remediation
- **Spec:** FR-S-07 says unresolved violations lead to `pending_review`,
  while FR-S-05 says an exhausted package proceeds to ValidatorAgent. The
  package state diagram routes `scan_exhausted` through `validating` first.
- **Implementation:** exhausting the budget stops automated remediation,
  then validation runs. Its result is recorded as `valid`, `invalid`, or
  `validation_error` before the package enters `pending_review`.
- **Implemented in Phase 0:** package transition table and readiness tests.

### CL-03 — LLM retry arithmetic
- **Spec conflict:** Section 3.2 states both "30 seconds per attempt, up to
  3 attempts" and "30s + 60s + 60s = maximum 150 seconds including backoff".
- **Implementation:** each attempt is limited to 30 seconds, with at most 3
  attempts. Backoff has a 1-second then 2-second exponential ceiling before
  full jitter. The wrapper has a separate hard 150-second deadline that clips
  attempts and backoff when needed. Ordinary three-attempt timeouts finish
  well before 150 seconds.
- **Implemented in Phase 1:** `RetryPolicy` and `LLMAdapter.complete_json`.

### CL-04 — Input length and validation order
- **Spec:** FR-I-01 sets a 10--2,000-character limit, and FR-I-02 calls for
  a 422 when infrastructure intent is absent; simultaneous failures have no
  stated priority.
- **Implementation:** reject control characters first, then measure Unicode
  code points after stripping surrounding whitespace and reject out-of-range
  input with the future HTTP 400 error, then apply the intent gate and use
  the future HTTP 422 error. Thus `hello` is a length error. The word-list
  gate favours false accepts over false rejects: one whole-word
  infrastructure term, including simple single-word inflections, is enough
  to proceed.
- **Implemented in Phase 2:** pure input rules and boundary tests. HTTP
  mapping remains Phase 4 work.

### CL-05 — Valid vague-description example
- **Spec conflict:** FR-A-03's verification input `a web app` has nine
  characters, below FR-I-01's ten-character minimum.
- **Implementation:** use `build a web app` in Phase 2 acceptance and
  evaluation tests; explicitly test that `a web app` fails the length rule.
- **Implemented in Phase 2:** input, agent, and evaluation tests.

### CL-06 — Full-package generator timing
- **Spec:** PR-05 describes 30 seconds per LLM attempt for every agent.
- **Implementation:** short calls keep the 30-second adapter default. A
  GeneratorAgent has a configurable 150-second overall budget and passes a
  configurable 120-second per-attempt timeout and 32,000 output-token limit
  for full-package calls. Remaining agent time still caps each call.
- **Reason:** a multi-file package is substantially longer than a plan.
- **Implemented in Phase 3:** per-call adapter overrides and generator settings.

### CL-07 — Local scanner availability and output (Phase 5)
- Checkov 3.3.21 and tfsec v1.28.14 are installed; tfsec is in maintenance
  mode and prints a Trivy banner on stderr in JSON mode. Checkov can return
  one report, a framework list, or a summary-only object for zero resources.
  It can exit 1 with valid finding JSON. `helm` is absent, so Checkov skips
  Helm chart scanning; Phase 5 does not install it.
- The committed scan-only evaluation records two gpt-oss packages with
  invalid Terraform. tfsec reports a file and line for each syntax error;
  both now have a CRITICAL `TERRAFORM_SYNTAX` finding and a syntax-limited
  scan instead of a scanner error. Checkov 3.3.21 reported zero parsing
  errors and zero resources on the same invalid `locals "x" { a = 1 }` file,
  so Checkov alone does not detect this syntax error.

---

## Open questions

### OQ-01 — HTTP 410 for expired packages (Deferred)
A missing package row cannot justify 410 on its own: the ERD allows 0–3
packages per run, so absence may mean "generation failed" or "removed by
retention". 410 needs a durable record of which variants once existed, for
example an `agent_events` row with a defined payload such as
`{"kind": "package_stored", "variant": "cost"}`. Decide in Phase 4 (event
payload schema) or Phase 7 (download/results endpoints). Phase 4 now records
`package_generated` with a variant and paths, providing durable evidence.
Phase 7 still decides and implements the 410 response. Until then, no 410.

### OQ-02 — Terminality of `invalid` and `validation_error` (Resolved)
Resolved by D-06 (Option C).

### OQ-03 — 30-second per-attempt LLM timeout
A full multi-file package may take longer than 30 s to generate. Measure it
in the Phase 1 spike before building on it.

**Measurement (2026-09-26):** Groq free tier via the OpenAI-compatible adapter,
model `openai/gpt-oss-120b`. The [full-package spike](spikes/phase1-llm-timing-openai-20260926T004541Z.md)
completed in one call in 24.6 s, at about 474 output tokens/s. It returned
11,660 output tokens; JSON parsed and was not truncated. In split mode, all
9 parallel file-group calls returned HTTP 429 and none generated output.
Groq's published free-plan limits for this model are 8K tokens/minute,
30 requests/minute, and 200K tokens/day ([rate limits](https://console.groq.com/docs/rate-limits)).
This measurement shows that full-package latency fits 30 s on a fast provider,
but free-tier per-minute token limits prevent parallel generation in this
setup. The stub result remains a report-format check only. **OQ-03 stays open**
until the evaluation provider is chosen.

### OQ-04 — Single-process assumption
The in-memory SSE broker requires a single backend process. Phase 4 relies on
this: `make run` starts one Uvicorn worker, and the README states the
requirement. The thesis design should state it in Section 4.4 or deployment.

### OQ-05 — End-to-end agent deadline (Resolved)
One monotonic `AgentBudget` tracks elapsed time across plan attempts, prompt
construction, validation, and LLM calls. Before each call, the agent passes the remaining
budget to `complete_json`; the call uses the shorter of that value and its
own policy deadline for attempts and backoff. If fewer than one second
remains before a call, the agent stops. A valid response returned within
its call deadline is accepted after validation without another budget check.
Implemented in Phase 2 and tested with an injectable clock.

### OQ-06 — Evaluation provider throughput
Evaluation provider must allow ~3 concurrent full generations (~36K
tokens/min); Groq free (8K TPM) does not. Decide before PR-01/PR-05
measurements.

### OQ-07 — Reasoning effort and generator quality (Mechanism resolved)
The optional request control is implemented in D-16. Compare output quality,
completion, and token use across settings in the evaluation before claiming
that any effort level improves generator results.

### OQ-08 — Strict JSON diagnostics and JSON mode (Mechanism implemented)
Malformed responses now produce a safe reason code and, for syntax errors,
only a character offset; response text is never logged. Optional
`LLM_RESPONSE_FORMAT=json_object` sends OpenRouter's documented JSON mode on
the OpenAI-compatible adapter, while Anthropic ignores it. The author must
measure whether the option improves completion reliability on real runs.

### OQ-09 — Feedback-only retry targeting (Deferred to Phase 7)
When review feedback arrives with no blocking scanner finding and no
file-linked failed validation check, Phase 5 has no file to target under its
one-call-per-file rule. It records a notice and report entry saying feedback
was not applied, then rescans. Phase 7 should decide whether to add another
file-targeting rule for feedback-only retries.

---

## Thesis text to update (collected)
- Explain the `TERRAFORM_SYNTAX` critical finding, the syntax-limited scan
  status, and the full rescan after repair. Note that Checkov 3.3.21 reported
  zero parsing errors on the invalid `locals "x" { a = 1 }` fixture while
  tfsec located the error.
- In FR-S-02, state the HIGH/MEDIUM/CRITICAL remediation threshold and the
  advisory policy; in FR-S-04, state the bounded advisory sample and diff.
- In FR-G-05, define zero Checkov HIGH/CRITICAL first-scan findings as the
  pass criterion, and report tfsec and combined counts as diagnostics.
- Update Appendix A with Checkov 3.3.21, tfsec v1.28.14, and Terraform
  v1.16.4; describe the missing Helm binary and tfsec maintenance status.
- Update the ERD with `generated_packages.original_files` JSONB, the
  session-based security report, and its cumulative versus per-session diffs.
- Add `Violation`'s severity, location, title, guide, and advisory fields to
  the class diagram; specify Phase 6 failed-check file paths for retries.
- In the run-state table, replace `failed = 0 packages` with `failed = 0 usable
  packages`: Phase 4 retains generated rows that ended `scan_error` for audit.
- Section 4.4: include the 202 acceptance response, 429 capacity response,
  SSE frame fields, startup recovery, and `created → failed` edge.
- Add the model-comparison table and a quality-versus-latency discussion
  using D-17's committed results.
- Record the Aurora example: a structurally complete package had an Aurora
  cluster without instances. Structural checks, Checkov, tfsec, and planned
  Validator checks would not detect this; human review remains necessary.
- Describe the fixed package layout in Chapter 4 or 5 (D-12).
- State that `FR-G-01`, `FR-G-06`, and `FR-G-07` pipeline integration tests
  arrive with the Phase 4 orchestrator.
- Show `optimisation_directive: str` and the typed `variant` on the
  GeneratorAgent class diagram; the implementation keeps run metrics and
  notes outside `IaCPackage` (D-15).
- State that Phase 4 persists generator design notes in the
  package-generated event payload for the UI.
- In the class diagram, show each generator subclass's `variant` and
  `optimisation_directive` instead of overriding `generate()` (D-15).
- In Chapter 4's generator pattern description, name both Template Method
  and Strategy, and describe the shared algorithm and varying directive.
- PR-05 / per-attempt timing: state the per-agent timeouts (CL-06).
- Tighten FR-S-07 wording to say that exhausted remediation stops fix passes,
  then validation runs before the package enters `pending_review` (CL-02).
- Section 4.2 retention paragraph: say that the sweep deletes only packages
  and that the app role cannot delete runs or modify events (D-03, D-04).
  The ERD already shows this; the paragraph does not yet.
- Section 4.4: state the single-process assumption for SSE (OQ-04).
- Fix the "30s + 60s + 60s" sentence in Section 3.2 (CL-03).
- Add the concrete `complete_json` method and async `send_prompt` to the
  LLMAdapter class diagram (D-07).
- Optional class-diagram polish: `run_id: UUID`, `llm_provider:
  LLMProvider`, `variant: Variant`, and field types for `DeploymentPlan`
  and `Violation`.
- Add an ADR row: agents are plain Python classes over the custom adapter;
  reject agent frameworks such as LangChain, LangGraph, and CrewAI because
  the pipeline is fixed and direct control of retries and deadlines keeps
  dependencies and contributions explicit.
- Add the strict `DeploymentPlan` field types to the class diagram.
- State that the orchestrator stores the plan in the `plan_created` event
  payload (Phase 4), since the ERD has no plan column.
- In FR-A-03, change the nine-character verification input `a web app` to
  `build a web app` so it meets FR-I-01's ten-character minimum (CL-05).
