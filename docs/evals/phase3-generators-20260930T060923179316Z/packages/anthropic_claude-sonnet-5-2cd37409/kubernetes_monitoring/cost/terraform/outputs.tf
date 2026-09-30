# Useful outputs for kubeconfig and endpoints
output "eks_cluster_name" {
  value = aws_eks_cluster.this.name
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "efs_id" {
  value = aws_efs_file_system.efs_storage.id
}

output "rds_endpoint" {
  value = aws_db_instance.rds_db.endpoint
}
