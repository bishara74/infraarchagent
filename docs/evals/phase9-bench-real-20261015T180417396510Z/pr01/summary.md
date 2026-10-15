# Phase 9 benchmark

Status: **PASS**

Mode: real

Production-ready rate among generated packages: **1/28 (3.57%)**.
Missing variants: 2; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 27 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| validation_failed | 24 |
| unresolved_security_findings | 20 |

| Failed check | Count |
|---|---:|
| terraform.validate: Missing required argument | 28 |
| terraform.validate: Unsupported argument | 26 |
| terraform.validate: Terraform configuration diagnostic | 15 |
| terraform.validate: Invalid reference | 14 |
| terraform.validate: Unsupported block type | 8 |
| terraform.validate: Invalid resource type | 7 |
| helm.lint: helm optional lint failed | 7 |
| terraform.validate: Reference to undeclared input variable | 4 |
| terraform.validate: Reference to undeclared resource | 3 |
| terraform.validate: Unsupported attribute | 3 |
| terraform.var_ref: var.lb_certificate_arn is not declared | 2 |
| document.parse: Document could not be parsed | 2 |
| terraform.var_ref: var.acm_certificate_arn is not declared | 2 |
| terraform.validate: Cycle | 2 |
| terraform.var_ref: var.aws_region is not declared | 1 |
| terraform.var_ref: var.api_image is not declared | 1 |
| terraform.var_ref: var.db_username is not declared | 1 |
| terraform.var_ref: var.db_password is not declared | 1 |
| terraform.var_ref: var.project_prefix is not declared | 1 |
| grafana.panels: Dashboard requires panels | 1 |

| Remaining blocking rule | Count |
|---|---:|
| CKV_AWS_144 | 10 |
| AWS-0132 | 8 |
| CKV_AWS_145 | 7 |
| CKV_AWS_18 | 7 |
| AWS-0176 | 6 |
| CKV_AWS_161 | 6 |
| AWS-0104 | 6 |
| AWS-0038 | 5 |
| KSV-0125 | 4 |
| AWS-0178 | 4 |
| AWS-0011 | 4 |
| AWS-0053 | 4 |
| CKV_AWS_91 | 4 |
| AWS-0028 | 4 |
| AWS-0131 | 4 |
| CKV_AWS_8 | 4 |
| CKV2_AWS_11 | 3 |
| CKV_AWS_103 | 3 |
| AWS-0065 | 3 |
| AWS-0010 | 3 |

pr01: {"count": 10, "median": 120.08073360800154, "p90": 137.73300016299982, "max": 142.71156639100082}; failed/incomplete: 0.

pr01 threshold: PASS.

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

Output tokens per attempt are in results.csv/results.json; event seconds and internal generator seconds are in agents.csv. PR-05 remains 150 seconds regardless of configured budgets.

Measured known cost: $0.081812; unknown costs stay unknown.
