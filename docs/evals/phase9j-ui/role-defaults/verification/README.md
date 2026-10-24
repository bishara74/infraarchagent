# Final verification — independent role defaults

| Command | Final result |
|---|---|
| `make lint` | Exit 0; Ruff/format, mypy 172 sources, ESLint and both TypeScript projects. |
| `make test` | 2,236 passed, 0 failed/skipped, 6 perf deselected; 370.79s. |
| `make frontend-test` | 413 passed, 0 failed/skipped, 38 files; 40.11s. |
| `make test-e2e` | 18 passed, 0 failed/skipped; 4.4m. |
| `make frontend-build` | Exit 0; production Vite build. |
| `make secret-scan` | Exit 0; 0 findings, 0 scan errors. |

Logs are preserved alongside this document. The secret scan covers refs/reflogs
and the working tree with excluded paths filtered before retrieval. Its report
is in [secret-scan](secret-scan/summary.md). Screenshot dimensions and SHA-256
hashes are in [screenshots.json](screenshots.json).

Backend and browser verification used real PostgreSQL 16 in a disposable UTF-8
cluster, a dedicated `infraarch_test` database and the existing owner/app grants.
The inspection role was provisioned as NOLOGIN before running unchanged
migrations. No production database or real provider service was used.

The absolute-path dotenv-disabled bootstrap was applied to verification and
migration subprocesses, with explicit test database URLs. Equivalent invocation
with separately provided test-only credentials:

```sh
export INFRAARCH_TEST_BOOTSTRAP=1
export PYTHONPATH="$PWD/backend/tests/bootstrap:$PWD/backend"
export TEST_DATABASE_URL='postgresql+asyncpg://infraarch_app:<test-password>@127.0.0.1:55448/infraarch_test'
export TEST_MIGRATION_DATABASE_URL='postgresql+asyncpg://infraarch_owner:<test-password>@127.0.0.1:55448/infraarch_test'
make test
make test-e2e
```

The browser server remains stub-only until tests select a synthetic credential;
all resulting inference/catalogue HTTP is mocked. A configured model/effort
baseline in the browser harness tests genuine independent environment fallback.
Fixed prompts in the new wire tests isolate configuration changes from natural
changes in Architect output.

Both new browser scenarios pass. Existing 1280/1920 desktop sweeps report no
console/page errors, failed requests, offscreen controls or horizontal overflow.
Architect-only selection checks focus and absence of page errors. The four new
1280×800 captures were visually inspected for readable sources and clipping;
older tracked galleries were restored after the suite regenerated them.

Early diagnostic runs exposed a missing inspection role in the disposable
cluster, old expectations for source-free labels, a Testing Library selector
option and an ordering assumption in the mocked catalogue. These were corrected
before the final full passing runs. No benchmark golden fixture was changed.
