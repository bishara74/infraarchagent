# Useful outputs
output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.this.endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.this.name
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_rds_instance.rds.endpoint
}
