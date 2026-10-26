# Phase 10 command audit

All 35 README shell blocks pass `bash -n` without execution; see the [block/line inventory](evals/phase10-verification/readme-command-audit.json). Command references/options were traced to their existing modules and contracts.

Every Make target was parsed with `make --dry-run` in a minimal environment. No dry run executes its printed command. Installation, download, paid-provider, rotation, sweep, database/tool and image commands remain author actions unless explicitly recorded as executed below. Actual pass/fail counts are in the [verification record](evals/phase10-verification/README.md).

| Target | Dry-run parse | Execution evidence |
|---|---|---|
| `make bench-broad` | valid | Author-only / online: not executed |
| `make bench-real` | valid | Author-only / online: not executed |
| `make bench-smoke` | valid | Author-only / online: not executed |
| `make bench-stub` | valid | Statically traced; not executed |
| `make benchmark` | valid | Statically traced; not executed |
| `make catalogue-inspect` | valid | Statically traced; not executed |
| `make catalogue-snapshot` | valid | Author-only / online: not executed |
| `make db-tools` | valid | Statically traced; not executed |
| `make down` | valid | Statically traced; not executed |
| `make eval-architect` | valid | Statically traced; not executed |
| `make eval-generators` | valid | Statically traced; not executed |
| `make eval-report` | valid | Statically traced; not executed |
| `make eval-security` | valid | Statically traced; not executed |
| `make eval-validation` | valid | Statically traced; not executed |
| `make experiment-estimate` | valid | Statically traced; not executed |
| `make frontend-build` | valid | Executed in Phase 10; see verification record |
| `make frontend-dev` | valid | Statically traced; not executed |
| `make frontend-install` | valid | Author-only / online: not executed |
| `make frontend-test` | valid | Executed in Phase 10; see verification record |
| `make install` | valid | Author-only / online: not executed |
| `make lint` | valid | Executed in Phase 10; see verification record |
| `make migrate` | valid | Statically traced; not executed |
| `make migrate-test` | valid | Executed in Phase 10; see verification record |
| `make prepare-db-tools` | valid | Statically traced; not executed |
| `make provider-schema` | valid | Statically traced; not executed |
| `make providers` | valid | Author-only / online: not executed |
| `make rotate-credential-key` | valid | Statically traced; not executed |
| `make run` | valid | Statically traced; not executed |
| `make run-pipeline` | valid | Statically traced; not executed |
| `make secret-scan` | valid | Executed in Phase 10; see verification record |
| `make spike` | valid | Statically traced; not executed |
| `make sweep` | valid | Statically traced; not executed |
| `make test` | valid | Executed in Phase 10; see verification record |
| `make test-e2e` | valid | Executed in Phase 10; see verification record |
| `make test-perf` | valid | Executed in Phase 10; see verification record |
| `make test-ui-perf` | valid | Statically traced; not executed |
| `make traceability` | valid | Executed in Phase 10; see verification record |
| `make up` | valid | Author-only / online: not executed |

Deployment scripts: `bash -n` passed; default deployment plan was executed and created no files. Installer/run mode was not executed. Dockerfiles: installed hadolint passed; full Compose parsed with `--env-file /dev/null --no-interpolate`. No image build/pull occurred. The production frontend bundle was built using existing dependencies.

The demo has a PostgreSQL-backed service test and loopback-client tests; no real account password or API key was used by the agent. Author execution and browser portability remain separate from test doubles. Existing online evaluation commands were reviewed against their target modules/options; they were not invoked.

Corrections: current remediation default is four passes; current nominal generator ceiling is 3 × 3 × 120 seconds before the shared 150-second budget clips work. Master-key generation captures its output into the process environment instead of printing it. Readiness download wording includes engineer_approved. Lesson policy and approval-category examples match the final contracts.
