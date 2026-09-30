# Outputs for cluster and data endpoints
output "eks_cluster_name" {
  value = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "rds_endpoint" {
  value = aws_db_instance.rds_db.address
}

output "efs_id" {
  value = aws_efs_file_system.efs_storage.id
}

output "rds_secret_arn" {
  value = aws_secretsmanager_secret.rds.arn
}
