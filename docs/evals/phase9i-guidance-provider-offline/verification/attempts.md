# phase9i: verification record

All Python commands used `INFRAARCH_TEST_BOOTSTRAP=1` with
`backend/tests/bootstrap` first on `PYTHONPATH`, disabling dotenv loading before
settings instantiate. Synthetic owner/app database URLs were supplied explicitly;
the verification launcher selects stub inference and clears credential settings.
No real model calls, keys, external network services, installs or pushes occurred.

Docker Desktop integration was unavailable for the original verification. Full
backend verification used installed PostgreSQL 16, a disposable cluster under `/tmp`,
synthetic credentials, normal role grants and all existing Alembic migrations.
The cluster was stopped after verification.

An initial full run produced 1,866 passed / 14 failed / 6 performance tests
deselected. Thirteen failures came from creating the temporary cluster with
SQL_ASCII encoding: JSONB rejected Unicode review identity text. The final cluster
uses UTF-8. One report fixture assumed no real broad evidence existed; it now
isolates the historical final-set prefix before adding its synthetic broad set.
No production behavior changed to address either verification prerequisite.

Final `make test`: **1,882 passed, 0 failed, 0 skipped, 6 deselected**, 838.74 s.
The final schema/report focused checks also passed: **63 passed, 0 failed or
skipped**. Real offline provider validation plus broad reporting: **12 passed**.
The focused checks cover optional-block inventories and empty optional sections;
the final full suite ran after all code changes. An earlier successful UTF-8 run
took 332.47 s. The final run overlapped fresh offline tool observations; neither
duration establishes a pipeline performance verdict.

`make lint` passed: Ruff checks/formatting, mypy on 165 application sources,
frontend ESLint and TypeScript. Backend and lint output are stored alongside this
record. No frontend code changed; separate frontend unit/browser suites were not
run for this follow-up.

Offline replay ran inside a Linux user/network namespace containing only
loopback, using the filesystem provider mirror and existing tool offline flags.
The final run binds every row to its execution manifest. Earlier observations
under different evaluator hashes never satisfy the final cache key.
All 48 saved plans are checked for unreported omissions of required guidance;
all proposal outputs are checked for idempotence. Two compatible provider
proposals expose underlying configuration errors and are rejected by the existing
guard. Retained validity and strict/v1/v2 deltas are zero.

The existing plan-to-resource-type mapping is unchanged. Broad scenario 3,
Serverless REST API, rounds 1 and 2, selects no schema types before or after the
change. This is a pre-existing mapping bug: Lambda/API Gateway services and
NoSQL/DynamoDB storage have no mapping, although both pinned indexes contain the
corresponding schemas. No budget overflow occurred. It was reported before
committing. See ../zero-schema-contexts.json for plan/run/index attribution.
This follow-up does not expand service mappings; coverage assertions apply to
selected types.

Original benchmark results, cached package snapshots and historical reports remain
unchanged. `unchanged-policy-and-guard.json` checks policy files, CandidateGuard,
validator and state rules byte-for-byte against the baseline commit.

Final evidence secret scan: **0 findings, 0 scan errors**. Final audit verifies
51 source hashes, 141 package hashes, 48 plan contexts and 55 evaluator files;
there are zero unreported required omissions and every character cap holds.

Commit preparation reran `make lint` successfully and `make test` with **1,882
passed, 0 failed, 0 skipped, 6 performance tests deselected**, in **307.45 s**.
The same disposable UTF-8 PostgreSQL 16 cluster and dotenv-disabled bootstrap were
used; PostgreSQL was stopped afterwards. No Docker startup was needed. The
staged guidance-only test subset also passed all **6** checks before its commit.
New logs are commit-backend.txt and commit-lint.txt; original verification results
are preserved. Lint logs omit the final empty line. All 55 evaluator and 51 input hashes still match the replay
manifests. The zero-schema mapping bug was reported before the first follow-up
commit; zero-schema-contexts.json adds attribution without changing replay rows.
Commit-time repository/history secret scan passed: **0 findings, 0 scan errors**
(commit-secret-scan.json). A targeted scan of all requested source/docs and replay
artifacts also found zero issues (commit-audit.json). No unrelated untracked files
are included in these commits.
