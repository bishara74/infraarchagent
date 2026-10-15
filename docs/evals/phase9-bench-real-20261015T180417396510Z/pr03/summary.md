# Phase 9 benchmark

Status: **FAIL**

Mode: real

Production-ready rate among generated packages: **0/12 (0.00%)**.
Missing variants: 0; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 12 |

| Review reason | Count |
|---|---:|
| validation_failed | 12 |
| unresolved_security_findings | 8 |

| Failed check | Count |
|---|---:|
| terraform.validate: Missing required argument | 30 |
| terraform.validate: Invalid reference | 14 |
| terraform.validate: Terraform configuration diagnostic | 9 |
| terraform.validate: Unsupported argument | 6 |
| helm.lint: helm optional lint failed | 6 |
| terraform.validate: Invalid resource type | 3 |
| terraform.validate: Invalid single-argument block definition | 2 |
| terraform.validate: Reference to undeclared input variable | 2 |
| terraform.validate: Unsupported block type | 2 |
| grafana.panels: Dashboard requires panels | 2 |
| terraform.var_ref: var.kms_key_id is not declared | 1 |
| terraform.var_ref: var.alb_cert_arn is not declared | 1 |
| terraform.var_ref: var.aws_region is not declared | 1 |
| terraform.var_ref: var.vpc_cidr is not declared | 1 |
| terraform.var_ref: var.environment is not declared | 1 |
| terraform.var_ref: var.api_image is not declared | 1 |
| terraform.var_ref: var.api_desired_count is not declared | 1 |
| terraform.var_ref: var.acm_certificate_arn is not declared | 1 |
| terraform.var_ref: var.db_master_username is not declared | 1 |
| terraform.var_ref: var.db_master_password is not declared | 1 |

| Remaining blocking rule | Count |
|---|---:|
| CKV_AWS_8 | 7 |
| AWS-0028 | 7 |
| AWS-0104 | 7 |
| CKV_AWS_130 | 6 |
| CKV_AWS_144 | 5 |
| CKV2_AWS_12 | 4 |
| AWS-0053 | 4 |
| AWS-0131 | 4 |
| CKV2_AWS_11 | 3 |
| AWS-0132 | 3 |
| CKV_AWS_129 | 2 |
| CKV_AWS_16 | 2 |
| CKV_AWS_161 | 2 |
| CKV_AWS_260 | 2 |
| CKV_AWS_293 | 2 |
| TERRAFORM_SYNTAX | 2 |
| CKV2_AWS_20 | 2 |
| CKV_AWS_103 | 2 |
| CKV_AWS_118 | 2 |
| CKV_AWS_91 | 2 |

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
| 1 | 4 | {"none": 3, "schema_invalid": 1} | cost#1:2072, security#1:2696, performance#1:5174, performance#2:3611 | {} | {} |
| 2 | 3 | {"none": 3} | cost#1:2854, security#1:3404, performance#1:4163 | {} | {} |
| 3 | 4 | {"none": 4} | security#1:3793, performance#1:4279, cost#1:3214, cost#2:3060 | {} | {} |
| 4 | 3 | {"none": 3} | security#1:4108, performance#1:3263, cost#1:4968 | {} | {} |

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.009243; unknown costs stay unknown.

Concurrent costs: {"cost_usd": 0.0092431, "average_cost_usd": 0.0030810333333333335, "average_label": "Total / 3 average; per-run costs not attributed", "run_ids": ["44138412-b009-44e4-ab61-2788df8172ef", "cafbf668-1754-4672-a3b1-2492b92228cc", "7812c7b9-57e1-4378-9fb4-f26d8447909c"], "before_remaining_usd": 10.67380774, "after_remaining_usd": 10.66456464}
