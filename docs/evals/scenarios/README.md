# Broad-v1 scenario registration

This file is fixed before benchmark execution. IDs 2, 9 and 10 copy the
final-set static-site, ECS and EKS prompt texts verbatim. The other seven
prompts copy the task descriptions without adding requirements. No generator
code, prompt template or policy is tuned to these scenarios.

The default is two runs per scenario, sequentially: **1–10, then 10–1**.
For other positive repetition counts, odd rounds ascend and even rounds descend.
The JSON records the default order. The benchmark records the SHA-256 of the
exact committed JSON bytes on every run, including unstarted slots.

## Complexity rubric

Levels are pre-assigned ordinal design categories, based on expected logical
resource count and service composition, not a score computed from output.
Counts are approximate and overlap: Terraform supporting resources (IAM,
security groups, attachments and policy documents) vary by implementation.
Generated resource counts never change a scenario's registered level.

| Level | Expected logical resource scale | Services and integration | IDs |
|---|---|---|---|
| 1 | 1 primary resource, about 1–5 with controls | Single storage service and backup controls | 1 |
| 2 | About 3–10 | Small composition: S3/CloudFront or API Gateway/Lambda/DynamoDB | 2, 3 |
| 3 | About 10–20 | Private network, subnets and compute/access or relational data | 4, 5 |
| 4 | About 15–30 | Managed orchestration plus ingress, database/cache or Helm workload | 6, 7, 8 |
| 5 | About 25 or more | Application platform integrated with CI/CD and monitoring | 9, 10 |

## Exact prompts

### 1. Backup bucket (level 1)

Private S3 bucket for backups with versioning, encryption and lifecycle rules.

### 2. Static website (level 2)

A static website hosted in a private AWS S3 bucket behind CloudFront with HTTPS, access logging, and Terraform infrastructure.

### 3. Serverless REST API (level 2)

Serverless REST API with API Gateway, Lambda and DynamoDB.

### 4. Private EC2 with SSM (level 3)

VPC with public and private subnets, a NAT gateway and an EC2 instance in a private subnet accessed through SSM Session Manager.

### 5. Private RDS application (level 3)

PostgreSQL on RDS in private subnets with automated backups, used by an EC2 application server.

### 6. Fargate HTTPS application (level 4)

Containerised web application on ECS Fargate behind an HTTPS Application Load Balancer.

### 7. Fargate database and cache (level 4)

ECS Fargate application with RDS PostgreSQL and ElastiCache Redis.

### 8. EKS Helm application (level 4)

EKS cluster running one web application deployed with a Helm chart.

### 9. ECS application anchor (level 5)

A Node.js REST API with a PostgreSQL database, autoscaling on ECS, a Jenkins CI/CD pipeline, Nginx reverse proxy, and Prometheus + Grafana monitoring stack on AWS.

### 10. EKS microservices anchor (level 5)

Python microservices on AWS EKS with autoscaling, a PostgreSQL database, a Jenkins CI/CD pipeline, and Prometheus monitoring with Grafana dashboards.
