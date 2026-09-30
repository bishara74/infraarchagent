# AWS EKS Deployment Package

This repository contains a minimal, security‑focused infrastructure‑as‑code package that provisions:
- A VPC with public and private subnets.
- An Amazon EKS cluster with private API endpoint.
- Two microservices (`microservice-a` and `microservice-b`) deployed as Kubernetes Deployments.
- An AWS Application Load Balancer (via the ALB Ingress Controller) exposing the microservices and Grafana over HTTPS.
- Prometheus and Grafana running inside the cluster (Prometheus is kept private).
- Encrypted EFS storage shared by the microservices.
- An encrypted RDS PostgreSQL instance used by `microservice-b`.
- An S3 bucket for logs with public‑access blocks and VPC flow logs for auditability.

All resources use least‑privilege IAM policies and have encryption‑at‑rest enabled. No secrets are hard‑coded; passwords are generated with `random_password`. Adjust variables in `terraform/variables.tf` as needed.
