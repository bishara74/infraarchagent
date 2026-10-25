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

- **Phase 6 clarification:** D-20 describes the historical security placeholder,
  not validation unavailability; D-26 records that separate placeholder.
- **Phase 5b update:** Phase 5 scanner names in this history are superseded by D-31.

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

- **Phase 5b update:** Phase 5 scanner/count naming is superseded by D-31 (policy 2): Checkov
  severities/thresholds stay unchanged; Trivy and Terraform counts are separate,
  combined counts sum all three tools, and FR-G-05 still measures Checkov alone.
  The historical Checkov severity derivation from tfsec remains its provenance.

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

- **Phase 5b update:** The Phase 5 environment/timeout implementation is superseded by D-31
  and D-32. All three scanners and version probes now receive fixed loopback
  refusal proxies, empty NO_PROXY, disabled Git prompting and tool-specific
  offline settings. `unshare -Urn` works in the Phase 5b session; namespace tests
  confirm offline execution, while runtime does not enforce kernel isolation.

### D-26 — Reached validation placeholder (Superseded by D-35 in Phase 6)
- **History:** Phase 5's real scan reached the Phase 6 placeholder.
  It records `scan_clean|scan_exhausted → validating → validation_error`
  and a stage notice, then the existing readiness rule sends the package to
  `pending_review`. Stub pipeline runs therefore end `partial_success`,
  never `production_ready`, until real validation arrives in Phase 6.
- **Phase 6 update:** the placeholder is removed. D-35 implements real validation
  and permits `production_ready` and run `success` under Option C.

### D-27 — Portable recorded scanner fixtures (Accepted)
- **Implementation:** recorded Checkov and tfsec JSON uses the fixed
  `/__RECORDED_ROOT__` marker in place of the capture machine's absolute
  package root. The test runner replaces it with each temporary scan root;
  a capture script normalizes new recordings and rejects captures without
  that root. This keeps scanner-path validation independent of checkout
  location while preserving the original relative file references.

- **Phase 5b update:** Phase 5 fixture formats are extended by D-31: active tfsec recordings
  are removed; Trivy relative Targets and recognized rootless Trivy/Terraform
  JSON are normalized without requiring a capture-machine path in every report.

### D-28 — Terraform parser failures as blocking findings (Accepted)
- **Implementation:** a tfsec HCL parse diagnostic with a package file,
  line, and parser message becomes a CRITICAL `TERRAFORM_SYNTAX` finding.
  Its scan is marked `syntax_limited`: tfsec produced no other findings, so
  a fix pass must repair syntax before a full rescan. The path is constrained
  to the package file map and the temporary root is never reported. Other
  malformed output, missing binaries, and timeouts still follow the scan
  retry and `scan_error` path. The evaluation includes the syntax finding
  and counts it once under tfsec, leaving FR-G-05's Checkov measure intact.

- **Phase 5b update:** The tfsec implementation is superseded by D-31. Terraform supplies
  critical syntax findings from a broadened, empirically verified allowlist.
  Checkov and Trivy still scan available resources; syntax-limited means
  Terraform coverage may be incomplete, not that all other findings disappear.
  Syntax is counted only under Terraform in the three-tool combined diagnostic.

### D-29 — Safe fix rejection reasons and descriptive metadata (Accepted)
- **Implementation:** invalid fix responses record a bounded schema field
  path and failure rule, a path mismatch, or a JSON-invalid category. The
  reason is assembled from fixed field names and error types; it never
  includes submitted values or provider response text. Package code, paths,
  and new files remain strict. The descriptive `fixes` list cannot reject
  otherwise valid code: summaries are capped at 200 characters and malformed
  entries are discarded. Reports and evaluation output retain the safe
  rejection reasons and counts.

### D-30 — Per-agent fixing model selection (Accepted)
- **Implementation:** optional `SECURITY_FIX_PROVIDER`,
  `SECURITY_FIX_MODEL`, and `SECURITY_FIX_REASONING_EFFORT` select the adapter
  for SecurityAgent fix calls only. Each unset value follows the run choice
  (or global reasoning setting). The shared LLM credential and
  OpenAI-compatible base URL still apply. The selected fixer is stored in
  each report session and in the latest security report. Remediation
  evaluation prices tokens using that fixer, independently of the generator
  model associated with the saved package.

### D-31 — tfsec replaced by Trivy v0.69.3 (Accepted)

tfsec is in maintenance mode; Trivy config is its official successor with
the shared rule library and broader Kubernetes/Helm coverage. Phase 5b uses
installed Trivy 0.69.3 with its embedded checks bundle, filtered
Terraform 1.16.4 syntax diagnostics, and Checkov 3.3.21. It supersedes active
tfsec scanning in D-22/D-25/D-28. Historical report findings retain `tool=tfsec`.
Trivy IDs are taken from actual output (AVDID if present, otherwise ID);
`AWS-0133` is confirmed in the vulnerable recording. No enhanced-monitoring
Trivy check was emitted; only the existing Checkov exemption remains.

Fresh per-scan cache, `--skip-check-update`, `--skip-version-check`, and
`--disable-telemetry` pin the embedded rules. All scanner/version environments
exclude application secrets and set fixed loopback refusal proxies (including
lowercase variables, with empty NO_PROXY); Git prompting is disabled. This
prevents practical download attempts from completing, without claiming kernel
network isolation. Local findings are retained when external module downloads
fail; `EXTERNAL_MODULE_NOT_SCANNED` explicitly marks literal remote sources.

Trivy silently skips tested malformed HCL; `fmt` misses extraneous labels.
`validate -json` without init supplies only demonstrated configuration-loading
and HCL parse summaries. Provider/module/reference/type errors are ignored;
Unsupported block type is limited by source context to avoid resource schemas.
The three tools run concurrently. Terraform syntax counts are separate and
included once in combined counts; FR-G-05 still measures Checkov alone.

The author confirms installation checksum output:
`trivy_0.69.3_Linux-64bit.tar.gz: OK` from `sha256sum -c`. This is author-confirmed
provenance, not an independently repeated installation verification. The task
identifies malicious 0.69.4 and CVE-2026-33634; runtime uses only installed
0.69.3. Trivy's built-in Helm renderer closes the Checkov-only Helm gap without
installing Helm. Network-isolated tests with `unshare -Urn` succeeded in this session (unlike
the earlier Phase 5 environment). Debug logs confirm 563 embedded checks and
no downloadable checks loaded. The fresh-cache fallback is logged as ERROR;
tests allow only that expected fallback and reject other errors. Two fresh
namespace scans produce identical normalized findings. Remote-module refusal
also preserves local findings. The [12-package evaluation](evals/phase5b-security-20261001T191131076470Z/summary.md)
retains both known syntax findings and records the one inaccessible registry
module explicitly. Runtime syntax diagnostics cover the root Terraform module
without init, not recursive semantic validation of uninstalled child modules.
Unknown diagnostic summaries/contexts are ignored until demonstrated with the
pinned Terraform version; normalized findings, not raw timestamps/IDs, are
the deterministic comparison.

### D-32 — Scanner timeout terminates the whole process group (Accepted)

The Phase 5 evaluation hung for 28 minutes after a timeout killed the Checkov
parent but left a forked worker holding stdout. Each scanner now starts a
new session. Timeout/cancellation sends SIGKILL to its process group; subsequent
communication is bounded to five seconds and transports close on expiry.
Deterministic subprocess regressions verify no surviving group and temp cleanup;
all three fail against the old parent-only kill logic.

Checkov 3.3.21 accepts `CHECKOV_PARALLELIZATION_TYPE` values `fork`, `spawn`,
`thread`, `none`; runtime sets `none`. Its interleaved-drain code is upstream,
not a local customization: installed
`/home/bishara/.local/share/pipx/venvs/checkov/lib/python3.12/site-packages/checkov/common/parallelizer/parallel_runner.py`,
lines 21–28 (switch), 132–135 (branch), 154–190 (drain). Downloading the exact
PyPI wheel with `pip download --no-deps` and comparing that file produced the
same SHA-256: `89019b62299807b8c5f21fda72e221a09d1c81a9ef53b1fd92006de99a99ee9b`.
This corrects the earlier characterization as a customization.

Single default/none timings (seconds), identical finding counts: vulnerable
3.795/3.505, fixed 3.324/3.269, syntax 3.175/3.202, committed gpt-oss
kubernetes-monitoring cost 3.285/3.406. No consistent speedup is claimed.
Evaluation now logs every attempt and preserves recovered timeouts.


---

### D-33 — Hybrid generation and remediation models (Accepted)

The author selects `anthropic/claude-sonnet-5` with reasoning off for generation,
and `openai/gpt-oss-120b:nitro` with reasoning low through `SECURITY_FIX_MODEL`
for fixes. The committed Phase 5b evaluation `20261001T200251953890Z` reduced
537 blocking findings to 34 (93.7%), with 4/12 packages clean, about 25 seconds
and one cent per package. Sonnet's two-package evaluation `20261001T215033464167Z`
reduced 44 to 3, but was about 3–4 times slower and 25 times more expensive.
After lenient metadata handling it had zero rejected fixes; the previous 10/20
baseline is author-reported historical evidence. MEDIUM remains blocking.

Phase 7b scopes `SECURITY_FIX_PROVIDER`, `SECURITY_FIX_MODEL` and
`SECURITY_FIX_REASONING_EFFORT` to runs whose resolved provider equals the
configured `LLM_PROVIDER`. Stub runs always use a stub fixer with model `stub`,
even when the deployment itself uses the stub provider. This preserves the
hybrid setup while preventing provider overrides from selecting paid fixers.
For FR-I-04, a different provider no longer inherits the deployment's model:
an omitted model resolves to `stub` for a stub override; a real-provider
override must explicitly supply a model or submission returns 400
`invalid_request`. Unchanged real providers continue to inherit `LLM_MODEL`.
Phase 8 section 0 makes model `stub` unconditional whenever the resolved
provider is stub, including a configured stub default with a real `LLM_MODEL`
and an explicit request model. The same domain resolution reaches adapters,
agents, persisted runs, evaluation summaries and archives. Historical rows
are not rewritten.

### D-34 — Optional prompt-cache measurement (Accepted)

`LLM_PROMPT_CACHE=off|system` defaults to off: output tokens dominate measured
costs. System mode marks one compatible Anthropic system text part with
`cache_control: {"type": "ephemeral"}` according to
[OpenRouter documentation](https://openrouter.ai/docs/guides/best-practices/prompt-caching).
Native Anthropic requests are unchanged. Cache-read tokens are optional metrics
in responses, attempt logs, reports and evaluations; missing remains unknown,
explicit zero remains zero. This mechanism supports a later richer-prompt
experiment; no paid measurement or cache-aware pricing is claimed.

### D-35 — Deterministic validator and offline tools (Accepted; implemented in Phase 6)

The versioned report centralizes outcome calculation: any ordinary failed check
makes a package invalid; otherwise a required Terraform check that cannot run
makes it an error; otherwise it is valid. A whole-stage deadline or internal
abort produces error even when partial checks contain failures. Required
Terraform outcomes and every failure are retained. Up to 200 other checks are
sampled in deterministic order, with full pre-sampling counts and omitted
counts. Every file-linked failure remains in `failed_checks_for_remediation`;
fileless failures remain in the main report. The report records whether
Terraform was required and any stage abort, so persisted outcomes can be
validated against the same rule.

The offline mirror contains AWS 5.100.0 and 6.68.0, random 3.9.1,
Kubernetes 2.38.0, Helm 2.17.0, TLS 4.4.1 and null 3.3.2 for linux_amd64.
The sole authorized provisioning invocation succeeded; its file size is
391,710,515 bytes (373.56 MiB). Terraform authenticated all seven packages as
signed by HashiCorp. Archive hashes and offline-derived lock records are in
`tools/terraform-providers/`. Runtime init uses `-backend=false -input=false
-plugin-dir=<mirror>`, permitting module installation only for recursively
verified local sources. Missing mirror, unavailable provider version, remote
module, missing executable and tool errors remain distinct skips. Full
provider-schema diagnostics are separate from the Phase 5b syntax filter;
malformed init still triggers validate to collect real syntax diagnostics.
Diagnostic summaries are allowlisted; source snippets and details are excluded
from reports. Phase 6b recognizes the safe title `Cycle`, stripping Terraform
cycle graph listings. Unknown titles retain reported file/range positions.
Unlocated Terraform diagnostics attach to main.tf (otherwise the first root
.tf file, then other Terraform files), with fallback line 1 as a remediation
anchor rather than a claimed source range. The original Sonnet three-tier
security package genuinely has a cycle among the alb/app/rds security groups;
offline init succeeded and real validate reported it without a range. Validator
availability/version and mirror presence are exposed in healthy and degraded
health responses.

Built-ins use the expressly approved PyYAML 6.0.3 and Python-HCL2 8.1.4,
with explicit Lark 1.3.1 and locked regex 2026.9.29 from the installed environment;
no installation was performed. YAML positions are retained in a shared index;
HCL reference locations are retained from the original parse tree before
serialization, without parsing twice; other HCL analysers retain deterministic
source-line fallback. Undeclared references emit one finding per file and
identifier, naming the reference and its first actual occurrence. Helm templates,
Ansible role task/support files and Prometheus rule files are distinguished
from standalone manifests, playbooks and scrape configs. Kubernetes identities
include namespace, kind and name.

Approved Nginx rule: extract the hostname from `proxy_pass`, removing URI,
port and quoting syntax. Accept normalized matches to defined upstreams, plan
services, Kubernetes Services or literal Helm releases in the same package,
IP addresses, hostnames containing a dot, or `# external-host:` comments.
Normalization lowercases and equates hyphens, underscores and dots. Variables
such as `$host` produce warnings. An unresolved bare name fails and its message
names the file and line. Quoted text and comments cannot invent directives;
`.Release.Name` does not invent a literal Helm release. Analysis tiers and
Terraform references use module-directory scopes, including `.tf.json`; local
outputs are inspected when their source is available. Variable and local
references in ordinary strings/comments are ignored. Filesystem references
cannot escape the package. Kubernetes references use exact names and namespaces;
selectorless Services have no selector to check, and missing Secrets warn.
Phase 6b extends reference targets to Helm template resources with explicit
literal kind, name and namespace, without rendering templates or running
Kubernetes structural checks on them. Unresolved references warn when Helm
contains that target kind with a templated name or namespace, or an omitted
release namespace (Phase 7 follow-up); a genuinely
missing kind still fails. An Ingress Service can resolve even when its port
is templated: that port check warns, while literal port mismatches fail.
Raw Kubernetes declarations take precedence over Helm templates with the same
identity, including literal port validation.
The actual original Sonnet variants differ: cost has a literal apps Service;
performance has a monitoring Service but an Ingress with no namespace (default),
which remains a genuine failure; security has templated identities and warns.

Helm remote dependency URLs warn when not vendored, and absent Values paths warn
because defaults may be intended. Ansible inventory groups are checked only
when inventory is present; symbolic host patterns warn, and role references
must exist. Prometheus rule paths/globs yield one finding per distinct reference.

Naming findings are warnings: FR-V-02 requires flagging, and fuzzy deployment
semantics must not invalidate packages. Rules lowercase names and equate `-`,
`_` and `.`, then require an exact normalized match or token-boundary embedding
of a plan service/storage name. Cross-artifact names may also match after
removing documented terminal suffixes (`service[s]`, `server[s]`, `svc`,
`deployment`, `upstream`, `job`). Unknown service-like names warn; Terraform vs
Ansible mismatch messages identify both files. Resource names and Name,
Application or Service tags are collected; infrastructure resource types and
reserved host/exporter groups are excluded from unknown-name warnings.

Applicability is centralized and conservative. Terraform can represent all
plan services/storage. Kubernetes Deployment/StatefulSet workloads, Nginx
upstreams and Prometheus jobs/targets represent application compute services;
cloud control planes and cluster services are excluded. Ansible expectations
apply to EC2 hosts. Helm charts may aggregate services, so no per-service chart
expectation is invented. Literal Helm release names are collected from
`helm_release.name`; symbolic references and `.Release.Name` do not invent
releases. Missing expected entities warn. These limits remain static because
the plan has no deployment-role metadata (OQ-10).

Optional linters run through the shared process runner in temporary copies,
with a 60-second per-tool timeout. Helm v4.3.0+gbec5b06 disables schema
validation/downloads; hadolint is 2.15.1; promtool is 3.15.0; ansible-lint is
26.9.0 (ansible-core 2.21.5, ansible-compat 26.9.0), with `--offline` and schema
refresh disabled. Terraform is 1.16.4. Actual captures are committed with
commands and fixture sources. Installed ansible-lint JSON is Code Climate:
blocker/critical/major/error fail, minor/info/warning/note warn; both actual
line-location forms are supported. Hadolint errors fail while warning/info/style
warn; Helm ERROR fails and WARNING/INFO warn; promtool configuration/rule errors
fail. Messages omit raw output and source text, retaining safe locations.
Missing executables skip as `not_installed`; crashes, timeouts, malformed output
and unsafe file inputs skip as `tool_error`. Optional skips do not cause error.
Ansible file lookups/dynamic external inputs and file-reading references that
escape temporary package copies are refused before launching optional tools.

The database-independent engine shares parsed documents, runs at most three
external commands per package and enforces a 120-second stage deadline. Tool
cancellation kills process groups before temporary-copy cleanup. A whole-stage
abort retains completed findings and produces error. Terraform file functions
also refuse paths outside the copy and uninspectable dynamic file inputs;
validation never reads the repository's dotenv file. ValidatorAgent implements
the existing protocol, row-locks and saves the complete validated JSONB report
in one transaction before the outcome transition, and emits lifecycle events
and one safe summary notice through EventLog. The app and security evaluator
use the real agent; the evaluator reloads persisted remediated files. Existing
Option C and review retry services are unchanged. Validation-only retry tests
prove feedback/failure delivery, rescan/revalidation and preserved baselines.
Phase 6b fixes the evaluator regression test to map both application and
migration URLs to the test database explicitly. A shared integration fixture
rejects non-test database connections before the DBAPI connects, including
connections attempted through settings-derived engines. Boundary assertions
check both roles without exposing credentials; verification uses distinct
development and test URLs so accidental dev connections cannot be hidden.

Acceptance evidence uses real mirror-backed Terraform inside network namespaces
for valid and invalid fixtures, real Terraform in complete stub success/mixed
runs, PostgreSQL lock observation, and forked-child deadline cleanup. Cache
metrics are read from raw SDK response JSON before SDK integer coercion;
boolean/string metrics remain unknown. Fixture normalization supports recorded
Terraform, Helm, hadolint, ansible-lint and promtool formats. The `scanners`
marker covers validators and their explicit tool/mirror/namespace prerequisites.

The original offline evaluation of the twelve Phase 3 packages measured
2 valid, 10 invalid and 0 error. The Phase 6b rerun measured 4 valid, 8 invalid
and 0 error; the previous report is retained alongside a new timestamped report
and per-package comparison. Sonnet monitoring cost/security became valid;
performance retains the genuine namespace mismatch described above. Sonnet
three-tier security remains invalid with the safe title Cycle, anchored to
terraform/alb.tf:1 because this package has no main.tf and Terraform supplied
no range. Both known gpt-oss syntax failures remained confirmed from real
Terraform diagnostics. All twelve source hashes and tool versions matched
between runs. No additional ambiguity or spec deviation was introduced.
The Aurora cluster without instances remains an undetected semantic deployment
gap: validation is static and does not prove that infrastructure will deploy.

The thesis artifact table is revised deliberately: Kubernetes, Jenkins, Nginx
and Grafana use the deterministic built-ins above. `kubectl --dry-run` requires
a cluster or kubeconfig; Jenkins pipeline-model-converter requires a running
Jenkins server; `nginx -t` requires the nginx binary and resolves upstream DNS;
`grafana-cli` requires a Grafana installation. Those external integrations are
out of scope for this offline phase. Helm, hadolint, ansible-lint and promtool
remain optional local linters. Built-ins need only the approved installed
Python libraries, with no service, credentials or extra executable.

### D-36 — Optional API key and fetch-based SSE (Accepted; Phase 7 auth and Phase 8 client implemented)

One pipeline-router dependency checks the static API_KEY SecretStr against the
X-API-Key header with hmac.compare_digest over UTF-8 bytes. Empty/unset means
open access with one startup warning; health remains public. Missing and wrong
headers receive identical generic 401 responses. Query-string authentication is
not supported. Phase 8 implements useRunStream over fetch/ReadableStream so it
sends this header; native EventSource cannot send custom headers. Keys are held in
sessionStorage and cleared on 401, with route-local re-entry.

Operator logs retain existing traceback rendering and absolute paths, while
configured LLM_API_KEY and API_KEY values are redacted, including traceback
text. Unexpected HTTP responses use {error, message}; correlation IDs stay in
logs. New output/persistence protection covers feedback, generated files,
security/validation reports, events, results and ZIP contents. Backend execution
paths are removed on those surfaces; legitimate deployment paths inside IaC
remain meaningful. No scanner policy or validation checks change.

### D-37 — Explicit review targets and results interpretation (Accepted; Phase 7)

Review retry targets combine remaining blocking findings, file-linked failed
validation checks and up to five explicit existing package paths. Deduplication
preserves that category order, with paths sorted within each category. Ordinary
automated fix calls keep their previous sorted order. Targetless feedback is
refused with `feedback_needs_target`; a targetless retry without feedback uses
`nothing_to_retry`. OQ-09 is resolved by this decision.

The results endpoint reads the architect plan from the latest `plan_created`
payload in the same SELECT as the run and packages; no plan column is added.
`packages` contains variants that produced files from `generated` onward.
Failed generation rows appear only in `missing_variants`. A missing retained
row does not establish a generation failure. Nullable baselines/reports retain
their persisted contents subject to secret protection. Review availability
requires `pending_review` and a terminal run; earlier review actions return
`run_in_progress`, preserving automated classification and timestamps.

Download archives use the terminal package transition event time, displayed as
**Labelled at**, replacing request-time download time. Decision provenance comes
from that same event and earlier engineer-requested retry events for the same
variant. Phase 8c distinguishes automatic, automatic after an engineer-requested
retry, and engineer decision; approve/reject take precedence. Screen 4 derives
the same text from SSE history without adding API or database fields.
Approve/reject resume the closed event stream after acceptance to retrieve
their recorded decision transition; only retry acceptance sets the retry latch.
Missing label events under D-19 yield fixed unavailable text.
Fixed metadata and `ZIP_DEFLATED` level 6 make repeated unchanged downloads
byte-identical. Readiness-name collisions use the reserved fallback, then the
first free deterministic numbered path, without overwriting package files.

### D-38 — Failed or interrupted review retries return to review (Accepted)

Migration `0003` adds nullable `generated_packages.review_retry_started_at`
TIMESTAMPTZ, with no backfill/default and unchanged table-level app grants.
Acceptance locks the package row and atomically saves `pending_review →
remediating`, feedback, zero consumed iterations and an application UTC
timestamp. Settlement clears the timestamp in the status transaction. Startup
selects non-NULL timestamps independently of run status and uses the reason
**review retry interrupted by server restart**. Events alone cannot identify
retries because state/event commits are separate. The marker never enters
`security_report`.

Review-only abort paths normalize `remediating` through `scanning` and add
guarded `scanning`/`validating → pending_review` arrows. Intermediate
scan/validation outcomes also recover through existing transitions; unmarked
automated transitions and interrupted-run recovery remain unchanged. Failures
preserve persisted files, baselines and report evidence; review scanner failure
never persists `scan_error`. Shutdown attempts bounded settlement; unsuccessful
cleanup leaves the timestamp for startup. Missing usable plan/context aborts
safely to review instead of fabricating a plan.

Retries share runner capacity and task ownership, using unique IDs for
concurrent variants of one run. SSE stays open through marked intermediate
states and waits for the final package frame, covering the state/event commit
gap. Operator logs retain tracebacks with both keys redacted; public errors
remain generic. D-19's separate transactions remain a known limit: a hard crash
can leave a labelled package without its label event, handled by the archive's
unavailable provenance/time text.

### D-39 — Security counts replace the mockup score (Accepted; implemented)

Comparison renders first automated blocking findings → current remaining blocking
findings, accepted fixes in retained sessions and final outcome. Initial counts
come from sessions[automated].iterations[0].scan.blocking, including MEDIUM under
the actual blocking policy. HIGH/CRITICAL summary fields are not blocking totals.
Omitted initial session history or missing evidence is labelled unavailable;
retained fix counts do not imply omitted history was empty. Accepted validation-only
review fixes remain part of that retained fix count. No composite score,
cost estimates, invented deployment traits or model timings are shown.

Diff annotations use only rule_ids of fixes linked to that exact file. Severity
badges for fixes require matching recorded finding evidence; validation-only fixes
may have empty rule_ids and are explicitly labelled as such. Validation check IDs
appear in the separate report tab, without becoming security annotations.

### D-40 — Frontend stack, delivery and stream settlement (Accepted; implemented)

Phase 8 uses React 19.3, Vite 8, TypeScript 6.0 in strict mode and plain CSS
with the fixed thesis tokens and system fonts. It supersedes AGENTS.md's
React 18/Tailwind stack line. Node ≥22.22.2 is the package engine requirement;
development uses Node 24 LTS (24.21.0). The specification's Node 18 minimum
needs updating. Exact direct pins and the resolved graph are committed in
frontend/package.json and frontend/package-lock.json. Releases were checked
against the 14-day cutoff at 2026-10-12 17:35:16 UTC before approval.
The [dependency record](evals/phase8-ui-20261012T204423Z/dependency-pins.md) retains
all 22 exact versions and their approved UTC publish dates. TypeScript 6.0.3 is an approved
compatibility exception because typescript-eslint does not support TypeScript 7.

The author approved two dev-package allowlist additions: @types/node 24.19.0
for typed tooling/E2E code, and @testing-library/dom 10.4.2 for Testing Library's
required peer. jsdiff 9.0.0 supplies declarations, so @types/diff is omitted.
The one initial npm install used --save-exact --ignore-scripts; subsequent
setup uses npm ci --ignore-scripts. No installation script or browser download
was enabled to make the toolchain work.

The development server proxies /api to localhost:8000 by default. Phase 8c adds
Make's PORT override for operator startup and INFRAARCH_BACKEND_URL for the
Vite proxy; E2E explicitly retains backend 8000/Vite 5173 regardless of those
operator overrides. Vite's envDir is false
so development, build and Vitest do not load dotenv files. The HTML language,
title and theme-colour metadata match the design system. color-scheme: dark
is in external CSS instead of the phase prompt's inline style attribute,
because the approved self-only style CSP will reject inline styles.

The implemented delivery uses a fetch/ReadableStream SSE client,
an API key stored only in sessionStorage and sent via X-API-Key, and optional
FastAPI SPA serving from frontend/dist, with API responses unaffected.
The API client, session state, parser, reducer and shared stream store are
implemented in section 2; section 4 implements optional SPA serving after
existing API routes. Static
assets and SPA responses have self-only CSP, nosniff and no-referrer headers;
API/docs responses remain unchanged. Missing dist requires no build in tests.
An internal dist-path override keeps synthetic error-route tests independent of
a developer build. Missing assets and traversal never fall back to index.html.

The sole approved results-schema addition is a required retry_in_progress
boolean on each package, derived from review_retry_started_at IS NOT NULL,
without exposing that timestamp or changing the database schema. Section 2
implements it alongside required TypeScript types and recorded real-tool
pending/repaired stub fixtures. At EOF, the client fetches
results once and considers the stream settled only when the run is terminal,
no package is scanning/remediating/validating and no retry_in_progress is true.
This covers D-38's marked intermediate states. An active EOF resumes with
Last-Event-ID and backoff; five EOF reconnect attempts without a new event are
allowed before pausing with a manual Reconnect notice. Normal settled EOF
does not reconnect; retry 202 explicitly reopens the stream. Verification uses a
Python sitecustomize bootstrap to disable dotenv before settings instantiate
in explicitly opted-in pytest/E2E processes and their migration/scanner children;
Vite uses envDir=false. Phase 8b corrects the original Make target-specific
PYTHONPATH export, which also disabled dotenv for ordinary migrate-test and
inherited test prerequisites. The bootstrap is now a no-op unless
INFRAARCH_TEST_BOOTSTRAP=1. A parent verification launcher resolves normal
operator settings, forwards only configured test database URLs, forces stub
defaults and clears LLM/API keys before executing pytest or E2E. The child
retains the Phase 8 dotenv-disabled guarantee; the parent and standalone
migrations/server/evaluations/Python retain normal settings loading. No runtime
settings-source change, hardcoded database URL, venv mutation, new dependency,
spec deviation or open question is introduced by this correction.
E2E starts fresh stub/review servers, because health cannot verify defaults of an
existing server without changing the API. Every submitted E2E run explicitly
requests stub. Browser/system prerequisites are installed only by the author.

Phase 8 browser reload exposed an existing backend SSE cleanup bug: Starlette's
level-triggered AnyIO disconnect cancellation can interrupt a PostgreSQL read
and its async session cleanup, returning a connection before asyncpg terminates
it. An unrelated pipeline borrowing that pooled connection then fails. The
author approved a narrow additional backend scope exception: shield only the
SSE replay reads and terminal/package close-check reads, including their session
cleanup, in api/pipeline.py. Yields, live-event waits and keep-alive waits remain
cancellable. No endpoint, schema, migration or dependency changes. The
synchronized PostgreSQL regression failed first at all three read points on the
unchanged code (3 failed, 2 cancellation-bound tests passed), then all 10 SSE
tests passed with the fix. Each canceled-read case also runs a complete stub
pipeline on the same engine/pool and requires three production-ready packages;
idle/live cancellation must finish within a 0.5-second deadlock watchdog.

The shared frontend store transfers ownership across synchronous navigation and
React StrictMode through a single resource-lease microtask; accepted events still
commit immediately. An accepted retry keeps a client operation latch until a
settled EOF snapshot, preventing stale results from restoring review controls.
This latch is client state, not another results field. Reusing the live log's
Intl.DateTimeFormat avoids repeated formatter allocation during those commits.
Elapsed stage activity is computed from the union of actual event timestamp
intervals across variants/retries, excluding review gaps and counting concurrent
activity once. Duration timers update text only, without API polling or batching.
Phase 8c stage summaries count the latest recorded scan/validation outcome per
variant, retaining mixed failures even when the last variant succeeds; a new
stage attempt clears that variant's prior outcome. No score or outcome is inferred.
Screen 4 has one readiness badge in the action row beside Download ZIP; its
header identifies the package. Pending review retains its heading and controls.
All four screens and real-backend acceptance checks are implemented; screenshot
comparisons and PR-02 development evidence are retained under docs/evals/.

### D-41 — Deterministic validation-review demo (Accepted; implemented)

PIPELINE_DEMO_SCENARIO=clean|review defaults to clean and only affects opt-in
pipeline stubs whose run provider resolves to stub. A real-provider default
with review logs a startup warning; a real run's stub fixer remains ordinary.
Existing spike/evaluation stubs retain their scripted behavior.

Only the security variant appends an output referencing local.review_demo,
without declaring it. Valid HCL avoids security syntax remediation; the
built-in terraform.local_ref check fails at terraform/main.tf:4. The existing
validation/readiness rules produce invalid then pending_review. A dedicated
fixer stub consumes the trusted requested path and nonce-delimited failed
validation targets, returns the real FixOutput shape and adds the missing
local. Feedback cannot redirect the demo fix to another file. Retry uses the
existing audit, rescan and revalidation paths, preserving original_files and
the run's frozen partial_success. Clean variants remain unchanged. This is a
test/demo aid, not deployable infrastructure; installed offline scanning and
Terraform prerequisites remain necessary for complete readiness settlement.

### D-42 — Built-in offline secret scanner (Accepted)

NFR-01 is checked by a Python standard-library scanner rather than gitleaks:
Phase 9 forbids new installations/dependencies and must work offline. It scans
working-tree text plus historical file blobs from all refs and reflogs. Excluded
paths are filtered before reading/retrieving content; dotenv secrets are never
opened, and symlinks are never followed. Only exact documented placeholders and
synthetic canaries are allowlisted; findings contain location/pattern metadata.

Limits: prefix/entropy heuristics are not proof of absence. Encoded/obfuscated
credentials, binary/archive contents, excluded dotenv/dependency/cache/build
paths, commit messages and unreachable objects outside refs/reflogs are not
covered. An unknown key format may escape detection. False positives must be
reviewed without printing matched values; do not broadly exempt test fixtures.

### D-43 — Phase 9 safe provider failures and evaluation method (Accepted)

Provider failures use eight fixed categories and public sentences. The author
approved request_rejected for otherwise unmapped 4xx responses; these fail fast,
as do authentication, spending-limit and missing-model failures. SDK wire bodies
may be inspected only to classify; no body/message/URL/identifier/amount survives.
Operator attempt logs retain category, actual HTTP status and original exception
class name, with no original exception object. HTTP-200 error envelopes are
classified before parsing. Existing agent deadlines and remediation policy remain.
Legacy internal stub/format reasons normalize at the reporting boundary.

Benchmark completion is measured from immediately before HTTP submission through
consumption of a final results response confirming a terminal run, settled package
states and no retry marker. This is API settlement, not browser appearance;
PR-02 supplies separate UI latency evidence. Pending review is settled.
PR-03's spec verdict uses an isolated identical-prompt baseline; same-prompt
PR-01 medians are labelled secondary references. Overlapping key usage cannot
attribute individual costs: retain a measured cohort total and total/3 average.
The cohort needs max(reserve, 2H, 4.5H) remaining credit. Unknown costs/credit stay
unknown and require explicit run bounds; no estimated benchmark measurements.


Verification evidence from the one Phase 9 stub rehearsal is retained: 14 runs
all succeeded and 10 downloads completed; PR-01 median 5.47s and PR-04 maximum
1.36s passed their thresholds. PR-03 ratios 2.76–2.78x failed the isolated-baseline
criterion with local scanners/validation. This is overhead rehearsal evidence,
not real-provider performance evidence; no runtime optimization was made.

The first settled real run produces a measured-cost/remaining-credit notice and
an informational simulation of the remaining finite schedule at that first cost.
The cohort is indivisible, with its 4.5H guard; zero/unknown costs are explicit.
The actual guard always rechecks fresh credit and measured maximum cost.

PR-04 uses a seeded synthetic archive calibrated just below 10 MB compressed,
so its stored source is larger than the normal generator size cap. Repository
path validation and existing state rules remain in force. This rejected synthetic
run has explicit synthetic notices and no claimed scanner/validator execution.

**Phase 9c output budget:** full-package output now defaults to 8,000 tokens,
about 60 seconds at the author's observed ~140 tokens/second. Generator prompt
v4 names the configured budget and limits files/comments/README prose without
weakening security, validity or variant directives. The former 32,000-token
limit allowed 10k–19k-token failed responses taking 70–138 seconds. The first
real attempt retained four usable runs out of eight, median 189.81 seconds,
three settled failures and one incomplete run, at measured cost $4.940978.

The existing max_completion_tokens request parameter is documented with the same
limit semantics as max_tokens in [OpenRouter's parameter reference](https://openrouter.ai/docs/api_reference/parameters).
Strict routing follows [OpenRouter's structured-output guidance](https://openrouter.ai/docs/guides/features/structured-outputs).
Provider enforcement varies, so local schema validation remains required.

**Phase 9c format enforcement:** LLM_STRUCTURED_OUTPUT applies only to generator
adapters. json_schema derives a closed wire representation from GeneratorOutput:
files become a nonempty list of path/content objects; notes is required. Internal
IaCPackage.files remains a dictionary, with duplicate paths rejected. OpenRouter
strict requests require supporting providers; no automatic fallback changes
requests. Refusals retain fixed categories and recommend json_object. Native
Anthropic/stub retain dictionary responses and share local validation/salvage.

The parser first accepts a schema-valid whole object, ignoring backticks in
string values. Only then does it inspect external fences/prose. Exactly one
balanced, schema-valid object may be salvaged and counted; multiple objects or
external fenced blocks remain rejected. The previous global four-backtick test
could reject valid README/template/script contents. A mocked valid response
reproduced this bug; raw invalid historical outputs were not retained, so no
specific historical attempt can be reclassified. OQ-08's mechanism is extended;
actual real-run reliability improvements remain unmeasured.

**Phase 9c retry/timing investigation:** the author confirms no shell overrides,
GENERATOR_ATTEMPT_TIMEOUT_SECONDS=150, GENERATOR_DEADLINE_SECONDS=270 and duplicate
LLM_DEADLINE_SECONDS assignments of 150 then 270. The installed settings loader
uses the last assignment, proven with a synthetic stream without reading .env.
A shared-clock mocked reproduction ends at 270 seconds with 150 then 120-second
attempt limits within one package attempt. Thus the 15 event durations above
150 seconds (maximum 270.03) are explained by the configured budget, not a
per-package reset. A slow 150-second call leaves ~120 seconds minus backoff for
another historically 70–150-second answer. PR-05 still requires 150 seconds.

Format retries now name the safe reason and repeat only the original prompt,
never invalid output. Safe attempt records include failures and salvage. Async
calls are cancelled at the shared generator deadline; no new attempt starts
after expiry. A fully valid package whose synchronous final validation overruns
is retained, with deadline_exceeded and overrun_seconds on the final attempt and
generator metrics. An injected-clock reproduction accepted a valid package at
151 seconds under a 150-second budget; retaining that paid-for work is the
author-approved exception to FR-G-06/PR-05, not a timing pass. Invalid late
packages cannot retry. The end-to-end budget flag compares configured time;
benchmark PR-05 always compares measured duration against 150 seconds.

Nominal defaults permit up to 2 package completions × 3 adapter attempts × 120
seconds = 720 seconds before backoff, but the one shared 150-second budget clips
calls/backoff. Exhausted format retries stop generation, rather than starting a
new package completion. A recommended 90-second attempt has a nominal 540-second
ceiling, also clipped to 150; a first 90-second timeout leaves under 60 seconds.

**Phase 9c benchmark evidence:** GET /api/benchmark/settings always requires a
configured matching X-API-Key, even when ordinary local pipeline authentication
is disabled. It exposes only the generator numeric/mode allowlist; health is
unchanged. Benchmarks capture server-effective settings before submission and
stop on unavailable/malformed evidence. Existing terminal generator events now
include safe attempt records, failure categories and overruns through EventLog.
Reports include all variants (including failed ones), per-attempt output tokens,
format-reason counts, and internal elapsed alongside event intervals. Historical
missing fields remain unknown; original first-run evidence is preserved.

The author recommendation is output=8,000, attempt=90, generator/completion=150,
with adapter/package attempts 3/2. Defaults keep attempt=120. Generator arguments
override general attempt=60/output=16,000 fallbacks; an unset generator output
picks the new 8,000 default. Settings resolve constructor > environment > dotenv
> defaults; one assignment per dotenv key avoids last-assignment ambiguity.
bench-smoke is three representative guarded real runs, not PR-01 acceptance.

### D-44 — Quality repairs before readiness (Accepted; implemented in Phase 9d)

Deterministic declaration repairs operate per Terraform module: missing inputs
have descriptions and no defaults, secret-like names are sensitive, and only
source-identical variable duplicates are removed. The only created data-source
kinds are aws_availability_zones (state=available), aws_caller_identity,
aws_region and aws_partition. Existing declarations and conflicting duplicates
are preserved. Repairs are logged and idempotent; unsafe modules are skipped.
The Architect supplies file types rather than exact file names; the generator
checklist derives required paths from the shared layout, without a schema change.
Readiness, severity/blocking policy and every validator check remain unchanged.
Automatic validation feedback uses the existing Retry fix pass and shared patch
and verification helpers. Preflight allows VALIDATION_REPAIR_MAX_ROUNDS=2;
security-modified invalid files receive at most one additional round. One
validation-deadline budget spans the repair phases, without per-round resets.
A candidate is kept only if failed checks decrease and no new blocking finding
fingerprints appear; otherwise the whole round rolls back and stops. Retry keeps
its existing per-proposal acceptance, feedback, ordering and recovery behavior.
Final validation and a scan-only security confirmation describe the same files;
original generation and typed repair history survive report replacement. Optional
preflight transitions are added to the domain state table; readiness is unchanged.
The explicit review-demo scenario bypasses automatic repair to preserve its
manual-review demonstration; this does not match or exempt benchmark prompts.

Security fix passes now default to four rather than the thesis default of three.
Each automated scan/fix iteration is capped at 60 seconds inside the existing
240-second security budget; fixer calls are clipped to remaining iteration time.
A timed-out fix round keeps its input files. A timed-out scan remains scan_error.
Fix prompt v2 names mirrored provider schemas and standalone S3 public-access
resources for every existing/new log or replica bucket. Ansible and Grafana
artifact guidance is shared with generators; no scanner/validator rule changes.

Generator prompt v5 renders a concrete minimum path checklist from shared layout
patterns for exactly the plan's file types, adding variables.tf and Helm values
and templates. It names offline provider pins and requires parseable documents,
fully qualified/named Ansible plays with accurate change reporting, and plain
Grafana provisioning dashboards with non-empty top-level panels. The generator
wire schema, 8,000-token default and 120-second attempt default are unchanged.
For fair author comparisons retain baseline overrides of 16,000/140.

Quality snapshots explicitly allow only status/review reasons, failed-check
IDs/messages/locations, remaining rule IDs and counts. No generated source,
diffs, feedback, fixer summaries or finding messages are saved in benchmark
quality inputs. Association uses run/variant directory names. The offline quality
subcommand accepts historical full API snapshots but writes only the allowlist
into a distinct new directory. Missing historical metrics stay unknown.
The separate baseline quality folder reproduces 1/36 ready and six missing;
original baseline files and cached input snapshots are not modified.

### D-45 — Syntax gates and schema-grounded repair (Accepted; Phase 9e)

The author approved generation-time validity checks, syntax checks for every
patch and version-correct offline schema grounding for both scanner fixes and
validation repairs. Provider indexes are built offline by make provider-schema
beside the installed mirror, with version/hash manifests; missing/corrupt
indexes degrade grounding with safe notices and never trigger downloads.
Schema exports capture structure, not every provider conditional constraint;
terraform validate remains authoritative. Readiness, blocking criteria,
severities and existing check meanings remain unchanged.

Approved extensions include exactly two new deterministic idiom repairs,
per-iteration Terraform regression rollback under the existing 60-second
ceiling, private initialized package workspaces, explicit timing/provenance,
and independent initial/post-security repair budgets. Scanner-only prompts receive the same 16000-character schema cap as repair;
the generator gets at most 6000 input characters without output-budget changes.
Initialized provider versions take precedence; namespace mismatches are never
grounded with unrelated schemas. Implementation choices and verification are
recorded in the Phase 9e section entries.

Each security iteration compares Terraform failures before/after the two idiom
repairs and restores its Terraform files on regression or unverifiable changes
(unless the candidate fully validates). Non-Terraform changes require security
verification. No-new-blocker protection and the 60-second ceiling remain;
rolled-back attempts consume allowance. Retry uses a fresh workspace shared
through validation. Existing control removal is rejected; same-kind replacements
retain control fields and still require scanner verification.

The approved 17 October follow-up removes repeated findings as a terminal
condition: started fix attempts, including rejected or rolled-back candidates,
consume the configured allowance, but unchanged findings do not stop remaining
attempts. Iteration deadlines discard pending changes and permit continuation
only within the remaining stage budget and allowance; fatal scanner failures
still stop verification. Retained files and their verified scan form the next
baseline. Separate redacted previous-attempt feedback is capped at 4,000
characters and labels candidate diagnostics explicitly. No validity comparison,
security-control protection, readiness condition or budget was relaxed.

The former `fingerprints in seen` / `no progress` exit originated in Phase 5,
commit `91633dc` (1 October 2026). Phase 9e's rollback/baseline reuse (`5584316`)
returned unchanged findings after rejection and exposed that shortcut. Saved
9e JSON proves scanner schema context was sent: 52 proposal measurements,
44 positive, including 11,689 and 15,452 characters for run `12a0fcfb…`.
The zero summary was a reporting-only error: the reader used top-level
iterations instead of nested sessions. A shared canonical session reader now
supports legacy reports without double counting; context coverage distinguishes
positive, zero and absent measurements and safe degraded reasons. Historical
reasons remain unknown. The separate sanitized audit preserves original reports
and read-only cached source JSON. Chapter 4/6 follow-ups include this corrected
diagnosis and measured continuation results; no real-run improvement is inferred.

Initialization is private per module and serialized per package; source sync
preserves tool data, and provider/constraint/inferred-dependency/local-module
changes invalidate it. Failed or cancelled initialization is never reused.
Workspaces are cleaned after subprocess termination; Retry creates a fresh one.
Generation gates record safe init categories rather than raw tool output and
require mirrored-version-compatible required_providers in generator prompts.

Initial repair has 120 seconds and post-security repair a fresh, configurable
60 seconds; security does not consume either budget. Generation repair shares
the generator deadline. PR-01 remains a measured threshold without a new
pipeline-wide timeout. Every patch parses touched HCL/YAML/JSON and renders
changed Helm charts. The gate also formats Terraform, runs installed offline
validation/lint/syntax tools and records unavailable reasons. The new idiom
repairs only remove literal empty default-SG rules and escape recognized AWS
flow-log placeholders (HCL/JSON); existing declaration repairs remain
generation-only.

Descriptive timings include tool queue waiting. Validator persistence is labelled
separately from actual validation. Benchmark outputs strictly project safe
metadata; uncertain, masked and historical failure origins stay unknown.
A separate, labelled scripted-fix/real-offline-Terraform rehearsal measures warm
verification under three concurrent workspaces because clean stub packages have
no scanner-fix iterations. It does not affect quality rates, PR thresholds or
benchmark prompts. Deadline-only rollbacks, pre-candidate stops and multiple
causes are separate; no estimate of real-run improvement is made.

### D-46 — Secure construction and guarded partial remediation (Phase 9f)

FR-S-02/03/04/09 and NFR-01: resource-specific AES256 evidence replaces the
package-wide substring exemption (R2). Parsed, uniquely associated bucket
configuration is required; ambiguous evidence stays blocking. Policy version 3
preserves all severities and the seven other explicit variant exemptions.
The saved final-file rescan found three old exemptions, all three resource-proven;
zero become blocking. Historical truncated advisory totals remain unknown.

Approved extensions: flagged-resource attribute catalogue and supporting-resource
templates, partial acceptance, bounded resource-focused fixing and existing-file
recovery. Their implementation details and thesis appendix follow below as each
section is verified. Readiness and all acceptance guards remain unchanged.


#### D-46 attribute catalogue (section 1)

All entries are checked against AWS 5.100.0 and 6.68.0 before emission and use
only scanner-flagged resources. No insecure-expression guessing, public-network
redesign, suppression or severity change is permitted. Provider validation and
no-new-blocker verification precede retention. Terraform source edits preserve
unrelated attributes/comments; JSON is parsed and rewritten structurally.

| Rules | Resource | Exact change | Preconditions / conflict | Justification |
|---|---|---|---|---|
| CKV_AWS_293 / AWS-0177 | aws_db_instance | deletion_protection=true | Literal/missing value | Prevent accidental deletion |
| CKV_AWS_161 / AWS-0176 | aws_db_instance | iam_database_authentication_enabled=true | Supported literal engine | Add IAM authentication |
| CKV_AWS_16 / AWS-0080 | aws_db_instance | storage_encrypted=true | Preserve KMS key; literal/missing | Encrypt storage |
| CKV_AWS_129 | aws_db_instance | enabled_cloudwatch_logs_exports union engine logs | Known postgres/mysql/mariadb; literal collection | Export audit/engine logs |
| CKV_AWS_353 / AWS-0133 | aws_db_instance | performance_insights_enabled=true | Known supported engine; cost variant remains exempt | Add diagnostics |
| CKV_AWS_118 | aws_db_instance | monitoring_interval=60 | Existing monitoring role; positive interval preserved | Enhanced monitoring |
| CKV_AWS_79 / AWS-0028 / AWS-0130 | aws_instance | metadata_options.http_tokens=required | Preserve other options; unresolved block skips | Require IMDSv2 |
| CKV_AWS_8 / AWS-0131 | aws_instance, aws_launch_configuration | root/ebs_block_device.encrypted=true | Preserve devices and keys; unresolved flag skips | Encrypt volumes |
| CKV_AWS_3 / AWS-0026 | aws_ebs_volume | encrypted=true | Literal/missing flag | Encrypt standalone volume |
| CKV_AWS_130 / AWS-0164 | aws_subnet | map_public_ip_on_launch=false | Proven private routing only | Avoid unintended public addresses |
| CKV_AWS_103 | aws_lb_listener | ssl_policy=ELBSecurityPolicy-TLS13-1-2-2021-06 | Existing HTTPS/TLS; preserve TLS1.2/1.3 policies | Require modern TLS |
| CKV_AWS_38 / AWS-0038 | aws_eks_cluster | enabled_cluster_log_types union all five streams | Literal collection | Capture control-plane logs |

Subnet intent resolves module-local explicit subnet/table associations, inline
and standalone routes and configured main/default tables. An Internet Gateway
route proves public intent; NAT routes do not. A fully resolved table without a
direct Internet Gateway route proves private intent. Missing/ambiguous/dynamic
routing remains unresolved. Public skips use `context: public subnet`; no Phase
9g exception profile is implemented.


#### D-46 supporting-resource templates (section 1b)

| Template | Resources and linkage | Required context / limits |
|---|---|---|
| KMS | One rotating symmetric aws_kms_key, 30-day deletion window, aws_kms_alias; linked S3 encryption, Performance Insights, EBS or CloudWatch encryption | Preserve existing keys and bucket-key options; literal/resolvable association; scoped log-service key permissions |
| Access logs | One SSE-S3 bucket, public-access block, enabled versioning, TLS-only bucket policy and scoped service delivery; source-specific S3/LB prefixes | Same default provider/module; no self-logging; incompatible/custom existing logging skips |
| VPC flow logs | Encrypted CloudWatch log group (365-day retention), scoped role/inline policy and linked aws_flow_log resources | Reuse generated compatible support; log delivery role needs DescribeLogGroups on * because that API has no resource-level permission |
| RDS monitoring | Role trusted by monitoring.rds.amazonaws.com, AmazonRDSEnhancedMonitoringRole attachment and linked instance interval=60 | Reuse compatible generated role; preserve existing custom role choices |

Every template validates emitted fields and required structure against both
pinned AWS schemas. Dependencies stay together during acceptance. New resources
are added at most once per module; subsequent flagged targets reuse supporting
resources. Aliased/dynamic/unresolvable context skips with a reason. Every
candidate passes syntax, preservation, Terraform non-regression and no-new-blocker
guards. Introduced rule/resource findings are recorded even when rejected; no
Phase 9g exception profile is implemented. The access-log destination may itself
trigger logging/KMS findings and therefore remain rejected under current policy.

AWS requires SSE-S3 for direct S3 server access logging and ALB access-log
destinations; the author approved AES256 for the shared destination while KMS
protects application storage and CloudWatch logs. No self-logging loop is added.
Sources: https://docs.aws.amazon.com/AmazonS3/latest/userguide/enable-server-access-logging.html
and https://docs.aws.amazon.com/elasticloadbalancing/latest/application/enable-access-logging.html.
Network LB logging requires a TLS listener and its own delivery.logs.amazonaws.com
permissions (https://docs.aws.amazon.com/elasticloadbalancing/latest/network/enable-access-logs.html).


#### D-46 partial acceptance (section 2)

Combined candidates remain subject to the existing guards. On failure, private
source snapshots are split by file and, where parseable, Terraform top-level
block. Changed declarations and their changed references form dependency groups
within a module. Each group is evaluated in deterministic path/block order
against the latest verified retained files, Terraform checks and scanner result.
SECURITY_PARTIAL_MAX_GROUPS defaults to 6 (range 1–64); the existing 60-second
iteration and 240-second stage ceilings take precedence. Validation and scans
are cached by complete source fingerprints inside an iteration; initialized
private workspaces remain reused.

Only completed, verified groups update a private checkpoint. Cancellation or
timeout preserves that checkpoint and discards pending edits; no source enters
public metadata. Reports distinguish kept, discarded and unevaluated groups and
record introduced findings and guard reasons. Existing review retries still
force a scan even when a proposed edit makes no change. Verification tool errors
settle through existing remediating -> scanning -> scan_error transitions.


#### D-46 focused calls and existing-file recovery (section 4)

SECURITY_FIX_MAX_RESOURCES=2 and SECURITY_FIX_MAX_FINDINGS=12 bound each fixer
call. Severity precedes deterministic rotation among equal-severity resources;
findings from equally severe resources are interleaved to avoid starvation.
Schema context selects flagged resources, and AWS-0104 no longer injects unrelated
S3 replication schemas. Catalogue guidance and 4000-character rejection feedback
remain separate from untrusted source data.

Fix prompt v5 supplies an existing-path inventory and full current content for
editable files. Optional `edits` maps existing paths to complete replacement
content; the old file/new_files shape remains supported. Existing paths returned
in new_files normalize to edits only when their current content was supplied.
Conflicting primary/secondary edits, missing context, stale source hashes, unsafe
paths, new suppressions and invalid syntax reject explicitly. Additional paths
remain capped at three. Calls sharing editable context run sequentially with
fresh source; independent calls retain bounded parallelism. Public reports retain
only paths, reasons, counts and recovery outcomes, never source hashes/content.

A scripted four-proposal collision corpus normalized all four proposals; three
survived all guards, and one introducing a new blocker remained rejected. This
is test evidence, not an estimate of recovery among the historical 47 rejections.
Candidate after_failed remains the rejected candidate count; retained_failed
separately describes the verified retained baseline. A verification regression
completed at the deadline remains a regression-plus-deadline observation.


#### D-46 secure generation (section 3)

Generator prompt v7 selects resource types from plan services/storage, adds the
catalogue and frequent supporting-resource requirements, and preserves the
existing combined 6000-character schema/checklist cap (schema <=4500, checklist
<=1500). Type selection uses fixed service tokens and storage kinds, never a
benchmark-prompt match or raw plan text in security guidance. Input truncation
and checklist lengths are explicit remediation metadata; output tokens and
provider pins are unchanged. Shared system prompts remain variant-independent
apart from their existing optimisation directive.


#### D-46 configurable fixer verification (section 5)

No default model or attempt timeout changes. OpenRouter Anthropic-family fixers
use the existing OpenAI-compatible adapter, local FixOutput validation and optional
JSON-object mode. Fix-only reasoning off maps to reasoning.enabled=false; the
gpt-oss baseline uses effort=low. Session reports now record effective fix attempt,
60-second iteration, stage and batching/group limits alongside model/provider.
Mocked HTTP through the factory, proposal, guards and PostgreSQL report proves
both model selections; a 45-second attempt clips to a 20-second remaining budget.
These tests establish wiring and format handling, not real model reliability.


#### D-46 PR-04 seed prerequisites (section 6)

The seed command previously constructed the full dotenv-disabled application
Settings, requiring migration/test URLs unrelated to its app-role database work.
A running PostgreSQL service does not supply those process settings. Reproduction
with a development app URL alone fails old Settings before database access;
minimal SeedSettings needs only DATABASE_URL. Missing/wrong role/database settings
now produce fixed safe prerequisite messages and bench-stub preflights before
submitting pipeline runs. Shared engine construction preserves SecretStr handling.
No new package/report fields or privilege/migration changes are required.
A real PostgreSQL regression creates the full-size rejected synthetic package and
downloads its labelled ZIP. This verifies the isolated stack, not the author's
unobserved environment; no .env or original credentials were inspected.


#### D-46 corrective generation and acceptance (2026-10-18)

FR-G-02, FR-S-03/04/09, FR-V-03/04, NFR-01 and PR-05: native Terraform parsing is
authoritative for changed Terraform files. The Python HCL parser accepts some
Terraform-invalid compact blocks and strings, so failure counts and scanner
fingerprints alone cannot prove syntax non-regression. Cache native checks by
file/content; reject invalid edits before retaining any checkpoint. Expanding a
single-line resource also inserts a newline after its opening brace. Declaration
deletions are checked against unchanged consumers, preventing the observed retained
deletion of variable.eks_name. No readiness, severity or blocker rule is weakened.

The author approved generation-only syntax recovery before its first parsable
baseline. The lexer/grammar normalizer only inserts newlines at unambiguous
argument boundaries in complete single-line blocks. Nontrivia token signatures
must match and normalization must be idempotent; ambiguous files, semicolons,
missing quotes and policies remain for LLM repair. Hashes/locations are logged.
At most two syntax-only rounds use exact private diagnostics/excerpts after secret
redaction. Scope, identities and existing control literals are preserved; syntax
is checked before retention. One regeneration may follow using the original
generator, feedback and output-token settings, without restarting recovery.
Initial generation, recovery and finalization share the original 150-second
deadline and reserve five seconds for finalization. Exhausted paths are explicit.
Previously hidden findings revealed during provisional generation stay blocking;
the no-new-blocker rule applies after that baseline is established.

Provenance deduplicates identical observations and carries unique unchanged source
anchors across line movement, while retaining unknown origins for genuinely
unresolved/incomplete evidence. Reports distinguish observed stage, action and
content hash. Final builtin checks are observed too. Security iterations allocate
55 seconds to work within their existing 60 seconds, clip publication to remaining
time, bound subprocess cleanup and batch event notices through EventLog. Reports
separate scan/construction/syntax/verification/cleanup/restoration/publication.
Interrupted template actions become explicit deadline/unavailability rejections.

Checkov's Helm chart-name path segment is resolved through package Chart.yaml
metadata to a unique exact source path. Traversal/ambiguity remains rejected;
mapping errors have their own category. Rendered line numbers are omitted when
their original source positions cannot be proved. No findings are discarded.

The saved A corpus remains read-only. Native replay repairs 3/11 affected files
and packages deterministically; scripted syntax fixes/regeneration repair the
remaining 8, reaching 11/11 with 24 -> 21 -> 0 native diagnostics. These are offline
test-oracle results, not real-model success or a new production-ready rate.
See phase9f-corrective-verification.md and the dated JSON replay artifact.
Benchmark A/prompt v7 remains historical evidence. Both author configurations
should use the corrected commit/prompt v8 to isolate fixer differences.

#### D-46 A2 declaration, deadline and completeness correction (2026-10-18)

FR-G-02, FR-S-03/04/09, FR-V-03, NFR-01 and PR-05. The six missing A2 variants
failed structural completeness after two successful model responses, in 2.97–4.81
seconds, before syntax recovery. Rejected file maps and detailed structure errors
were not saved; their exact defects remain unknown. New per-attempt metadata
records only categories/counts, missing types, authoritative layout patterns and
concrete suggested paths. The next attempt receives that missing inventory outside
the ten-error general-feedback truncation. Alternative allowed layouts still pass.
The author explicitly changed GENERATOR_MAX_PACKAGE_ATTEMPTS's default from 2 to
3, including the initial call. Explicit overrides remain effective. Prompt v9
records the feedback change; A2 used v8/two attempts. Generator model/output-token
limits, the shared 150 seconds, two syntax rounds and one regeneration are unchanged.

Declaration repair previously skipped two syntax-invalid originals and was not
retried after syntax repair because the generation gate existed. Completion now
tracks module content fingerprints, and repair runs after syntax recovery and
accepted generation changes before establishing the baseline. Native checks remain
mandatory; unresolved syntax stays blocking. Replay against the saved parsable
final checkpoints adds 19 and 12 declarations, removes all 31 builtin variable
failures, passes native parsing and is idempotent. This is not a new readiness rate
or a replay of real syntax-model calls. All fourteen A2 JSON inputs remain unchanged.

One absolute security-iteration window now includes scanning, verification,
cancellation, restoration, notices and closing state/event persistence. Work stops
with five seconds reserved. Child shutdown, PostgreSQL statement/lock waits,
connection/transaction acquisition, EventLog publication and workspace locking use
remaining time. Parsed documents/trees and reference/declaration indexes have bounded,
content-keyed caches within each package; no parsing workers or new dependencies
are added. Cooperative checkpoints permit deadline handling between analysis passes.
If mandatory finalization itself cannot finish, the iteration fails closed. Its
legal stage-fault settlement is bounded by the original remaining stage budget;
that tail and any actual overrun remain visible rather than becoming a new fix
allowance or a passing PR-05 measurement. CPU work remains cooperative, so no hard
real-time scheduling guarantee is claimed under external contention.

Variable-reference provenance uses file/module/rule/reference identity independent
of line movement, preserving first observation across partial checks. Metadata
distinguishes first observation from a conservatively proven introduction.
Additional PR-05 workload views separate isolated PR-01, isolated PR-03 baseline
and concurrent PR-03 cohort observations; historical unclassified rows stay unknown.
The existing aggregate verdict, timestamp boundaries and 150/60-second thresholds
are unchanged. A2 remains FAIL: 0/159 isolated PR-01 failures, 0/19 isolated baseline
failures and 5/57 concurrent failures. The observed 3/41 to 1/36 readiness change
has two-sided Fisher exact p=0.618259407733092; correlated variants and changed
prompts prevent causal attribution. No readiness, severity, blocking, privilege or
state-transition rule changes; no migration or Phase 9g exception profile.

#### D-46 measured reporting and final guard checks (section 7)

Benchmark snapshots explicitly project catalogue controls, template outcomes and
introduced rule counts, kept/discarded/unevaluated groups, normalized/retained
existing-file proposals, findings/resources per call and fixer configurations.
Missing historical fields remain unknown; canonical sessions avoid duplicate
aliases. Near misses count only packages whose final validation result is valid,
with 1, 2–3 or 4+ blocking findings. Per-rule remaining counts remain unchanged.
Authenticated benchmark settings add numeric security limits without exposing
model strings, credentials or arbitrary configuration.

Verified checkpoints preserve both per-iteration diffs and proposal-retention
metrics on cancellation. Changed provider configuration stays with other module
changes. Public catalogue/template notices go through EventLog with safe
rule/resource/outcome metadata. Independently valid unrelated declarations can
be retained; legacy tests now use genuinely invalid supporting declarations when
asserting rejection, while keeping their original security assertions.

No Phase 9g exception profile, real model benchmark, readiness/severity change,
new dependency or migration is introduced. New template findings remain blocking.


#### D-46 Phase 9g template representation correction

FR-S-02/03 and FR-V-03: access-log versioning/public-access protection already
existed. An offline counterexample proved Trivy reports AWS-0090/AWS-0132 on
correct nested Terraform JSON (both list/object block encodings) but neither
finding on equivalent HCL. Emit new supporting resources in security_support.tf
using the schema-aware native renderer; preserve all controls and old files.
Malformed non-object module documents now conservatively prevent construction.
Real Checkov/Trivy and both pinned providers verify each template. Access-log
destinations still have documented strict logging/KMS/replication blockers;
replication is not a new contextual exception. No scanner, severity, fingerprint
or no-new-blocker acceptance rule changes. SSE-S3 remains required for log delivery.

#### D-46 Phase 9g credit, quota and fixer transport correction

PR-01/03, FR-A-03, FR-S-02/09 and NFR-01. OpenRouter account /credits is
queried alongside /key; the guard uses the minimum known account/key/effective
balance. Account probe failure remains unknown, never a fictional balance.
Architect events now retain provider failure categories; security/validation
fixing and syntax repair expose typed quota failures. The first observed
usage_limit stops new submissions; already submitted work is observed. Remaining
planned measurements are not_started without invented run IDs, timing or cost.
All Make targets forward BASE_URL/BUDGET/MAX_RUNS; smoke caps at three while
respecting smaller explicit positive limits and rejecting zero before submission. bench-real already forwarded these values;
the historical prompt's contrary statement was disproved during investigation.

The historical fixer omitted the generator response-validator context, so its
json_schema setting never reached fixer requests. FixAgent now shares that
mechanism for every supported model and all three repair paths. Its existing
patch fields become closed path/content arrays on the strict wire, normalized
back to internal dictionaries; fix summaries are typed. json_schema sends
strict=true and OpenRouter provider.require_parameters=true. Configured
json_object/off, local validation, unambiguous salvage, retry correction and
unsupported-capability behavior match generators, with no automatic downgrade.
Patch paths, suppression, preservation, syntax, strict acceptance and budgets
are unchanged. Safe per-attempt outcomes/format reasons are persisted/exported;
missing historical or interrupted-call coverage stays unknown. Mocked HTTP
tests establish request semantics, not measured real-provider reliability.

Complete format-failure baselines: A3 unknown (no saved attempt logs); complete
B unknown (snapshots lack per-attempt outcomes). The preserved partial B log
excerpt at evals/phase9-bench-real-20261018T231027886459Z/fixer-log-excerpt.txt
contains 14/22 non-quota Haiku invalid_json/prose_before failures and eight
successes. Four additional quota failures are excluded. This is an illustrative
partial sample only. The 140 A3 / 32 B security proposal records are not attempt
counts. No cached results or historical evaluation files were changed.

### D-47 — Honest check and engineer-decision labels (Phase 9g)

FR-S-08/10 and FR-UI-06/07: automatic strict clean scan plus valid validation
is named `checks_passed`. Approval produces `engineer_approved`; rejection is
`rejected`. Required reviewer name/reason and application UTC decision time are
persisted and shown with self-declared identity provenance. Local mode explicitly
states no authentication. Reports/findings remain visible after decisions; no
label implies a successful cloud deployment. Migration 0004 leaves events
immutable, distinguishes recorded approvals, and returns unverifiable legacy
success claims to pending_review. Missing historical identity/reason is unknown.
Historical reports are never rewritten; compatibility output discloses mapping.
SSE replay reconciles its latest legacy outcome with the migrated row; an
ambiguous event cannot claim checks_passed or leave a settled stream open.
Synthetic benchmark fixtures identify themselves and never invent a human review.
Final provenance audit added 0007 rather than editing already-applied 0004:
a migrated success needs a recorded automatic valid -> production_ready event
(or a current checks_passed event). Clean reports with a missing/ambiguous
transition cannot establish automatic provenance and return to pending review.
The data-only downgrade never restores an unverifiable success claim. Events and
original decision records remain untouched.

Round 3 (author-approved): checks_passed can transition only to rejected for
engineering judgement; approval and retry remain unavailable there. Check results,
files and the completed run status/timing remain unchanged. Every new approve or
reject requires a fixed reason category and free-text reason; identity policy is
unchanged. Existing JSONB decision/event records hold category, with historical
missing values projected as null / “not recorded”, without a schema migration or
historical event rewrite. Readiness documents add only the category information.
Decision reasons are never remediation feedback or LLM inputs in this phase.

### D-48 — Versioned secondary exception assessments (Phase 9g appendix)

FR-S-04, FR-UI-05 and NFR-01. Bundled strict/contextual-v1 JSON profiles are
version 1 on strict policy 3. The selected identifier is persisted per run by
migration 0006, emitted in its acceptance event and included in results, archives
and benchmark records. Both assessments use the same stored final findings;
strict findings, severities, official labels and every acceptance guard remain
unchanged. Missing/contradictory scan metadata cannot establish assessment
success; strict still requires a recorded clean scan and valid validation.
Excepted records retain rule/resource/path, entry ID and justification.
This is experimental analysis: author/supervisor approval is outstanding before
reported thesis use. It is not an approved security release policy.

| Entry | Checkov IDs | Trivy IDs | Resources / exact parsed condition | Justification / reference |
|---|---|---|---|---|
| s3-log-target-sse-s3 | CKV_AWS_145 | AWS-0132 | Unique S3 bucket/encryption association; source bucket differs from destination; source logging resolves to destination; destination is proven AES256 | Delivery-compatible SSE-S3; AWS S3 enable-server-access-logging guide |
| s3-log-target-no-recursion | CKV_AWS_18 | AWS-0089 | Exact destination of another bucket's inline/standalone logging configuration | Avoid recursive server logging; AWS S3 ServerLogs guide |
| public-subnet-addressing | CKV_AWS_130 | AWS-0164 | Unique explicit/main/default route table and default IGW route; IGW and subnet belong to the same resolved VPC | Intentional public subnet; AWS VPC Internet Gateway guide |
| public-lb-exclusive-egress | none curated | AWS-0104 | Security group/rule with completely resolved consumers exclusively public application aws_lb/aws_alb resources, internal=false | Public-LB traffic; AWS ALB security-groups guide |
| public-lb-https-redirect | none curated | AWS-0053 | Public application LB, HTTP:80 default redirect HTTPS:443 (301/302), HTTPS listener, no HTTP listener-rule bypass | Intentional public HTTPS endpoint; AWS ALB rule-action-types guide |
| public-lb-http-ingress | CKV_AWS_260 | none curated | Exact public TCP:80 ingress; group exclusively serves the above redirecting LBs; broad rules cannot qualify | Redirect-only HTTP; AWS ALB rule-action-types guide |

Exact URLs are retained in each JSON entry. Missing curated equivalent IDs are
explicitly empty; different scanner controls are never paired. All resources,
references and scope are parsed; comments, README names, substring matches,
dynamic instances, aliased providers, malformed modules and unresolved bindings
cannot prove an exception. External/literal IDs and hidden module consumers
remain unresolved. Plan-only NAT/public-tier mappings are omitted because no
resource-address binding exists. IPv6 HTTP ingress and custom HTTP listener rules
are conservatively omitted. CKV_AWS_144 is rejected as a new exception: a missing
replication requirement is not proof that replication is unnecessary. Existing
strict variant exemptions remain exactly as policy 3 defines them.

Offline reclassification: evals/phase9g-reclassification-20261019 contains sanitized
metadata and SHA-256 input manifests. A3 strict/contextual-v1 are 1/29 and 1/29;
B is 1/9 and 1/9. Additional validation-valid packages retain noncandidate
blockers. Both original benchmarks remain incomplete provider-limited evidence;
no new model reliability or production deployment claim follows. All source
snapshots and original evaluation folders are unchanged.

### D-49 — HttpOnly login and explicit local mode (Phase 9g)

NFR-01: shared-key login issues a random 256-bit token; only its SHA-256 hash is
stored in auth_sessions (migration 0005). HttpOnly/SameSite=Strict/Path=/api,
configurable Secure for HTTPS, same-origin browser mutations, and bounded login
attempts replace browser key storage. Headers remain supported for scripts.
Idle/absolute defaults are 1800/43200 seconds. Active SSE emits and heartbeats
renew idle activity atomically; expiry/revocation cannot be revived and absolute
expiry is never extended. No user accounts or verified reviewer identities.

With API_KEY configured, direct Uvicorn and the author's VS Code configuration
stay unchanged. Only unset-key startup requires the validated app.server launcher
bound to 127.0.0.1; unknown/other binds fail startup with a fixed clear message.
Session status/UI visibly disclose no authentication in local mode. Owned SSE
session-renewal transactions and connection cleanup finish before disconnect
cancellation; live/heartbeat waits remain cancellable. Origin-less scripts may
use a valid header at login/logout too; an explicit bad Origin is always denied.
Tests use
an explicit synthetic local bind and isolated PostgreSQL, never author settings.

### D-50 — Accounts and authenticated review identity (Phase 9h)

NFR-01 / FR-UI-07: usernames are case-insensitively unique and passwords use
salted standard-library scrypt (32768/8/1, 32 bytes). HttpOnly hashed sessions
bind to users; password resets and disabling revoke sessions. Bootstrap is
serialized and requires a local peer without forwarding headers or the API
header, plus existing Origin checks. The author explicitly changes D-49: local
open mode exists only until the first account; the unset-key loopback startup
restriction remains. Historical decisions are untouched. New account decisions
snapshot user ID and username; script/local identities remain self-declared.
Legacy key login remains a transitional pre-account API path only and is absent
from the browser. Bootstrap revokes all unbound sessions as well as migration
0008 revoking existing sessions. Header access is unaffected.

D-04 extension (Phase 9h): an inspection-only role is cluster-provisioned by
bootstrap, then receives schema usage, SELECT and future-table SELECT grants
from migration 0012. The owner/app privilege boundary remains unchanged;
pgAdmin is optional and loopback-only. Existing volumes must provision the role
before migration. No pgAdmin image was pulled by Codex.

### D-51 — Encrypted provider credentials (Phase 9h)

NFR-01 is amended by author instruction to permit authenticated ciphertext in
PostgreSQL, never plaintext. AES-256-GCM binds provider and UUID as associated
data; versioned encrypted envelopes, fresh nonces and key versions support
rotation. CREDENTIAL_ENCRYPTION_KEY is process-environment-only (base64 32 bytes).
Missing/wrong keys fail closed. Dynamic secrets join public/log redaction.
OpenRouter, OpenAI, native Anthropic and custom-compatible API-key presets use
existing SDKs; provider probes use mocked HTTP in tests. credential_type and
api_protocol are extensible strings; future OAuth access/refresh tokens and
expiry metadata fit the same envelope without a schema migration. Future OpenAI
"Sign in with ChatGPT" with Responses transport requires an authentication
resolver/adapter implementation and policy verification; none is implemented.

Dependency inventory: cryptography 50.0.2 (Apache-2.0 OR BSD-3-Clause), cffi 2.1.1
(MIT-0), pycparser 3.11 (BSD-3-Clause), exact locked distributions. cryptography
is the sole new direct dependency; the other two are its required transitives.

### D-52 — Per-agent models, thinking and request compatibility (Phase 9h)

FR-P-04 / NFR-01: freeze five effective role selections and retain provider,
model, configured effort, effective effort and request style. Three UI controls
have optional per-generator overrides. Explicit interactive configuration uses
one provider credential; metadata or admin-declared capabilities govern valid
combinations. Unknown structured-output capability cannot qualify explicit
Generator/Fixer selections. Native thinking/structured output is opt-in new
configuration, preserving the legacy native adapter's omitted parameters.

Header runs without explicit selections retain environment resolution, including
SECURITY_FIX_* fallback and omitted reasoning; unset is never rewritten as off.
The baseline commit 26ef29f's captured golden request parameters include complete
strict schemas/routing and are compared as serialized bytes. Legacy environment
requests remain usable without a new catalog dependency; capability enforcement
applies to explicit model selections. No readiness/blocking rule changes.

Phase 9j role-default correction: each role resolves run, personal, administrator,
then environment independently. Within each tier, a specific generator precedes
the Generators group; a higher-tier group beats a lower-tier specific generator.
Selecting Architect never supplies another role's fallback. The selected provider
chooses transport/credential only; freeze all five selections before assigning the
legacy representative run model. Explicit null thinking remains provider default.
An unconfigured role requires its own choice/default; fully explicit roles need no
environment model. Existing header benchmark request bytes remain unchanged.

OAuth with consumer subscriptions (ChatGPT/Codex/Anthropic) and future OpenAI
Sign in with ChatGPT/Responses transport are out of scope. D-51 reserves typed
credential/protocol fields and encrypted envelope capacity, without implementing
OAuth, refresh tokens or Responses. Future work requires provider-policy and
availability verification; no consumer subscription entitlement is assumed.

### D-53 — Server-authoritative preferences and browser fallback (Phase 9h)

FR-UI-01 / FR-P-04: account preferences persist role defaults, prompt/configuration
drafts and allowlisted UI settings in PostgreSQL with optimistic revisions.
Recent-run rows reference shared runs and bound cursors to real per-run events.
After login the server copy wins; conflicts preserve a separate recoverable
unsaved draft. Versioned user-scoped localStorage is a validated, bounded cache
and offline fallback; no authentication/credential form state is serialized.
SSE cursor restoration hydrates history through that cursor before live resume,
using the same historical-label interpretation. Hydration failure replays from
zero. The API returns history in pages of 500; current EventLog retrieval still
loads the run history internally and is not a large-history optimization.

### D-54 — Runtime attribution and rejected-repair scan short-circuit (Phase 9h follow-up)

PR-01/05, FR-P-04, FR-S-03/09, FR-V-03 and NFR-01: validation repairs defer
baseline/candidate scans until proposal/syntax checks pass and validation improves.
Every improved candidate still passes both scans and the existing new-blocker
comparison. Strict output, acceptance, partial-group limits, deadlines and
readiness remain unchanged. This is an execution-order optimization, not a
relaxation of the acceptance predicate.

Additive result telemetry and batched immutable stage-notice events retain safe
per-attempt reasoning counts and per-invocation/local-evaluation timings. A
context-local collector isolates concurrent work. Timestamped interval unions
distinguish elapsed wall time from overlapping invocation totals; group spans
contain their child tool spans. Cache reuse is explicit, with no invented tool
invocations. Observed cancellations are retained; a process crash or exhausted
publication deadline can still leave incomplete telemetry. Existing absolute
deadlines are not extended to make reporting complete.

Optional LOG_FILE writes only allowlisted app.llm.base structured diagnostics,
redacted with existing filters, to an operator-owned untracked file. No new
dependency or database migration. Legacy frozen selections retain their wire
behavior; reporting marks missing catalog capability as unknown/unprobed.
Historical missing counts remain unknown, including all A3 reasoning tokens.

Offline replay and counterfactual PR-01 estimates are documented in
phase9-runtime-attribution.md. No additional scan caching or duplicate-group
optimization is implemented; those remain proposals pending measurement.

### D-55 — Final evaluation method and descriptive statistics (Phase 9b)

PR-01/03/04/05, NFR-01/02: the final report reads immutable committed evidence,
records SHA-256 inputs and never rewrites historical benchmark folders. Only the
two matched final sets are pooled. Missing variants are disclosed and excluded
from generated-package rates. Historical contextual assessments remain unknown
unless stored; they are experimental and never alter strict readiness (D-48).
Wilson 95% intervals and probability-ordered two-sided Fisher exact tests use
standard-library arithmetic. Package-level independence is unrealistic because
three variants share one plan; p-values are optimistic and descriptive. An
adjacent run-level sensitivity includes complete failed runs and counts runs
with at least one passing package. Repeated prompts still limit inference.
The schedule is fourteen runs across three prompt texts per final set, not
fourteen distinct prompts. No threshold or acceptance guard changes.

The author approved a counts-and-identifiers-only supplemental folder projected
from read-only cached snapshots: source filenames/hashes, run/variant IDs and
proposal acceptance counts. No generated content, diffs, prompts, model outputs
or secrets are exported. Its built-in secret scan precedes commitment. Reporter
execution reads the committed supplement rather than cached inputs. Proposals
are distinct from LLM attempts and verified retained changes. Full historical
attempt and reasoning coverage stays unknown.

NFR-02 role-swap tests exercise the existing injection seams without peer or
orchestrator edits. Concrete-class recovery checks and private generator runtime
metadata remain explicit contract-review limitations; no unrestricted
replaceability claim follows. NFR-04 clean deployment remains manual/unverified.
The isolated E2E server uses a larger fixture login allowance to avoid cumulative
rate-limit timing dependence; production authentication policy is unchanged.

PR-04 attribution uses loopback HTTP full-body timing, not the spec's curl
client. It is an offline attribution measurement with a synthetic near-10 MB
archive, ten alternating samples and two warm-ups per condition. Only the quiet
run is official new evidence; an exploratory overlapped run is excluded. The
measurement-only session-touch control never changes production authentication.
The quiet session maximum is 0.721118 s; historical failures remain failures.
No clear auth bottleneck justifies a runtime fix. PR-03's revised wording is an
unadopted supervisor-review draft in phase9b-performance-gaps.md.

Benchmark CSV exports now use explicit bounded columns and a results.json row
reference. Large runtime/attempt detail stays in JSON. Historical oversized CSV
readers raise and restore the parser field limit; historical files are untouched.
LF CSV output avoids Git newline normalization changing reproduction bytes.

The complete counts-only cached-input audit additionally hashes the empty failed
A3 snapshot: 42 source snapshots correspond to 119 generated-package records.
The final matrix uses committed section 2 collection evidence; later reporting
unit tests are listed in the implementation log, without misrepresenting the
collection as an execution result. Prompt version identifiers were captured from
the recorded source commits during investigation; generation reads only evidence
blobs and uses that documented identifier lookup, with unknown for unlisted
historical stub commits. Final-set pooling rejects dirty/mismatched code,
settings, tool versions, selections or exact-text schedules.

### D-56 — Phase 9i guarded repairs and versioned offline assessments

FR-G-02, FR-S-04/09, FR-V-01/03, FR-UI-05 and NFR-01: author-approved
Phase 9i adds bounded schema guidance, documented equivalent/format repairs,
dependency-aware subnet defaults and guarded VPC/RDS defaults. contextual-v2
is an independent experimental assessment; contextual-v1 predicates, JSON and
stored results remain frozen. Strict controls repair acceptance, readiness and
downloads. Run profile selection and persistence are unchanged; no migration.
No threshold, deadline or dependency changes are authorised.

Schema/provider follow-up (FR-G-02, FR-V-03/04, NFR-01): guidance uses three
global tiers: unconditional required arguments/blocks recursively, conditional
requirements under optional ancestors, then optional attributes and optional
blocks. Conditional shells carry `if_used: true`; common recursive structure is
shared across provider versions without losing version-specific requirements.
Caps remain 4,500 schema / 1,500 checklist / 6,000 combined characters.

Author clarification: when a required tier exceeds its cap, include only complete
per-resource-type groups, prioritising types mapped directly from structured plan
services/storage in encounter order before inferred support types. Skip a group
that does not fit and continue considering subsequent types. Tier 2 never
displaces tier 1: omitted conditional groups retain their unconditional cores.
Generation continues. Events, quality exports and benchmark reports carry an
explicit overflow flag and separate omitted-type lists for the two tiers.
Unavailable schema indexes retain the existing degraded-guidance behavior.

The additive `generator_schema_only_context_chars` measures schema characters
before checklist concatenation. Historical `generator_schema_context_chars`
sometimes measured the combined context; preserve it and all historical values
without deriving or backfilling an allegedly exact schema-only measurement.
Absent new metadata remains unknown.

Duplicate `terraform.required_providers` declarations are consolidated atomically
within one module when provider sources agree and numeric Terraform version
constraints have a provably nonempty intersection. Distinct providers and
compatible aliases are unioned; constraints remain a conjunction, independent of
mirrored pins. Unsupported syntax, ambiguous declarations, source conflicts and
empty intersections remain for LLM repair. Unrelated source/settings survive.
The existing CandidateGuard and failed-check improvement rule decide retention;
proposals, hashes and accepted/rejected/skipped reasons are recorded. This adds
no new validity threshold. Evidence is separate in
`docs/evals/phase9i-guidance-provider-offline/`; guidance alone receives no
attributed package improvement. No new dependency, migration or open question.


Offline attribution found a pre-existing service-selection bug: broad scenario 3
(Serverless REST API), both rounds, selects no resource types because Lambda/API
Gateway and NoSQL/DynamoDB mappings are absent. Both pinned AWS indexes contain
the corresponding schemas. Both pre-change and current schema contexts are zero;
no overflow occurred. Required-coverage claims apply to selected types, not every
service in a plan. This gap was reported before committing and is deferred from
the schema-budget/provider-merge scope; see the evidence zero-schema-contexts.json.

Service-mapping follow-up (FR-G-02, FR-V-03, NFR-01): resolve the above gap
before the next real benchmark. The Architect's service field was an open string,
not a finite enum. It now advertises 33 supported labels as schema examples,
retaining free-form validation compatibility; its schema-derived prompt version
advances from 2 to 3. Coverage tests independently enumerate that vocabulary and
all saved broad/final-set service labels against both pinned AWS indexes, listing
unmapped services or non-indexed types on failure. Aliases are matched only in
structured aws_service fields. Named storage services precede generic kind
fallbacks; NoSQL/cache kinds now have fallbacks. Explicit plan types retain their
priority over inferred network support types; budgets and tiers are unchanged.

Author clarification: plain Prometheus/Grafana inherit explicitly planned
EC2/ECS/EKS hosting resources. Only explicitly managed labels map to AWS workspace
types. Monitoring without an explicit host remains unresolved; arbitrary strings
outside the advertised vocabulary remain possible and cannot be exhaustively
covered. Neither case invents infrastructure. All 48 saved plans are covered;
the two zero-schema contexts now measure 4,471 characters each. Before/after
per-service coverage and context sizes are recorded separately in
`docs/evals/phase9i-service-mapping-offline/`. Historical evidence is unchanged;
no inferred validity/security gain, readiness, blocking or threshold change,
new dependency or open question.

AWS major-version drift follow-up (2026-10-22; FR-G-02, FR-V-03, NFR-01):
paired offline replay covers both broad cohorts and both final sets. Add only
version-bound documented migrations when the module selects the mirrored AWS
6.x schema: literal aws_eip.vpc=true becomes domain="vpc"; a scalar SSM association
instance_id becomes one InstanceIds target with the original expression; a flow
log's uniquely bound CloudWatch group name reference becomes log_destination
using that same group's ARN. Existing destination/targets, dynamic or false EIP
values, unbound literal log names, malformed/ambiguous modules, custom sources and
unknown schemas skip edits. Provider constraints and resolved majors are preserved.
Native validation plus the unchanged CandidateGuard/failed-check improvement
rule decide retention; records include hashes and outcomes. Parameters.commands
list-to-string rewriting is not a v5-only migration and is outside this change.

The [pinned provider migration guide](https://github.com/hashicorp/terraform-provider-aws/blob/v6.68.0/website/docs/guides/version-6-upgrade.html.markdown)
documents the three removed fields. The round-2 audit finds retained EIP and SSM
cases; the flow-log occurrence is confined to original generator output and had
already been repaired historically. Original and retained observations are kept
separate, so that prior repair is not counted as a new gain. No additional
v5-only configured resource/data fields or nested blocks were found in the
inspectable round-2 modules selecting 6.x. One original module has a parse failure,
so its audit is incomplete; all retained round-2 modules are parseable. Computed-only
references and removed resource types are outside that configured-argument audit.

Advertise and map subnet to aws_subnet/aws_route_table_association and ssm to
aws_ssm_association/aws_ssm_document/aws_iam_instance_profile. Coverage now spans
35 advertised labels and all 68 saved plans from the four cohorts. The embedded
Architect schema changes prompt version 4; there is no new inference run. Existing
guidance caps/tiers, strict policy, readiness, blocking and thresholds are unchanged.
Evidence is separate in docs/evals/phase9i-v6-migrations-offline/. Fresh paired
native observations cover every changed proposal. Byte-identical packages retain
explicitly labelled frozen baselines with matched tool/provider versions and
unchanged observational validator/scanner/policy sources. Historical inputs and
reports remain frozen. Provider major drift is a discussion finding, not evidence
that Architect prompt v3 or guidance tiers caused the model's provider choice;
see docs/thesis-notes/chapter6-evaluation.md. No dependency or new open question.

Literal file-path follow-up (2026-10-22; FR-G-02, FR-V-03, PR-01, NFR-01):
propose a source-preserving `file()` path rebase only for a literal canonical
relative path whose module-relative target is absent and whose exact package-root
artifact exists. Emit `file("${path.module}/<relative path to that artifact>")`
after proving the resolved destination remains inside the copied package.
An existing root-working-directory target is also authoritative in child modules.
Do not search by basename, create files, read the host filesystem, change artifact
contents or alter a valid existing read. Dynamic, escaping, dotenv, malformed and
ambiguous inputs skip. Parsed HCL, interpolated heredocs and Terraform JSON
expressions preserve unrelated source, comments and string escapes. No prompt
text is matched. The documented semantics of
[file()](https://developer.hashicorp.com/terraform/language/functions/file) and
[path.module](https://developer.hashicorp.com/terraform/language/expressions/references#filesystem-and-workspace-info)
preserve the expression's string type; native schema validation remains
authoritative. The additive `terraform_file_path` repair kind records proposal
hashes and the unchanged validity/security guard's accepted/rejected outcome.

Offline evidence in `docs/evals/phase9i-file-paths-offline/` covers all 201 saved
packages from both broad cohorts and both final sets. Its baseline is the
hash-reconstructed retained v6 replay, keeping path effects separate from prior
migration gains. Every changed proposal receives paired native checks/scans;
identity cases use explicitly labelled prior observations with matched tools,
provider indexes and unchanged observational sources. Per-scenario candidate and
retained validity/strict/v1/v2 deltas distinguish rejected proposals. Historical
inputs and reports remain immutable. Ten proposals yield seven accepted edits
and three no-improvement rejections. Only broad cohort 2 scenario 10 gains a
valid package (2/6 to 3/6); overall validity rises from 98/201 to 99/201. Its two
existing KSV-0125 blockers remain, so strict/v1/v2 pass deltas are zero in every
scenario; blocker-count deltas are also zero. All other scenario validity deltas
are zero. No SSM commands coercion, prompt/guidance,
readiness, blocking, threshold, dependency or database change; no new open question.

Kubernetes follow-up (FR-S-04/09, FR-V-01, FR-UI-06): a missing-only,
source-preserving pod catalogue supports Deployment/StatefulSet/DaemonSet/Job,
regular and init containers. Real offline Helm output establishes resource
bindings. Dynamic control flow, ambiguous YAML and unsupported bindings skip
edits; explicit and inherited values remain authoritative. New Helm defaults
are operator-overridable under `infraarchSecurity.<workload-id>.<container-id>`.
Accepted, still-current records annotate archives with **runtime compatibility
unverified**. Static acceptance never proves image startup compatibility.

| Entry | Rules | Change / justification | Functional risk |
|---|---|---|---|
| Identity | CKV_K8S_23/40; KSV-0012/0118 | Missing non-root identity, UID/GID 10001; avoid root and low host UIDs | Image files, entrypoints and low ports may require another identity |
| Escalation | CKV_K8S_20; KSV-0001 | Missing allowPrivilegeEscalation=false | setuid-based startup can fail; privileged/SYS_ADMIN conflicts skip |
| Filesystem | CKV_K8S_22; KSV-0014 | Missing readOnlyRootFilesystem=true; emptyDir /tmp; Helm writablePaths override | Other writes may fail; /tmp is ephemeral; existing/overlapping mounts survive |
| Capabilities | CKV_K8S_37; KSV-0003/0004/0106 | Missing capabilities.drop=[ALL]; preserve explicit lists | Applications requiring capabilities may fail |
| Seccomp | CKV_K8S_31; KSV-0104 | Missing RuntimeDefault; retain explicit profiles | Runtime default may deny application syscalls |
| Resources | CKV_K8S_10/11/12/13 | Missing requests 100m/128Mi and limits 500m/512Mi; fill only consistent pairs | Scheduling pressure, CPU throttling, OOM; these are starting defaults, not capacity estimates |

No permission-changing init containers or PVC ownership changes are introduced.
Linux controls skip explicitly Windows pods. Catalogue construction is separate
from integration; existing guards remain the sole authority for retention.

Image configuration follow-up: literal Helm images gain repository/tag/digest
values under `infraarchImages`, preserving their rendered identity exactly.
Existing bindings and plain manifest images survive. Blank/latest tags remain
blocking (CKV_K8S_14 / KSV-0013); parameterisation alone does not resolve
KSV-0125 registry trust. No registry, digest or version is invented. KSV-0117
(low ports) is outside this catalogue; ports, probes and Services are unchanged.

Real render output also binds templated container names by position only when
source/rendered cardinalities match and rendered names are unique. Whole-document
`if` wrappers are supported without moving edits outside their closing action;
disabling the condition still renders no resource. Inner branches, `else`, dynamic
container ranges and ambiguous bindings remain untouched and recorded as skips.

Kubernetes integration uses the same strict CandidateGuard as existing repairs.
Validation constructs helpers/Grafana plus pod/image changes atomically and
retains the existing failed-check improvement requirement. Security remediation
uses the catalogue path with its existing guards; it does not impose a new
validation-improvement threshold. Rendering/construction consume the enclosing
budget. Candidate records distinguish skipped entries from accepted/rejected
proposals; reason strings never contain raw tool output. Pod inheritance is
added only when all regular/init identities are understood and compatible.
Explicit Windows OS/node selectors skip Linux controls. Duplicate/aliased values
files are not extended. The new report fields are additive; no database,
selectable profile, policy or official label changes are introduced.

The follow-up replay is separate: `docs/evals/phase9i-kubernetes-offline/`.
Historical retained bytes use the unchanged pinned `c3be20c` transforms and
recorded decisions, with before/candidate/retained hash checks for every stage.
Fresh observations include all findings (including advisory findings), all three
assessments, failed checks and unknown outcomes. Independent pod and atomic
format proposals are reported alongside cumulative equivalents/addressing/
formats/defaults/pod stages. Cached observations require matching source, plan,
variant, tool/provider/configuration and evaluator fingerprints. Strict/v1 stored
assessments remain golden-tested on all 81 original packages. No real inference,
image pull, Kubernetes cluster deployment or runtime startup test is performed.

Measured Kubernetes follow-up results are published in
`docs/evals/phase9i-kubernetes-offline/FINDINGS.md`. Ten packages retain defaults
(three ECS, seven EKS). Strict blockers 334→324, v1 329→319, v2 297→287;
all findings fall by 75 occurrences (ten blocking, 65 advisory), with zero new
retained finding identities. Blocking reductions are CKV_K8S_40 −2, KSV-0104 −4
and KSV-0118 −4. Capability/identity/seccomp controls also remove advisory
CKV_K8S_28/29/31/37, KSV-0003/0004/0020/0021/0030/0106 occurrences;
per-entry rule lists identify direct controls, while replay lists every observed
consequential rule. Image parameterisation has synthetic preservation/override
coverage and receives no retained-corpus improvement credit.

Validity remains 45/81 and strict/v1/v2 passes remain 20/81: ECS valid 29/47,
passes 5/47; EKS valid 3/16, passes 2/16; static valid/passes 13/18 under each
profile. All twelve historical new-blocker format candidates remain rejected;
new strict identities fall from the historical 189 to the current 81. Of those,
35 concern tags, registry trust or low ports; the rest include preserved values
and conservative source-structure limits. Historical candidate counts remain
labelled separately from fresh current scans. Nonempty flow mappings at edited
structures and inner/dynamic Go bindings are skipped; empty flow maps and safe
whole-document if guards are supported. No intent or blocking rule is discarded.

All 81 stored strict/v1 assessments match; baseline discrepancies and unknown
scan/validation outcomes are zero. The follow-up proves 324 idempotent catalogue
candidates and 648 reconstructed stage hashes. Full backend verification passes
1,818 tests (six performance tests deselected), frontend 113 and stub E2E seven;
report robustness adds eight focused passes after full-suite collection. Python
starts with dotenv disabled and disposable PostgreSQL uses synthetic credentials.
Runtime compatibility, application capacity, image existence/trust beyond scanner
configuration and live-pipeline/model latency remain unverified. Existing deferred
work and the main CloudFront VPC-origin architectural option remain unchanged.

Offline evidence lives in `docs/evals/phase9i-offline/`. Its input manifest
hashes all 81 generated packages from the two final sets, retaining three
missing variants. Stored results and fresh observations are distinct. The
replay never instantiates operator settings or invokes an LLM. Raw generated
source remains in the original read-only snapshots, outside committed evidence.
Independent and cumulative replay results include before/candidate/retained
validity, failed checks, strict/v1/v2 blockers and exceptions, introduced/removed
findings, rejection reasons and hashes. Final candidates and the final-validator
baseline run in an isolated Linux user/network namespace with offline tools and
mirrored providers. The original pre-change baseline used offline flags and
dead proxies; these observations remain explicitly separate. Cache identity
includes package/plan/variant, versions, schemas, evaluator and configuration.

Generation prioritises required attributes, optional names/types and relevant
nested shapes within the existing 4,500-character schema and 6,000-character
envelope. Per-plan measurements include security-checklist size, total size,
requested/included resource types and truncation. Guidance is not credited with
package improvements without generated evidence; no real model calls were made.
Only documented DB-name, inline-route CIDR and listener-path-map equivalents
are transformed. Expressions/values survive; conflicts, ambiguous structures
and unsupported schemas are skipped. Other invalid security/availability intent
remains for schema-grounded model repair, never argument deletion.

The new shared resolver is separate from v1: at most 64 instances/declaration,
1,024/module and 16 local-reference levels. Literal collections, locals, bounded
count/for_each, indexing, splats and supported collection operations resolve;
variable defaults never establish deployment values. Cycles, overflow, external
modules, unknown expressions and ambiguous references fail conservatively.
Subnet defaults account for implicit EC2 addressing, explicit launch settings,
ASGs, ECS public-IP choices, EKS placements and ENIs. Uncertain consumers skip
repair. Backup retention rises to seven days only for known lower/missing
values. Managing an actual VPC default SG requires proving that consumers do
not need its rules; explicit required rules and unknown launch paths survive.

Recognised Grafana envelopes preserve their dashboard object. Only statically
referenced missing standard Helm helpers and their transitive dependencies are
added within a chart. Custom helpers, existing definitions, remote dependencies
and escaped expressions are not invented or overwritten. Diagnostics retain
bounded helper identifiers and package-relative locations through public-data
redaction. Deterministic format/equivalent records include kind, location,
hashes and accepted/rejected outcomes. Existing syntax, validity-improvement
and no-new-strict-blocker guards remain mandatory.

v2 normalises numeric literal ports and protocol spelling for comparison only;
invalid values and expressions remain unknown. Public ALBs qualify with HTTPS
alone or HTTPS plus redirect-only HTTP, certificates and no redirect bypass.
Public NLBs require exclusively TLS listeners, certificates and a checked-in
TLS 1.2+ policy from AWS's protocol tables; unknown/default/older policies and
TCP/UDP do not qualify. Routing needs bounded, unique, consistent subnet/table/
IGW evidence. SG source-only traffic permissions do not establish attachments;
actual non-LB consumers and unresolved potential consumers still deny exceptions.
All three assessments are returned and displayed; old responses show v2 as
unavailable. v2 exceptions never affect candidate acceptance.

Measured limitations and exact outcomes are in the Phase 9i replay report.
Across 81 packages, cumulative validity rises from 23 to 45 and strict blockers
fall from 391 to 334 (57 removed, none introduced and retained). v1 blockers
fall from 370 to 329; v2 reports 318 before infrastructure changes and 297 after.
Strict passes rise from 15 to 20. Addressing removes 42 findings in 17 packages;
backup retention removes 15 in 15 packages. No saved default-SG candidate has
sufficient consumer evidence, so its tested implementation receives no corpus
improvement credit. Twelve format candidates expose 189 strict findings and
are rejected; two are retained and one has no validation improvement. Thirty-one
equivalent candidates are retained; seven fail the unchanged improvement guard.
All 648 independent/cumulative transformations match final candidate/retained
hashes and are idempotent; no scan or Terraform verification outcome is unknown.

Generation schema sizes are 595–4,493 characters before and 4,478–4,489 after;
checklists 404–1,010 before and 404–1,190 after; total contexts 999–5,503 before
and 4,889–5,668 after. Truncation rises from 43/81 to 81/81 as optional names,
types and nested structures are added. Identical version fields are compacted;
differences remain explicitly version-labelled. More context may affect model
quality/cost/latency; none was measured through real inference. Repair-schema
previews use the existing 16,000-character default and are not model requests;
historical overrides cannot be recovered from package snapshots alone.

Helm repairs can expose previously unrendered workload findings and be rejected;
such findings are retained as candidate evidence, not counted as improvements.
Static validation does not prove an AWS deployment, live deadline success,
model-generation quality or end-to-end networking. Conservative omission remains
the rule for launch settings, unresolved variables and unsupported expressions.
No new spec ambiguity or open question was introduced.

Ranks 4, 6, 7 and 8 remain deferred. Thesis future work includes image-registry
trust (KSV-0125), compatible logging controls, broader unsupported-intent repair and
architectural isolation. Rank 8's main option is CloudFront VPC origins to an
internal ALB; both mirrored AWS versions expose `aws_cloudfront_vpc_origin`.
This is future architecture, not a Phase 9i infrastructure change or policy fix.

### D-57 — Broad benchmark method and pre-registration (Phase 9i evaluation)

PR-01/05, NFR-01: broad-v1 is a pre-registered descriptive quality benchmark,
separate from the specified PR-01 acceptance measurement and PR-03 concurrency
measurement. Ten fixed prompts span five ordinal complexity levels. Anchors
2/9/10 retain the final-set static/ECS/EKS texts verbatim. The other prompts copy
the task descriptions; no generator/prompt-template tuning is introduced.
Complexity reflects expected resource scale and service integration, not observed
output or a causal explanatory variable. Supporting resource counts vary.

The registration was committed in 7884c2f before rehearsal. Each invocation
verifies its JSON bytes against Git HEAD, copies those exact bytes into evidence,
and records their SHA-256 on every scheduled run (including not_started).
The registration commit and schedule identity are validated again by reporting.
Default execution is twenty sequential runs: IDs 1–10, then 10–1. Other positive
RUNS_PER_SCENARIO values alternate forward/reverse rounds. No concurrency cohort,
PR-04 seed/download or unrelated scripted verification is included.

The existing account/key credit guard, first-cost affordability advisory,
usage_limit stop, finite submission cap, per-call telemetry and redaction remain.
BUDGET is a minimum-credit reserve, not a total-spend cap. Remaining scheduled
slots are not_started after a stop. PR-01 timing is descriptive with no verdict;
PR-05 retains the existing per-agent thresholds. Readiness, strict candidate
guards, experimental profiles, deadlines and blocking criteria are unchanged.

Reports read immutable committed evidence only, append separate broad sections
and CSVs, and never rewrite historical rows or pool broad and final datasets.
Stub rehearsals are explicitly separate from real-provider statistics. Package
rates use generated packages from confirmed settled runs; missing variants are
reported separately for those runs. Unstarted slots are excluded. Accepted runs
without confirmed settlement have unknown variant slots, not assumed generation
failures. Pipeline timing medians use the existing success/partial-success
eligibility; costs use known settled sequential deltas with sample counts.
Complete failed runs remain in the run-level comparison denominator.

Scenario/complexity rates use Wilson 95% intervals. Exact-text anchor comparisons
against each final set and the matched final pool use probability-ordered,
two-sided Fisher tests at package and run level. A passing run has at least one
passing package. Missing historical profiles, especially contextual-v2, remain
unavailable; reporting does not rescan or rewrite them. Top blockers are stored
strict findings minus stored exceptions for each experimental assessment.

One model family, two runs per scenario by default, shared plans/variants,
repeated prompts, changed code and provider routing/load limit inference. Actual
repetitions and model selections are disclosed. Package p-values assume
unrealistic independence and are optimistic; run sensitivity does not remove all
clustering. Statistics are descriptive and cannot isolate the causal effect of
9i, prove general reliability or establish deployment success. The author runs
real inference later. No new specification ambiguity or open question is added.

### D-58 — UI polish and truthful configuration labels (Phase 9j)

Round 3 section 1: authentication has an explicit /login route. Only a recognised
signed-out deep link creates transient router return state; login consumes it by
replacement. Root/login entry and explicit logout lead to New request. No last
route is read from preferences or persistent storage. Authentication and local
mode policy are unchanged. No new open question.

FR-UI-01–07, FR-P-04, PR-02 and NFR-01. The author-approved Phase 9j
polish follows the existing working UI and the thesis wireframes. Server-side
readiness, strict assessment, authentication and review rules remain authoritative.

Section 0: Recent runs restarted preference hydration on mount; the application
access gate unmounted it while loading, causing an endless mount/load cycle even
with successful empty responses. Hydration now belongs to the app boundary and
is deduplicated per account. Finite JSON requests have a 15-second deadline;
streaming requests retain their own lifetime. Failed loads expose retry and
cached data is identified. Empty recent history provides a New request action.

The author's safe API projection identified a saved personal Architect default
of google/gemini-3.8-flash:batch with null thinking, no administrator override,
a separate explicit draft openai/gpt-oss-120b selection, and environment default
openai/gpt-oss-120b:nitro with low thinking. Preserve these settings. Null means
provider default, never inherited low/off. Role-specific generator settings take
precedence over a generators-group setting within the same tier. The approved
role-default correction applies run > personal > administrator > environment
before specificity, replacing the earlier flattened-dictionary policy.
No catalogue ordering chooses a default. No new specification open question.

Section A: wireframe text is #e6e6e6; warning uses the orange accent and a faint
#484f58 token is available for nonessential decoration only. UI fonts are locally
bundled Space Grotesk 400/500/600/700; mono is JetBrains Mono 400/500. Packages
@fontsource/space-grotesk 5.3.0 and @fontsource/jetbrains-mono 5.3.0 are OFL-1.1;
@vscode/codicons 0.0.46-24 is CC-BY-4.0. Exact pins/lockfile and attribution in
frontend/THIRD_PARTY_NOTICES.md preserve offline runtime operation. These three
dependencies are explicitly authorised by the author. No UI framework/CDN.

Section C: one accessible searchable model combobox is shared by request and
Settings. It filters ID/name, skips disabled unsuitable models on keyboard
selection and shows capabilities/prices. Null thinking is provider default;
changing default thinking creates an explicit model choice. The public catalogue
adds server_default_max_iterations and an allowlisted resolution_context of
non-secret provider/model/thinking inputs so UI labels can mirror independent
role baselines and explicit SECURITY_FIX_* overrides without guessing. The earlier
selected-provider Architect fallback was an execution bug, also encoded in a
shared fixture; the role-default correction removes it from both layers. Shared
JSON cases cover all 64 combinations of absent/group/specific/both at the run,
personal and administrator tiers for each generator. Controls and Settings
previews retain tier boundaries and identify “from this run”, “from your defaults”,
“from administrator defaults”, or “server default”; mixed generator sources are
shown per variant. Provenance is derived locally without changing public schemas.
Capability validation and header-authenticated golden request bytes are preserved.

Section E: subtitles use available structured network/storage plan facts, marked
“planned”. The current shared plan cannot prove different AZ/capacity/encryption
properties for each variant. Missing facts are omitted instead of inferring them
from variant names, arbitrary generated text or product names. Existing server
readiness/download flags control comparison actions and static checks remain
explicitly distinct from deployment. No new open question.

Section G: add existing UTC created_at/last_login_at metadata to administrator
user listings and each account's own session projection. Explicit projections
exclude hashes/credentials. POST /api/auth/users/{id}/enable is administrator-only,
reviewer-only and clears disabled_at without modifying any session revocation.
Old sessions remain unusable; fresh login is required. No migration/privilege or
authentication-policy changes. UI provides confirmation/password rules, account
metadata, provider no-credit save warning and Revoke confirmation. Capability
declarations are restricted in the UI to custom OpenAI-compatible providers.

Section H: preserve all comparison counts inside an initially collapsed Check
details disclosure so primary evidence, file trees and actions fit at 1280×800.
Model lists virtualise a bounded window with ARIA total/position metadata;
invalid inherited defaults receive field-level explanations, and server model
validation opens configuration with actionable guidance. Mixed per-role defaults
are identified honestly in the collapsed summary. Native dialog focus and long
account names are handled without changing user/account policy.

Browser verification supports optional test-only INFRAARCH_E2E_FRONTEND_PORT and
INFRAARCH_E2E_BACKEND_PORT, retaining default ports, loopback binds, database-role
checks, mocked provider HTTP and refusal to reuse an existing server. This allows
isolated verification alongside the author's running instance. Screenshot/evidence
files live under docs/evals/phase9j-ui/. No new specification open question.

Round 2 section 0: the approved pre-code sweep and four model-dropdown root
causes are recorded in docs/evals/phase9j-ui/round2/BUG_SWEEP.md. Cancelling a
provider probe now clears its activity independently of provider-save actions;
obsolete results cannot restore stale status. Password forms provide username
context without storing password values. Existing session/CSRF/readiness behavior
is unchanged. No new open question.

Round 2 section 2: catalogue failure statuses are first-class UI states with
safe guidance and Retry. GET /api/models?refresh=true bypasses probe cache;
unsuccessful probes are not retained. Screens revalidate on mount/account change,
ignore obsolete responses and never interpret an unavailable catalogue as proof
that a saved model disappeared. Capability null/missing is distinct from false.
Unprobed inherited environment selections retain legacy request semantics;
explicit choices still require catalogue verification. Header/benchmark paths
remain unchanged. Virtual spacers are internal to a bounded content-sized list,
with viewport-aware placement and reachable rendered keyboard targets.

Round 2 section 1: new request editors start empty, with explicit Restore,
Discard and session-only hint dismissal. Prompt text is independent of saved
configuration. Existing preference-row UTC updated_at is projected on saved
GET/PUT responses and cached account-wise; it dates the last saved snapshot,
including legacy drafts. No historical prompt-edit timestamp is invented. Discard
waits for in-flight autosaves, preserves configuration and remains retryable on
failure. No database migration or new specification open question.

Round 2 section 3: frontend/src/config/recommended-models.v1.json (version 1)
contains only the author-confirmed OpenRouter openai/gpt-oss-120b:nitro entry.
The UI intersects it with the selected provider's confirmed structured-output
catalogue; no capabilities, prices or context lengths are invented by membership.
All-compatible mode adds other confirmed models, sorted by provider/name. Both
views hide :free, provider-declared deprecated and expired expiration_date
entries. Unknown lifecycle data is not guessed from names. The built-in stub demo
is available for offline use, without an additional production-tested claim.
Filtering affects interactive presentation only; header/benchmark request logic
and environment defaults retain existing semantics. No new open question.

Round 2 section 4: ui.hide_whitespace_only_changes defaults true in server
preferences and the optional account cache. Whitespace-normalised alignment is
presentation only: equivalent pairs show current text as context with both line
numbers, and formatting-only hunks receive a neutral label. Counts distinguish
meaningful added/removed rows from hidden formatting pairs, blank lines and EOF
formatting. Like a whitespace-ignoring diff, this is not a semantic equivalence
proof. Disabling restores the retained raw unified diff; files, originals and ZIP
bytes are never rewritten. Existing preference JSON needs no migration.

Round 2 section 5: the author-approved overview replaces always-visible file trees
with summary cards and Inspect this variant links. Files, Security fixes, Findings
(including validation) and Review are URL-addressable inspection tabs. Reviews
retain existing per-variant identity/reason/readiness rules. Architecture is shared
planned evidence, optimisation trade-offs are explicitly goals/review concerns,
and infrastructure cost remains unavailable because no estimate exists in the
API. No measured per-variant properties or costs are invented.

GET /api/pipeline/{run_id}/download-all requires all three existing download gates.
A repeatable-read snapshot keeps packages and label events consistent. The service
reuses unchanged deterministic individual ZIP generation and copies its exact
payload bytes into cost/, performance/ and security/ folders. Top-level README.md
and version-1 manifest.json record run/readiness, individual ZIP filenames/hashes,
and every payload/README hash; only the self-referential manifest hash is excluded.
Individual archives remain unchanged. Missing/unlabelled variants yield no partial
bundle. Optional test-only Vite cache isolation avoids optimizer collisions with
an existing developer instance. No migration or new specification open question.

Round 3 section 2: OpenRouter routing suffixes nitro/floor/exacto/online resolve
metadata from the catalogue ID while the exact configured model ID remains on
inference requests. Catalogue variants (including free/batch) and unknown suffixes
are preserved. Tested recommendations are derived only from provider evidence;
base prices describe catalogue rates, not a guaranteed routed charge. Moving
aliases are hidden in Recommended and labelled in all-compatible. Missing-details
copy has Retry; inherited effort remains visible even without metadata. Compact
80px rows share CSS/virtual geometry. Existing null-thinking and header/benchmark
semantics remain. No new open question.

Round 3 section 3: results add server-derived review_actions while preserving
review_available. The author-requested administrator-only Review history Settings
tab lists retained approval/rejection events across runs, with 25-row pages and
category/decision/inclusive UTC date filters in the URL. Existing require_admin
semantics (including trusted shared-key scripts) are reused; reviewers are denied.
Event timestamp and states are retained facts; absent historical details remain
unknown. Exports cover all filtered matches under a repeatable-read snapshot,
include filters/count/version/export time metadata, and project only the nine
specified decision fields. CSV uses four # metadata lines and spreadsheet-formula
escaping; JSON preserves redacted reason text. No package contents or credential
fields/hashes are projected. Event history remains after package retention. No
curated lessons, new dependencies, migration or specification open question.
Closing verification also restricts missing-model guidance to actual configured
selections, preserves invalid-field focus after the reject dialog closes, gives
select controls explicit accessible names and retains the checks_passed badge
beside Reject/Download. History export requests use the existing 15-second finite
request deadline.

### D-59 — Architect-model experiment and provider preference (Phase 9k)

Section 1 (FR-A-01, FR-P-04, NFR-01): broad benchmarks accept an explicit
Architect model and optional thinking override through the existing five-role
resolver. Header-authenticated role overrides use environment credentials and
role defaults; they never inherit saved browser/admin defaults or credentials.
The author explicitly selects the experiment model; no recommendation selects
it automatically. Architect requests remain JSON-object requests with local
DeploymentPlan validation. The task prompt's reference to an existing strict
Architect json_schema wire was incorrect; adding one would confound the
experiment. Generator/Fixer HTTP bytes remain unchanged for Architect-only
selection changes. No prompts, deadlines, profiles or readiness rules change.

Section 2 (FR-P-04, PR-01, NFR-01): optional per-role provider preferences
become OpenRouter provider.order plus allow_fallbacks=true, merged with existing
strict-schema require_parameters. A preference never propagates between roles.
The shared resolver validates configured model/provider pairs against the local
snapshot; header overrides now consume that snapshot rather than authenticated
provider catalogue probes. POST /api/benchmark/preflight accepts only the existing
master X-API-Key header and projects model/thinking/order and snapshot provenance.
It submits nothing, accesses no saved credential repository and writes no rows.
Public metadata/status GETs use fresh anonymous clients, trust_env=false, no
redirects or credential/settings imports. Unknown/degraded status requires
confirmation or --force; incompatibility and missing snapshots cannot be forced.
Per-run provider statistics deduplicate calls, exclude unknown serving providers
from fallback-share denominators and retain unknown counts. No readiness or retry
policy change. The snapshot producer follows in section 3.

Section 3 (FR-A-01, PR-01, NFR-01): author-run catalogue-snapshot fetches only
anonymous public models/model-endpoints metadata into ignored .cache/openrouter/.
It does not instantiate Settings, read keys/dotenv, authenticate or perform
inference. A public-access failure never triggers authenticated fallback.
Snapshot provenance includes source URLs, capture time and a payload hash.
Pinned Sonnet recommendations are advisory and metadata-derived; explicit
ARCHITECT_MODEL is authoritative and both IDs are recorded. Medium thinking is
recommended through the existing reasoning.effort mapping. Strict-schema support
is declared metadata, distinct from JSON-object support and runtime verification.
No remembered real Sonnet ID, price or context length is introduced.

Cost estimation replays all recorded Architect attempts from the two real broad
rounds (40 runs; 64,871 input and 31,582 output tokens). Output usage already
includes reasoning tokens. Reports distinguish replacement, incremental and
projected full-run costs for one run, scenarios 6/9/10 and twenty runs. Current
snapshot prices reprice baseline Architect usage; historical total-run usage
deltas estimate the other roles. Conservative projections use the maximum
eligible fallback-endpoint price and observed full-run usage. They are neither
quotes nor spending bounds for a different model/thinking configuration. The
existing credit guard uses the conservative estimate before its first measured
cost, without treating it as a measurement or changing reserve semantics.
Missing snapshots/pricing/capability evidence stop the experiment. Raw snapshots
remain uncommitted; manifests retain provenance, price basis and source hashes.

Section 4 (FR-A-01, FR-P-04, PR-01, NFR-01): the broad report accepts an
explicit experiment folder and compares it with the two pooled real broad rounds,
only after checking the registration and Generator/Fixer model/thinking identity.
Stub and smoke cannot enter the full-round comparison. Per-scenario/complexity
outputs retain validity, strict/v1/v2 passes and specific AWS-0053/CKV_AWS_91
package/finding counts. Fallback shares retain known/unknown denominators and
resolve display-name/routing-tag aliases only from snapshot metadata.

LB audits classify explicit structured plan services independently from original
and retained Terraform; bounded instance resolution reuses the existing parser.
Missing, dynamic, unparseable and external-module evidence remains unknown.
Absent LB declarations never imply private ingress. Omitted aws_lb/aws_alb.internal
uses the documented HashiCorp AWS default false; classic ELB omission and custom
providers remain unknown. These observational rules do not alter scanner policy,
CandidateGuard or readiness. Resource/file locations and hashes are source-free
projections; configured scheme does not establish actual reachability. The new
baseline audit checks 120 packages/40 cached snapshots against committed quality
and records source/code hashes without rewriting historical evidence. Run-level
plan records also preserve plans when generation yields no packages.

LLM attempt telemetry adds allowlisted raw finish reasons, retaining reasoning,
latency and truncation/timeout/deadline diagnostics separately from plan-quality
results. Unknown historical finish reasons remain unknown. Reports disclose
historical revisions/prompt evolution and provider routing as confounders; they do
not claim causal isolation or deployment success.

Section 5 (PR-01/05, NFR-01): SMOKE=1 selects registered IDs 6/9/10 once each,
with its own explicit smoke manifest flag and a finite cap of three. Registration
bytes and the full twenty-run alternating schedule remain unchanged. Broad
reporting labels smoke separately and refuses pooling it as a full experiment.
Anonymous metadata-only tools and the master-header read-only API remain separate.
Preflight refuses non-OpenRouter environments rather than invoking an unrelated
authenticated catalogue probe. Advisory candidate listing tolerates unserved
models, while execution still refuses missing endpoint/pricing evidence. A real
local stub tool-chain rehearsal and a separate fake-metadata client rehearsal
exercise the schedule and experiment plumbing without real inference.

Closing verification: snapshot loading rejects direct or symlinked dotenv paths
before any file read. Rejected experiment preflight preserves redacted requested
model/thinking/provider inputs and every unstarted schedule slot. The final
backend suite passes 2,297 tests (six perf deselected), frontend 413, browser 18;
the real local stub smoke completes three runs/nine packages. No real catalogue
snapshot or inference was used, so real model metadata and dollar projections
remain author-run outputs rather than invented evidence. No new open question.

Results section 1 (FR-A-01, FR-P-04, PR-01, NFR-01): the author subsequently
committed a real three-run smoke and twenty-run Sonnet Architect round. The
[Chapter 6 results](thesis-notes/chapter6-evaluation.md#phase-9k--stronger-architect-experiment-results)
recompute counts from committed per-package quality and per-run telemetry,
cross-checking the immutable phase9k-architect-report JSON/CSV audits. Full-round
strict pass is 24/56 (42.9%) versus pooled gpt-oss 43/120 (35.8%), package Fisher
p=0.40692; four high-level variants are missing. Levels 1–3 pass 24/30 vs 39/60
(p=0.22199), valid 28/30 vs 43/60 (p=0.02634). Levels 4–5 pass 0/26 vs 4/60
(p=0.31013), valid 8/26 vs 29/60 (p=0.15898). These splits are exploratory,
chosen after seeing the data, and uncorrected for multiple comparisons.
Packages share a plan; any-pass run sensitivity is 10/20 vs 23/40 (p=0.59569).
Any-valid run sensitivity is 16/20 vs 34/40 (p=0.71810); Chapter 6 also records
run-level splits. Historical code/prompt and provider differences remain
confounders. No causal model superiority or deployment success is inferred.

Sonnet level 4–5 plans are public-LB 10/10, never internal; baseline plans omit
an explicit LB in 12/20 runs. Baseline scenario 7 has four LB-absent plans but
10/12 original packages with public LBs (two unknown). AWS-0053 leads the full
round's retained findings with 27 occurrences. The author's interpretation is
that a stronger Architect improves simpler-scenario validity but leaves the
level 4–5 wall: internet-facing requirements can lead Generators to public LBs
even without an explicit planned LB, suggesting a downstream blocker. This is
the author's reading, not a causal claim or a statement that all scenarios
explicitly demand public ingress.

Corrections to the author's figures: full-round telemetry has 21 unique Architect
calls, not 42 (24 including smoke), and two unique finish_reason=length calls,
not eight, both gpt-oss Fixer; none are Architect. All 395 known full-round
Generator/Fixer calls used Cerebras with zero recorded fallbacks; one additional
cancelled Fixer call has unknown serving provider. All 21 Architect calls used
Claude Platform on AWS. Smoke adds 83 Cerebras and three Claude Platform on AWS
calls, no unknowns or fallbacks. Repeated evidence projections are not new calls.

Measured known full/smoke costs are $1.85209835 / $0.35977435; pooled baseline
is $2.69311165. Architect usage at captured input/output prices gives $0.367124
(19.82%) / $0.065698 (18.26%), a token-priced role attribution rather than
independent role billing. The manifest's $0.222781 Architect projection is an
estimate, not measured cost. The canonical snapshot
`anthropic/claude-sonnet-5.5-20260928` is author-observed in the OpenRouter
activity view for an inspected request; telemetry records the unpinned alias.
Committed evidence, prompts, profiles, thresholds and readiness remain unchanged.

Results section 2 (FR-A-01, NFR-01): offline adapter/golden-wire inspection
finds medium OpenRouter requests send top-level `reasoning: {effort: medium}`
through SDK extra_body, together with `response_format: {type: json_object}`.
There is no native reasoning_effort, Anthropic thinking/output_config, explicit
enabled flag or separate thinking-token budget for this request. Architect
requests do not use the strict json_schema/provider.require_parameters path;
DeploymentPlan validation remains local. The adapter parses only
`usage.completion_tokens_details.reasoning_tokens`, retaining integer zero and
using None for missing/unusable detail. All 21 unique full-round Architect calls
(24 with smoke) report zero, not 42 distinct calls. The author's billing check
of 2,245 in / 1,260 out gives $0.01709, rounded $0.0171 at recorded prices, with
no additional reasoning output reported or billed. This is author-observed
billing, not an independently fetched record.

"thinking requested at medium; no reasoning tokens reported or billed; the experiment therefore tests a stronger Architect model without extended thinking".

Possible causes remain unverified hypotheses: ignored/mapped effort, a different
model/endpoint activation requirement, interaction with JSON-object output, or
incomplete/different usage accounting. Code and mocked wires cannot establish
provider behavior. No provider documentation is asserted from memory, no live
request was made and no adapter fix is introduced. See the Chapter 6 offline
wire inspection for the exact fields and test references.

Results section 3 (NFR-01): eval-report resolves relative output destinations
against the evidence repository root, including when Make runs the command from
backend/. Absolute destinations inside the repository retain their location;
resolved paths outside it (including traversal and symlink escapes) are refused
before evidence processing or output creation. Existing fresh-directory,
committed-evidence and cache protections remain. Tests generate deterministic
reports under temporary repository-local directories and clean them afterward;
the README reproduction example now uses a fresh docs/evals/ destination.
This corrects a reporting-tool path bug; no thesis policy, readiness condition,
threshold, source evidence or adapter behavior changes, and no new open question.

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
  `scanning`. Following the approved Phase 9e follow-up, `iteration_count`
  counts started fix passes, including rejected, rolled-back or timed-out
  attempts; baseline verification and terminal scans do not consume an attempt.
  It never exceeds `max_iterations`.
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
  configurable 120-second per-attempt timeout and 8,000 output-token limit
  for full-package calls. Remaining agent time still caps each call. A fully
  valid package finishing synchronous final validation after the budget is
  retained with an explicit deadline flag/overrun (D-43); no late retry starts.
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

- **Phase 5b update:** Phase 5 tool availability/syntax observations are superseded by D-31.
  Active tools are Checkov 3.3.21, Trivy 0.69.3 and Terraform 1.16.4. Trivy
  silently skipped the malformed HCL probes, so the filtered Terraform gate
  supplies syntax findings. Trivy renders and scans Helm templates without
  the Helm executable, closing the Checkov-only gap; Checkov still skips Helm.

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
Phase 7 deliberately keeps 404 for absent/expired packages and defers 410.
Retention absence is not listed as a generation failure in results. A future
410 contract still needs an explicit durable expiry interpretation.

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

### OQ-09 — Feedback-only retry targeting (Resolved by D-37)
Explicit existing target_files resolve feedback-only retries; targetless requests are rejected before mutation. See D-37.

### OQ-10 — Static naming applicability without deployment roles
The plan does not distinguish application workloads from control-plane and
infrastructure services. Phase 6 uses the centralized conservative rules in
D-35 without adding schema fields. Their warnings are evidence for review;
dynamic names, Helm aggregate workloads and workload kinds outside the named
Deployment/StatefulSet categories are not fully comparable. Any richer role
metadata or semantic naming inference is a later design decision.

---

## Thesis text to update (collected)

- Phase 9i / Chapters 4–6 (D-56): explain guarded documented equivalents,
  lossless document repairs, dependency-aware subnet/default-SG decisions and
  seven-day recovery retention. Publish independent and cumulative replay of
  all 81 packages, including rejected candidates, unknowns and context coverage.
  Separate strict and frozen contextual-v1 results from experimental v2 policy
  classification; preserve readiness/acceptance thresholds and historical sets.
- Phase 9i future work: defer ranks 4, 6, 7 and 8. Workload/container hardening
  and image-registry trust (KSV-0125), compatible log-bucket controls and broader
  schema-grounded repairs
  need separate validation. **Main architectural option (rank 8): CloudFront VPC
  origins to an internal ALB**, supported by the mirrored provider schemas.
  Evaluate regional/service restrictions, ingress trust, certificates, WAF and
  operational costs before implementation. No architectural gain is claimed
  from the current offline replay.

- Phase 9h / Chapters 4–6: accounts and authenticated identity (D-50), encrypted
  provider credentials and key rotation (D-51), five resolved model/thinking
  choices with preserved benchmark defaults (D-52), server-authoritative user
  persistence and browser fallback (D-53). Incorporate the upgrade/backup path,
  read-only database inspection and docs/agent-tools.md harness sequence.
- Future work (D-51/D-52): evaluate authorised OpenAI Sign in with ChatGPT using
  Responses and refresh-token handling without schema changes. Consumer OAuth
  and network/HTTPS deployment remain unimplemented; subscription entitlement
  and provider policy must be verified when that work is undertaken.


- R1 amendment / Chapters 3–4 and state diagrams (D-47): replace the old
  production-ready outcome with checks_passed for strict automatic scan-clean
  plus valid validation only. Human approval is engineer_approved, rejection is
  rejected, and unresolved decisions remain pending_review. Specify mandatory
  reviewer name/reason, application UTC time and self-declared identity under
  shared-key authentication; disclose unauthenticated local review explicitly.
  No static or human label proves successful cloud deployment. Migration 0004
  preserves immutable historical events and reports category counts; unverifiable
  success claims return to review. Show legacy-label interpretation in readers.
- Chapters 4–5 (D-49): add hashed, revocable HttpOnly sessions, login/logout,
  Origin/Host checks, 30-minute idle / 12-hour absolute expiry, SSE heartbeat
  activity and the localhost-only guarded open-mode launcher. Shared-key login
  authenticates access, not an individual engineer's self-declared identity.
- R2 / policy appendix (D-48): list every versioned parsed-resource condition,
  equivalent IDs, justification, references and conservative omissions. Strict
  alone controls labels and template acceptance; contextual-v1 is an adjacent
  experimental assessment requiring supervisor approval before reported use.
- Chapter 6 (D-46/D-48): A3 and B are incomplete provider-usage-limited
  measurements, not complete matched benchmark sets. Reclassification preserves
  strict/contextual 1/29 and 1/29 (A3), 1/9 and 1/9 (B), with 4/24 missing
  variants respectively. Attribute rapid failures to typed provider usage_limit.
  Complete fixer format-failure baselines are unavailable; the partial B excerpt
  is 14/22 non-quota invalid_json/prose_before failures, not a complete-run rate.
  Do not treat proposal counts as attempts or mocked strict-wire tests as a
  real-provider reliability gain. Explain the Terraform-JSON scanner artifact,
  native-HCL correction, account/key credit guard and stopped-run ledger.

- Chapter 4 / D-46: append the schema-versioned attribute and supporting-template
  tables, configuration-derived subnet intent, focused calls, existing-file edit
  recovery and dependency-group partial acceptance under unchanged guards/budgets.
  Include native syntax acceptance, lexer normalization, provisional generation
  recovery, deletion checks against unchanged consumers and stage/action provenance.
  Add content-specific declaration completion after syntax recovery, cached parsing,
  complete iteration deadlines and source-free completeness diagnostics (default
  three package attempts; prompt v9).
- Chapter 6 / D-46: compare the preserved 9e real baseline (1/40 ready; 35 with
  blockers; 16 accepted / 61 unchanged / 77 rolled-back iterations) with separate
  author-run 9f gpt-oss and Haiku-class fixer measurements. Keep stub/rehearsal,
  scripted recovery (4 normalized / 3 retained) and real quality evidence distinct;
  include near misses, introduced template blockers, timings and model settings.
  Add the benchmark-A corrective replay separately (3 deterministic + 8 scripted
  recoveries); disclose prompt v7/v8 and recovery changes in any real comparison.
  Keep A2's 1/36 generated / six missing variants and five concurrent-cohort PR-05
  failures distinct from the 31-variable offline repair replay. Report isolated
  and concurrent PR-05 views without changing the aggregate verdict, and disclose
  the subsequent v9/three-attempt setting change in matched author comparisons.


- Chapter 4 / D-45: tool-grounded generation, scanner fixes and repair; offline
  versioned schemas, syntax/validity ordering and bounded workspace reuse.
- Chapter 6 / D-45: compare 9d and 9e using actual timing, rollback/deadline
  causes and production-ready counts; never infer missing historical origins.

- Chapter 4 / D-44: add Validator feedback into the shared remediation path;
  describe deterministic declarations, bounded pre/post-security repair,
  rollback acceptance and final validation/security confirmation. Readiness and
  validator meanings remain unchanged; engineer Retry keeps its policy.
- Chapter 6 / D-44: report the original 1/36 production-ready baseline and six
  missing variants; author measures the after-change rate/runtime using the same
  16,000-token/140-second generator overrides. Do not substitute stub outcomes
  for real quality measurements.

- Chapter 6 / Phase 9c: the first real benchmark failed for generator output
  reliability on larger plans. Four usable runs of eight had a 189.81s median;
  three settled failures and one incomplete run cost $4.940978 in measured
  total. Larger ~4.5–5.5K-character plans produced 10–19K-token failed answers,
  taking 70–138s or timing out. Describe the 8,000-token budget, closed strict
  wire schema, whole-object-first parser, counted safe salvage and reason-only
  retries. Internal code fences could have caused false multiple_blocks errors,
  but absent raw outputs prevent proving individual historical cases. Explain
  the author's 150/270/270 attempt/generator/completion settings, last-assignment
  duplicate-key behavior, authenticated effective-settings evidence and PR-05's
  unchanged 150-second threshold. Post-change real outcomes remain unmeasured.

- Phase 9 / NFR-01: describe the standard-library working-tree/ref/reflog scanner,
  exact placeholders/canaries, safe location-only findings and D-42 limitations.
- NFR-04 still names tfsec 1.x: update to the installed/pinned Trivy version (D-31).
  Clean Ubuntu deployment evidence remains Phase 10, not an inferred Phase 9 pass.
- PR-03 distinguishes free stub overhead rehearsal from author-run real-provider
  measurements. Use the isolated identical-prompt baseline for the <=1.5x check;
  PR-01 exact-prompt medians are secondary references and never change the verdict.
- Cost method: OpenRouter lifetime key-usage deltas and effective remaining-credit
  budgets; no token-price estimates. Concurrent cost is a measured cohort total
  and total/3 average, with individual costs not attributed. Document max(reserve,
  2H, 4.5H) cohort admission and informational first-cost affordability projection.
- Phase 9 reports collect annotations and measured samples, not inferred coverage
  or author final results. PR-01 ends at API-confirmed settlement; PR-02 separately
  measures live server-event-to-DOM latency. Missing metrics remain unknown.



- Figure “Comparison panel”: replace the composite security score with first
  automated blocking findings → remaining blocking findings, accepted fixes in
  retained sessions and outcome (D-39). Include MEDIUM under the actual policy;
  unavailable/omitted history must not be treated as zero.
- Screen 4 diff annotations use only security rule IDs linked to the exact file
  by retained fix records, never every finding's IDs. Validation-only fixes may
  have no security rule IDs; their check IDs stay in the report tab (D-39).
- Screen 4 has accessible “Security fixes” and “Validation report” tabs, including
  passed/failed/warning/skipped labels and file/line links (FR-UI-05).
- PR-02 development method: correlate each badge data-seq mutation with the
  persisted event's UTC timestamp; use MutationObserver oldValue records to
  reconstruct multiple changes within one callback. Require observed live
  transitions for every stage; exclude historical replay; retain samples/max/
  median. Latest development result: 32 samples, max 663ms, median 165.5ms.
  These are Phase 8 checks; final measurements remain Phase 9.
- Stage durations use the union of active timestamp intervals across variants
  and retries, excluding idle review gaps; elapsed timers never poll the API.

- Frontend build requirement: "Node.js 22.22 or later (developed on Node 24 LTS)";
  operational package minimum is 22.22.2. Appendix A should list React 19.3.0,
  Vite 8.3.1, TypeScript 6.0.3 and the exact package.json/package-lock.json pins,
  with plain CSS replacing the standing React 18/Tailwind description (D-40).
- Document the derived results retry_in_progress boolean, EOF snapshot
  settlement rule and five-attempt EOF reconnect cap (D-40; implemented in section 2).
- Explain the external-CSS dark colour scheme under self-only style CSP (D-40).
- Authentication: X-API-Key header, open-when-unset rule and fetch-based SSE (D-36).
- Download ZIP includes a readiness file, “Labelled at” event timestamp and static-deployability caveat.
- ERD: new column review_retry_started_at (nullable TIMESTAMPTZ, D-38).
- Package diagram: guarded review-retry scanning/validating abort arrows to pending_review.
- Review body: target_files, feedback_needs_target/nothing_to_retry and terminal-run gate.
- Revise the artifact-validation table: deterministic built-ins for Kubernetes,
  Nginx, Jenkins and Grafana; keep `promtool`, `hadolint`, `helm lint` and
  `ansible-lint`. Explain why kubectl dry-run, Jenkins pipeline-model-converter,
  nginx testing and Grafana CLI integration need unavailable runtime services
  or executables and are out of scope (D-35).
- FR-V-02 flags naming mismatches as warnings. Document normalization, token
  boundaries, suffix rules and conservative artifact applicability (OQ-10).
- FR-V-03 uses the offline provider mirror and real provider-schema validation;
  distinguish this from the Phase 5b syntax-only gate. Document required-tool
  skips, failure precedence and whole-stage aborts.
- Update Appendix A: Terraform 1.16.4, Helm v4.3.0+gbec5b06, hadolint 2.15.1,
  promtool 3.15.0 and ansible-lint 26.9.0. List linux_amd64 providers AWS 5.100.0
  and 6.68.0, random 3.9.1, Kubernetes 2.38.0, Helm 2.17.0, TLS 4.4.1 and null
  3.3.2, with committed lock hashes/signature evidence and the 373.56 MiB mirror.
- Show the versioned ValidationReport, file-linked retry targets, row-locked
  persistence before events, three-command concurrency limit and 120-second
  stage deadline. Option C now permits a complete stub run to reach success.
- Record D-33's hybrid generation/remediation evidence and MEDIUM blocking;
  D-34 adds optional cached-input metrics with caching off by default, without
  a paid experiment or cache-aware price claims.
- Report the Phase 6 original-package evaluation: 2 valid, 10 invalid, 0 error;
  both known gpt-oss syntax failures detected. Static validation still misses
  Aurora clusters without instances and does not prove deployability.
- Explain the safe rejection reason taxonomy, lenient descriptive fix
  metadata with strict file validation, and the per-agent fixing model
  override. Evaluation should compare generator and fixing models separately
  and price remediation tokens using the latter.
- Explain the `TERRAFORM_SYNTAX` critical finding, the syntax-limited scan
  status, and the full rescan after repair. Note that Checkov 3.3.21 reported
  zero parsing errors on the invalid `locals "x" { a = 1 }` fixture. Trivy
  silently skipped it; filtered Terraform validate detects it (D-31 supersedes
  the old tfsec implementation).
- In FR-S-02, state the HIGH/MEDIUM/CRITICAL remediation threshold and the
  advisory policy; in FR-S-04, state the bounded advisory sample and diff.
- In FR-G-05, define zero Checkov HIGH/CRITICAL first-scan findings as the
  pass criterion, and report Trivy, Terraform and combined counts as diagnostics.
  Historical tfsec reports preserve their original attribution.
- FR-S-01 and NFR-04 name tfsec 1.x; update them to Trivy v0.69.3 (D-31).
- Update Appendix A with Checkov 3.3.21 (exact installation pin
  `pipx install "checkov==3.3.21"`), Trivy v0.69.3, and Terraform v1.16.4.
  Record Helm scanning without Helm and tfsec's maintenance status.
- Add one sentence on the malicious Trivy v0.69.4 supply-chain incident
  (CVE-2026-33634), version pinning and author-confirmed release checksum.
- Add one sentence on process-group termination and bounded pipe cleanup
  as robustness measures (D-32). Checkov's interleaved drain is published
  upstream 3.3.21 code, verified against its PyPI wheel, not a customization.
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
  cluster without instances. Historical Phase 5 structural checks, Checkov,
  tfsec (superseded by Trivy in D-31), and implemented
  Phase 6 Validator checks do not detect this; human review remains necessary.
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
- PR-05 / per-attempt timing: state the per-agent timeouts (CL-06),
  author-confirmed first-run 270-second overrides and the retained-valid-late
  validation exception with explicit deadline flags/overrun evidence (D-43).
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
