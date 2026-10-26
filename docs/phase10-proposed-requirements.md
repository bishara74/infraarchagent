# Proposed requirement amendments — author/supervisor approval pending

These are proposals, not approved specification IDs. They do not enter pytest
requirement markers, the 59-ID traceability denominator or compliance counts.
`docs/spec/` is unchanged. D-62 and OQ-11 record the approval boundary.

| Proposed ID | Delivered feature to specify | Existing decision / evidence |
|---|---|---|
| FR-I-05 | Independent per-role model/thinking selection, defaults and frozen provenance | D-52/D-58/D-59; agent-selection and role-default tests |
| FR-C-01 | Encrypted provider credential management and key rotation, with no plaintext secret projection | D-51; credential/canary tests and rotation command |
| FR-UI-10 | Account preferences, explicit draft recovery, recent runs and offline cache rules | D-53/D-58; preference/reload/browser tests |
| FR-S-13 | Versioned contextual assessments alongside unchanged strict readiness | D-48/D-56; frozen-profile/replay evidence |
| FR-UI-11 | Decision-specific categories, immutable review history/export and accepted-risk counts | D-47/D-58/D-60; Phase 10 review/insight tests |
| FR-S-11 | Human lesson governance, including immediate screened admin activation and reviewer approval by a different admin | Existing D-60 proposal; amended author policy in Phase 10 |
| FR-S-12 | Layered lesson injection defenses with explicit semantic/filter limitations | Existing D-60 proposal; v1/v2 corpus and boundary tests |
| FR-P-05 | Lesson set snapshots, dispatch-use provenance, kill-switch generation and archive evidence | Existing D-60 proposal; transport/archive tests |
| FR-UI-08 | Lesson management, exact live pre-submit preview and version history | Existing D-60 proposal; Phase 10 unit/browser evidence |
| FR-UI-09 | Deterministic feedback insights with links to retained decisions | Existing D-60 proposal; insights tests |
| NFR-05 | Fail closed on incompatible database schema, with public health guidance and explicit owner migration | D-61; schema compatibility tests |
| NFR-06 | Reproducible bounded benchmarks, source/measurement provenance, traceability and honest unknown results | D-43/D-55/D-57/D-59/D-62; reporting/benchmark tests |

The authentication/account extension also needs the Chapter 1/3 non-goal amendment
recorded in D-62. This does not imply tenant isolation or run ownership.

Separate unresolved evidence decisions: the draft PR-03 revision is not approved;
the current target remains not met. NFR-04 cannot be accepted from recipes or
existing-host tests; the author must commit clean-machine and Windows-browser
results. Proposed IDs should be approved together with measurable acceptance
wording before they become specification commitments.
