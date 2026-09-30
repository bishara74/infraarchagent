# Terraform variables
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "eks-cluster"
}

variable "ssh_key_name" {
  description = "Existing EC2 SSH key pair name for node group remote access"
  type        = string
  default     = "eks-key"
}
