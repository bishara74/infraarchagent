# Cluster outputs
output "cluster_name" {
  value = aws_eks_cluster.eks.name
}

output "kubeconfig_certificate_authority_data" {
  value = aws_eks_cluster.eks.certificate_authority[0].data
}

output "kubeconfig_endpoint" {
  value = aws_eks_cluster.eks.endpoint
}
