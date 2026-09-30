# Shared naming and tagging locals
locals {
  name_prefix = "${var.project}"
  common_tags = {
    Project   = var.project
    ManagedBy = "terraform"
  }
  services = {
    microservice_a = "microservice-a"
    microservice_b = "microservice-b"
    grafana         = "grafana"
    prometheus      = "prometheus"
  }
  storage = {
    efs = "efs-storage"
    rds = "rds-db"
  }
}
