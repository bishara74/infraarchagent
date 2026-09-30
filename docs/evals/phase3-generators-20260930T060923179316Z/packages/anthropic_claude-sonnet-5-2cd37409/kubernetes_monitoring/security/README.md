# AWS EKS Microservices Platform

Deploys `microservice-a`, `microservice-b`, `prometheus`, and `grafana` on Amazon EKS with EFS shared storage and an encrypted RDS PostgreSQL database (`rds-db`).

## Structure
- `terraform/` - VPC, EKS, RDS, EFS, IAM (least privilege, IRSA), S3 logging bucket, KMS encryption
- `k8s/` - Kubernetes manifests for microservices, EFS PVC, ALB ingress
- `helm/monitoring/` - Prometheus + Grafana chart
- `monitoring/prometheus`, `monitoring/grafana` - scrape configs, alert rules, dashboards

## Security notes
- Only ALB (port 443) is open to 0.0.0.0/0; all other traffic is scoped to security groups.
- EKS control plane secrets, RDS, and EFS are encrypted with dedicated KMS keys.
- RDS credentials stored in Secrets Manager, never hardcoded.
- S3 bucket has public access fully blocked and versioning/logging enabled.
- Prometheus runs as a private service; only Grafana can reach it via NetworkPolicy.

## Prerequisites
- Provide the Grafana admin credential via a pre-created Kubernetes secret named `grafana-admin-credentials` with key `password` (not managed by this IaC to avoid embedding secrets).
