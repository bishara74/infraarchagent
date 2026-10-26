# Codex task — Phase 10b: security remediation must not break planned exposure

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-44 to D-62),
the security loop and Fixer prompt builder, the existing rollback rules
(validity/Terraform regression, deadline rollbacks), the plan model
(`network.public_services`, `private_services`, `ingress`), the readiness
logic, the Phase 9k load-balancer exposure audit
(`backend/scripts/phase9k_audit.py` and `docs/evals/phase9k-architect-report/`)
and the committed benchmark evidence folders. Phases 0–10 are complete.

## Finding (author's manual ECS test, runs 3 and 4)

The plan listed the ALB as a public service with `HTTPS 443 from 0.0.0.0/0`.
The Generators wrote `internal = false` (correct). During security
remediation the Fixer changed it to `internal = true` to clear AWS-0053
("Load balancer is exposed to the internet"). The finding disappeared, and
two packages became **`checks_passed`** although the API is unreachable from
the internet, contradicting the request and the plan:

- run 3 cost variant: original `internal = false` → final `true`, checks_passed
- run 3 security variant: original `false` → final `true`
- run 4 performance variant: original `false` → final `true`, checks_passed

The Fixer never sees the plan's exposure intent, and no rollback rule checks
plan conformance. Remediation therefore optimised the scanner result at the
expense of a functional requirement.

## Rules

No real LLM calls, no `.env` reads, no installs, no network, no push.
Profiles, scanner rules and thresholds unchanged; the strict profile still
decides labels. Plan mode first: confirm the root cause in code, list every
plan property that remediation can currently violate, and report before
changing code. One commit per section, prefix `phase10b:`, requirement IDs
(FR-S-02, FR-S-03, FR-S-07, FR-A-05, NFR-02 where relevant),
implementation-log entries with real counts. Document in a new D-63.

## 1. Deterministic plan-conformance guard

After every Fixer candidate (each iteration and partial group), compare the
candidate with the plan and the pre-fix files for exposure invariants:

- A service listed in `network.public_services` (load balancers, API
  gateways, CloudFront and similar) must stay internet-facing: no change of
  `internal`/`scheme` to internal, no move from public to private subnets
  only, no removal of the listener/ingress the plan requires.
- A service listed in `private_services` must not become public.
- Planned ingress rules must not be removed.

A violating candidate is **rolled back** like a validity regression, with a
recorded reason (`plan_conformance_regression`), the rule IDs it targeted and
the property it violated. The finding stays open, so the package ends in
`pending_review` with an explicit review reason instead of a false
`checks_passed`. Unknown or dynamic values are treated conservatively (no
silent acceptance). Tests: the observed ALB flip (HCL and JSON), scheme on
NLB, subnet move, private service made public, unrelated fixes still
accepted, unknown values, partial groups.

## 2. Fixer context

Give the Fixer the plan's network section (public/private services and
ingress) as structured data with a fixed instruction that planned exposure is
a requirement and must not be changed to clear a finding; findings that
conflict with planned exposure should be left for engineer review. The guard
in section 1 remains authoritative. Golden-wire tests for the changed Fixer
request; disclose the prompt version change.

## 2b. Optional Fixer-scoped lessons

Add a lesson scope role `fixer` that an admin or reviewer must choose
explicitly; `all_generators` does **not** include the Fixer. Approved Fixer
lessons are rendered through the existing lesson renderer into the Fixer's
user message, in the same delimited advisory block as the plan context, with
the same limits, filter, versioning, provenance, kill switch and benchmark
bypass. The plan-conformance guard (section 1), scanners, validation and
readiness remain authoritative: a Fixer lesson can never permit a change the
guard rejects. Update D-60/D-63 with the added injection surface and its
mitigations. Tests: role scoping (generators never receive Fixer lessons and
vice versa), golden-wire bytes unchanged when no Fixer lesson exists,
provenance per Fixer call, guard still rolls back a lesson-encouraged
violation.

## 3. Readiness and review visibility

When a finding was left open because fixing it would contradict the plan,
show this in the package's findings and review tab ("kept open: required by
the plan's internet exposure") and in the results overview. No change to
which rules block.

## 4. Audit of existing evidence

Using the committed benchmark evidence and the 9k exposure audit, count for
every benchmark folder (final sets, broad rounds, Architect experiment) how
many packages had a plan-public load balancer that was public in the
original files but internal in the retained files, and how many of those
were `checks_passed` under each profile. Recompute the affected pass rates
with those packages counted as failures, side by side with the published
rates. Do not modify historical folders; write a new report folder. Record
the result honestly in D-63, the thesis notes and the evidence index
(affected claims become partly met if needed).

## 5. Replay

Add the author's run 3 and run 4 packages as fixed regression fixtures
(synthetic copies, no real keys) proving the guard now rolls back the flip.

## 6. Lesson provenance bug (Phase 10 section 0)

In the author's run 4 manifest, a lesson that an admin proposed **after** the
Phase 10 migration activated immediately (correct), but its entry records
`"approval": "self_approved"`, `"self_approved": true` and
`"approval_actor": null`. It should record `admin_direct` with the admin's
identity. Find where the run manifest, events or archive derive these fields
(for example a legacy mapping or a missing actor join), fix it for new runs,
and keep historical records unchanged and readable. Tests: admin-direct
lesson → manifest/archive/event show `admin_direct` and the actor; legacy
self-approved lessons still read as before; reviewer-proposed lesson approved
by an admin shows that admin as actor.

## 7. Inspect the lesson effect in the author's runs (analysis only)

The author ran the same ECS prompt four times with the default models:
`docs/evals/phase10b-author-lesson-runs/run1-no-lessons.json` (no lessons),
`run2-lesson-v1.json` (lesson 1: outbound access via NAT/VPC endpoints, all
generators), `run3-lessons-v2.json` (+ lesson 2: access logs inside the one
load balancer resource, performance generator), `run4-lessons-v5.json`
(+ lesson 3: internet-facing load balancer in public subnets, all
generators). These are results API responses saved by the author.

Run the secret scan over the folder first. Then, deterministically and per
run and variant:

- Confirm from telemetry that each lesson reached exactly its scoped roles
  (block hash, lesson IDs) and never the Architect or Fixer.
- In the **Generator's original files** (before remediation), check whether
  each lesson's instruction was followed: NAT gateway or ECR/Logs/Secrets
  Manager endpoints with a route for private subnets; no duplicate
  resource blocks; load balancer internet-facing and in public subnets
  across two availability zones.
- Compare with the **final** files to separate Generator behaviour from
  Fixer changes (e.g. the `internal` flips).
- Record side effects that coincide with a lesson (e.g. access logs dropped
  after lesson 2) and other differences (plan changes between runs).
- Report one table (run × variant × lesson: followed / not followed / not
  applicable / unknown) plus the side effects, and state clearly that one
  run per configuration is a demonstration of the mechanism, not a measured
  effect; plans differed between runs. No LLM calls.

Commit the four files and the analysis under
`docs/evals/phase10b-author-lesson-runs/` only if the secret scan reports 0
findings; summarise the result in D-60 and the thesis notes.

## Finish

Run `make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make test-perf`, `make secret-scan` and the traceability and evidence-index
reports (real counts). Summary in the `AGENTS.md` §10 format, starting with
the audit numbers from section 4.
