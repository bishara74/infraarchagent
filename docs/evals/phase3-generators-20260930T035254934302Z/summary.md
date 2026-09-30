# Phase 3 GeneratorAgent evaluation

## three_tier

| Variant | stub outcome | stub time/tokens |
| --- | --- | --- |
| cost | PASS | 0.000s / 1000/2000 |
| performance | PASS | 0.000s / 1000/2000 |
| security | PASS | 0.001s / 1000/2000 |

- stub three-variant parallel wall time: 0.004s

## kubernetes_monitoring

| Variant | stub outcome | stub time/tokens |
| --- | --- | --- |
| cost | PASS | 0.001s / 2000/4000 |
| performance | PASS | 0.000s / 1000/2000 |
| security | PASS | 0.000s / 1000/2000 |

- stub three-variant parallel wall time: 0.003s

## Directive compliance and notes

### stub / three_tier / cost

- Notes: Cost uses small on-demand resources.
- Package/LLM attempts: 1/1
- Structure error counts: [0]
- PASS: small instance classes — All 1 explicit instance classes are micro or small.
- PASS: single-AZ preference — No multi_az = true setting found.

### stub / three_tier / performance

- Notes: Performance uses multi-AZ and autoscaling.
- Package/LLM attempts: 1/1
- Structure error counts: [0]
- PASS: relational DB multi-AZ — Found multi_az = true for a plan with a relational DB.
- PASS: autoscaling construct — Found Terraform autoscaling or a Kubernetes HPA.

### stub / three_tier / security

- Notes: Security enables encryption and limits ingress.
- Package/LLM attempts: 1/1
- Structure error counts: [0]
- PASS: RDS storage encryption — Found storage_encrypted = true.
- PASS: S3 encryption — Found an S3 server-side encryption configuration.
- PASS: S3 public access block — Found an S3 public access block.
- PASS: public ingress port — No broad ingress found outside port 443.
- PASS: IAM wildcard actions — No wildcard IAM action was found.

### stub / kubernetes_monitoring / cost

- Notes: Cost uses small on-demand resources.
- Package/LLM attempts: 2/2
- Structure error counts: [4, 0]
- FAIL: small instance classes — Found 1 larger or unknown instance classes.
- PASS: single-AZ preference — No multi_az = true setting found.

### stub / kubernetes_monitoring / performance

- Notes: Performance uses multi-AZ and autoscaling.
- Package/LLM attempts: 1/1
- Structure error counts: [0]
- PASS: relational DB multi-AZ — Found multi_az = true for a plan with a relational DB.
- PASS: autoscaling construct — Found Terraform autoscaling or a Kubernetes HPA.

### stub / kubernetes_monitoring / security

- Notes: Security enables encryption and limits ingress.
- Package/LLM attempts: 1/1
- Structure error counts: [0]
- PASS: RDS storage encryption — Found storage_encrypted = true.
- PASS: public ingress port — No broad ingress found outside port 443.
- FAIL: IAM wildcard actions — Found an IAM action wildcard.

## Totals

- stub: success 100.0%; compliance 87.5%; median 0.000s; tokens 21000; estimated cost 0.035000
