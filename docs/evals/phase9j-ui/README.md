# Phase 9j UI evidence

All screenshots are 1280×800 viewport captures, with local fonts loaded and
reduced motion. Data is synthetic, generated through the existing test server,
real PostgreSQL, mocked provider HTTP and offline local scanners/validators.
No real model inference, author credential, dotenv read or cloud deployment is
part of this evidence. Capture code: frontend/e2e/ui-polish.spec.ts and the
first-run setup flow. The gallery records actual API data and UI states.

## Investigations

Recent runs restarted preference hydration on mount. The access gate unmounted
it during loading, then remounted it after completion, repeating forever. An
empty successful browser fixture produced seven preference/history request pairs
while showing “Loading saved preferences…”. Application-owned deduplicated
hydration, error/retry and a clear empty state resolve this lifecycle bug.

The author's safe API fields establish a saved personal Architect default of
`google/gemini-3.8-flash:batch` with provider-default thinking, no administrator
Architect override, a separate explicit draft `openai/gpt-oss-120b`, and environment
`openai/gpt-oss-120b:nitro` with low thinking. No catalogue-order bug selected
Gemini. Existing saved choices are preserved; labels and inheritance are explicit.
Shared backend/frontend fixtures prove role/default model and thinking parity.

## Gallery

| Screen/state | Screenshot |
|---|---|
| First administrator setup | [setup](setup.png) |
| Centred login, logo only | [login](login.png) |
| New request, collapsed configuration | [new request](new-request.png) |
| Account menu | [account menu](account-menu.png) |
| Empty recent history | [empty history](recent-empty.png) |
| Populated recent history | [populated history](recent-populated.png) |
| Expanded configuration | [configuration](configuration.png) |
| Advanced configuration, scrolled to actions | [advanced](configuration-advanced.png) |
| Model search | [model search](model-search.png) |
| Pipeline progress | [progress](progress.png) |
| Variant comparison | [comparison](comparison.png) |
| Pending authenticated review | [review](review.png) |
| Validation report | [validation](validation.png) |
| Security-fix diff after retry | [diff](diff.png) |
| Provider settings | [provider](settings-provider.png) |
| Saved credentials, scrolled | [saved credentials](settings-provider-saved.png) |
| Models/defaults | [models](settings-models.png) |
| Reasoning/context/pricing from mocked provider | [reasoning models](settings-models-reasoning.png) |
| Administrator defaults, scrolled | [admin defaults](settings-models-admin.png) |
| Users table | [users](settings-users.png) |
| Reset-password dialog | [reset password](reset-password.png) |
| Account/password/preferences | [account](settings-account.png) |
| Account preferences, scrolled | [preferences](settings-account-preferences.png) |

## Verification

- `make lint`: passed Ruff/format, mypy on 167 app sources, ESLint and TypeScript.
- `make test`: **1,986 passed, 0 failed, 0 skipped; 6 performance tests deselected**
  in 411.38 seconds. This uses real PostgreSQL 16 with existing owner/app/readonly
  roles, synthetic credentials and dotenv disabled before settings instantiate.
- `make frontend-test`: **151 passed, 0 failed/skipped**, 27 files.
- `make test-e2e`: **8 passed, 0 failed/skipped**, 1.8 minutes. The existing @perf
  browser test remains excluded by the default command.
- `make frontend-build`: passed; fonts and Codicons emitted as local assets.
- Additional configured/non-null public model-metadata assertions: **4 passed**.
- `make secret-scan`: **0 findings, 0 scan errors** across the working tree, all refs and reflogs. Evidence is relocated under [verification/secret-scan](verification/secret-scan/).

[Raw verification logs](verification/) and the [screenshot/source SHA-256 manifest](manifest.json)
provide the exact captured evidence. All **23 PNG files** are 1280×800. Some longer
Settings/configuration views have explicitly named scrolled captures. Optional
browser ports 5179/8019 and a separate test cluster avoid the author's live app;
backend and E2E suites used separate isolated PostgreSQL clusters.

The first browser attempt had **6 passed / 2 failed**: the new visibility button
made a non-exact Confirm password locator ambiguous, preventing setup; the next
keyboard-login flow then lacked its setup prerequisite. Exact labels fix this.
One browser rerun and one secret scan were terminated with exit 143 before a
result; their partial outputs are not passing evidence. Subsequent complete
browser runs pass all eight tests, including after final control/error refinements.

Visual review moved secondary comparison details into disclosures to keep primary
labels, counts, file trees and actions in view. It also compacted Models settings,
verified the 36px defaults button with Advanced expanded, and added coverage for
large model lists, invalid inherited defaults, error recovery and dialog focus.
Static evidence does not establish deployment or real-provider availability.
