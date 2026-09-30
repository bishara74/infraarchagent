# Root Terraform configuration: providers and shared locals
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  cluster_name = "eks-cluster"
  common_tags = {
    Project = "microservices-platform"
    Env     = var.environment
  }
}
