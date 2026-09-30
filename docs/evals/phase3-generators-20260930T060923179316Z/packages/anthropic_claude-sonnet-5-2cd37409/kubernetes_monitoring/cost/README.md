# Microservices Platform on AWS EKS

Cost-optimized deployment using t3.micro/db.t3.micro instances, single-AZ RDS, no NAT gateway, and minimal replica counts.

## Components
- EKS cluster (eks-cluster) hosting microservice-a, microservice-b, prometheus, grafana
- EFS (efs-storage) shared by microservice-a and microservice-b
- RDS PostgreSQL (rds-db) used by microservice-a
- ALB Ingress exposing /api/a, /api/b, /grafana publicly

## Deploy
1. `terraform init && terraform apply` in `terraform/`
2. Apply `k8s/` manifests (replace `EFS_FILE_SYSTEM_ID` with the Terraform output `efs_id`)
3. `helm install monitoring helm/monitoring -n apps`
