# Round 2 bug sweep

The pre-change stub-provider sweep covered setup, login, request/configuration
(including Advanced/search), live progress, comparison, diff, review/retry,
recent runs, Provider/Models/Users/Account Settings, account menu and native
revoke/reset/reject dialogs at 1280×800 and 1920×1080. Only synthetic credentials,
an isolated PostgreSQL test cluster and mocked provider HTTP were used.

Normal flows produced **0 console errors/warnings, failed requests or unhandled
rejections**. No horizontal page overflow was found. Loading captured during
initial Provider/Models navigation settled normally. Dialog Tab cycles can visit
browser chrome (`document.hasFocus() === false`, active element BODY); background
controls remain inert. Escape closes dialogs and restores their triggers.
The raw `focusEscaped` field in baseline measurements counts that native browser
chrome visit, not a focus leak into the application.

| Screen / finding | Cause | Fix / section |
|---|---|---|
| Provider: endless “Testing or saving…” after changing provider during a probe | Aborting ignores the old request's finalizer, while provider changes never clear its busy flag | Separate probe/action activity; abort and reset on identity edits (0) |
| Account / password reset: Chromium informational password-form diagnostic | Forms omit username context | Supply the account/reset target's autocomplete username (0) |
| Request / Models: only Use default, no actionable catalogue retry | HTTP 200 failure statuses ignored; failed probe cached 300 seconds | Shared status handling, safe failure guidance, retry bypass (2) |
| Request / Models: unknown capability marked incompatible | Missing/null metadata and confirmed false share one condition | Three-state capability handling and choice-origin-aware guidance (2) |
| Request / Models: missing saved model error on Use default | Error selected by role without checking choice origin or successful catalogue availability | Name only actually missing saved selections; retain environment default (2) |
| Model popup: 22,802px tall for 300 models | Virtual spacer padding becomes the scroll container's minimum height, defeating max-height | Internal spacers and content-sized bounded scroll container (2) |
| Model keyboard End references absent option | Oversized scroll viewport prevents the active option entering the rendered window | Correct viewport/window geometry; always render active option (2) |
| Model chevron cannot close popup | Refocusing invokes the input's unconditional open handler | Separate focus from toggle intent (2) |
| Request: saved prompt inserted after login | Textarea directly reads persisted prompt_draft | Empty editor with explicit Restore / Discard / Dismiss (1) |

The account hydration gate and selected-credential cache identity do not explain
these reproductions. Capability data was never obtained from real inference.
Baseline files in [baseline/](baseline/) retain the measured geometry and
controlled fault results; fault fixtures are distinct from the normal sweep.
The original frontend baseline passed 151 tests; 10 model/metadata backend tests
(including golden-wire cases) and lint passed. One browser replay overlapped a
database-resetting test suite and was discarded; the clean sweep ran sequentially
afterward. A first Vite launch shared optimizer artifacts with an existing dev
server and returned outdated-dependency 504s; the clean sweep used its own cache.
These harness failures are not reported as application defects or passing runs.

All listed findings are fixed in the six approved section commits. Final visual
review additionally compacted the comparison cards so inspection and download
actions fit the initial projector viewport. The repeated sweeps report zero
normal-flow browser errors/failures or horizontal overflow at both sizes. See
[final gallery and exact verification results](README.md).
