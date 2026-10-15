# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **1/40 (2.50%)**.
Missing variants: 2; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 39 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| validation_failed | 36 |
| unresolved_security_findings | 28 |

| Failed check | Count |
|---|---:|
| terraform.validate: Missing required argument | 58 |
| terraform.validate: Unsupported argument | 32 |
| terraform.validate: Invalid reference | 28 |
| terraform.validate: Terraform configuration diagnostic | 24 |
| helm.lint: helm optional lint failed | 13 |
| terraform.validate: Invalid resource type | 10 |
| terraform.validate: Unsupported block type | 10 |
| terraform.validate: Reference to undeclared input variable | 6 |
| terraform.validate: Unsupported attribute | 4 |
| grafana.panels: Dashboard requires panels | 3 |
| terraform.validate: Reference to undeclared resource | 3 |
| terraform.var_ref: var.acm_certificate_arn is not declared | 3 |
| terraform.var_ref: var.aws_region is not declared | 2 |
| terraform.var_ref: var.api_image is not declared | 2 |
| terraform.var_ref: var.lb_certificate_arn is not declared | 2 |
| document.parse: Document could not be parsed | 2 |
| terraform.validate: Cycle | 2 |
| terraform.validate: Invalid single-argument block definition | 2 |
| terraform.var_ref: var.db_username is not declared | 1 |
| terraform.var_ref: var.db_password is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| CKV_AWS_144 | 15 |
| AWS-0104 | 13 |
| AWS-0132 | 11 |
| AWS-0028 | 11 |
| CKV_AWS_8 | 11 |
| CKV_AWS_18 | 9 |
| CKV_AWS_130 | 9 |
| CKV_AWS_161 | 8 |
| CKV_AWS_145 | 8 |
| AWS-0053 | 8 |
| AWS-0131 | 8 |
| AWS-0176 | 6 |
| CKV2_AWS_11 | 6 |
| CKV_AWS_91 | 6 |
| CKV2_AWS_12 | 6 |
| AWS-0178 | 5 |
| CKV_AWS_103 | 5 |
| AWS-0164 | 5 |
| AWS-0038 | 5 |
| KSV-0125 | 4 |

pr01: {"count": 10, "median": 120.08073360800154, "p90": 137.73300016299982, "max": 142.71156639100082}; failed/incomplete: 0.

pr01 threshold: PASS.

pr03: {"count": 4, "median": 262.7745457085002, "p90": 266.3793322010024, "max": 266.3793322010024}; failed/incomplete: 0.

PR-03 uses the isolated baseline; PR-01 ratios are secondary.

Cohort references: {"run_id": "7812c7b9-57e1-4378-9fb4-f26d8447909c", "ratio_to_baseline": 2.7086972766503963, "ratio_to_pr01_prompt_median": 2.1584702751227014, "pr01_prompt_median_seconds": 122.75835593100237, "pr01_reference_count": 4}

Cohort references: {"run_id": "44138412-b009-44e4-ab61-2788df8172ef", "ratio_to_baseline": 2.7231016998876374, "ratio_to_pr01_prompt_median": 2.169948678285686, "pr01_prompt_median_seconds": 122.75835593100237, "pr01_reference_count": 4}

Cohort references: {"run_id": "cafbf668-1754-4672-a3b1-2492b92228cc", "ratio_to_baseline": 2.66380520838531, "ratio_to_pr01_prompt_median": 2.122697287209193, "pr01_prompt_median_seconds": 122.75835593100237, "pr01_reference_count": 4}

pr03 threshold: FAIL.

PR-05 individual thresholds: PASS. Missing metrics unknown; Validator descriptive.

Generator attempts (missing historical metrics remain unknown):

| Run | Attempts | Format reasons | Output tokens / attempt | Failures | Overruns |
|---|---:|---|---|---|---|
| 1 | 3 | {"none": 3} | cost#1:3440, performance#1:4409, security#1:3759 | {} | {} |
| 2 | 3 | {"none": 3} | performance#1:4302, security#1:3458, cost#1:3376 | {} | {} |
| 3 | 3 | {"none": 3} | cost#1:1000, performance#1:1041, security#1:1609 | {} | {} |
| 4 | 4 | {"none": 4} | cost#1:3211, performance#1:5028, security#1:3310, security#2:3471 | {} | {} |
| 5 | 4 | {"none": 4} | cost#1:3243, security#1:1580, security#2:3032, performance#1:2727 | {"security": "incomplete_package"} | {} |
| 6 | 3 | {"none": 3} | cost#1:1231, security#1:1044, performance#1:1575 | {} | {} |
| 7 | 4 | {"none": 4} | cost#1:3561, security#1:3398, performance#1:2246, performance#2:4924 | {} | {} |
| 8 | 4 | {"none": 4} | performance#1:2522, security#1:3546, cost#1:1517, cost#2:2292 | {"cost": "incomplete_package"} | {} |
| 9 | 3 | {"none": 3} | cost#1:890, performance#1:977, security#1:1111 | {} | {} |
| 10 | 3 | {"none": 3} | performance#1:3928, cost#1:3769, security#1:4272 | {} | {} |
| 11 | 4 | {"none": 3, "schema_invalid": 1} | cost#1:2072, security#1:2696, performance#1:5174, performance#2:3611 | {} | {} |
| 12 | 3 | {"none": 3} | cost#1:2854, security#1:3404, performance#1:4163 | {} | {} |
| 13 | 4 | {"none": 4} | security#1:3793, performance#1:4279, cost#1:3214, cost#2:3060 | {} | {} |
| 14 | 3 | {"none": 3} | security#1:4108, performance#1:3263, cost#1:4968 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.091055; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0092431, "average_cost_usd": 0.0030810333333333335, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["44138412-b009-44e4-ab61-2788df8172ef", "cafbf668-1754-4672-a3b1-2492b92228cc", "7812c7b9-57e1-4378-9fb4-f26d8447909c"], "before_remaining_usd": 10.67380774, "after_remaining_usd": 10.66456464}

First-run affordability advisory: {"measured_first_run_cost_usd": 0.0, "remaining_credit_usd": 10.75561959, "planned_runs_remaining": 13, "run_cap_remaining": null, "projected_further_runs": 13, "assumption": "Projection at first measured cost; fresh guard checks decide."}
