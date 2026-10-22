# phase9i: literal file-path rebasing — offline replay

201 saved packages: 60 broad-1, 60 broad-2, 40 final-1 and 41 final-2. Three missing final variants remain separate. Baseline is the committed v6-retained replay, not original generator output. No inference, deployment or new real benchmark.

Every path proposal receives paired native validation and scans, then the existing checked_one/CandidateGuard decides retention. Byte-identical packages reuse hash-verified prior retained observations with matching tool/provider versions and unchanged observational sources. Each row states its baseline method. Only file-path proposals run; other repairs and provider consolidation are not rerun.

| Cohort / scenario | Packages | Valid before → retained (delta) | Strict passes | v1 passes | v2 passes | Strict / v1 / v2 blocker deltas |
|---|---:|---|---|---|---|---|
| broad-1 / all | 60 | 35 → 35 (+0) | 24 → 24 (+0) | 24 → 24 (+0) | 24 → 24 (+0) | +0 / +0 / +0 |
| broad-2 / all | 60 | 40 → 41 (+1) | 22 → 22 (+0) | 22 → 22 (+0) | 22 → 22 (+0) | +0 / +0 / +0 |
| final-1 / all | 40 | 9 → 9 (+0) | 7 → 7 (+0) | 7 → 7 (+0) | 7 → 7 (+0) | +0 / +0 / +0 |
| final-2 / all | 41 | 14 → 14 (+0) | 8 → 8 (+0) | 8 → 8 (+0) | 8 → 8 (+0) | +0 / +0 / +0 |
| broad-1 / 1 | 6 | 6 → 6 (+0) | 6 → 6 (+0) | 6 → 6 (+0) | 6 → 6 (+0) | +0 / +0 / +0 |
| broad-1 / 2 | 6 | 3 → 3 (+0) | 3 → 3 (+0) | 3 → 3 (+0) | 3 → 3 (+0) | +0 / +0 / +0 |
| broad-1 / 3 | 6 | 3 → 3 (+0) | 3 → 3 (+0) | 3 → 3 (+0) | 3 → 3 (+0) | +0 / +0 / +0 |
| broad-1 / 4 | 6 | 6 → 6 (+0) | 6 → 6 (+0) | 6 → 6 (+0) | 6 → 6 (+0) | +0 / +0 / +0 |
| broad-1 / 5 | 6 | 4 → 4 (+0) | 3 → 3 (+0) | 3 → 3 (+0) | 3 → 3 (+0) | +0 / +0 / +0 |
| broad-1 / 6 | 6 | 4 → 4 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-1 / 7 | 6 | 4 → 4 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-1 / 8 | 6 | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | +0 / +0 / +0 |
| broad-1 / 9 | 6 | 4 → 4 (+0) | 2 → 2 (+0) | 2 → 2 (+0) | 2 → 2 (+0) | +0 / +0 / +0 |
| broad-1 / 10 | 6 | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-2 / 1 | 6 | 6 → 6 (+0) | 4 → 4 (+0) | 4 → 4 (+0) | 4 → 4 (+0) | +0 / +0 / +0 |
| broad-2 / 2 | 6 | 3 → 3 (+0) | 2 → 2 (+0) | 2 → 2 (+0) | 2 → 2 (+0) | +0 / +0 / +0 |
| broad-2 / 3 | 6 | 5 → 5 (+0) | 5 → 5 (+0) | 5 → 5 (+0) | 5 → 5 (+0) | +0 / +0 / +0 |
| broad-2 / 4 | 6 | 5 → 5 (+0) | 5 → 5 (+0) | 5 → 5 (+0) | 5 → 5 (+0) | +0 / +0 / +0 |
| broad-2 / 5 | 6 | 5 → 5 (+0) | 5 → 5 (+0) | 5 → 5 (+0) | 5 → 5 (+0) | +0 / +0 / +0 |
| broad-2 / 6 | 6 | 6 → 6 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-2 / 7 | 6 | 5 → 5 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-2 / 8 | 6 | 2 → 2 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-2 / 9 | 6 | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | +0 / +0 / +0 |
| broad-2 / 10 | 6 | 2 → 3 (+1) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| final-1 / final-0 | 23 | 3 → 3 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | +0 / +0 / +0 |
| final-1 / final-1 | 8 | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| final-1 / final-2 | 9 | 6 → 6 (+0) | 6 → 6 (+0) | 6 → 6 (+0) | 6 → 6 (+0) | +0 / +0 / +0 |
| final-2 / final-0 | 24 | 6 → 6 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| final-2 / final-1 | 8 | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | +0 / +0 / +0 |
| final-2 / final-2 | 9 | 7 → 7 (+0) | 7 → 7 (+0) | 7 → 7 (+0) | 7 → 7 (+0) | +0 / +0 / +0 |

Broad scenario IDs keep their registered meaning. Final scenario IDs come from existing metadata: final-0 ECS (including PR-03), final-1 EKS, final-2 static site. No prompt-text matching.

| Path proposal | Guard outcome | Failed checks before → candidate | Retained validity |
|---|---|---|---|
| final-1/95c60392-4ffe-4afb-9882-ef802a45bcdd/cost | improved | 4 → 3 | invalid |
| final-2/464124e4-03d5-4be3-a1ac-f25ee0d6207f/cost | improved | 2 → 1 | invalid |
| final-2/464124e4-03d5-4be3-a1ac-f25ee0d6207f/security | no_improvement | 2 → 2 | invalid |
| broad-1/da77c0c2-59a4-4a45-bafe-5ae68abf8318/performance | no_improvement | 9 → 9 | invalid |
| broad-1/14decd94-ff04-45f7-9b4f-5c2a0e0ab35e/performance | improved | 4 → 3 | invalid |
| broad-1/a9e7620f-df79-4124-b53f-50d0f0d00da1/performance | improved | 2 → 1 | invalid |
| broad-2/cda319c1-6b38-4534-96aa-ca36b37795de/performance | no_improvement | 2 → 2 | invalid |
| broad-2/9a277d2d-e667-4a06-9f21-f369f64786d4/performance | improved | 1 → 0 | valid |
| broad-2/d08be9f7-dc06-4d8a-a7dc-649fd495b96f/cost | improved | 3 → 2 | invalid |
| broad-2/d08be9f7-dc06-4d8a-a7dc-649fd495b96f/performance | improved | 2 → 1 | invalid |

A literal canonical file() argument is rebased only when the module-relative target is absent, the exact package-root artifact exists and the replacement remains inside the package. An existing root-working-directory target is also authoritative for child modules. No basename search, file creation, host filesystem reads or artifact-content changes. Dynamic, escaping, missing or ambiguous inputs skip. Existing valid paths remain unchanged.

Semantics: [file()](https://developer.hashicorp.com/terraform/language/functions/file), [path.module](https://developer.hashicorp.com/terraform/language/expressions/references#filesystem-and-workspace-info). The expression still returns a string; pinned schemas and native validation remain authoritative. [Per-package evidence](per-package-deltas.json) records before/candidate/retained hashes, guard records and findings. Manifests bind all 201 inputs, prior evidence and evaluator sources. Unknown/error observations never count as passes.

These are offline effects on saved bytes. Static validity does not prove deployment success. SSM commands coercion, prompts, guidance caps/tiers, readiness, blocking and thresholds are unchanged.
