# Codex task — Phase 9g: Honest labels, login cookie, exception profile

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-40 to D-46),
the latest `docs/IMPLEMENTATION_LOG.md` entries, the supervisor's checkpoint-4
audit (`docs/reviews/checkpoint4-audit.md`, R1 and R2), the readiness rule,
`ReviewService`, `backend/app/security/policy.py`, the class-B templates
(Phase 9f), API auth (`deps.py`, D-36), the frontend API client and key
handling, the archive builder (`INFRAARCHAGENT_READINESS.md`), the results/
review UI, `backend/scripts/benchmark.py`, `run_phase9_benchmarks.py` and the
`Makefile`. Phases 0–9f are complete.

## Why this phase exists

1. **R1 (audit):** automatic check success, engineer approval, rejection and
   deployability must never be confused. Today an engineer *approve* maps a
   package to `production_ready`, which can present failed checks as passed.
2. **Login (author decision D2):** the browser should not hold the raw
   `API_KEY` in sessionStorage; use an HttpOnly session cookie.
3. **Exception profile (option 6):** a documented, resource-specific profile
   for context-dependent scanner rules, reported **next to** the strict
   result, never instead of it.
4. **Evidence from the latest real benchmarks**
   (`docs/evals/phase9-bench-real-20261018T213645241170Z` = A3, gpt-oss fixer,
   10 complete runs, 1/29; `…20261018T231027886459Z` = B, Haiku fixer,
   3 complete runs; both stopped by provider HTTP 402 `usage_limit`):
   - No valid package has fewer than 4 blocking findings.
   - Class-B templates are counter-productive: `access_logs` rejected 103×
     (A3) / 28× (B), introducing AWS-0090 (log bucket without versioning);
     templates introduced AWS-0132 138× / 43×.
   - Top remaining rules (A3): AWS-0104 43, CKV_AWS_130 21, AWS-0164 20,
     AWS-0053 18, CKV2_AWS_12 18, CKV_AWS_18 17, CKV_AWS_91 17, CKV_AWS_260 13,
     AWS-0132 12, CKV_AWS_145 12, KSV-0118 12, AWS-0090 11, CKV_AWS_21 11.
   - The benchmark guard reported ~$8 "remaining credit" (key
     `limit_remaining`) while the provider returned 402, and the script kept
     submitting runs that failed in 0.2 s.
   - `make bench-real BASE_URL=… BUDGET=…` does not forward the variables to
     the script.
   - Haiku as fixer: frequent `invalid_json` with `format_reason=prose_before`
     despite `json_schema`; median security iteration 23.7 s vs 10.4 s.

Saved results (read-only, never commit): `.cache/phase9f-a3-results/`,
`.cache/phase9f-b-results/`.

## Rules

No real LLM calls, no `.env` reads, no installs/downloads, no push, no new
dependencies. One commit per numbered section, prefix `phase9g:`, requirement
IDs, implementation-log entries with real test counts. Plan mode first:
report section 0 before code changes.

**Raise quality, not the label** still applies: the strict readiness rule,
blocking criteria, severities and check meanings stay unchanged. The
exception profile is an additional, separately labelled view.

## 0. Investigate (report first)

- Every place that sets, stores, displays or archives a readiness label or
  review decision (domain, DB enum/columns, API schemas, events, UI badges,
  archive text, benchmark summaries, `quality` subcommand, historical
  evidence folders). Which migrations and API fields change, and how
  existing runs are presented afterwards.
- Current frontend key flow (where `API_KEY` is entered, stored, sent; how
  SSE authenticates today).
- Why the templates are rejected (sample from A3), and which rules each
  template introduces on which resource.
- How the benchmark guard computes "remaining credit", and why runs
  continued after the first 402.

## 1. Separate labels (R1, decision D5)

- Rename the automatic label `production_ready` → **`checks_passed`**
  (clean blocking scan + valid validation, rule unchanged). Persisted
  outcomes: `checks_passed`, `engineer_approved` (manual approval of a
  package whose checks did not all pass), `rejected`, `pending_review`.
  A manual decision can never produce `checks_passed`.
- Engineer approval records who/when/why and keeps failed checks and
  remaining findings visible everywhere (UI, API, events, archive).
- `INFRAARCHAGENT_READINESS.md` states exactly what passed, what did not,
  the human decision, and that no label implies a successful cloud
  deployment (static checks only).
- Migration preserving history: old automatic `production_ready` →
  `checks_passed`; rows that reached it through an approval →
  `engineer_approved` with their original decision record. Report counts.
- Benchmark and `quality` output: report "checks-passed rate"; when reading
  historical folders, map the old label and say so in the output (never
  modify historical folders).
- Tests: a manual decision never reports failed checks as passed (API, UI,
  archive, events); migration of both historical cases; label provenance
  end to end.

## 2. Login with an HttpOnly session cookie (decision D2)

- `POST /api/auth/login` (body: the `API_KEY`, constant-time comparison,
  attempt rate limit), `POST /api/auth/logout`, `GET /api/auth/session`.
- On success: random session token (≥ 256 bit) in a cookie `HttpOnly`,
  `SameSite=Strict`, `Path=/api`, `Secure` when served over HTTPS (setting;
  off for local http), idle and absolute expiry (settings, propose
  defaults). Store only a hash of the token server-side (DB table with
  expiry/revocation); logout and expiry invalidate it.
- CSRF: SameSite=Strict plus an `Origin`/`Host` check on state-changing
  requests.
- All authenticated endpoints, including SSE streams and downloads, accept
  the session cookie; the `X-API-Key` header stays for scripts and the
  benchmark (document both paths).
- Frontend: a login screen; the raw key is no longer stored in
  sessionStorage or anywhere in the browser; 401 → back to login.
- Tests: login success/failure, rate limit, expiry, logout, tampered/unknown
  token, CSRF origin rejection, SSE with cookie, header path unchanged,
  canaries (the key never appears in responses, logs, events, cookies).
  Update the Playwright E2E flow.

## 3. Template fixes (quality, from the A3/B evidence)

- Access-log bucket template: add versioning and a public-access block (and
  whatever else your sample shows it needs) so it no longer introduces
  blocking findings; keep SSE-S3 (AWS requires it for server access-log
  targets).
- KMS template: find why it is rejected and fix the cause.
- A template is applied only if the result introduces no new blocking
  finding (unchanged rule); add tests per template that its output scans
  clean apart from documented context-dependent rules (section 4).

## 4. Exception profile (option 6)

- Versioned, file-based policy profiles: `strict` (default, exactly today)
  and `contextual-v1`, selectable per run, recorded in the run, events,
  archive and benchmark output.
- Each entry: Checkov and Trivy IDs of the same control, resource type, a
  **parsed, resource-specific condition**, justification, references. Never
  substring or comment matching (R2 lesson); unresolvable conditions stay
  blocking.
- Candidates from the evidence (verify each condition is parseable; drop any
  that is not; justify each in one or two lines):
  - CKV_AWS_145 / AWS-0132 (KMS encryption) and CKV_AWS_18 (access logging)
    **on a bucket that is the server-access-log target** of another bucket
    in the package (AWS requires SSE-S3 there; logging the log bucket
    recurses).
  - AWS-0104 (unrestricted egress) on a security group attached only to
    resources the plan marks internet-facing or egress (NAT, ALB, public
    tier).
  - AWS-0164 / CKV_AWS_130 (public IP on launch) on subnets the plan marks
    public (the IGW-route subnet intent from 9f).
  - AWS-0053 (public load balancer) and CKV_AWS_260 (port 80 from
    0.0.0.0/0) only on a load balancer the plan marks internet-facing, with
    port 80 limited to a redirect to HTTPS where checkable.
  - CKV_AWS_144 (cross-region replication): propose with justification or
    reject.
- Excepted findings stay visible as `excepted` with the profile entry in UI,
  API, archive and reports.
- Benchmark/`quality`: report the checks-passed rate under **both** profiles
  from the same stored findings (re-classification, no LLM calls), clearly
  labelled; strict stays the headline number. Also re-classify the A3 and B
  folders into a new output folder.
- The author obtains supervisor approval of the list before reported use.
- Tests: each condition positive/negative, unresolvable → blocking, strict
  unchanged, both-profile reporting.

## 5. Benchmark tooling fixes

- Credit guard: use the stricter of the key `limit_remaining` and the
  account balance (`GET {base_url}/credits`, mocked in tests); if the account
  endpoint is unavailable, record "unknown" and rely on the key.
- Stop the benchmark set immediately after the first run that fails with
  `usage_limit` (HTTP 402); mark the remaining planned runs `not_started`
  (not `failed`), and state the stop cause in `summary.md`.
- `make bench-real` / `bench-smoke` / `bench-stub` forward `BASE_URL`,
  `BUDGET`, `MAX_RUNS` to the script.
- Fixer model compatibility: report whether `json_schema` is actually
  enforced for `anthropic/*` models via the OpenAI-compatible endpoint (from
  request/response handling, mocked) and why `prose_before` occurs; document
  it in D-46. Do not add model-specific parsing hacks.

## 6. Documentation and finish

D-47 (labels + rename), D-48 (exception profile, full table = thesis
appendix), D-49 (session cookie login), D-46 update (templates, guard, fixer
compatibility), README, and "Thesis text to update" notes (R1 contract
amendment; Chapter 6: report A3/B as incomplete because of the provider
limit).

Finish with `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make secret-scan`, `make provider-schema`, `make bench-stub` (real counts).
Summary in the `AGENTS.md` §10 format, starting with the section 0 findings,
the migration counts, and the A3/B re-classification under both profiles.
