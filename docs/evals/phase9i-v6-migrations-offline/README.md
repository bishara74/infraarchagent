# phase9i: documented AWS v6 migrations — offline replay

201 immutable stored final packages: 60 broad-1, 60 broad-2 and 81 final-set packages. Three missing final variants remain separate. No inference, deployment or new benchmark.

Changed proposals receive paired native validation and scans. Unchanged packages reuse hash-verified frozen observations with matching tools and unchanged validator/scanner/policy sources. Byte-identical packages have identity deltas. The recorded baseline_method identifies each source. Before/candidate/retained observations use validators and strict scanners offline. Only the new v6 equivalents are proposed; unrelated existing repairs and provider merging are not rerun. Guidance changes alter no replayed IaC bytes and receive no attributed validity/security gain.

| Cohort / scenario | Packages | Valid before → retained (delta) | Strict passes | v1 passes | v2 passes | Strict / v1 / v2 blocker deltas |
|---|---:|---|---|---|---|---|
| broad-1 / all | 60 | 35 → 35 (+0) | 24 → 24 (+0) | 24 → 24 (+0) | 24 → 24 (+0) | +0 / +0 / +0 |
| broad-2 / all | 60 | 37 → 40 (+3) | 19 → 22 (+3) | 19 → 22 (+3) | 19 → 22 (+3) | +0 / +0 / +0 |
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
| broad-2 / 4 | 6 | 2 → 5 (+3) | 2 → 5 (+3) | 2 → 5 (+3) | 2 → 5 (+3) | +0 / +0 / +0 |
| broad-2 / 5 | 6 | 5 → 5 (+0) | 5 → 5 (+0) | 5 → 5 (+0) | 5 → 5 (+0) | +0 / +0 / +0 |
| broad-2 / 6 | 6 | 6 → 6 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-2 / 7 | 6 | 5 → 5 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-2 / 8 | 6 | 2 → 2 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| broad-2 / 9 | 6 | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | +0 / +0 / +0 |
| broad-2 / 10 | 6 | 2 → 2 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| final-1 / final-0 | 23 | 3 → 3 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | +0 / +0 / +0 |
| final-1 / final-1 | 8 | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| final-1 / final-2 | 9 | 6 → 6 (+0) | 6 → 6 (+0) | 6 → 6 (+0) | 6 → 6 (+0) | +0 / +0 / +0 |
| final-2 / final-0 | 24 | 6 → 6 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | 0 → 0 (+0) | +0 / +0 / +0 |
| final-2 / final-1 | 8 | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | 1 → 1 (+0) | +0 / +0 / +0 |
| final-2 / final-2 | 9 | 7 → 7 (+0) | 7 → 7 (+0) | 7 → 7 (+0) | 7 → 7 (+0) | +0 / +0 / +0 |

Broad scenario IDs retain their pre-registration meaning. Final scenario IDs use existing prompt_index metadata: final-0 ECS application (including registered PR-03), final-1 EKS microservices, final-2 static site. No prompt-text matching or cross-scenario pooling.

| Changed proposal | Guard outcome | Failed checks before → candidate | Retained valid |
|---|---|---|---|
| broad-2/67345bcd-26be-493f-89fa-abfeed909159/cost | improved | 2 → 1 | invalid |
| broad-2/67345bcd-26be-493f-89fa-abfeed909159/performance | improved | 1 → 0 | valid |
| broad-2/67345bcd-26be-493f-89fa-abfeed909159/security | improved | 1 → 0 | valid |
| broad-2/9a277d2d-e667-4a06-9f21-f369f64786d4/performance | improved | 2 → 1 | invalid |
| broad-2/0452eefa-601d-4cd3-8934-d23d13c5b5cb/cost | improved | 1 → 0 | valid |

[Migration inventory](migration-inventory.json) includes original generator bytes as a separate audit only. [Per-package evidence](per-package-deltas.json) records candidate/retained hashes, guard records, blocker changes and unknown observations. Inputs and evaluator/tool/provider hashes are bound in the manifests. Unknown/error observations never count as passes.

Provider major-version drift is a discussion finding: a generator can choose a valid v6 constraint while emitting removed v5 syntax. This replay measures narrow migration effects on saved bytes; it does not isolate prompt/guidance causation or establish live deadline/deployment success. Fixed generation caps, recursive tiers, strict acceptance, readiness and thresholds remain unchanged.
