# Phase 9f corrective verification — 2026-10-18

Requirements: FR-G-02, FR-S-03/04/09, FR-V-03/04, NFR-01, PR-01/03/04/05.
Implementation/design rationale: D-46. No real LLM calls, dotenv reads,
installations, downloads, new dependencies, migrations or pushes were used.

## Preserved investigation evidence

Author benchmark A remains unchanged at
`evals/phase9-bench-real-20261017T220548142797Z`: 3/41 production ready,
PR-01 PASS (median 133.921535 s), PR-05 FAIL. Full source JSON in
`.cache/phase9f-a-results/` was read-only; replay records SHA-256 input hashes.

All 20 remaining TERRAFORM_SYNTAX findings originated in generation, including
10 multi-line-string diagnostics caused by two missing closing AMI-pattern
quotes. Representative original/final locations in terraform/main.tf:

| Run prefix / variant | Source evidence | Findings |
|---|---|---:|
| 070c80f8 / security | Compact egress, line 153 | 1 |
| 0c07b234 / security | Compact egress, original 424 -> final 426 after TLS edit | 1 |
| 2feb779a / performance | Missing quote at 474; file unchanged | 8 |
| 47561150 / cost | Compact egress 92; IAM policy semicolon 190; unchanged | 2 |
| 47561150 / security | Missing quote 424; unchanged | 4 |
| 6f80d5cb / performance | Compact egress 160; original also contains latent syntax errors | 1 |
| e986acdc / cost | IAM policy semicolons 492; unchanged | 2 |
| e986acdc / security | Compact egress 99 | 1 |

Seven document.parse failures were also original source: four Terraform files
above and three Grafana JSON files with unescaped PromQL quotes (158be78a/cost,
line 13; 1c3abc8d/cost and performance, line 1). Duplicate gate observations made
all seven origins unknown. Other lost identities involved shifted diagnostics
and incomplete prior Terraform validation. One actual partial-acceptance defect
deleted variable.eks_name while main.tf:192 retained its reference in
4feb09fe/performance; the builtin reference failure was not observed by the
security verifier.

PR-05 overran only in security variant iteration 0: 6f80d5cb took 65.530602 s
(+5.530602), and e986acdc took 60.375424 s (+0.375424). The first exhausted its
work during template verification before any LLM or partial evaluation. The
second reached partial evaluation, keeping one group. Both finalized outside
their work timeout; the corrected implementation reserves bounded finalization.
Existing event data cannot resolve every millisecond of publication/cleanup.

1c3abc8d/security failed its first scan with `checkov scan invalid_json` before
any template or fix. Two native offline replays returned valid JSON but exposed
21 Helm findings with rendered chart-name paths absent from the source map:
`/helm/eks/eks-workloads/templates/workloads.yaml` versus
`helm/eks/templates/workloads.yaml`. Chart metadata now resolves that precise
mapping; ambiguous/unsafe locations still fail and are labelled path_mapping.
The corrected native offline replay preserved all 107 reported findings, including
all 21 mapped Helm findings; rendered line positions remain unclaimed. See
[Helm replay](evals/phase9f-corrective-helm-replay-20261018.json).

## Generation replay

Command (no model calls):

```sh
cd backend
.venv/bin/python -m scripts.phase9f_syntax_replay
```

Artifact: [phase9f-corrective-replay-20261018.json](evals/phase9f-corrective-replay-20261018.json).

| Recovery | Files | Packages |
|---|---:|---:|
| Deterministic whitespace-only normalization | 3 | 3 |
| Additional scripted syntax-only repair | 7 | 7 |
| Additional scripted regeneration | 1 | 1 |
| Total parsable at generation | 11/11 | 11/11 |

Native diagnostics: **24 initially -> 21 after normalization -> 0 after the
scripted recovery flow**. This count differs from the historical scanner's 20
syntax findings plus seven document.parse failures because parser coverage and
duplicate observations differ. Native replay includes previously masked errors.
The script's correction strings are explicit test oracles, not production
normalization rules or evidence of real-model reliability. Syntax recovery is
not a new production-ready rate; all semantic/security criteria still apply.

## Verification results

- `make lint`: Ruff/format, mypy (124 application sources), frontend ESLint/TS PASS.
- `make test`: final Docker-backed run **1,481 passed, 0 failed, 0 skipped,
  6 performance tests deselected (199.43 s)**. Six final targeted Helm/reporting
  checks also passed (2.29 s), including three Helm cases added after full-suite
  collection; all current tests were exercised. The preceding local PostgreSQL
  run passed 1,479 tests (213.81 s) before the two publication deadline cases.
- `make frontend-test`: 100 tests / 15 files PASS.
- `make test-e2e`: 6 PASS (1.6 min) against isolated Docker PostgreSQL 16
  using the repository initialization script.
- `make provider-schema`: all seven pinned versions exported offline, including
  AWS 5.100.0 and 6.68.0; no provider installation/download.
- `make secret-scan`: 0 findings / 0 scan errors; dated evidence under
  `evals/phase9-secret-scan-20261018T150931250888Z/` (working tree and all
  refs/reflogs through corrective implementation/evidence commit 26ed06a).

The first backend run had four failures (1,462 passed): the new native guard
caught expansion of single-line resources without a newline after `{`; review
retry boundaries, independent injected clocks and provenance matching also
needed correction. The next run had only an outdated prompt-v7 assertion
(1,475 passed). Targeted generation/recovery/guard tests passed after fixes.
The reserve-aware late-output fixture now returns within the 145-second work
window while retaining its original 151-second elapsed/overrun assertions.

The first stub launch stopped at the existing authenticated-settings preflight
because the local server lacked a synthetic API key. The authenticated rerun
completed. After the session pause, Docker's WSL connection and the task database
port disappeared; E2E initially stopped before startup. An already installed
PostgreSQL 16 server supplied an isolated replacement with normal owner/app
roles, SCRAM host authentication and unchanged application privileges. Nothing
was installed, and no real application database was used. Docker and port 5432
subsequently recovered. Final E2E and backend verification use a fresh task-owned
Docker PostgreSQL 16 on port 55441; the existing application container was untouched.

## Stub benchmark and limits

Artifact: [summary](evals/phase9-bench-stub-20261017T233429468115Z/summary.md).
Fourteen pipeline runs yielded 42/42 ready packages; ten separately labelled
synthetic PR-04 ZIP downloads remain excluded from quality rates.

- PR-01 PASS: median 14.703493 s, maximum 18.832189 s.
- PR-03 FAIL: cohort ratios 2.444690–2.458220 versus unchanged 1.5x threshold.
- PR-04 PASS: median 1.415957 s, maximum 1.695589 s.
- PR-05 PASS at unchanged 150-second generator/architect and 60-second security
  iteration thresholds.

The benchmark overlapped offline/backend verification; timings are observed
stub overhead, not isolated real-model performance. Clean stub packages required
no syntax recovery or security fixes. Separate scripted rehearsal measurements
remain descriptive, and no historical unknown measurement is filled in.

Author settings remain 45-second fixer attempts, 60-second iterations,
240-second stages, four iterations, two resources/12 findings and six partial
evaluations. Default models/output limits and all readiness/blocking rules are
unchanged. Prompt v8 and generation recovery differ from preserved benchmark A's
v7: use the same corrected commit for both author fixer configurations, or
explicitly report this confounder. Haiku and corrected real benchmarks were not run.

Task-owned PostgreSQL containers were removed and the temporary local server
was stopped after verification. The existing PostgreSQL container on
5432 remains available; only pre-existing untracked workspace files remain.
