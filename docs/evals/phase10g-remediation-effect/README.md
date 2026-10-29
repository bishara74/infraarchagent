# Phase 10g — does remediation reduce violations on every package?

The universal criterion of reducing violations on every generated package was not met. Across nine development rounds (491 generated packages), recorded strict blocking findings decreased in 465 of 488 comparable packages, were unchanged and non-zero in 19, were zero at both endpoints in 4, and increased in 0; 3 packages lacked a usable comparison. In the final round, the corresponding counts were 57, 1, 0 and 0 out of 58 (0 unknown). All 298 of 298 packages with recorded unresolved blockers were pending_review with the blocking findings visible in their exported reports. Advisory findings are a separate policy category and may remain on packages labelled checks_passed. When advisory findings are included, totals increased on 10 packages overall and 2 in the final round, so a blanket claim that violations never increased is not supported. These are observed scan counts on retained files, with scanner limitations disclosed; repeated scenarios and shared plans make the pooled result descriptive rather than a causal or deployment-security guarantee.

## Inputs and method

Committed evidence revision: `8316d00af00965c12d415932ffe215866167bb00`. [Package CSV](packages.csv) contains one row for each generated package; [input manifest](input-manifest.json) pins committed blobs, cache export bytes, verification outcomes and the analysis script.

The nine agreed rounds are included once each. Missing variants are not generated packages and are excluded; schedule slots are not observations. The aborted first 10e attempt (27 settled packages, 8 checks_passed) is excluded as in Phase 10f. No smoke/stub samples or earlier development rounds enter this pool. The 504 scheduled variant slots comprise 491 generated packages and 13 missing variants, distinct from the three unknown comparisons.

The first endpoint is the earliest recorded automated security scan, after any pre-security generation/validation repair. The endpoint is final_verification on retained files after validation repair. Candidate after_failed/retained_failed are Terraform validation-check counts and are never scanner finding counts. Canonical sessions take precedence over legacy iteration aliases; omitted original sessions make the first endpoint unknown. No rescans, native tools, model calls or external services are used by this analysis.

Strict means recorded strict blocking flags, including existing variant exemptions; contextual-v1/v2 reclassification is not applied. HIGH/CRITICAL counts include only Checkov + Trivy, retaining cross-tool duplicate detections. The stored combined first count can include Terraform and is deliberately not used. All findings = blocking + complete advisory_count. Severity totals cross-check totals; omitted advisory samples do not become invented rule identities or tool attributions.

Classes: reduced means strictly fewer; unchanged_nonzero means equal positive counts; already_zero means both endpoints are zero; increased includes zero to positive; unknown means missing/unverified/inconsistent data. Not increased = reduced + unchanged_nonzero + already_zero. Class percentages use all generated packages in that row; the final two rates use comparable packages only. Counts are per package, not numbers of distinct rule IDs.

### Cache verification coverage

| Round | Generated | Missing variants | Verified exports | Whole-export pin / content projection |
|---|---:|---:|---:|---:|
| final_set_1 | 40 | 2 | 14/14 | 40 / 0 packages |
| final_set_2 | 41 | 1 | 14/14 | 41 / 0 packages |
| broad_1 | 60 | 0 | 20/20 | 60 / 0 packages |
| broad_2 | 60 | 0 | 20/20 | 60 / 0 packages |
| sonnet | 56 | 4 | 20/20 | 0 / 56 packages |
| 10b | 60 | 0 | 20/20 | 60 / 0 packages |
| 10c | 59 | 1 | 20/20 | 59 / 0 packages |
| 10d | 57 | 3 | 20/20 | 57 / 0 packages |
| 10e_final | 58 | 2 | 20/20 | 0 / 58 packages |

Earlier exports match previously committed whole-file SHA-256 values. Sonnet and final 10e instead match committed plan/original/retained canonical hashes plus status, final rule multiplicities, blocking totals, review reasons and validation result. This corroborates package content and final state; their first-scan metadata has no independent historical whole-export attestation. Newly recording export hashes makes this analysis reproducible but does not create that attestation. Any failed verification invalidates the export-derived comparison, while independently committed final blocker counts remain available.

## Counts and percentages

### blocking

| Group | N | Reduced | Unchanged non-zero | Already zero | Increased | Unknown | Reduced/comparable | Not increased/comparable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pooled (nine rounds) | 491 | 465 (94.70%) | 19 (3.87%) | 4 (0.81%) | 0 (0.00%) | 3 (0.61%) | 465/488 (95.29%) | 488/488 (100.00%) |
| final_set_1 | 40 | 40 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 40/40 (100.00%) | 40/40 (100.00%) |
| final_set_2 | 41 | 40 (97.56%) | 1 (2.44%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 40/41 (97.56%) | 41/41 (100.00%) |
| broad_1 | 60 | 57 (95.00%) | 2 (3.33%) | 1 (1.67%) | 0 (0.00%) | 0 (0.00%) | 57/60 (95.00%) | 60/60 (100.00%) |
| broad_2 | 60 | 59 (98.33%) | 0 (0.00%) | 1 (1.67%) | 0 (0.00%) | 0 (0.00%) | 59/60 (98.33%) | 60/60 (100.00%) |
| sonnet | 56 | 53 (94.64%) | 1 (1.79%) | 2 (3.57%) | 0 (0.00%) | 0 (0.00%) | 53/56 (94.64%) | 56/56 (100.00%) |
| 10b | 60 | 49 (81.67%) | 8 (13.33%) | 0 (0.00%) | 0 (0.00%) | 3 (5.00%) | 49/57 (85.96%) | 57/57 (100.00%) |
| 10c | 59 | 53 (89.83%) | 6 (10.17%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 53/59 (89.83%) | 59/59 (100.00%) |
| 10d | 57 | 57 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 57/57 (100.00%) | 57/57 (100.00%) |
| 10e_final | 58 | 57 (98.28%) | 1 (1.72%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 57/58 (98.28%) | 58/58 (100.00%) |
| pooled level 1 | 42 | 37 (88.10%) | 5 (11.90%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 37/42 (88.10%) | 42/42 (100.00%) |
| pooled level 2 | 84 | 66 (78.57%) | 11 (13.10%) | 4 (4.76%) | 0 (0.00%) | 3 (3.57%) | 66/81 (81.48%) | 81/81 (100.00%) |
| pooled level 3 | 84 | 83 (98.81%) | 1 (1.19%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 83/84 (98.81%) | 84/84 (100.00%) |
| pooled level 4 | 121 | 120 (99.17%) | 1 (0.83%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 120/121 (99.17%) | 121/121 (100.00%) |
| pooled level 5 | 79 | 79 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 79/79 (100.00%) | 79/79 (100.00%) |
| legacy complexity unassigned | 81 | 80 (98.77%) | 1 (1.23%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 80/81 (98.77%) | 81/81 (100.00%) |
| broad_1 level 1 | 6 | 6 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 6/6 (100.00%) | 6/6 (100.00%) |
| broad_1 level 2 | 12 | 9 (75.00%) | 2 (16.67%) | 1 (8.33%) | 0 (0.00%) | 0 (0.00%) | 9/12 (75.00%) | 12/12 (100.00%) |
| broad_1 level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| broad_1 level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| broad_1 level 5 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| broad_2 level 1 | 6 | 6 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 6/6 (100.00%) | 6/6 (100.00%) |
| broad_2 level 2 | 12 | 11 (91.67%) | 0 (0.00%) | 1 (8.33%) | 0 (0.00%) | 0 (0.00%) | 11/12 (91.67%) | 12/12 (100.00%) |
| broad_2 level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| broad_2 level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| broad_2 level 5 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| sonnet level 1 | 6 | 6 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 6/6 (100.00%) | 6/6 (100.00%) |
| sonnet level 2 | 12 | 9 (75.00%) | 1 (8.33%) | 2 (16.67%) | 0 (0.00%) | 0 (0.00%) | 9/12 (75.00%) | 12/12 (100.00%) |
| sonnet level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| sonnet level 4 | 15 | 15 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 15/15 (100.00%) | 15/15 (100.00%) |
| sonnet level 5 | 11 | 11 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/11 (100.00%) | 11/11 (100.00%) |
| 10b level 1 | 6 | 5 (83.33%) | 1 (16.67%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 5/6 (83.33%) | 6/6 (100.00%) |
| 10b level 2 | 12 | 4 (33.33%) | 5 (41.67%) | 0 (0.00%) | 0 (0.00%) | 3 (25.00%) | 4/9 (44.44%) | 9/9 (100.00%) |
| 10b level 3 | 12 | 11 (91.67%) | 1 (8.33%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/12 (91.67%) | 12/12 (100.00%) |
| 10b level 4 | 18 | 17 (94.44%) | 1 (5.56%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 17/18 (94.44%) | 18/18 (100.00%) |
| 10b level 5 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10c level 1 | 6 | 3 (50.00%) | 3 (50.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 3/6 (50.00%) | 6/6 (100.00%) |
| 10c level 2 | 12 | 9 (75.00%) | 3 (25.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 9/12 (75.00%) | 12/12 (100.00%) |
| 10c level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10c level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| 10c level 5 | 11 | 11 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/11 (100.00%) | 11/11 (100.00%) |
| 10d level 1 | 6 | 6 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 6/6 (100.00%) | 6/6 (100.00%) |
| 10d level 2 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10d level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10d level 4 | 16 | 16 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 16/16 (100.00%) | 16/16 (100.00%) |
| 10d level 5 | 11 | 11 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/11 (100.00%) | 11/11 (100.00%) |
| 10e_final level 1 | 6 | 5 (83.33%) | 1 (16.67%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 5/6 (83.33%) | 6/6 (100.00%) |
| 10e_final level 2 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10e_final level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10e_final level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| 10e_final level 5 | 10 | 10 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10/10 (100.00%) | 10/10 (100.00%) |

### high_critical

| Group | N | Reduced | Unchanged non-zero | Already zero | Increased | Unknown | Reduced/comparable | Not increased/comparable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pooled (nine rounds) | 491 | 414 (84.32%) | 22 (4.48%) | 52 (10.59%) | 0 (0.00%) | 3 (0.61%) | 414/488 (84.84%) | 488/488 (100.00%) |
| final_set_1 | 40 | 39 (97.50%) | 1 (2.50%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 39/40 (97.50%) | 40/40 (100.00%) |
| final_set_2 | 41 | 39 (95.12%) | 2 (4.88%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 39/41 (95.12%) | 41/41 (100.00%) |
| broad_1 | 60 | 48 (80.00%) | 1 (1.67%) | 11 (18.33%) | 0 (0.00%) | 0 (0.00%) | 48/60 (80.00%) | 60/60 (100.00%) |
| broad_2 | 60 | 49 (81.67%) | 3 (5.00%) | 8 (13.33%) | 0 (0.00%) | 0 (0.00%) | 49/60 (81.67%) | 60/60 (100.00%) |
| sonnet | 56 | 50 (89.29%) | 0 (0.00%) | 6 (10.71%) | 0 (0.00%) | 0 (0.00%) | 50/56 (89.29%) | 56/56 (100.00%) |
| 10b | 60 | 44 (73.33%) | 5 (8.33%) | 8 (13.33%) | 0 (0.00%) | 3 (5.00%) | 44/57 (77.19%) | 57/57 (100.00%) |
| 10c | 59 | 47 (79.66%) | 5 (8.47%) | 7 (11.86%) | 0 (0.00%) | 0 (0.00%) | 47/59 (79.66%) | 59/59 (100.00%) |
| 10d | 57 | 52 (91.23%) | 1 (1.75%) | 4 (7.02%) | 0 (0.00%) | 0 (0.00%) | 52/57 (91.23%) | 57/57 (100.00%) |
| 10e_final | 58 | 46 (79.31%) | 4 (6.90%) | 8 (13.79%) | 0 (0.00%) | 0 (0.00%) | 46/58 (79.31%) | 58/58 (100.00%) |
| pooled level 1 | 42 | 22 (52.38%) | 3 (7.14%) | 17 (40.48%) | 0 (0.00%) | 0 (0.00%) | 22/42 (52.38%) | 42/42 (100.00%) |
| pooled level 2 | 84 | 39 (46.43%) | 9 (10.71%) | 33 (39.29%) | 0 (0.00%) | 3 (3.57%) | 39/81 (48.15%) | 81/81 (100.00%) |
| pooled level 3 | 84 | 80 (95.24%) | 4 (4.76%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 80/84 (95.24%) | 84/84 (100.00%) |
| pooled level 4 | 121 | 119 (98.35%) | 1 (0.83%) | 1 (0.83%) | 0 (0.00%) | 0 (0.00%) | 119/121 (98.35%) | 121/121 (100.00%) |
| pooled level 5 | 79 | 76 (96.20%) | 2 (2.53%) | 1 (1.27%) | 0 (0.00%) | 0 (0.00%) | 76/79 (96.20%) | 79/79 (100.00%) |
| legacy complexity unassigned | 81 | 78 (96.30%) | 3 (3.70%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 78/81 (96.30%) | 81/81 (100.00%) |
| broad_1 level 1 | 6 | 1 (16.67%) | 0 (0.00%) | 5 (83.33%) | 0 (0.00%) | 0 (0.00%) | 1/6 (16.67%) | 6/6 (100.00%) |
| broad_1 level 2 | 12 | 6 (50.00%) | 0 (0.00%) | 6 (50.00%) | 0 (0.00%) | 0 (0.00%) | 6/12 (50.00%) | 12/12 (100.00%) |
| broad_1 level 3 | 12 | 11 (91.67%) | 1 (8.33%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/12 (91.67%) | 12/12 (100.00%) |
| broad_1 level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| broad_1 level 5 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| broad_2 level 1 | 6 | 4 (66.67%) | 0 (0.00%) | 2 (33.33%) | 0 (0.00%) | 0 (0.00%) | 4/6 (66.67%) | 6/6 (100.00%) |
| broad_2 level 2 | 12 | 5 (41.67%) | 1 (8.33%) | 6 (50.00%) | 0 (0.00%) | 0 (0.00%) | 5/12 (41.67%) | 12/12 (100.00%) |
| broad_2 level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| broad_2 level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| broad_2 level 5 | 12 | 10 (83.33%) | 2 (16.67%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10/12 (83.33%) | 12/12 (100.00%) |
| sonnet level 1 | 6 | 6 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 6/6 (100.00%) | 6/6 (100.00%) |
| sonnet level 2 | 12 | 6 (50.00%) | 0 (0.00%) | 6 (50.00%) | 0 (0.00%) | 0 (0.00%) | 6/12 (50.00%) | 12/12 (100.00%) |
| sonnet level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| sonnet level 4 | 15 | 15 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 15/15 (100.00%) | 15/15 (100.00%) |
| sonnet level 5 | 11 | 11 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/11 (100.00%) | 11/11 (100.00%) |
| 10b level 1 | 6 | 2 (33.33%) | 0 (0.00%) | 4 (66.67%) | 0 (0.00%) | 0 (0.00%) | 2/6 (33.33%) | 6/6 (100.00%) |
| 10b level 2 | 12 | 3 (25.00%) | 3 (25.00%) | 3 (25.00%) | 0 (0.00%) | 3 (25.00%) | 3/9 (33.33%) | 9/9 (100.00%) |
| 10b level 3 | 12 | 11 (91.67%) | 1 (8.33%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/12 (91.67%) | 12/12 (100.00%) |
| 10b level 4 | 18 | 16 (88.89%) | 1 (5.56%) | 1 (5.56%) | 0 (0.00%) | 0 (0.00%) | 16/18 (88.89%) | 18/18 (100.00%) |
| 10b level 5 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10c level 1 | 6 | 2 (33.33%) | 1 (16.67%) | 3 (50.00%) | 0 (0.00%) | 0 (0.00%) | 2/6 (33.33%) | 6/6 (100.00%) |
| 10c level 2 | 12 | 6 (50.00%) | 3 (25.00%) | 3 (25.00%) | 0 (0.00%) | 0 (0.00%) | 6/12 (50.00%) | 12/12 (100.00%) |
| 10c level 3 | 12 | 11 (91.67%) | 1 (8.33%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/12 (91.67%) | 12/12 (100.00%) |
| 10c level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| 10c level 5 | 11 | 10 (90.91%) | 0 (0.00%) | 1 (9.09%) | 0 (0.00%) | 0 (0.00%) | 10/11 (90.91%) | 11/11 (100.00%) |
| 10d level 1 | 6 | 6 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 6/6 (100.00%) | 6/6 (100.00%) |
| 10d level 2 | 12 | 7 (58.33%) | 1 (8.33%) | 4 (33.33%) | 0 (0.00%) | 0 (0.00%) | 7/12 (58.33%) | 12/12 (100.00%) |
| 10d level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10d level 4 | 16 | 16 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 16/16 (100.00%) | 16/16 (100.00%) |
| 10d level 5 | 11 | 11 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/11 (100.00%) | 11/11 (100.00%) |
| 10e_final level 1 | 6 | 1 (16.67%) | 2 (33.33%) | 3 (50.00%) | 0 (0.00%) | 0 (0.00%) | 1/6 (16.67%) | 6/6 (100.00%) |
| 10e_final level 2 | 12 | 6 (50.00%) | 1 (8.33%) | 5 (41.67%) | 0 (0.00%) | 0 (0.00%) | 6/12 (50.00%) | 12/12 (100.00%) |
| 10e_final level 3 | 12 | 11 (91.67%) | 1 (8.33%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/12 (91.67%) | 12/12 (100.00%) |
| 10e_final level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| 10e_final level 5 | 10 | 10 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10/10 (100.00%) | 10/10 (100.00%) |

### all

| Group | N | Reduced | Unchanged non-zero | Already zero | Increased | Unknown | Reduced/comparable | Not increased/comparable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pooled (nine rounds) | 491 | 447 (91.04%) | 31 (6.31%) | 0 (0.00%) | 10 (2.04%) | 3 (0.61%) | 447/488 (91.60%) | 478/488 (97.95%) |
| final_set_1 | 40 | 38 (95.00%) | 1 (2.50%) | 0 (0.00%) | 1 (2.50%) | 0 (0.00%) | 38/40 (95.00%) | 39/40 (97.50%) |
| final_set_2 | 41 | 39 (95.12%) | 1 (2.44%) | 0 (0.00%) | 1 (2.44%) | 0 (0.00%) | 39/41 (95.12%) | 40/41 (97.56%) |
| broad_1 | 60 | 53 (88.33%) | 4 (6.67%) | 0 (0.00%) | 3 (5.00%) | 0 (0.00%) | 53/60 (88.33%) | 57/60 (95.00%) |
| broad_2 | 60 | 58 (96.67%) | 2 (3.33%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 58/60 (96.67%) | 60/60 (100.00%) |
| sonnet | 56 | 51 (91.07%) | 5 (8.93%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 51/56 (91.07%) | 56/56 (100.00%) |
| 10b | 60 | 47 (78.33%) | 9 (15.00%) | 0 (0.00%) | 1 (1.67%) | 3 (5.00%) | 47/57 (82.46%) | 56/57 (98.25%) |
| 10c | 59 | 51 (86.44%) | 7 (11.86%) | 0 (0.00%) | 1 (1.69%) | 0 (0.00%) | 51/59 (86.44%) | 58/59 (98.31%) |
| 10d | 57 | 56 (98.25%) | 0 (0.00%) | 0 (0.00%) | 1 (1.75%) | 0 (0.00%) | 56/57 (98.25%) | 56/57 (98.25%) |
| 10e_final | 58 | 54 (93.10%) | 2 (3.45%) | 0 (0.00%) | 2 (3.45%) | 0 (0.00%) | 54/58 (93.10%) | 56/58 (96.55%) |
| pooled level 1 | 42 | 26 (61.90%) | 10 (23.81%) | 0 (0.00%) | 6 (14.29%) | 0 (0.00%) | 26/42 (61.90%) | 36/42 (85.71%) |
| pooled level 2 | 84 | 62 (73.81%) | 17 (20.24%) | 0 (0.00%) | 2 (2.38%) | 3 (3.57%) | 62/81 (76.54%) | 79/81 (97.53%) |
| pooled level 3 | 84 | 83 (98.81%) | 1 (1.19%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 83/84 (98.81%) | 84/84 (100.00%) |
| pooled level 4 | 121 | 120 (99.17%) | 1 (0.83%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 120/121 (99.17%) | 121/121 (100.00%) |
| pooled level 5 | 79 | 79 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 79/79 (100.00%) | 79/79 (100.00%) |
| legacy complexity unassigned | 81 | 77 (95.06%) | 2 (2.47%) | 0 (0.00%) | 2 (2.47%) | 0 (0.00%) | 77/81 (95.06%) | 79/81 (97.53%) |
| broad_1 level 1 | 6 | 4 (66.67%) | 0 (0.00%) | 0 (0.00%) | 2 (33.33%) | 0 (0.00%) | 4/6 (66.67%) | 4/6 (66.67%) |
| broad_1 level 2 | 12 | 7 (58.33%) | 4 (33.33%) | 0 (0.00%) | 1 (8.33%) | 0 (0.00%) | 7/12 (58.33%) | 11/12 (91.67%) |
| broad_1 level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| broad_1 level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| broad_1 level 5 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| broad_2 level 1 | 6 | 6 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 6/6 (100.00%) | 6/6 (100.00%) |
| broad_2 level 2 | 12 | 10 (83.33%) | 2 (16.67%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10/12 (83.33%) | 12/12 (100.00%) |
| broad_2 level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| broad_2 level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| broad_2 level 5 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| sonnet level 1 | 6 | 4 (66.67%) | 2 (33.33%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 4/6 (66.67%) | 6/6 (100.00%) |
| sonnet level 2 | 12 | 9 (75.00%) | 3 (25.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 9/12 (75.00%) | 12/12 (100.00%) |
| sonnet level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| sonnet level 4 | 15 | 15 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 15/15 (100.00%) | 15/15 (100.00%) |
| sonnet level 5 | 11 | 11 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/11 (100.00%) | 11/11 (100.00%) |
| 10b level 1 | 6 | 3 (50.00%) | 2 (33.33%) | 0 (0.00%) | 1 (16.67%) | 0 (0.00%) | 3/6 (50.00%) | 5/6 (83.33%) |
| 10b level 2 | 12 | 4 (33.33%) | 5 (41.67%) | 0 (0.00%) | 0 (0.00%) | 3 (25.00%) | 4/9 (44.44%) | 9/9 (100.00%) |
| 10b level 3 | 12 | 11 (91.67%) | 1 (8.33%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/12 (91.67%) | 12/12 (100.00%) |
| 10b level 4 | 18 | 17 (94.44%) | 1 (5.56%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 17/18 (94.44%) | 18/18 (100.00%) |
| 10b level 5 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10c level 1 | 6 | 2 (33.33%) | 4 (66.67%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 2/6 (33.33%) | 6/6 (100.00%) |
| 10c level 2 | 12 | 8 (66.67%) | 3 (25.00%) | 0 (0.00%) | 1 (8.33%) | 0 (0.00%) | 8/12 (66.67%) | 11/12 (91.67%) |
| 10c level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10c level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| 10c level 5 | 11 | 11 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/11 (100.00%) | 11/11 (100.00%) |
| 10d level 1 | 6 | 5 (83.33%) | 0 (0.00%) | 0 (0.00%) | 1 (16.67%) | 0 (0.00%) | 5/6 (83.33%) | 5/6 (83.33%) |
| 10d level 2 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10d level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10d level 4 | 16 | 16 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 16/16 (100.00%) | 16/16 (100.00%) |
| 10d level 5 | 11 | 11 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 11/11 (100.00%) | 11/11 (100.00%) |
| 10e_final level 1 | 6 | 2 (33.33%) | 2 (33.33%) | 0 (0.00%) | 2 (33.33%) | 0 (0.00%) | 2/6 (33.33%) | 4/6 (66.67%) |
| 10e_final level 2 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10e_final level 3 | 12 | 12 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 12/12 (100.00%) | 12/12 (100.00%) |
| 10e_final level 4 | 18 | 18 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 18/18 (100.00%) | 18/18 (100.00%) |
| 10e_final level 5 | 10 | 10 (100.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 10/10 (100.00%) | 10/10 (100.00%) |

## Unchanged, increased and unknown cases

Every package with an unchanged non-zero, increased or unknown result for any metric is listed below. The CSV includes all three before/after counts, per-metric classes, first/final blocker IDs, advisory sample IDs, scanner statuses and structured reason_evidence. Proposal retained flags describe local actions, not final retention when a later guard rolls back. Reasons are recorded observations with overlap, not exclusive causal assignments. Proposed/introduced findings and rolled-back candidates are labelled separately in reason_evidence; they do not establish a retained regression. No unrecorded explanation is inferred from an unchanged count.

| Round / run / variant | Blocking / HIGH-CRITICAL / all | Recorded reasons | Final blocker IDs |
|---|---|---|---|
| final_set_1 / 9cfb1b01-0754-4796-9443-d88594066dde / cost | 1→0 (reduced) / 1→0 (reduced) / 16→17 (increased) | fix_marked_retained | none recorded |
| final_set_1 / d2512668-53d6-475a-88ae-c5c00f4ddcd1 / cost | 1→0 (reduced) / 1→0 (reduced) / 12→12 (unchanged_nonzero) | fix_marked_retained | none recorded |
| final_set_1 / b0f4701c-ffff-420f-bebd-64df235c1187 / performance | 18→15 (reduced) / 10→10 (unchanged_nonzero) / 44→40 (reduced) | iteration_deadline, iteration_limit, new_blocking_findings, no_improvement, reference_regression, supporting_resources, templates_marked_retained, unknown, unresolved_security_findings, validation_failed | AWS-0052, AWS-0053, AWS-0054, AWS-0077, AWS-0104, AWS-0164, CKV2_AWS_12, CKV2_AWS_20, CKV_AWS_103, CKV_AWS_130, CKV_AWS_2, CKV_AWS_260, CKV_AWS_378, CKV_AWS_91 |
| final_set_2 / eef68d9a-4f49-4c0f-baaf-b7ff9e3d593e / security | 19→19 (unchanged_nonzero) / 10→10 (unchanged_nonzero) / 32→32 (unchanged_nonzero) | already_secure, fix_marked_retained, guards_passed, improved, iteration_limit, new_blocking_findings, no_improvement, reference_regression, round_limit, security_control_removed, terraform_regression, unknown, unresolved_security_findings, validation_failed | AWS-0039, AWS-0040, AWS-0041, AWS-0090, AWS-0104, AWS-0132, AWS-0164, CKV_AWS_130, CKV_AWS_144, CKV_AWS_145, CKV_AWS_157, CKV_AWS_18, CKV_AWS_21, CKV_AWS_354, CKV_AWS_38, CKV_AWS_39, CKV_AWS_58 |
| final_set_2 / 94cf6e79-169f-4929-8bcf-fef1ac7e4ddc / cost | 14→12 (reduced) / 8→8 (unchanged_nonzero) / 28→26 (reduced) | fix_marked_retained, guards_passed, iteration_limit, new_blocking_findings, reference_regression, security_control_removed, supporting_resources, templates_marked_retained, unknown, unresolved_security_findings | AWS-0053, AWS-0054, AWS-0164, CKV2_AWS_12, CKV2_AWS_20, CKV_AWS_103, CKV_AWS_130, CKV_AWS_2, CKV_AWS_378, CKV_AWS_91 |
| final_set_2 / 7cd84341-9393-4947-aa26-f14da8cd17d1 / cost | 22→18 (reduced) / 13→12 (reduced) / 70→71 (increased) | fix_marked_retained, guards_passed, invalid_patch, invalid_syntax, iteration_deadline, iteration_limit, no_improvement, security_control_removed, supporting_resources, templates_marked_retained, unknown, unresolved_security_findings, validation_failed | AWS-0053, AWS-0054, AWS-0090, AWS-0104, AWS-0164, CKV2_AWS_12, CKV2_AWS_20, CKV_AWS_103, CKV_AWS_130, CKV_AWS_2, CKV_AWS_21, CKV_AWS_260, CKV_AWS_378 |
| broad_1 / f7bdc81f-5f5b-46e4-8cb8-88cc99257710 / cost | 1→0 (reduced) / 0→0 (already_zero) / 16→18 (increased) | supporting_resources, templates_marked_retained | none recorded |
| broad_1 / 73e03ef0-86b8-45bc-91b1-2148e8a12e65 / cost | 2→0 (reduced) / 1→0 (reduced) / 17→20 (increased) | fix_marked_retained, supporting_resources, templates_marked_retained | none recorded |
| broad_1 / c81ea7ea-2559-4e20-8173-47f699e12546 / cost | 2→2 (unchanged_nonzero) / 0→0 (already_zero) / 14→14 (unchanged_nonzero) | iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0001, AWS-0024 |
| broad_1 / c81ea7ea-2559-4e20-8173-47f699e12546 / performance | 1→1 (unchanged_nonzero) / 0→0 (already_zero) / 16→16 (unchanged_nonzero) | iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0024 |
| broad_1 / e6dd4c58-6020-4708-bc4a-306885186454 / security | 4→3 (reduced) / 2→2 (unchanged_nonzero) / 24→22 (reduced) | improved, iteration_limit, supporting_resources, templates_marked_retained, terraform_regression, unresolved_security_findings | AWS-0104, CKV_AWS_157 |
| broad_1 / f5fd82a1-8048-4d3e-a78b-f4d2e4ecbd5c / cost | 2→0 (reduced) / 0→0 (already_zero) / 14→14 (unchanged_nonzero) | fix_marked_retained | none recorded |
| broad_1 / f5fd82a1-8048-4d3e-a78b-f4d2e4ecbd5c / security | 0→0 (already_zero) / 0→0 (already_zero) / 12→12 (unchanged_nonzero) | unknown | none recorded |
| broad_1 / 9872a498-f18a-4a9a-a2fa-919c3ca9e983 / cost | 1→0 (reduced) / 0→0 (already_zero) / 6→8 (increased) | supporting_resources, templates_marked_retained | none recorded |
| broad_2 / 93c30ed8-db20-44ba-b701-054f8f6e15b4 / security | 23→21 (reduced) / 9→9 (unchanged_nonzero) / 46→44 (reduced) | catalogue_marked_retained, conflicting_edits, invalid_patch, iteration_limit, new_blocking_findings, no_improvement, secure_default, supporting_resources, templates_marked_retained, terraform_regression, unknown, unresolved_security_findings, validation_failed | AWS-0053, AWS-0077, AWS-0080, AWS-0104, AWS-0164, AWS-0177, CKV2_AWS_12, CKV_AWS_118, CKV_AWS_129, CKV_AWS_130, CKV_AWS_157, CKV_AWS_16, CKV_AWS_260, CKV_AWS_293, CKV_AWS_353, CKV_AWS_354, CKV_AWS_91 |
| broad_2 / d08be9f7-dc06-4d8a-a7dc-649fd495b96f / cost | 18→16 (reduced) / 11→11 (unchanged_nonzero) / 48→46 (reduced) | iteration_limit, new_blocking_findings, no_improvement, security_control_removed, supporting_resources, templates_marked_retained, unknown, unresolved_security_findings, validation_failed | AWS-0053, AWS-0054, AWS-0104, AWS-0107, AWS-0164, CKV2_AWS_12, CKV2_AWS_20, CKV_AWS_103, CKV_AWS_130, CKV_AWS_2, CKV_AWS_24, CKV_AWS_260, CKV_AWS_378, CKV_AWS_91 |
| broad_2 / f46d7016-5b7d-4e38-bee2-3ca0bfe8df07 / performance | 2→0 (reduced) / 0→0 (already_zero) / 14→14 (unchanged_nonzero) | fix_marked_retained | none recorded |
| broad_2 / f46d7016-5b7d-4e38-bee2-3ca0bfe8df07 / security | 0→0 (already_zero) / 0→0 (already_zero) / 14→14 (unchanged_nonzero) | unknown | none recorded |
| broad_2 / c566276f-6530-4b68-9c10-ddf0e2ea11bc / performance | 4→3 (reduced) / 1→1 (unchanged_nonzero) / 16→14 (reduced) | fix_marked_retained, guards_passed, improved, iteration_limit, new_blocking_findings, unresolved_security_findings | AWS-0010, AWS-0011, CKV_AWS_18 |
| sonnet / 7d188d8d-a6d2-4266-969d-472006dee85f / cost | 2→0 (reduced) / 1→0 (reduced) / 6→6 (unchanged_nonzero) | improved, iteration_deadline, supporting_resources, templates_marked_retained | none recorded |
| sonnet / bd33911a-807d-4337-97c0-841ae46861c4 / performance | 0→0 (already_zero) / 0→0 (already_zero) / 22→22 (unchanged_nonzero) | unknown | none recorded |
| sonnet / b0aef019-6efd-4037-b819-911c7aec6402 / performance | 0→0 (already_zero) / 0→0 (already_zero) / 26→26 (unchanged_nonzero) | validation_error | none recorded |
| sonnet / b0aef019-6efd-4037-b819-911c7aec6402 / security | 1→1 (unchanged_nonzero) / 0→0 (already_zero) / 27→27 (unchanged_nonzero) | iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0024 |
| sonnet / 16a38922-8c26-43dc-ad0d-3966d7e82e36 / cost | 2→0 (reduced) / 1→0 (reduced) / 7→7 (unchanged_nonzero) | improved, supporting_resources, templates_marked_retained | none recorded |
| 10b / 4ce9ac90-85de-4c74-ad25-7442f525eb35 / cost | 2→0 (reduced) / 1→0 (reduced) / 7→7 (unchanged_nonzero) | improved, round_limit, supporting_resources, templates_marked_retained | none recorded |
| 10b / aab554ad-00d6-4309-bd3d-825436367ef9 / performance | 3→3 (unchanged_nonzero) / 1→1 (unchanged_nonzero) / 14→14 (unchanged_nonzero) | improved, iteration_limit, new_blocking_findings, terraform_regression, unresolved_security_findings | AWS-0010, AWS-0011, CKV_AWS_18 |
| 10b / 3fdbf756-39d7-451f-9a74-f400b8065eb7 / cost | 2→2 (unchanged_nonzero) / 0→0 (already_zero) / 23→23 (unchanged_nonzero) | iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0001, AWS-0024 |
| 10b / 3fdbf756-39d7-451f-9a74-f400b8065eb7 / performance | None→0 (unknown) / None→None (unknown) / None→None (unknown) | unsafe_file_input | none recorded |
| 10b / 3fdbf756-39d7-451f-9a74-f400b8065eb7 / security | None→0 (unknown) / None→None (unknown) / None→None (unknown) | unsafe_file_input | none recorded |
| 10b / f20ea1e7-75cf-4584-a29f-f91137433ac6 / cost | 9→9 (unchanged_nonzero) / 5→5 (unchanged_nonzero) / 16→16 (unchanged_nonzero) | conflicting_edits, iteration_limit, plan_conformance_conflict, plan_conformance_regression, unresolved_security_findings, validation_failed | AWS-0104, AWS-0107, AWS-0164, AWS-0178, CKV2_AWS_11, CKV2_AWS_12, CKV_AWS_130, CKV_AWS_24, CKV_AWS_260 |
| 10b / f2834e66-2618-434a-b5c7-ae44bed633fe / performance | 6→6 (unchanged_nonzero) / 6→6 (unchanged_nonzero) / 6→6 (unchanged_nonzero) | already_secure, fix_marked_retained, guards_passed, iteration_limit, new_blocking_findings, plan_conformance_conflict, plan_conformance_regression, unresolved_security_findings, validation_failed | AWS-0039, AWS-0040, AWS-0041, CKV_AWS_38, CKV_AWS_39, CKV_AWS_58 |
| 10b / 5c8ae47a-c276-4b66-8212-844ffe886365 / cost | None→0 (unknown) / None→None (unknown) / None→None (unknown) | unsafe_file_input | none recorded |
| 10b / 5c8ae47a-c276-4b66-8212-844ffe886365 / performance | 1→1 (unchanged_nonzero) / 0→0 (already_zero) / 11→11 (unchanged_nonzero) | iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0024 |
| 10b / e722a370-517e-4839-999e-bf0c80de0449 / cost | 4→4 (unchanged_nonzero) / 2→2 (unchanged_nonzero) / 16→16 (unchanged_nonzero) | iteration_limit, new_blocking_findings, no_improvement, plan_conformance_conflict, plan_conformance_regression, unresolved_security_findings, validation_failed | AWS-0010, AWS-0011, AWS-0132, CKV_AWS_18 |
| 10b / e722a370-517e-4839-999e-bf0c80de0449 / performance | 5→5 (unchanged_nonzero) / 2→2 (unchanged_nonzero) / 16→16 (unchanged_nonzero) | fix_marked_retained, guards_passed, improved, iteration_limit, new_blocking_findings, no_improvement, plan_conformance_conflict, plan_conformance_regression, round_limit, unresolved_security_findings, validation_failed | AWS-0010, AWS-0011, AWS-0132, CKV_AWS_145, CKV_AWS_18 |
| 10b / fe00a53b-444d-40d4-baca-18a270073ca7 / cost | 1→0 (reduced) / 0→0 (already_zero) / 6→8 (increased) | supporting_resources, templates_marked_retained | none recorded |
| 10b / fe00a53b-444d-40d4-baca-18a270073ca7 / security | 2→2 (unchanged_nonzero) / 0→0 (already_zero) / 5→5 (unchanged_nonzero) | fix_marked_retained, guards_passed, improved, iteration_limit, new_blocking_findings, plan_conformance_conflict, plan_conformance_regression, terraform_regression, unresolved_security_findings | CKV_AWS_144, CKV_AWS_18 |
| 10c / 8728994d-b9ff-4442-87fe-a8683597f109 / cost | 3→3 (unchanged_nonzero) / 0→0 (already_zero) / 16→16 (unchanged_nonzero) | group_limit, iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0065, CKV_AWS_18, TERRAFORM_FILE_INPUT |
| 10c / 8728994d-b9ff-4442-87fe-a8683597f109 / security | 7→7 (unchanged_nonzero) / 2→2 (unchanged_nonzero) / 20→20 (unchanged_nonzero) | iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0132, CKV_AWS_144, CKV_AWS_145, TERRAFORM_FILE_INPUT |
| 10c / 48945ef8-eb70-41f8-8d07-a7531801b43c / cost | 2→0 (reduced) / 1→0 (reduced) / 13→16 (increased) | fix_marked_retained, plan_conformance_regression, supporting_resources, templates_marked_retained, terraform_regression, validation_failed | none recorded |
| 10c / 1fe0fcae-f8ec-407e-8b46-ebc61499b395 / performance | 2→2 (unchanged_nonzero) / 0→0 (already_zero) / 16→16 (unchanged_nonzero) | iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0024, TERRAFORM_FILE_INPUT |
| 10c / 3c9563c8-ca0c-4578-ad32-598d1bfc0186 / cost | 4→2 (reduced) / 1→1 (unchanged_nonzero) / 6→4 (reduced) | iteration_limit, no_improvement, plan_conformance_conflict, plan_conformance_regression, supporting_resources, templates_marked_retained, unresolved_security_findings, validation_failed | AWS-0164, CKV_AWS_130 |
| 10c / 4254d079-0fbf-4082-9bc0-00209e59e319 / cost | 3→3 (unchanged_nonzero) / 1→1 (unchanged_nonzero) / 29→29 (unchanged_nonzero) | iteration_limit, security_control_removed, terraform_verification_unavailable, unresolved_security_findings, validation_error | AWS-0024, AWS-0104, TERRAFORM_FILE_INPUT |
| 10c / 60bf910d-20e6-4cc4-bea1-7896d6b3880b / performance | 6→6 (unchanged_nonzero) / 1→1 (unchanged_nonzero) / 18→18 (unchanged_nonzero) | iteration_limit, new_blocking_findings, plan_conformance_conflict, plan_conformance_regression, unresolved_security_findings | AWS-0010, AWS-0011, AWS-0065, AWS-0090, CKV_AWS_18, CKV_AWS_21 |
| 10c / 60bf910d-20e6-4cc4-bea1-7896d6b3880b / security | 7→4 (reduced) / 1→1 (unchanged_nonzero) / 18→14 (reduced) | fix_marked_retained, guards_passed, improved, iteration_deadline, iteration_limit, new_blocking_findings, terraform_regression, unresolved_security_findings | AWS-0010, AWS-0011, CKV_AWS_144, CKV_AWS_18 |
| 10c / 826f97bd-5027-49dc-a257-1eef183d8124 / cost | 2→0 (reduced) / 0→0 (already_zero) / 14→14 (unchanged_nonzero) | fix_marked_retained, supporting_resources, templates_marked_retained | none recorded |
| 10c / 826f97bd-5027-49dc-a257-1eef183d8124 / performance | 2→2 (unchanged_nonzero) / 0→0 (already_zero) / 14→14 (unchanged_nonzero) | group_limit, iteration_limit, terraform_verification_unavailable, unresolved_security_findings, validation_error | CKV_AWS_18, TERRAFORM_FILE_INPUT |
| 10d / 4500d38d-2a86-47f3-a4a5-cb96763609b6 / cost | 2→0 (reduced) / 1→0 (reduced) / 6→7 (increased) | fix_marked_retained, supporting_resources, templates_marked_retained, unknown | none recorded |
| 10d / 9373ec16-fcbe-48d0-bbe5-3ccae6f424cd / security | 5→3 (reduced) / 2→2 (unchanged_nonzero) / 17→14 (reduced) | fix_marked_retained, guards_passed, iteration_limit, new_blocking_findings, plan_conformance_conflict, plan_conformance_regression, terraform_regression, unresolved_security_findings | AWS-0010, AWS-0011, AWS-0013 |
| 10e_final / 8384aa1c-8138-450a-8daa-79ec186b7e53 / cost | 1→0 (reduced) / 0→0 (already_zero) / 6→8 (increased) | supporting_resources, templates_marked_retained | none recorded |
| 10e_final / e463e960-e1f3-496d-813b-e10ca3384087 / cost | 5→2 (reduced) / 1→1 (unchanged_nonzero) / 21→17 (reduced) | fix_marked_retained, guards_passed, iteration_limit, terraform_regression, unresolved_security_findings | AWS-0010, AWS-0011 |
| 10e_final / 04eec50b-fdfa-4d79-a7d4-1125a1cf0237 / performance | 5→2 (reduced) / 2→2 (unchanged_nonzero) / 19→15 (reduced) | improved, iteration_limit, supporting_resources, templates_marked_retained, terraform_regression, unresolved_security_findings | AWS-0104 |
| 10e_final / f046df7f-dca6-40e4-8746-156dd2e99643 / cost | 7→2 (reduced) / 1→1 (unchanged_nonzero) / 16→16 (unchanged_nonzero) | fix_marked_retained, guards_passed, invalid_syntax, iteration_limit, new_blocking_findings, supporting_resources, templates_marked_retained, unresolved_security_findings, validation_failed | CKV_AWS_55, TERRAFORM_SYNTAX |
| 10e_final / f046df7f-dca6-40e4-8746-156dd2e99643 / performance | 2→1 (reduced) / 0→0 (already_zero) / 14→16 (increased) | fix_marked_retained, guards_passed, iteration_limit, new_blocking_findings, terraform_verification_unavailable, unresolved_security_findings, validation_error | TERRAFORM_FILE_INPUT |
| 10e_final / f046df7f-dca6-40e4-8746-156dd2e99643 / security | 3→3 (unchanged_nonzero) / 1→1 (unchanged_nonzero) / 12→12 (unchanged_nonzero) | iteration_limit, new_blocking_findings, terraform_regression, unknown, unresolved_security_findings | AWS-0132, CKV_AWS_144, CKV_AWS_145 |

## Review visibility and literal-criterion qualifications

- pooled (nine rounds): 298/298 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 189 advisory-only packages, of which 126 are checks_passed.
- final_set_1: 24/24 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 16 advisory-only packages, of which 7 are checks_passed.
- final_set_2: 28/28 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 13 advisory-only packages, of which 8 are checks_passed.
- broad_1: 26/26 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 34 advisory-only packages, of which 24 are checks_passed.
- broad_2: 33/33 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 27 advisory-only packages, of which 19 are checks_passed.
- sonnet: 31/31 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 25 advisory-only packages, of which 24 are checks_passed.
- 10b: 47/47 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 10 advisory-only packages, of which 7 are checks_passed.
- 10c: 38/38 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 21 advisory-only packages, of which 11 are checks_passed.
- 10d: 38/38 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 19 advisory-only packages, of which 11 are checks_passed.
- 10e_final: 33/33 unresolved-blocker packages have pending_review, full recorded blocker IDs, unresolved_security_findings and review_available=true; 24 advisory-only packages, of which 15 are checks_passed.

Blocking-status/visibility exceptions: **0**.

Advisory-only packages outside pending_review are exceptions to a literal requirement that every remaining finding forces review, although strict readiness deliberately permits advisories. Their identifiers and sample-only visibility limits follow:

- final_set_1 / eb3fca7b-e12c-4ef2-b91b-82a4ba9de4d7 / cost: checks_passed, 27 advisories; recorded sample IDs AWS-0017, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_5, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_336, CKV_AWS_338, CKV_AWS_354, CKV_AWS_394, CKV_AWS_65, CKV_AWS_88; omitted identities 7.
- final_set_1 / fc77f4a8-0d04-4eb3-aba6-756eab6dbc80 / cost: checks_passed, 18 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_1 / 9cfb1b01-0754-4796-9443-d88594066dde / cost: checks_passed, 17 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_1 / 9cfb1b01-0754-4796-9443-d88594066dde / performance: checks_passed, 17 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_1 / d2512668-53d6-475a-88ae-c5c00f4ddcd1 / cost: checks_passed, 12 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_174, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_1 / d2512668-53d6-475a-88ae-c5c00f4ddcd1 / performance: checks_passed, 16 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_1 / d2512668-53d6-475a-88ae-c5c00f4ddcd1 / security: checks_passed, 15 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_2 / 0ce03b0b-e05d-476b-a08d-42de4692f6a8 / performance: checks_passed, 16 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_2 / 0ce03b0b-e05d-476b-a08d-42de4692f6a8 / security: checks_passed, 14 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_2 / eef68d9a-4f49-4c0f-baaf-b7ff9e3d593e / cost: checks_passed, 22 advisories; recorded sample IDs AWS-0017, AWS-0078, CKV2_AWS_30, CKV2_AWS_60, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145, CKV_AWS_157, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_338, CKV_AWS_354, CKV_AWS_355, CKV_AWS_394; omitted identities 2.
- final_set_2 / b510f683-95e9-4cb0-8482-482e93409ad0 / cost: checks_passed, 17 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_2 / b510f683-95e9-4cb0-8482-482e93409ad0 / performance: checks_passed, 14 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_2 / b510f683-95e9-4cb0-8482-482e93409ad0 / security: checks_passed, 18 advisories; recorded sample IDs AWS-0089, AWS-0099, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_5, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_23, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_2 / c0d5bbc8-36b6-4641-9a2f-5faeb3b96ba7 / cost: checks_passed, 20 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- final_set_2 / c0d5bbc8-36b6-4641-9a2f-5faeb3b96ba7 / security: checks_passed, 12 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- broad_1 / f7bdc81f-5f5b-46e4-8cb8-88cc99257710 / cost: checks_passed, 18 advisories; recorded sample IDs AWS-0017, AWS-0066, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_144, CKV_AWS_145, CKV_AWS_158, CKV_AWS_173, CKV_AWS_272, CKV_AWS_338, CKV_AWS_50; omitted identities 0.
- broad_1 / f7bdc81f-5f5b-46e4-8cb8-88cc99257710 / performance: checks_passed, 10 advisories; recorded sample IDs AWS-0066, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_144, CKV_AWS_272, CKV_AWS_50; omitted identities 0.
- broad_1 / f7bdc81f-5f5b-46e4-8cb8-88cc99257710 / security: checks_passed, 12 advisories; recorded sample IDs AWS-0066, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_173, CKV_AWS_272, CKV_AWS_301, CKV_AWS_363, CKV_AWS_50; omitted identities 0.
- broad_1 / 73e03ef0-86b8-45bc-91b1-2148e8a12e65 / cost: checks_passed, 20 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_42, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145, CKV_AWS_174, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- broad_1 / c81ea7ea-2559-4e20-8173-47f699e12546 / security: checks_passed, 14 advisories; recorded sample IDs AWS-0004, AWS-0025, AWS-0066, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_363, CKV_AWS_50, CKV_AWS_59; omitted identities 0.
- broad_1 / 34568752-de05-4ede-a5d9-0d22aafeffc6 / cost: checks_passed, 7 advisories; recorded sample IDs AWS-0017, AWS-0099, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_23, CKV_AWS_338; omitted identities 0.
- broad_1 / 34568752-de05-4ede-a5d9-0d22aafeffc6 / performance: checks_passed, 11 advisories; recorded sample IDs AWS-0017, AWS-0124, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_23, CKV_AWS_290, CKV_AWS_338, CKV_AWS_355; omitted identities 0.
- broad_1 / 34568752-de05-4ede-a5d9-0d22aafeffc6 / security: checks_passed, 4 advisories; recorded sample IDs CKV_AWS_126, CKV_AWS_135, CKV_AWS_338, CKV_AWS_394; omitted identities 0.
- broad_1 / 5fff70ec-0135-4c61-acda-683e7aebb59a / cost: checks_passed, 15 advisories; recorded sample IDs AWS-0078, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_226, CKV_AWS_23, CKV_AWS_354; omitted identities 0.
- broad_1 / 5fff70ec-0135-4c61-acda-683e7aebb59a / security: checks_passed, 11 advisories; recorded sample IDs AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_226, CKV_AWS_23, CKV_AWS_394; omitted identities 0.
- broad_1 / b7c1aa22-26fa-45a7-9754-ea487df14e75 / cost: checks_passed, 9 advisories; recorded sample IDs CKV2_K8S_6, CKV_K8S_15, CKV_K8S_21, CKV_K8S_38, CKV_K8S_43, CKV_K8S_8, CKV_K8S_9, KSV-0110; omitted identities 0.
- broad_1 / 2917b836-744c-443e-8a7a-10d97ad8f659 / cost: checks_passed, 34 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_150, CKV_AWS_157, CKV_AWS_158, CKV_AWS_184, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_336, CKV_AWS_338, CKV_AWS_354, CKV_AWS_355, CKV_AWS_65; omitted identities 14.
- broad_1 / a4ce7d9a-54e9-4a64-b158-c0e0896c519f / cost: checks_passed, 49 advisories; recorded sample IDs CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_62, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_226, CKV_AWS_23, CKV_AWS_336, CKV_AWS_354, CKV_AWS_65; omitted identities 29.
- broad_1 / e6dd4c58-6020-4708-bc4a-306885186454 / performance: checks_passed, 11 advisories; recorded sample IDs AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_226, CKV_AWS_23, CKV_AWS_394; omitted identities 0.
- broad_1 / 5c6df590-c0db-4e15-b602-335adc304e94 / cost: checks_passed, 8 advisories; recorded sample IDs AWS-0017, AWS-0124, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_23, CKV_AWS_338, CKV_AWS_394; omitted identities 0.
- broad_1 / 5c6df590-c0db-4e15-b602-335adc304e94 / performance: checks_passed, 5 advisories; recorded sample IDs AWS-0017, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_338; omitted identities 0.
- broad_1 / 5c6df590-c0db-4e15-b602-335adc304e94 / security: checks_passed, 5 advisories; recorded sample IDs AWS-0124, CKV2_AWS_5, CKV_AWS_126, CKV_AWS_135, CKV_AWS_23; omitted identities 0.
- broad_1 / f5fd82a1-8048-4d3e-a78b-f4d2e4ecbd5c / cost: checks_passed, 14 advisories; recorded sample IDs AWS-0017, AWS-0025, AWS-0066, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_158, CKV_AWS_272, CKV_AWS_309, CKV_AWS_338, CKV_AWS_363, CKV_AWS_50, CKV_AWS_66; omitted identities 0.
- broad_1 / f5fd82a1-8048-4d3e-a78b-f4d2e4ecbd5c / security: checks_passed, 12 advisories; recorded sample IDs AWS-0004, AWS-0025, AWS-0066, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_237, CKV_AWS_272, CKV_AWS_50, CKV_AWS_59; omitted identities 0.
- broad_1 / 113c0c5b-49cc-468b-a712-74c7c2d1adf1 / performance: checks_passed, 15 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_175, CKV_AWS_192, CKV_AWS_305, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- broad_1 / 113c0c5b-49cc-468b-a712-74c7c2d1adf1 / security: checks_passed, 12 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- broad_1 / 9872a498-f18a-4a9a-a2fa-919c3ca9e983 / cost: checks_passed, 8 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145, CKV_AWS_300; omitted identities 0.
- broad_1 / 9872a498-f18a-4a9a-a2fa-919c3ca9e983 / performance: checks_passed, 6 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144; omitted identities 0.
- broad_1 / 9872a498-f18a-4a9a-a2fa-919c3ca9e983 / security: checks_passed, 3 advisories; recorded sample IDs CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_300; omitted identities 0.
- broad_2 / 7b0493ba-e06b-4b1c-9f1e-18d1df8b7d23 / cost: checks_passed, 14 advisories; recorded sample IDs AWS-0066, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_144, CKV_AWS_272, CKV_AWS_363, CKV_AWS_50; omitted identities 0.
- broad_2 / 7b0493ba-e06b-4b1c-9f1e-18d1df8b7d23 / security: checks_passed, 9 advisories; recorded sample IDs AWS-0066, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_272, CKV_AWS_50; omitted identities 0.
- broad_2 / da8bc90b-31d5-44d6-bf01-e149ee3b362c / security: checks_passed, 9 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- broad_2 / 1c410860-15e7-495e-8567-50debdd8d438 / cost: checks_passed, 22 advisories; recorded sample IDs AWS-0003, AWS-0004, AWS-0017, CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_338, CKV_AWS_50, CKV_AWS_59, CKV_AWS_73; omitted identities 2.
- broad_2 / 1c410860-15e7-495e-8567-50debdd8d438 / security: checks_passed, 20 advisories; recorded sample IDs AWS-0004, AWS-0017, AWS-0025, AWS-0066, CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_338, CKV_AWS_50, CKV_AWS_59; omitted identities 0.
- broad_2 / 3f908f47-88ef-41a9-82e5-11a9c2301141 / cost: checks_passed, 19 advisories; recorded sample IDs AWS-0078, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_126, CKV_AWS_135, CKV_AWS_144, CKV_AWS_145, CKV_AWS_157, CKV_AWS_226, CKV_AWS_290, CKV_AWS_354, CKV_AWS_355, CKV_AWS_394; omitted identities 0.
- broad_2 / 3f908f47-88ef-41a9-82e5-11a9c2301141 / security: checks_passed, 11 advisories; recorded sample IDs CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV2_AWS_64, CKV_AWS_126, CKV_AWS_135, CKV_AWS_226, CKV_AWS_290, CKV_AWS_338, CKV_AWS_355, CKV_AWS_394; omitted identities 0.
- broad_2 / 93c30ed8-db20-44ba-b701-054f8f6e15b4 / cost: checks_passed, 26 advisories; recorded sample IDs AWS-0034, CKV2_AWS_30, CKV2_AWS_60, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145, CKV_AWS_150, CKV_AWS_157, CKV_AWS_226, CKV_AWS_23, CKV_AWS_261, CKV_AWS_336, CKV_AWS_354, CKV_AWS_394, CKV_AWS_65; omitted identities 6.
- broad_2 / a62094cd-8a5a-42c5-9970-c583a56c1129 / cost: checks_passed, 14 advisories; recorded sample IDs AWS-0078, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_226, CKV_AWS_23, CKV_AWS_354; omitted identities 0.
- broad_2 / a62094cd-8a5a-42c5-9970-c583a56c1129 / performance: checks_passed, 15 advisories; recorded sample IDs AWS-0017, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_338, CKV_AWS_394; omitted identities 0.
- broad_2 / a62094cd-8a5a-42c5-9970-c583a56c1129 / security: checks_passed, 12 advisories; recorded sample IDs AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_355; omitted identities 0.
- broad_2 / 0452eefa-601d-4cd3-8934-d23d13c5b5cb / performance: checks_passed, 3 advisories; recorded sample IDs CKV_AWS_126, CKV_AWS_135, CKV_AWS_394; omitted identities 0.
- broad_2 / 0452eefa-601d-4cd3-8934-d23d13c5b5cb / security: checks_passed, 8 advisories; recorded sample IDs CKV2_AWS_19, CKV2_AWS_64, CKV_AWS_126, CKV_AWS_135, CKV_AWS_290, CKV_AWS_338, CKV_AWS_355, CKV_AWS_394; omitted identities 0.
- broad_2 / f46d7016-5b7d-4e38-bee2-3ca0bfe8df07 / cost: checks_passed, 12 advisories; recorded sample IDs AWS-0017, AWS-0025, AWS-0066, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_158, CKV_AWS_272, CKV_AWS_309, CKV_AWS_338, CKV_AWS_50; omitted identities 0.
- broad_2 / f46d7016-5b7d-4e38-bee2-3ca0bfe8df07 / performance: checks_passed, 14 advisories; recorded sample IDs AWS-0017, AWS-0025, AWS-0066, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_158, CKV_AWS_173, CKV_AWS_272, CKV_AWS_309, CKV_AWS_338, CKV_AWS_50, CKV_AWS_66; omitted identities 0.
- broad_2 / f46d7016-5b7d-4e38-bee2-3ca0bfe8df07 / security: checks_passed, 14 advisories; recorded sample IDs AWS-0017, AWS-0025, AWS-0066, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_158, CKV_AWS_173, CKV_AWS_272, CKV_AWS_309, CKV_AWS_338, CKV_AWS_363, CKV_AWS_50; omitted identities 0.
- broad_2 / c566276f-6530-4b68-9c10-ddf0e2ea11bc / cost: checks_passed, 16 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145, CKV_AWS_175, CKV_AWS_192, CKV_AWS_305, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- broad_2 / 8e7ace81-03e9-4fcf-9258-a326211fb0d9 / cost: checks_passed, 7 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144; omitted identities 0.
- broad_2 / 8e7ace81-03e9-4fcf-9258-a326211fb0d9 / performance: checks_passed, 12 advisories; recorded sample IDs AWS-0017, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_158, CKV_AWS_290, CKV_AWS_338, CKV_AWS_355; omitted identities 0.
- sonnet / 7d188d8d-a6d2-4266-969d-472006dee85f / cost: checks_passed, 6 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145; omitted identities 0.
- sonnet / 7d188d8d-a6d2-4266-969d-472006dee85f / performance: checks_passed, 2 advisories; recorded sample IDs CKV2_AWS_62, CKV_AWS_144; omitted identities 0.
- sonnet / 41e955c2-905f-4694-a060-a42971ebd38e / cost: checks_passed, 16 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- sonnet / 41e955c2-905f-4694-a060-a42971ebd38e / performance: checks_passed, 17 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_38, CKV2_AWS_39, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- sonnet / bd33911a-807d-4337-97c0-841ae46861c4 / cost: checks_passed, 26 advisories; recorded sample IDs CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_173, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_338, CKV_AWS_50, CKV_AWS_59, CKV_AWS_73; omitted identities 6.
- sonnet / bd33911a-807d-4337-97c0-841ae46861c4 / performance: checks_passed, 22 advisories; recorded sample IDs AWS-0003, AWS-0004, AWS-0017, CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_338, CKV_AWS_50, CKV_AWS_59, CKV_AWS_73; omitted identities 2.
- sonnet / bd33911a-807d-4337-97c0-841ae46861c4 / security: checks_passed, 23 advisories; recorded sample IDs AWS-0003, AWS-0004, AWS-0017, CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_50, CKV_AWS_59, CKV_AWS_73; omitted identities 3.
- sonnet / 9a1ab4bb-5605-4077-a857-702114488fd1 / cost: checks_passed, 5 advisories; recorded sample IDs AWS-0124, CKV_AWS_126, CKV_AWS_135, CKV_AWS_23, CKV_AWS_394; omitted identities 0.
- sonnet / 9a1ab4bb-5605-4077-a857-702114488fd1 / performance: checks_passed, 5 advisories; recorded sample IDs AWS-0124, CKV_AWS_126, CKV_AWS_135, CKV_AWS_23, CKV_AWS_394; omitted identities 0.
- sonnet / 9a1ab4bb-5605-4077-a857-702114488fd1 / security: checks_passed, 3 advisories; recorded sample IDs CKV_AWS_126, CKV_AWS_135, CKV_AWS_338; omitted identities 0.
- sonnet / 65f335f3-cea4-489c-8c25-633a6ea22947 / cost: checks_passed, 16 advisories; recorded sample IDs AWS-0017, AWS-0078, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_158, CKV_AWS_226, CKV_AWS_290, CKV_AWS_338, CKV_AWS_354, CKV_AWS_355, CKV_AWS_394, CKV_AWS_88; omitted identities 0.
- sonnet / 65f335f3-cea4-489c-8c25-633a6ea22947 / performance: checks_passed, 5 advisories; recorded sample IDs CKV2_AWS_30, CKV2_AWS_5, CKV2_AWS_60, CKV_AWS_226, CKV_AWS_394; omitted identities 0.
- sonnet / db8947e0-0f5c-4ae8-8f6b-87223cabc014 / cost: checks_passed, 14 advisories; recorded sample IDs AWS-0017, AWS-0078, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_158, CKV_AWS_226, CKV_AWS_338, CKV_AWS_354, CKV_AWS_394, CKV_AWS_88; omitted identities 0.
- sonnet / db8947e0-0f5c-4ae8-8f6b-87223cabc014 / performance: checks_passed, 17 advisories; recorded sample IDs AWS-0027, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_189, CKV_AWS_226, CKV_AWS_23, CKV_AWS_394, CKV_AWS_88; omitted identities 0.
- sonnet / db8947e0-0f5c-4ae8-8f6b-87223cabc014 / security: checks_passed, 15 advisories; recorded sample IDs AWS-0027, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_126, CKV_AWS_135, CKV_AWS_189, CKV_AWS_226, CKV_AWS_290, CKV_AWS_338, CKV_AWS_355, CKV_AWS_394, CKV_AWS_88; omitted identities 0.
- sonnet / 88540900-8bda-4d2a-8378-0efad3d13b6e / cost: checks_passed, 5 advisories; recorded sample IDs AWS-0099, CKV_AWS_126, CKV_AWS_135, CKV_AWS_23, CKV_AWS_394; omitted identities 0.
- sonnet / 88540900-8bda-4d2a-8378-0efad3d13b6e / performance: checks_passed, 2 advisories; recorded sample IDs CKV_AWS_126, CKV_AWS_135; omitted identities 0.
- sonnet / 88540900-8bda-4d2a-8378-0efad3d13b6e / security: checks_passed, 2 advisories; recorded sample IDs CKV_AWS_126, CKV_AWS_135; omitted identities 0.
- sonnet / b0aef019-6efd-4037-b819-911c7aec6402 / cost: checks_passed, 22 advisories; recorded sample IDs AWS-0003, AWS-0004, AWS-0017, CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_338, CKV_AWS_50, CKV_AWS_59, CKV_AWS_73; omitted identities 2.
- sonnet / 7cf44f18-6db7-4a1b-8a53-be141696b973 / cost: checks_passed, 23 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 3.
- sonnet / 7cf44f18-6db7-4a1b-8a53-be141696b973 / performance: checks_passed, 15 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- sonnet / 7cf44f18-6db7-4a1b-8a53-be141696b973 / security: checks_passed, 15 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_38, CKV2_AWS_39, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- sonnet / 16a38922-8c26-43dc-ad0d-3966d7e82e36 / cost: checks_passed, 7 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145, CKV_AWS_300; omitted identities 0.
- sonnet / 16a38922-8c26-43dc-ad0d-3966d7e82e36 / performance: checks_passed, 2 advisories; recorded sample IDs CKV2_AWS_62, CKV_AWS_144; omitted identities 0.
- 10b / 4ce9ac90-85de-4c74-ad25-7442f525eb35 / cost: checks_passed, 7 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145, CKV_AWS_300; omitted identities 0.
- 10b / 4ce9ac90-85de-4c74-ad25-7442f525eb35 / performance: checks_passed, 4 advisories; recorded sample IDs CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_300; omitted identities 0.
- 10b / 4ce9ac90-85de-4c74-ad25-7442f525eb35 / security: checks_passed, 5 advisories; recorded sample IDs AWS-0089, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_300; omitted identities 0.
- 10b / c5f34525-c392-49e2-b57d-dcd5a8f1116b / performance: checks_passed, 14 advisories; recorded sample IDs AWS-0017, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_338; omitted identities 0.
- 10b / c5f34525-c392-49e2-b57d-dcd5a8f1116b / security: checks_passed, 14 advisories; recorded sample IDs AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_355, CKV_AWS_394; omitted identities 0.
- 10b / fe00a53b-444d-40d4-baca-18a270073ca7 / cost: checks_passed, 8 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145, CKV_AWS_300; omitted identities 0.
- 10b / fe00a53b-444d-40d4-baca-18a270073ca7 / performance: checks_passed, 4 advisories; recorded sample IDs CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_300; omitted identities 0.
- 10c / 48945ef8-eb70-41f8-8d07-a7531801b43c / security: checks_passed, 10 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_175, CKV_AWS_192, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- 10c / 1fe0fcae-f8ec-407e-8b46-ebc61499b395 / cost: checks_passed, 23 advisories; recorded sample IDs AWS-0003, AWS-0004, CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_338, CKV_AWS_363, CKV_AWS_50, CKV_AWS_59, CKV_AWS_73; omitted identities 3.
- 10c / 3c9563c8-ca0c-4578-ad32-598d1bfc0186 / security: checks_passed, 6 advisories; recorded sample IDs AWS-0017, CKV2_AWS_19, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_338; omitted identities 0.
- 10c / c54428da-5e1f-4eeb-8bc1-424098d364c2 / cost: checks_passed, 17 advisories; recorded sample IDs AWS-0078, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_354, CKV_AWS_355, CKV_AWS_394; omitted identities 0.
- 10c / c54428da-5e1f-4eeb-8bc1-424098d364c2 / performance: checks_passed, 11 advisories; recorded sample IDs AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_226, CKV_AWS_23; omitted identities 0.
- 10c / 8612043e-16e1-442d-9758-ac6479c5fd7b / security: checks_passed, 11 advisories; recorded sample IDs AWS-0034, AWS-0124, CKV2_AWS_30, CKV2_AWS_60, CKV_AWS_226, CKV_AWS_23, CKV_AWS_336, CKV_AWS_394, CKV_AWS_65; omitted identities 0.
- 10c / 69bf73f7-a381-4cec-8029-5b2890734fa4 / cost: checks_passed, 17 advisories; recorded sample IDs AWS-0017, AWS-0078, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_338, CKV_AWS_354, CKV_AWS_394; omitted identities 0.
- 10c / 69bf73f7-a381-4cec-8029-5b2890734fa4 / performance: checks_passed, 17 advisories; recorded sample IDs AWS-0017, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_338, CKV_AWS_355, CKV_AWS_394; omitted identities 0.
- 10c / 69bf73f7-a381-4cec-8029-5b2890734fa4 / security: checks_passed, 15 advisories; recorded sample IDs AWS-0017, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_338, CKV_AWS_355; omitted identities 0.
- 10c / 4254d079-0fbf-4082-9bc0-00209e59e319 / performance: checks_passed, 12 advisories; recorded sample IDs AWS-0017, AWS-0025, AWS-0066, CKV_AWS_115, CKV_AWS_116, CKV_AWS_119, CKV_AWS_158, CKV_AWS_272, CKV_AWS_309, CKV_AWS_338, CKV_AWS_363, CKV_AWS_50; omitted identities 0.
- 10c / 826f97bd-5027-49dc-a257-1eef183d8124 / cost: checks_passed, 14 advisories; recorded sample IDs AWS-0066, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_144, CKV_AWS_145, CKV_AWS_272, CKV_AWS_50; omitted identities 0.
- 10d / 4500d38d-2a86-47f3-a4a5-cb96763609b6 / cost: checks_passed, 7 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145; omitted identities 0.
- 10d / 4500d38d-2a86-47f3-a4a5-cb96763609b6 / performance: checks_passed, 3 advisories; recorded sample IDs CKV2_AWS_62, CKV_AWS_144, CKV_AWS_300; omitted identities 0.
- 10d / 4500d38d-2a86-47f3-a4a5-cb96763609b6 / security: checks_passed, 2 advisories; recorded sample IDs CKV2_AWS_62, CKV_AWS_300; omitted identities 0.
- 10d / a2adf369-600c-4472-960f-d32ae39e0790 / security: checks_passed, 24 advisories; recorded sample IDs AWS-0003, AWS-0004, CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_217, CKV_AWS_23, CKV_AWS_237, CKV_AWS_272, CKV_AWS_338, CKV_AWS_394, CKV_AWS_50, CKV_AWS_59, CKV_AWS_73; omitted identities 4.
- 10d / 1404d80a-5bbd-472f-9cd8-7b257919f3d6 / cost: checks_passed, 4 advisories; recorded sample IDs AWS-0124, CKV_AWS_126, CKV_AWS_135, CKV_AWS_23; omitted identities 0.
- 10d / 1404d80a-5bbd-472f-9cd8-7b257919f3d6 / security: checks_passed, 5 advisories; recorded sample IDs AWS-0124, CKV_AWS_126, CKV_AWS_135, CKV_AWS_23, CKV_AWS_394; omitted identities 0.
- 10d / 2a69d77d-3e8c-48bd-9fe9-65746b54bb1b / cost: checks_passed, 14 advisories; recorded sample IDs AWS-0078, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_226, CKV_AWS_23, CKV_AWS_354; omitted identities 0.
- 10d / 2a69d77d-3e8c-48bd-9fe9-65746b54bb1b / security: checks_passed, 17 advisories; recorded sample IDs AWS-0017, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_338; omitted identities 0.
- 10d / 897fb4bb-1f6d-4bdd-bf75-a5a9bb9237c7 / cost: checks_passed, 3 advisories; recorded sample IDs CKV_AWS_126, CKV_AWS_135, CKV_AWS_394; omitted identities 0.
- 10d / 897fb4bb-1f6d-4bdd-bf75-a5a9bb9237c7 / performance: checks_passed, 3 advisories; recorded sample IDs CKV2_AWS_41, CKV_AWS_126, CKV_AWS_135; omitted identities 0.
- 10d / 3dae2cb1-be93-44cf-b0c9-00dcb92105f7 / performance: checks_passed, 13 advisories; recorded sample IDs AWS-0004, AWS-0025, AWS-0066, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_50, CKV_AWS_59; omitted identities 0.
- 10e_final / 8384aa1c-8138-450a-8daa-79ec186b7e53 / cost: checks_passed, 8 advisories; recorded sample IDs CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_145, CKV_AWS_300; omitted identities 0.
- 10e_final / 8384aa1c-8138-450a-8daa-79ec186b7e53 / performance: checks_passed, 3 advisories; recorded sample IDs CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144; omitted identities 0.
- 10e_final / 8384aa1c-8138-450a-8daa-79ec186b7e53 / security: checks_passed, 2 advisories; recorded sample IDs CKV2_AWS_62, CKV_AWS_300; omitted identities 0.
- 10e_final / e463e960-e1f3-496d-813b-e10ca3384087 / performance: checks_passed, 17 advisories; recorded sample IDs CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_38, CKV2_AWS_39, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144, CKV_AWS_175, CKV_AWS_192, CKV_AWS_233, CKV_AWS_310, CKV_AWS_374; omitted identities 0.
- 10e_final / e463e960-e1f3-496d-813b-e10ca3384087 / security: checks_passed, 15 advisories; recorded sample IDs AWS-0089, CKV2_AWS_31, CKV2_AWS_32, CKV2_AWS_47, CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_175, CKV_AWS_192, CKV_AWS_290, CKV_AWS_310, CKV_AWS_355, CKV_AWS_374; omitted identities 0.
- 10e_final / 5232a134-8866-48fb-8f05-8cd18f15df8a / cost: checks_passed, 2 advisories; recorded sample IDs CKV_AWS_126, CKV_AWS_135; omitted identities 0.
- 10e_final / 5232a134-8866-48fb-8f05-8cd18f15df8a / security: checks_passed, 7 advisories; recorded sample IDs AWS-0027, CKV_AWS_126, CKV_AWS_135, CKV_AWS_189, CKV_AWS_290, CKV_AWS_355, CKV_AWS_394; omitted identities 0.
- 10e_final / 04eec50b-fdfa-4d79-a7d4-1125a1cf0237 / cost: checks_passed, 14 advisories; recorded sample IDs AWS-0078, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_226, CKV_AWS_23, CKV_AWS_354, CKV_AWS_394; omitted identities 0.
- 10e_final / 04eec50b-fdfa-4d79-a7d4-1125a1cf0237 / security: checks_passed, 13 advisories; recorded sample IDs AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_355; omitted identities 0.
- 10e_final / 441d1377-5495-4b45-bd5d-cfd740096e82 / performance: checks_passed, 1 advisories; recorded sample IDs CKV_AWS_394; omitted identities 0.
- 10e_final / 07cae62b-a795-4143-a142-a901a242cdf4 / cost: checks_passed, 18 advisories; recorded sample IDs AWS-0017, AWS-0078, AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_157, CKV_AWS_158, CKV_AWS_226, CKV_AWS_23, CKV_AWS_338, CKV_AWS_354; omitted identities 0.
- 10e_final / 07cae62b-a795-4143-a142-a901a242cdf4 / performance: checks_passed, 10 advisories; recorded sample IDs AWS-0124, CKV2_AWS_30, CKV2_AWS_41, CKV2_AWS_60, CKV_AWS_126, CKV_AWS_135, CKV_AWS_226, CKV_AWS_23, CKV_AWS_290, CKV_AWS_355; omitted identities 0.
- 10e_final / 8acefba7-e492-4865-add0-54929c7a15b9 / cost: checks_passed, 4 advisories; recorded sample IDs AWS-0124, CKV_AWS_126, CKV_AWS_135, CKV_AWS_23; omitted identities 0.
- 10e_final / 8acefba7-e492-4865-add0-54929c7a15b9 / security: checks_passed, 6 advisories; recorded sample IDs AWS-0017, CKV_AWS_126, CKV_AWS_135, CKV_AWS_158, CKV_AWS_338, CKV_AWS_66; omitted identities 0.
- 10e_final / 1fed5896-3968-40b9-a79c-8fcc8244731a / cost: checks_passed, 22 advisories; recorded sample IDs AWS-0003, AWS-0004, AWS-0017, CKV2_AWS_29, CKV2_AWS_4, CKV2_AWS_51, CKV2_AWS_53, CKV_AWS_115, CKV_AWS_116, CKV_AWS_117, CKV_AWS_119, CKV_AWS_120, CKV_AWS_158, CKV_AWS_217, CKV_AWS_237, CKV_AWS_272, CKV_AWS_338, CKV_AWS_50, CKV_AWS_59, CKV_AWS_73; omitted identities 2.

### All-finding increases and observed added rule IDs

Positive rule-multiplicity deltas require complete first/final identity lists. Truncated samples leave added identities unknown. Retained template/Fixer records identify recorded actions, not an exclusive causal explanation for each advisory. Rejected template introduced_findings are candidate-only, never retained deltas.

| Round / run / variant | All findings | Added rule IDs | Recorded actions |
|---|---:|---|---|
| final_set_1 / 9cfb1b01-0754-4796-9443-d88594066dde / cost | 16→17 | CKV2_AWS_31, CKV_AWS_175, CKV_AWS_192 | security::accepted |
| final_set_2 / 7cd84341-9393-4947-aa26-f14da8cd17d1 / cost | 70→71 | unknown (sample truncated) | templates:access_logs:retained, templates:kms:retained |
| broad_1 / f7bdc81f-5f5b-46e4-8cb8-88cc99257710 / cost | 16→18 | CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145 | security::accepted, templates:access_logs:retained |
| broad_1 / 73e03ef0-86b8-45bc-91b1-2148e8a12e65 / cost | 17→20 | CKV2_AWS_31, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145, CKV_AWS_175, CKV_AWS_192 | security::accepted, templates:access_logs:retained |
| broad_1 / 9872a498-f18a-4a9a-a2fa-919c3ca9e983 / cost | 6→8 | CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145 | security::accepted, templates:access_logs:retained |
| 10b / fe00a53b-444d-40d4-baca-18a270073ca7 / cost | 6→8 | CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145 | security::accepted, templates:access_logs:retained |
| 10c / 48945ef8-eb70-41f8-8d07-a7531801b43c / cost | 13→16 | CKV2_AWS_31, CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145, CKV_AWS_175, CKV_AWS_192 | security::accepted, templates:access_logs:retained |
| 10d / 4500d38d-2a86-47f3-a4a5-cb96763609b6 / cost | 6→7 | CKV2_AWS_61, CKV2_AWS_62, CKV2_AWS_64, CKV_AWS_144 | security::accepted, templates:access_logs:retained |
| 10e_final / 8384aa1c-8138-450a-8daa-79ec186b7e53 / cost | 6→8 | CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144, CKV_AWS_145 | security::accepted, templates:access_logs:retained |
| 10e_final / f046df7f-dca6-40e4-8746-156dd2e99643 / performance | 14→16 | CKV2_AWS_61, CKV2_AWS_62, CKV_AWS_144 | security::accepted |

## Limitations and thesis interpretation

Legacy final sets use three prompt texts rather than registered complexity levels; their complexity remains unassigned instead of being invented from later anchors. Later levels 1–5 are ordinal registered scenario labels. Packages share plans and scenarios repeat across changed code/models; pooling is a descriptive inventory, not the matched-cohort readiness pooling in D-55 or a causal improvement estimate.

Syntax-limited scans and refused file inputs describe observed findings only, not complete security coverage. The three 10b exports with unsafe_file_input have no usable scan pair; empty stored blockers in such a failure do not establish cleanliness. Pre-security repairs are outside the first-to-final interval. Post-security repairs are included, so the difference is a retained pipeline outcome rather than attribution to the LLM Fixer alone. Advisory samples omit identities but retain total counts. Visibility is proven at the recorded API/presentation level, not by a fresh browser session. Zero blockers alone does not prove validation, plan conformance or deployment.

### Proposed thesis paragraph

The universal criterion of reducing violations on every generated package was not met. Across nine development rounds (491 generated packages), recorded strict blocking findings decreased in 465 of 488 comparable packages, were unchanged and non-zero in 19, were zero at both endpoints in 4, and increased in 0; 3 packages lacked a usable comparison. In the final round, the corresponding counts were 57, 1, 0 and 0 out of 58 (0 unknown). All 298 of 298 packages with recorded unresolved blockers were pending_review with the blocking findings visible in their exported reports. Advisory findings are a separate policy category and may remain on packages labelled checks_passed. When advisory findings are included, totals increased on 10 packages overall and 2 in the final round, so a blanket claim that violations never increased is not supported. These are observed scan counts on retained files, with scanner limitations disclosed; repeated scenarios and shared plans make the pooled result descriptive rather than a causal or deployment-security guarantee.

## Reproduction

From the repository root, using the same cache folders and a new output directory:

```bash
backend/.venv/bin/python backend/scripts/phase10g_remediation_effect.py \
  --revision 8316d00af00965c12d415932ffe215866167bb00 \
  --output-dir docs/evals/phase10g-remediation-effect-reproduced
```

Run the module from the root with PYTHONPATH=backend, or use Python's script path `backend/scripts/phase10g_remediation_effect.py`. Only the standard library is required. Existing output directories are refused. No dotenv is read. Verification results are recorded in the implementation log and adjacent verification.json.
