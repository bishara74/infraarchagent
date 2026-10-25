# Phase 9l UI evidence

Chromium captures at **1280×800**, using the isolated PostgreSQL 16 test
database, existing offline scanner/provider tools and the stub model. Names,
decisions and counts are browser-test fixtures recorded through the real API;
no real provider inference or deployment is represented.

| Capture | Verified state |
|---|---|
| [Feedback insights](feedback-insights.png) | Named-admin aggregates, visible decision filter, snapshot coverage and count links |
| [Linked decision](insight-decision.png) | The matching retained decision, required category/reason and unchanged export controls |

The fixture rejection is validation-related, so its recorded remaining-blocking
rule list is empty. The empty ranking is shown explicitly. Backend tests also
cover nonempty rankings, per-decision rule deduplication and missing historical
snapshots. Screenshots use only the existing design tokens, locally bundled
fonts and accessible text controls. Both views were checked for document-level
horizontal overflow. See D-60 and the implementation log for test results and
the limitations of advisory lessons.
