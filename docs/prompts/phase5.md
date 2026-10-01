# Codex task — Phase 5: SecurityAgent (scanning and autonomous remediation)

Read `AGENTS.md`, `docs/design-deviations.md` and `docs/IMPLEMENTATION_LOG.md`
first. The specification is in `docs/spec/`. This task is **Phase 5 only**.
Phases 0–4 are complete. Reuse their components; do not re-implement them.

## Goal

Replace `UnavailableSecurityStage` with the real **SecurityAgent**. It must:
1. scan each package with **Checkov and tfsec concurrently**;
2. classify findings by a **documented severity policy**;
3. fix **blocking** findings with **one LLM call per affected file**, with the
   files fixed in parallel;
4. validate every fix and apply it;
5. rescan until the package is clean or the iteration limit is reached;
6. store every iteration's report and one cumulative unified diff.

This is thesis contribution **C2**.

Relevant spec:
- **FR-S-01 to FR-S-07;**
- FR-S-09: the retry entry point only. The endpoint comes in Phase 7;
- FR-G-05 ("zero HIGH" on the first scan, measured);
- PR-01;
- the package state machine, and **CL-01**: the iteration limit is checked in
  `remediating`;
- the class diagram: `SecurityAgent.remediate(package, violations, feedback,
  validation_failures)`;
- NFR-01.

**Installed on the author's machine** (WSL), and recorded for Appendix A:
- Checkov **3.3.21** (installed with pipx);
- tfsec **v1.28.14** (in maintenance mode; it prints a "joining the Trivy
  family" banner);
- Terraform v1.16.4.

## Decisions already made by the author (do not revisit)

1. **Severity policy.**
   - **Blocking** findings (CRITICAL, HIGH, MEDIUM) are remediated.
   - **Advisory** findings (LOW, unmapped Checkov checks, and per-variant
     exemptions) are reported but never block a package.
   - tfsec provides severities itself. Free Checkov does not, so a curated
     table maps common Checkov check IDs to severities, and unlisted Checkov
     checks are advisory (LOW).
   - This reinterprets FR-S-02's "every violation" as "every violation at or
     above the policy threshold". Record it as a deviation, with the
     reasoning.
2. **Per-file remediation.** There is one fix call per affected file,
   carrying all of that file's blocking findings. Files are fixed
   concurrently. Untouched files stay byte-identical. A fix may add a few new
   files, e.g. `kms.tf`.
3. **Two-layer tests.**
   - Most tests use **recorded real scanner JSON**, captured once with the
     installed tools and saved as fixtures.
   - A few tests run the real tools, and **skip automatically** if the tools
     aren't installed.

## Definition of done

- `make test` and `make lint` pass.
- The scanner-dependent tests pass on the author's machine, and skip cleanly
  where the tools are missing.
- With `LLM_PROVIDER=stub`, `make run` plus `make run-pipeline` shows real
  scanning and settles the run as `partial_success`. That's honest, because
  validation is still a placeholder (section 8).
- `make eval-security --scan-only` works on the committed Phase 3 packages.
- Docs are updated per `AGENTS.md` §8.

Commit after each numbered section. Do not read `.env`. **No real LLM calls.**
Running the installed Checkov and tfsec locally **is allowed**: they are local
programs, and you need them to capture fixtures.

---

## 1. Findings model and severity policy (`app/security/`)

**Extend `Violation`** (`app/domain/models.py`). It stays backwards compatible,
with every new field optional or defaulted:
- `severity: Severity`, a StrEnum: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`,
  `UNKNOWN`;
- `line_start: int | None` and `line_end: int | None`, for FR-S-04;
- `title`, a short check name;
- `guide_url: str | None`;
- `blocking: bool`, set by the policy;
- `advisory_reason: str | None`. It is one of `low_severity`,
  `unmapped_checkov`, or `variant_exemption:<reason>`.

`fingerprint()` stays `(rule_id, file_path, resource)`. Update the existing
tests and fixtures.

**Policy (`app/security/policy.py`), versioned as `SECURITY_POLICY_VERSION =
"1"`:**
- `BLOCKING_SEVERITIES = {CRITICAL, HIGH, MEDIUM}`.
- **`CHECKOV_SEVERITY`:** a curated mapping of ~40–60 common Checkov check IDs
  to severities. It covers:
  - AWS: S3 public access and encryption, RDS encryption and public access,
    security group ingress from `0.0.0.0/0` on sensitive ports, IAM wildcard
    actions and resources, EBS/EFS encryption, ALB HTTPS/TLS, CloudTrail and
    logging, secrets in plain text, EKS public endpoint;
  - Kubernetes: privileged containers, run-as-root, `allowPrivilegeEscalation`,
    host network/PID, missing resource limits;
  - Dockerfile: no `USER`, `latest` tags.

  **Assign severities consistently with tfsec's equivalents where one exists,**
  and document the source of each assignment in a comment. Unlisted Checkov IDs
  get `UNKNOWN`, and are advisory (`unmapped_checkov`).
- **`VARIANT_EXEMPTIONS`:** a short documented list of `(variant, rule_id or
  tfsec long ID, reason)` entries for checks that contradict a variant's
  directive. They are reported as advisory for that variant only. At least:
  - **cost:**
    - cross-region replication (`CKV_AWS_144`);
    - RDS multi-AZ;
    - RDS Performance Insights and enhanced monitoring (Checkov and tfsec
      IDs);
    - "S3 encrypted with KMS by default" (`CKV_AWS_145`), where SSE-AES256 is
      present;
  - **performance:** cross-region replication.

  Keep the list minimal and justified: security checks are never exempted
  from the **security** variant.
- **`classify(violations, variant) -> list[Violation]`** sets `blocking` and
  `advisory_reason`.
- **Deduplicate:** when both tools report the same issue on the same
  resource, keep both records. Group them for remediation, so the fix call
  sees them together.

## 2. Scanner runner (`app/scanners/`)

- **A `ToolRunner` protocol,** `async run(tool, workdir) -> ToolResult`
  (stdout, stderr, exit code, duration). There are two implementations:
  - the real one, using `asyncio.create_subprocess_exec`. **No shell.** It
    uses a per-call timeout (`SCANNER_TIMEOUT_SECONDS`, default 120);
  - a **recorded** one for tests.
- **Subprocess environment (NFR-01):** pass a **minimal environment**, i.e.
  PATH, HOME, LANG, and the variables each tool needs. **Never** pass
  `LLM_API_KEY`, the database URLs, or any other application secret to a
  scanner process. Test this with the canary.
- **Commands.** Verify the flags against the installed versions' `--help`, and
  confirm the tools run **without network access**:
  - **Checkov:** `checkov -d <dir> -o json --quiet --compact
    --skip-download` (plus whatever framework flags are needed for terraform,
    kubernetes, helm, and dockerfile).
    - Checkov's helm framework needs the `helm` binary. If it's absent, helm
      charts are not scanned by Checkov. **Record that limitation;** don't
      install helm.
    - The output is either a single report object or a list (one per
      framework). Handle both.
  - **tfsec:** `tfsec <dir> --format json --no-color --soft-fail`.
    - tfsec exits non-zero when it finds problems unless `--soft-fail` is
      given. Treat valid JSON as success either way.
    - **The Trivy banner:** check whether it reaches stdout in JSON mode. If
      it does, extract the JSON robustly.
- **Parsers** (`checkov_parser.py`, `tfsec_parser.py`) produce `Violation`
  objects:
  - paths normalised to **package-relative** POSIX paths, with no temp-dir
    prefixes, validated with the Phase 0 path rules;
  - line ranges included;
  - the resource name included;
  - tfsec severity mapped directly;
  - Checkov severity taken from the policy.
- **The scan step:**
  1. write the package files to a fresh `TemporaryDirectory`;
  2. run both tools **concurrently** (FR-S-01);
  3. parse, then classify;
  4. clean up.

  If either tool crashes, times out, is missing, or produces unparseable
  output, **retry the whole scan once**. A second failure is a **scan error**
  naming the tool and the category, never raw stderr in user-facing messages.
- **Version capture:** record each tool's version once at startup and include
  it in reports. Add `scanners: {checkov: {"available": bool, "version":…},
  tfsec: {…}}` to `/api/health`. The health check stays 200 even when the
  scanners are missing.

**Fixtures** (`backend/tests/fixtures/security/`):
- a small **known-vulnerable** package with:
  - a public S3 ACL and no encryption;
  - an RDS instance that's unencrypted and `publicly_accessible`;
  - a security group allowing `0.0.0.0/0` on port 22;
  - an IAM policy with `"Action": "*"`;
  - a Kubernetes Deployment with a privileged container running as root;
- the same package **fixed**;
- the **real JSON outputs** of both tools for both, captured with the
  installed versions. Note the versions and the capture commands in a fixture
  README.

## 3. Fix generation (`app/agents/security/`)

**`FixAgent`, one LLM call per file,** using `complete_json` with overrides:
- `deadline` = what remains of the package's security budget;
- `attempt_timeout = FIX_ATTEMPT_TIMEOUT_SECONDS` (default 90);
- `max_output_tokens = FIX_MAX_OUTPUT_TOKENS` (default 16000).

**The prompt** (`app/agents/prompts/security_fix.py`, `SECURITY_FIX_PROMPT_VERSION
= "1"`):
- **The system rules:**
  - fix **every listed finding** in this file, and change nothing else;
  - preserve the plan's service names and the variant's intent. **Include that
    variant's `optimisation_directive` text**, taken from the generator
    classes;
  - **never add suppression annotations** (`checkov:skip`, `tfsec:ignore`,
    `trivy:ignore`, `#nosec`, and similar);
  - never hardcode secrets;
  - new files only when needed (at most 3), within the package layout and the
    plan's file types;
  - output only `{"file": {"path":…, "content":…}, "new_files": {path:
    content}, "fixes": [{"rule_id":…, "resource":…, "summary": ≤200 chars}]}`.
- **The user prompt:**
  - the numbered findings: rule, severity, resource, lines, title;
  - the file content, wrapped in tags carrying a **random per-call nonce**,
    e.g. `<file_content id="7f3a…">`, and declared as data. **Do not alter the
    file content.** Neutralising `<` would corrupt code; the nonce prevents
    early tag closing instead;
  - on a review retry (FR-S-09): the engineer's feedback and the failed
    validation checks, in their own tagged sections.

**Fix validation:** a fix is **rejected** (recorded with its reason, the
original file kept, and the findings left in place) if:
- the path differs from the requested one;
- the content is empty;
- it **adds** a suppression annotation not present before (match
  case-insensitively against the known patterns);
- a new file breaks the layout or adds an unplanned type;
- the whole package after the change fails `package_structure_errors`;
- the size limits are exceeded;
- the LLM call fails (`llm_failure`).

## 4. The remediation loop (`app/agents/security/agent.py`)

**`SecurityAgent`** implements the Phase 4 `SecurityStage` protocol. Extend
`StageContext` with the run's `max_iterations`, taken from the resolved run
config.

**The loop, using only legal transitions through `ctx.writer`:**
1. **`generated → scanning`, then scan.**
   - On a scan error (after the retry), go to `scan_error`.
   - With no blocking findings, go to **`scan_clean`**. Advisory findings may
     remain.
   - Otherwise go to **`remediating`**.
2. **In `remediating`, the CL-01 budget check.** Call
   `remediation_budget_decision(iteration_count, max_iterations)`.
   - If the budget is used up, go to **`scan_exhausted`**.
   - Also go to `scan_exhausted` (reason "no progress") **if the set of
     blocking fingerprints is identical to the previous iteration's, or
     repeats an earlier set.** That's convergence detection.
   - Also go to `scan_exhausted` (reason "time budget") **if the security
     budget (`SECURITY_DEADLINE_SECONDS`, default 240) is nearly used up**.
3. **Otherwise, run one fix pass.**
   - Group the blocking findings by file, and fix those files concurrently,
     limited by `SECURITY_MAX_PARALLEL_FIXES` (default 4).
   - Validate and apply the fixes.
   - Record the iteration's per-file unified diff.
   - Increment `iteration_count`.
   - Go to **`scanning`** and loop.
4. **When the package leaves the loop** (`scan_clean`, `scan_exhausted` or
   `scan_error`), persist the results in one repository call:
   - the **final files**, i.e. the remediated version;
   - `security_report`;
   - `remediation_diff`, the cumulative unified diff from the original files
     to the final files, across all files (FR-S-06);
   - `iteration_count`.

   Add `PackageRepository.save_security_results(...)`.

**The `security_report` JSON** is bounded and versioned:

```
{ "policy_version", "prompt_version", "tools": {checkov: version, tfsec: version},
  "iterations": [ { "index", "scan": { "blocking": [...], "advisory_count", "advisory_sample": [≤20],
                                        "counts_by_severity", "tool_status" },
                    "fixes": [ { "file", "rule_ids", "accepted", "reason"?, "summaries", "new_files" } ],
                    "diff": "<per-iteration unified diff, capped>" } ],
  "final": { "outcome": "clean|exhausted|error", "reason", "remaining_blocking": [...],
             "first_scan_high_or_critical": int } }
```

Cap the large fields, and include the counts when you truncate.
`first_scan_high_or_critical` makes FR-G-05 measurable.

**Events:**
- `agent_state` for `security`;
- package transitions;
- one `stage_notice` per iteration with `{iteration, blocking_by_severity,
  advisory_count, fixes_accepted, fixes_rejected}`. **No file contents** in
  any event.

**The retry entry point** (FR-S-09, used by Phase 7):
- `SecurityAgent.remediate_from_review(ctx, variant, package, feedback,
  validation_failures)` resets `iteration_count` to 0;
- it moves `pending_review → remediating` and runs the same loop, with the
  feedback and validation failures included in **every** fix prompt of that
  loop;
- test it with the stub. The endpoint itself is Phase 7.

## 5. Wiring

- `create_app` uses the real `SecurityAgent` instead of
  `UnavailableSecurityStage`. **Delete `UnavailableSecurityStage`,** and update
  D-20 (the placeholder has been removed).
- The `AgentFactory` gains `create_security_agent(run_config)`, so remediation
  uses the run's provider and model.
- **If the scanners are missing at runtime,** the scan fails, then fails again
  on retry, so the package goes to `scan_error` with "checkov is not
  installed" (or tfsec). Log one warning at startup.
- **Add new settings to `.env.example` and the README:**
  - `SECURITY_DEADLINE_SECONDS`;
  - `SCANNER_TIMEOUT_SECONDS`;
  - `FIX_ATTEMPT_TIMEOUT_SECONDS`;
  - `FIX_MAX_OUTPUT_TOKENS`;
  - `SECURITY_MAX_PARALLEL_FIXES`.

## 6. Tests

- **Recorded runner (most tests):** use the fixtures and a scripted
  `FixAgent` stub. Tag tests with `req` markers.

**Parsers:**
- both tools' recorded outputs, from vulnerable and fixed packages;
- Checkov list-or-object output;
- tfsec JSON with the banner present;
- path normalisation (no temp prefixes);
- line ranges;
- severity mapping;
- malformed output becomes a scan error.

**Policy:**
- the blocking/advisory classification;
- an unmapped Checkov check is advisory;
- variant exemptions apply only to their variant;
- **a security check is never exempted for the security variant.**

**Loop:**
1. **Clean on the first scan:** `scan_clean`, no LLM call, an empty diff
   (`req("FR-S-01")`).
2. **A violation fixed in one pass:** rescan, then `scan_clean`. The diff
   shows the change, and the report has two iterations
   (`req("FR-S-02","FR-S-03","FR-S-04","FR-S-06")`).
3. **A violation needing two passes:** the loop runs twice and exits clean
   (`req("FR-S-03")`).
4. **Unfixable, with `max_iterations=1`:** `scan_exhausted`, the remaining
   findings recorded, and the orchestrator then reaches `pending_review`
   (`req("FR-S-05","FR-S-07")`).
5. **No progress:** the same fingerprints twice means `scan_exhausted` with
   reason "no progress", before the limit.
6. **A fix adding a `checkov:skip` comment is rejected,** the finding remains,
   and the reason is recorded.
7. **A fix touching the wrong path or breaking the layout is rejected.**
8. **Untouched files stay byte-identical,** and the cumulative diff covers
   only the changed files.
9. **A scanner crash then success** on the retry continues; **two crashes**
   mean `scan_error`, with a message naming the tool.
10. **The time budget** (fake clock): `scan_exhausted` with "time budget", and
    no fix call is started after that point.
11. **Concurrency:**
    - **both tools are invoked before any fix call**
      (`req("FR-S-01")`), instrumented;
    - fixes for 3 files run concurrently, and the semaphore is respected.
12. **Retry:** `remediate_from_review` resets the count to 0, and **the fix
    prompt contains the feedback string and the validation failures**
    (`req("FR-S-09")`).
13. **`first_scan_high_or_critical`** is computed correctly.

**Orchestrator integration:**
- a full stub pipeline with the recorded runner and validation placeholder
  ends `partial_success`, with the packages in `pending_review`;
- the events include the per-iteration notices.

**Real tools** (a `scanners` marker; skip if `shutil.which` can't find them):
- scanning the vulnerable fixture finds the expected rule IDs with both tools;
- scanning the fixed fixture finds no blocking findings;
- one run with **no network** works. Monkeypatch a minimal environment and
  assert there are no network errors.

**Canary (NFR-01):**
- the scanner subprocess environment contains no canary key and no database
  URL. Capture the environment through a fake executable;
- the reports and events contain no canary.

## 7. Evaluation script (`backend/scripts/eval_security.py`, `make eval-security`)

**Inputs:**
- `--packages`: one or more saved package directories, i.e. the committed
  Phase 3 runs' `packages/<model>/<plan>/<variant>/`. **Defaults:** the
  committed gpt-oss v3 run and the Sonnet reasoning-off run;
- `--scan-only`: free; no LLM calls;
- `--remediate`: runs the full loop with the configured LLM, so it costs
  money;
- `--max-iterations`;
- `--price-in` / `--price-out`, as in Phase 3.

**Per package, report:**
- the generator model, plan and variant;
- the first-scan **blocking counts by severity**, the advisory count, and
  `first_scan_high_or_critical` (**FR-G-05 for the security variant**);
- the top rule IDs.

With `--remediate`, also report:
- the outcome;
- iterations;
- fixes accepted and rejected (with reasons);
- the remaining blocking findings;
- elapsed time, tokens and estimated cost.

**Aggregate per generator model:** the mean blocking findings per package, the
share of packages clean on the first scan, and FR-G-05 pass/fail.

**Output:** `docs/evals/phase5-security-<timestamp>/`, containing:
- `summary.md`;
- `results.json`;
- the diffs, optionally, with `--save-diffs`.

**Verify `--scan-only` yourself** on the committed packages. That's allowed:
it uses local tools only. Commit that scan-only report.

## 8. Validation placeholder (until Phase 6)

`UnavailableValidationStage` is now reached. It must move `scan_clean` or
`scan_exhausted` → `validating` → `validation_error`, with a `stage_notice`
saying "validation is not available in this build". The orchestrator then
applies `readiness_after_validation`, which gives `pending_review` (Option C).
Runs therefore settle as `partial_success`, and no package is ever
`production_ready` before Phase 6. Update D-20's text and test this path.

## 9. Documentation

- **D-22, the severity policy:** blocking vs advisory; the curated Checkov map
  and its sources; the variant exemptions with reasons; FR-S-02 reinterpreted;
  how FR-G-05 is measured.
- **D-23:** per-file remediation, new-file limits, byte-identical untouched
  files.
- **D-24:** the suppression-annotation guard.
- **D-25:** the minimal scanner subprocess environment (NFR-01).
- **D-26:** the validation placeholder is now reached; runs end
  `partial_success` until Phase 6.
- **CL-07:** Checkov's helm scanning needs `helm`; tfsec is in maintenance
  mode (Trivy), with the versions used.
- **"Thesis text to update", add:**
  - FR-S-02's threshold wording;
  - FR-G-05's measurement;
  - the Appendix A tool versions (Checkov 3.3.21, tfsec v1.28.14, Terraform
    v1.16.4);
  - the security-report structure (Chapter 4/5);
  - `Violation`'s new fields (class diagram).
- **README:** the scanner prerequisites and install commands (pipx checkov,
  the tfsec release binary, Terraform from the HashiCorp apt repository), the
  new settings, `make eval-security` usage, and that runs now end
  `partial_success` until Phase 6.
- **Implementation log:** entry with real test counts, including how many
  tests skipped because of missing scanners, if any.

## 10. Out of scope

- The ValidatorAgent (Phase 6).
- The review, results and download endpoints (Phase 7).
- Frontend.
- Installing helm.
- Trivy.
- Real LLM calls.

Finish with the summary format from `AGENTS.md` §10.
