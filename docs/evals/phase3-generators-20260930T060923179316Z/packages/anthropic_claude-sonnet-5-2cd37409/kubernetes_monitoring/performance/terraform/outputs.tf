# Outputs consumed by CI/CD and kubeconfig generation
output "eks_cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "eks_cluster_name" {
  value = aws_eks_cluster.this.name
}

output "rds_db_endpoint" {
  value = aws_db_instance.rds_db.endpoint
}

output "efs_storage_id" {
  value = aws_efs_file_system.efs_storage.id
}
