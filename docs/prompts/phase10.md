# Codex task — Phase 10: packaging, deployment evidence and requirement closure

Fresh session. Read `AGENTS.md`, all of `docs/spec/` (introduction,
requirements, design — **read only, never edit**), `docs/design-deviations.md`
(all entries, especially D-31, D-47 to D-61 and the validator-coverage
revision near the artifact table), the latest `docs/IMPLEMENTATION_LOG.md`
entries, the README, the Makefile, `docker-compose` files, the traceability
tooling (`backend/scripts/traceability.py`, `pytest_traceability.py`) and the
newest traceability report. Phases 0–9m are complete.

## Why

The system is feature-complete. The committee will compare the specification
with the delivered system. Close every remaining evidence gap, make the
system installable by someone other than the author, and give one honest
overview of which requirements are met, partly met, not met or unverified.

## Rules

- No real LLM calls, no `.env` reads, no installs, no downloads, no network,
  no push. You cannot build images or provision machines: write the files,
  scripts and checklists, verify them statically and with existing tools, and
  give the author exact commands to run.
- **Trivy:** any install script or Dockerfile pins Trivy **0.69.3** and
  verifies its checksum. Never reference 0.69.4 (malicious release,
  CVE-2026-33634) or an unpinned/latest version.
- Never put secrets, real keys or the master key into images, scripts,
  examples or evidence. Placeholders only.
- Readiness, blocking rules, profiles, scanners and thresholds unchanged.
  `docs/spec/` unchanged.
- Plan mode first: report the current state for every section (what exists,
  what is missing) before changing anything. One commit per section, prefix
  `phase10:`, requirement IDs, implementation-log entries with real counts.

## 0. Lesson approval policy (author decision)

Replace the self-approval flow (D-60/D-61) with this policy:

- **Admin proposals become active immediately** when they pass the
  structural checks and the current filter (v2): a new active-set version is
  created in the same transaction, recorded as `approval: admin_direct` with
  the admin's identity in the lesson, audit event, run manifest and archive.
  No separate approval step and no second confirmation.
- **Reviewer proposals always require approval by an admin**, who must be a
  different person (a reviewer can never approve).
- The exact prompt preview and the live filter result are shown **in the
  proposal form before submitting**, for admins and reviewers.
- The filter, length limits, role scoping, delimiting, output gates, kill
  switch, versioning and provenance stay unchanged; admin lessons that fail
  the filter are rejected like any other.
- Replace `LESSONS_REQUIRE_SECOND_APPROVER` with
  `LESSONS_ADMIN_DIRECT_ACTIVATION` (default `true`); `false` restores the
  previous behaviour where admin proposals also wait for approval by a
  different admin. Migrate existing records and settings additively; keep
  historical `self_approved` records readable.
- Replace the "four-eyes review is off" warning with a neutral policy note:
  "Admin lessons activate directly; reviewer lessons require admin approval."
- Update D-60 (and record the decision in a new or extended entry): admins
  are trusted operators who can already change server configuration; the
  residual risk is a mistaken or malicious admin lesson, mitigated by the
  filter, the pre-submit preview, the kill switch and full provenance.
- Tests: admin direct activation (passing and filter-rejected), reviewer
  proposal → admin approval, reviewer cannot approve, setting `false`
  behaviour, provenance in manifest and archive, Playwright for both flows.

## 0b. UI polish from the author's test (same commit series as section 0)

- **Unavailable-action hint** (D-61 gate wrapper), e.g. under "Download all
  three": today it is small grey text that receives a grey selection-style
  highlight on hover/focus. Restyle it as a proper hint: readable contrast
  in both themes, a small info icon, comfortable spacing, the outstanding
  variants as clear inline links or small secondary buttons ("Review
  Performance", "Review Security"), no text-selection look on hover/focus,
  and consistent use of the existing design tokens. Apply the same style to
  every gate hint.
- **"Propose a lesson" button** in the Review tab: today it sits wrapped
  below the decision buttons and looks cramped and disabled. Give it its own
  clearly separated row or section after a decision is recorded (short
  heading, one-line explanation, secondary button style), with consistent
  spacing and alignment next to Approve / Retry / Reject / Download ZIP.
- Keep behaviour, availability rules and accessibility unchanged. Update
  Vitest/Playwright and the 1280×800 screenshots.

## 0c. Review tab after a decision, approval categories, label colours

- **After a final decision** (`engineer_approved` or `rejected`), the
  Approve / Retry / Reject controls are currently still shown, greyed out.
  FR-UI-07 requires them to be hidden once the package is settled, with the
  ordinary download control restored. Hide them and show instead: the label,
  a compact decision summary (reviewer, time, category, reason), **Download
  ZIP** as the primary action, and the lesson section (0b). For
  `checks_passed` packages, keep Reject available as today. Tidy spacing and
  alignment of the whole decision area.
- **Approval categories:** today the D-47 categories are rejection reasons,
  so approvals end up as "other". Add a separate fixed list for approvals:
  meets requirements, accepted risk, approved with follow-ups,
  organisational exception, other. The UI offers the list that matches the
  chosen action; the API validates the category against the decision.
  Additive migration; existing decisions keep their stored category. Include
  approval categories in review history, export and feedback insights (for
  example count accepted-risk approvals and the blocking rules they
  accepted). Update D-47 and the review documentation.
- **Label colours:** `engineer_approved` uses a green style that is distinct
  from `checks_passed` (for example green outline plus a person icon versus
  solid green), `rejected` and `pending_review` unchanged; text labels stay
  so colour is never the only signal; check contrast in both themes.
- Tests: hidden controls after approve and reject, retained Reject for
  `checks_passed`, category validation per decision, export/insights counts,
  label styles; Vitest, Playwright, screenshots.

## 1. NFR-04 clean-deployment kit

- A step-by-step checklist and a script for a **clean Ubuntu 24.04**
  environment (for example a fresh, separately named WSL distribution) that
  installs only the documented prerequisites, clones the repository at a
  given revision, sets up PostgreSQL, the master key (generated locally, never
  printed), migrations, the frontend build and a **stub** pipeline run, then
  checks `/api/health` and records tool versions and outcomes into an
  evidence folder template.
- A manual browser checklist (Chrome, Firefox, Edge on Windows): login, new
  request, progress, results, review, download, settings; no plugins.
- State in the evidence template that tfsec is superseded by Trivy (D-31).
- The author will run it; leave the evidence folder for the author's results.

## 2. Containers

Dockerfiles for backend and frontend (and a compose file for the full stack
if it fits the existing setup), using pinned versions, non-root users,
no secrets in layers, scanners pinned as above, and the existing offline
provider mirror approach. Document build and run commands for the author.
Statically check them (hadolint if already installed; otherwise review).

## 3. Traceability gaps

- Link the frontend tests (Vitest and Playwright) to requirement and use-case
  IDs and include them in the traceability report. Close the gaps for
  FR-UI-02, FR-UI-03, FR-UI-04, FR-UI-05, UC-05 and UC-08; strengthen
  FR-P-02 and FR-S-06 where coverage is thin.
- NFR-02: one replacement test per agent role through the documented
  contracts without editing the orchestrator; keep the recorded
  recovery/telemetry coupling limitation honest.
- Map the specification's TC identifiers (TC-pipeline-01, TC-security-01,
  TC-ui-01, TC-generator-01, TC-perf-01, TC-adapter-01, TC-review-01) to the
  real tests and evidence in a mapping table.

## 4. Specification alignment entries

Add deviation entries (or extend existing ones) so every place where
`docs/spec/` no longer describes the system is explained:

- The introduction's non-goal "single-user prototype; multi-user
  authentication out of scope": state that D-49/D-50 supersede it, why
  (supervisor feedback on usability and API keys), and what remains out of
  scope.
- A summary entry comparing the design chapter's four endpoints and three
  tables with the final API and data model (list endpoints and tables, with
  the deviation that introduced each).
- FR-G-03, FR-G-04, FR-G-05: compute from the committed real benchmark
  evidence how often the cost variant used Free Tier/micro classes, how often
  the performance variant had Multi-AZ and autoscaling, and how often the
  security variant had zero HIGH findings on its first scan. Record that these
  are generator directives, not guaranteed properties, with the measured rates.
- Features without a specification requirement (model/thinking selection,
  credentials, preferences, contextual profiles, review categories and
  history, lessons, schema gate, benchmark tooling): list the proposed IDs
  for the author and supervisor to approve.

## 5. Evidence index

One page (`docs/evals/EVIDENCE.md`): every requirement and use case → status
(met / partly met / not met / unverified) → test types → evidence paths →
deviations. PR-03 stays **not met** unless an approved revised target exists;
NFR-04 stays **unverified** until the author's clean-deployment evidence is
committed. No status without evidence.

## 6. Demo data and README

- A reproducible demo seed (stub runs with all labels, reviews with
  categories, one approved lesson, review history) for the defence, created
  through the application's own services, never with real model output
  presented as genuine.
- README checked command by command; add troubleshooting for the cases seen
  in practice (migration not applied, master key not loaded, ports in use,
  Docker not running, CRLF in downloaded scripts).

## Finish

Run `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make test-perf`, `make secret-scan` and the traceability report (real
counts). Prepare a `v1.0` changelog but do **not** create the tag; give the
author the tag and push commands. Summary in the `AGENTS.md` §10 format,
starting with the requirement status counts from the evidence index.
