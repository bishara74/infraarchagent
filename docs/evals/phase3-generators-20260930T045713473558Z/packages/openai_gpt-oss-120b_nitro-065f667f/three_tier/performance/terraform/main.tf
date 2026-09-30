# Provider configuration
provider "aws" {
  region = var.region
}

# VPC and networking
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.9.0"

  name = var.project_name
  cidr = "10.0.0.0/16"
  azs  = data.aws_availability_zones.available.names

  public_subnet_tags = {
    Tier = "public"
  }
  private_subnet_tags = {
    Tier = "private"
  }

  enable_dns_hostnames = true
  enable_dns_support   = true
}

# Security groups
module "sg" {
  source = "./security_groups"
}

# ECS cluster and services
module "ecs" {
  source = "./ecs"
}

# Application Load Balancer
module "alb" {
  source = "./alb"
}

# RDS instance
module "rds" {
  source = "./rds"
}

# S3 bucket
module "s3" {
  source = "./s3"
}

# Autoscaling policies
module "autoscaling" {
  source = "./autoscaling"
}