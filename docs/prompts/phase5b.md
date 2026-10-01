# Codex task — Phase 5b: scanner hang fix and migration from tfsec to Trivy

You are starting a **fresh session**. First read:
- `AGENTS.md`;
- `docs/design-deviations.md`;
- `docs/IMPLEMENTATION_LOG.md`, especially all Phase 5 entries;
- `docs/prompts/phase5.md`, which describes the original Phase 5 design.

Phases 0–5 are complete. This task changes **only** the scanner layer and what
depends on it. Keep every other behaviour.

## Background (what you need to know)

The SecurityAgent (Phase 5) scans each package with **Checkov 3.3.21** and
**tfsec v1.28.14**:
- the scans run concurrently, through `RealToolRunner` in `app/scanners/`;
- findings are classified by the severity policy in `app/security/policy.py`;
- blocking findings go to a per-file LLM fix loop;
- tfsec HCL parse errors become CRITICAL `TERRAFORM_SYNTAX` findings, which the
  loop repairs. This matters, because **Checkov 3.3.21 does not report
  Terraform syntax errors** (it was verified to report zero parsing errors on
  invalid files).

Two changes are needed.

**A. A real bug, found in an evaluation run.**
- A Checkov scan hung on a `kubernetes_monitoring` package during a post-fix
  rescan.
- The 120 s timeout called `process.kill()`, which killed **only** the main
  Checkov process.
- A **forked Checkov worker** (same command line, re-parented to PID 13)
  survived and kept the stdout pipe open.
- `RealToolRunner` then blocked forever in an unbounded `await
  process.communicate()` after the kill.
- The evaluation hung for 28 minutes. In a real pipeline, this freezes a
  package indefinitely.

**B. The author decided to replace tfsec with Trivy.** tfsec is in
maintenance mode, and Trivy's `trivy config` is its official successor, with
the same rule library and wider coverage (Kubernetes, Helm, Dockerfile).

**Trivy installed on the author's machine:** **v0.69.3**. It was pinned and
verified with the release checksum. v0.69.4 was a malicious release
(CVE-2026-33634); v0.69.2 and v0.69.3 are vendor-confirmed safe. **Do not
install, upgrade, or download any other Trivy version.** Use the installed
binary only.

Rules for this task:
- Running Checkov, Trivy and Terraform locally is allowed.
- **No real LLM calls.**
- Do not read `.env`.
- Commit after each numbered section.
- Do not push.

---

## 1. Fix the scanner hang (do this first; it applies to every tool)

In `RealToolRunner`:
1. **Start each scanner in its own session:** `start_new_session=True`.
2. **On timeout,** send `SIGKILL` to the **whole process group**
   (`os.killpg(process.pid, signal.SIGKILL)`). Ignore a
   `ProcessLookupError`.
3. **After a kill, wait for exit with a short bound** (e.g. 5 s). **Never**
   await `communicate()` or read the pipes without a timeout after a kill.
   Close the transports if needed.
4. **Return `ToolFailure(tool, "timeout")`,** and make sure the temporary
   directory is still removed.

**Regression test:**
- **A fake scanner executable** (written to `tmp_path`) forks a child that
  inherits stdout and sleeps forever, while the parent also sleeps.
- **With a 1 s timeout,** `run()` must return the timeout failure within a few
  seconds.
- **Afterwards,** `os.killpg(pgid, 0)` must raise `ProcessLookupError`, i.e.
  no process of that group survives.
- **Verify the test fails against the old kill logic,** then restore.

**Checkov parallelism:** check, in the installed Checkov 3.3.21 source or
docs, whether its parallel or forked runners can be disabled (e.g. an
environment variable such as `CHECKOV_PARALLELIZATION_TYPE`; confirm the
exact name and values).
- **If it's supported,** set it in the scanner's minimal environment. Measure
  the scan time on the recorded fixtures and on one committed Phase 3
  `kubernetes_monitoring` package, before and after.
- **Either way,** record the result.

**Progress and diagnostics in `backend/scripts/eval_security.py`:**
- **Print one progress line per package and per scan to stderr:** the package,
  iteration, tool, and duration or timeout.
- **Record any scan timeout** with the package, iteration and tool in the
  results.
- **Add `--packages-limit N`** for quick runs.

## 2. Replace tfsec with Trivy

**Command.** Confirm every flag with the installed `trivy config --help`:

```
trivy config <dir> --format json --exit-code 0 --quiet --skip-check-update --cache-dir <per-scan temp dir>
```

- **`--skip-check-update`** (or the installed version's equivalent) makes
  Trivy use its **embedded** checks bundle, so scans are deterministic and
  need no network. **Confirm that a scan works with no network access.** If
  the installed version needs a different flag or setting to avoid
  downloading checks, use that, and document it.
- **The cache dir** lives inside the scan's temporary directory, so nothing
  persists between scans.
- The same minimal subprocess environment as the other tools: **no secrets**
  (NFR-01, already tested by the canary; extend it to Trivy).

**Parser (`app/scanners/trivy_parser.py`).** Trivy JSON has `Results[]`, each
with `Target`, `Class`, `Type`, and `Misconfigurations[]`. Each
misconfiguration has:
- `ID` / `AVDID`;
- `Title`, `Message`, `Resolution`;
- `Severity`, `Status`;
- `PrimaryURL`;
- `CauseMetadata.{Resource, StartLine, EndLine}`.

Keep only `Status == "FAIL"`. Map them to `Violation` objects:
- `tool="trivy"`;
- `rule_id` = the AVD ID;
- the severity, mapped directly;
- the package-relative path, from `Target` normalised against the temp root,
  validated with the Phase 0 path rules;
- the lines and resource.

Handle Results without misconfigurations, and an empty `Results`.

**Terraform syntax errors.** This keeps the Phase 5 guarantee.
- **Test with the existing syntax-error fixture**
  (`backend/tests/fixtures/security/syntax_error/`) whether Trivy v0.69.3
  reports HCL parse errors, and how: an error exit, a message, or a result.
- **If Trivy surfaces them,** convert them into the existing CRITICAL
  `TERRAFORM_SYNTAX` finding (tool `trivy`), with the package-relative path
  and line.
- **If Trivy skips invalid files silently** (as Checkov does), add a
  **syntax pre-check** using the installed Terraform, which parses HCL without
  `init`:
  - for example `terraform fmt -check -recursive -no-color <dir>/terraform`
    (verify the behaviour);
  - distinguish **parse errors** from "file needs formatting" output; only
    parse errors produce `TERRAFORM_SYNTAX` findings (tool `terraform`);
  - formatting differences are ignored.
- **Either way:** add a real-tool test proving that the syntax-error fixture
  yields a `TERRAFORM_SYNTAX` finding, and keep the existing fix-loop test for
  syntax repair.

**Helm.** Check whether Trivy v0.69.3 scans Helm charts **without** the `helm`
binary.
- **If it does,** record that this closes the Checkov Helm gap (CL-07).
- **If not,** keep CL-07 as it is.

**Policy (`app/security/policy.py`, `SECURITY_POLICY_VERSION = "2"`).**
- **Severity:** Trivy supplies severities directly. Remove the tfsec handling;
  the Checkov severity map is unchanged.
- **Variant exemptions:** replace every tfsec long ID with the matching Trivy
  AVD ID. For example, RDS Performance Insights and enhanced monitoring.
  Confirm each ID against the installed embedded checks (`trivy config` output
  on a fixture that triggers it), not from memory.
- The rule that **security checks are never exempted for the security
  variant** is unchanged.

**Everything else that names tfsec:**
- the tool enum and values;
- the scan step (Checkov and Trivy run concurrently; plus the Terraform
  syntax pre-check, if added, concurrently as well);
- version capture;
- `/api/health` (`scanners.trivy`, plus `terraform` if the pre-check is used);
- the startup warning;
- the `security_report` keys: `first_scan_tfsec_high_or_critical` becomes
  `first_scan_trivy_high_or_critical`. Old stored reports may still contain
  the tfsec key; the readers and the eval must tolerate both;
- the eval script columns and aggregates;
- the README install instructions (below);
- comments and docstrings.

Remove the tfsec runner and parser code, and their fixtures, once nothing uses
them.

**Fixtures.**
- Re-capture **real** Trivy JSON for the vulnerable, fixed and syntax-error
  fixtures with v0.69.3.
- Normalise the paths with the existing `normalize_security_fixture.py`,
  extending it for Trivy's `Target` and paths.
- Update the fixture README with the tool versions and exact capture commands.
- The tests must stay path-independent (the Phase 5 portability fix).

## 3. Tests

- **The parser:**
  - the recorded vulnerable output gives the expected AVD IDs, severities,
    lines and relative paths;
  - the fixed output has no blocking findings;
  - empty results;
  - malformed JSON becomes a scan error;
  - `Status` other than `FAIL` is ignored.
- **The policy:**
  - the Trivy-ID exemptions apply to their variant only;
  - none apply to the security variant.
- **The loop and orchestrator:** the existing behaviour, re-run with Trivy
  recordings: clean, fixed in one or two passes, exhausted, no progress, the
  syntax repair, the retry sessions.
- **Real tools** (the existing `scanners` marker; it now requires Checkov,
  Trivy, and Terraform if the pre-check is used; skip if missing):
  - the vulnerable fixture shows the expected findings from both tools;
  - the syntax-error fixture gives `TERRAFORM_SYNTAX`;
  - **a scan works with network access disabled** (minimal environment, no
    proxy; assert there are no download attempts or errors).
- **The canary:** the Trivy subprocess environment contains no canary key and
  no database URL.
- **The hang regression test** from section 1.

## 4. Evaluation

Run `make eval-security EVAL_ARGS="--scan-only"` on the committed Phase 3
packages (local tools only, no LLM). Commit the report under
`docs/evals/phase5b-security-<timestamp>/`.

In the implementation log, compare it with the last tfsec-based scan-only
report:
- the blocking counts per package;
- the HIGH/CRITICAL counts per tool;
- whether the two gpt-oss packages still show `TERRAFORM_SYNTAX`;
- any package whose results changed a lot, with the likely reason.

## 5. Documentation

- **New deviation entry:** "tfsec replaced by Trivy v0.69.3", with:
  - the reason (maintenance mode; Trivy is the official successor with the
    same rule library);
  - the version pin and checksum verification, referencing CVE-2026-33634 and
    the malicious v0.69.4;
  - embedded checks with `--skip-check-update` (deterministic and offline);
  - the syntax-error handling chosen;
  - the Helm result.
- **New deviation entry:** "scanner timeout terminates the whole process
  group", covering the incident, the root cause (forked workers holding the
  pipe), the fix, the regression test, and the Checkov parallelism finding.
- **Update** D-22, D-25, CL-07, and every tfsec mention in
  `design-deviations.md`. Historical entries keep their wording, with a note
  "superseded by …" where relevant.
- **"Thesis text to update", add:**
  - FR-S-01 and NFR-04 name tfsec 1.x; they become Trivy v0.69.3;
  - Appendix A tool versions: Checkov 3.3.21, Trivy v0.69.3, Terraform
    v1.16.4;
  - one sentence on the supply-chain incident and version pinning;
  - one sentence on process-group termination as a robustness measure.
- **README:**
  - replace the tfsec install with the pinned, checksum-verified Trivy install
    below, and note that installs via `get.trivy.dev`, apt/rpm, or "latest"
    must not be used for reproducibility;
  - update the health output description.
- **Implementation log:** entry with real test counts, including the number
  of skipped scanner tests if any.

**README install snippet** (it must match what the author ran):

```bash
V=0.69.3
cd /tmp
curl -fsSLO https://github.com/aquasecurity/trivy/releases/download/v${V}/trivy_${V}_Linux-64bit.tar.gz
curl -fsSLO https://github.com/aquasecurity/trivy/releases/download/v${V}/trivy_${V}_checksums.txt
grep " trivy_${V}_Linux-64bit.tar.gz$" trivy_${V}_checksums.txt | sha256sum -c -
tar -xzf trivy_${V}_Linux-64bit.tar.gz trivy
sudo install -m 0755 trivy /usr/local/bin/trivy
trivy --version
```

## 6. Out of scope

- The ValidatorAgent (Phase 6).
- Endpoints and frontend.
- Changing the fix-loop logic or severity thresholds.
- Real LLM calls.
- Installing or upgrading Trivy, Checkov or helm.

Finish with the summary format from `AGENTS.md` §10, and state explicitly:
- whether Trivy reports syntax errors and which approach you used;
- whether Trivy scans Helm without the helm binary;
- whether Checkov parallelism could be disabled.
