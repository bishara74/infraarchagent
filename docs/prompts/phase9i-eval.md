# Codex task — Phase 9i evaluation: broad scenario benchmark (preparation only)

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-55, D-56),
`docs/evals/phase9-final-report/`, `docs/evals/phase9i-offline/`,
`docs/evals/phase9i-kubernetes-offline/FINDINGS.md`, `backend/scripts/benchmark.py`
(including the existing `--prompts` option from Phase 9c),
`backend/scripts/run_phase9_benchmarks.py`, `backend/scripts/phase9b_report.py`
and the `Makefile`. Phases 0–9i are complete.

## Why

The final sets used only three prompt texts, and 13/15 passes came from the
static-site prompt. The Phase 9i improvements were measured offline only
(replay: valid 23 → 45/81, strict passes 15 → 20/81). The author will now run a
**broad, pre-registered real benchmark** to measure (a) how the checks-passed
rate depends on scenario complexity and (b) whether the 9i changes help on new
scenarios, not only on the three known ones. You prepare everything; the author
runs it.

## Rules

No real LLM calls, no `.env` reads, no installs/downloads, no new
dependencies, no push. Readiness, blocking criteria, profiles and thresholds
unchanged. Plan mode first: report section 0 before changes. One commit per
section, prefix `phase9i:`, implementation-log entries with real test counts.

## 0. Investigate (report first)

- How `--prompts` works today (file format, how prompts map to runs, which
  PR measurements are computed, whether PR-03 can be skipped), and the
  smallest change needed for a quality-only schedule.
- How the 9b report generator selects folders, so the new benchmark can be
  added without changing historical rows.

## 1. Pre-registered scenario set (fixed before any run)

Create `docs/evals/scenarios/broad-v1.json` (and a readable `README.md`) with
exactly these ten scenarios, an ID, a complexity level (1–5, defined in the
README by resource count / services involved), and the exact prompt text.
Commit it **before** the benchmark; its SHA-256 is recorded in every run.
Scenarios 2, 9 and 10 reuse the existing final-set prompt texts verbatim
(anchors for comparison).

1. Private S3 bucket for backups with versioning, encryption and lifecycle rules. (1)
2. Static website — existing prompt text, verbatim. (2)
3. Serverless REST API with API Gateway, Lambda and DynamoDB. (2)
4. VPC with public and private subnets, a NAT gateway and an EC2 instance in a private subnet accessed through SSM Session Manager. (3)
5. PostgreSQL on RDS in private subnets with automated backups, used by an EC2 application server. (3)
6. Containerised web application on ECS Fargate behind an HTTPS Application Load Balancer. (4)
7. ECS Fargate application with RDS PostgreSQL and ElastiCache Redis. (4)
8. EKS cluster running one web application deployed with a Helm chart. (4)
9. ECS application — existing prompt text, verbatim. (5)
10. EKS microservices — existing prompt text, verbatim. (5)

Do not tune any code or prompt template for these scenarios.

## 2. Quality-only schedule

- `make bench-broad` (forwarding `BASE_URL`, `BUDGET`, `RUNS_PER_SCENARIO`,
  default 2): sequential runs only, no PR-03 cohort, using the scenario file;
  same guards as `bench-real` (account/key credit, stop on first
  `usage_limit`, `not_started` for the rest), same per-call telemetry and
  `LOG_FILE` support, results stored as a normal evidence folder
  `docs/evals/phase9-bench-broad-<timestamp>/` with the scenario ID and
  complexity on every row.
- Report PR-01 descriptively for these runs (not a PR-01 verdict, because the
  prompt set differs from the specified one) and PR-05 as usual.
- Stub rehearsal: `make bench-broad` against the stub provider must complete.

## 3. Report

Extend the 9b report generator (new section, historical rows unchanged):
per scenario and per complexity level — packages, valid, strict / contextual-v1
/ contextual-v2 checks-passed with Wilson CI, missing variants, top blockers,
median run time and cost; anchor scenarios 2/9/10 compared with the final sets
(Fisher exact, package and run level, clustering caveat); a simple table of
pass rate vs complexity level (and a CSV for a chart). State clearly that this
is one model family, two runs per scenario, and descriptive statistics.

## 4. Finish

D-57 (broad benchmark method, pre-registration), README "Running the broad
benchmark" with the exact author commands (quiet machine, `LOG_FILE`, master key
for the server, `BUDGET`). Run `make lint`, `make test`, `make frontend-test`,
`make test-e2e`, `make secret-scan`, and the stub rehearsal (real counts).
Summary in the `AGENTS.md` §10 format, with the expected cost range per run
from the final sets.
