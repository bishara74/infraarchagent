# Broad benchmark preparation — verification

Four sections prepare the author-run benchmark. The registration was committed
first (`7884c2f`); execution and reporting followed in `8d5e38f` and `975c326`.
D-57 and the README document the method and exact author commands. No real broad
benchmark was run. Dates here use Europe/Budapest; evidence timestamps use UTC.

| Check | Final result |
|---|---|
| `make lint` | passed (Ruff, mypy 164 source files, frontend ESLint/TypeScript) |
| `make test` | 1,851 passed, 0 failed/skipped, 6 performance tests deselected |
| `make frontend-test` | 113 passed in 17 files, 0 failed/skipped |
| `make test-e2e` | 7 passed, 0 failed/skipped |
| `make secret-scan` | 0 findings, 0 scan errors |
| `make bench-broad MODE=stub BASE_URL=http://127.0.0.1:8765 RUNS_PER_SCENARIO=2` | 20 settled runs; 60 package records; 0 missing; $0; PR-05 PASS |

[Machine-readable results](verification-results.json), [rehearsal assertions](rehearsal-checks.json)
and [raw verification logs](verification/) record the actual checks. The complete
[stub evidence](../phase9-bench-broad-20261020T225308383413Z/summary.md) preserves
normal run, event, agent, quality and telemetry records. All twenty JSON/CSV rows
and sixty package snapshots carry the matching scenario SHA-256. The order is
1–10 then 10–1. No cohort or PR-01 threshold verdict was emitted. Server LOG_FILE
recorded 80 calls, all provider=stub; those call logs remain intentionally untracked.

The initial migration prerequisite failure is preserved in
[backend-prerequisite.txt](verification/backend-prerequisite.txt). The first full
suite found one compatibility regression (1,850 passed / one failed / six
deselected): a legacy runner caller did not supply the new broad argument. The
runner now defaults it to false. [backend-first.txt](verification/backend-first.txt)
preserves the failure; 29 focused tests and the final complete suite pass.

All Python parents/children disabled dotenv through the existing test bootstrap.
A disposable PostgreSQL 16 container used synthetic credentials, the real
app/owner roles and both normal database names. Its missing inspection role was
provisioned with the existing script, without changing application privileges.
The container and stub server were stopped after verification. Installed tools,
local provider mirrors and cached Chromium were used; no installs/downloads,
real model calls, real keys, migrations to the author's database or pushes occurred.
E2E mock provider names do not represent real inference.

Some independent E2E/backend checks overlapped part of the stub rehearsal, using
separate test/development databases. Stub timings are rehearsal evidence only.
The broad environment's tracked-dirty flag records finishing documentation and
the compatibility correction; actual source is included in the finishing commit.
The real author benchmark should run from the committed source on a quiet machine.

The final secret scan is
[recorded separately](../phase9-secret-scan-20261020T230012192768Z/summary.md).
Historical final sets, the checked-in final report, both offline collections and
docs/spec remain unchanged. Historical report/CSV preservation is also covered by
an immutable-fixture regression test. No new open question was added.

Final-set individually priced runs ranged from $0.02594 to $0.19225. A twenty-run
extrapolation is approximately $0.52–$3.85, not a bound for these new scenarios.
Real broad results, live deadline reliability and deployment success remain
unmeasured. The author next runs the README's real command, commits its evidence
and generates a fresh report; contextual-v2 remains unavailable for old final sets.
