# Package quality

Production-ready rate among generated packages: **1/36 (2.78%)**.
Missing variants: 6; runs without quality snapshots: 0.

| Package status | Count |
|---|---:|
| pending_review | 35 |
| production_ready | 1 |

| Review reason | Count |
|---|---:|
| validation_failed | 35 |
| unresolved_security_findings | 30 |

| Failed check | Count |
|---|---:|
| terraform.validate: Terraform configuration diagnostic | 28 |
| terraform.validate: Missing required argument | 22 |
| terraform.validate: Unsupported argument | 15 |
| ansible-lint.lint: ansible-lint optional lint failed | 14 |
| terraform.var_ref: var.acm_certificate_arn is not declared | 10 |
| terraform.validate: Reference to undeclared input variable | 10 |
| helm.templates: Chart requires templates | 10 |
| terraform.validate: Reference to undeclared resource | 9 |
| grafana.panels: Dashboard requires panels | 7 |
| terraform.var_ref: var.project_name is not declared | 7 |
| terraform.validate: Duplicate variable declaration | 7 |
| terraform.validate: Unsupported block type | 6 |
| terraform.var_ref: var.aws_region is not declared | 5 |
| document.parse: Document could not be parsed | 5 |
| terraform.var_ref: var.lb_logs_bucket is not declared | 3 |
| terraform.var_ref: var.vpc_id is not declared | 3 |
| terraform.var_ref: var.log_bucket_name is not declared | 3 |
| k8s.configmap_ref: ConfigMap reference must resolve in its namespace | 3 |
| terraform.var_ref: var.db_password is not declared | 2 |
| terraform.var_ref: var.vpc_cidr is not declared | 2 |

| Remaining blocking rule | Count |
|---|---:|
| AWS-0086 | 19 |
| AWS-0087 | 19 |
| AWS-0091 | 19 |
| AWS-0093 | 19 |
| CKV_AWS_144 | 15 |
| CKV_AWS_18 | 13 |
| AWS-0052 | 12 |
| AWS-0065 | 12 |
| KSV-0125 | 10 |
| AWS-0053 | 9 |
| CKV2_AWS_12 | 5 |
| CKV_AWS_111 | 5 |
| AWS-0104 | 5 |
| CKV_AWS_145 | 5 |
| CKV_AWS_161 | 4 |
| CKV_AWS_21 | 4 |
| CKV_AWS_130 | 3 |
| AWS-0079 | 3 |
| CKV_AWS_354 | 3 |
| TERRAFORM_SYNTAX | 3 |
