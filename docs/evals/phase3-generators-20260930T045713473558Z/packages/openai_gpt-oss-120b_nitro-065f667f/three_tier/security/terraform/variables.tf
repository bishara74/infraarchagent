# Input variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR for the private subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "alb_name" {
  description = "Name of the Application Load Balancer"
  type        = string
  default     = "alb"
}

variable "alb_certificate_arn" {
  description = "ARN of ACM certificate for HTTPS listener"
  type        = string
  default     = ""
}

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "app-cluster"
}

variable "app_service_1_name" {
  description = "ECS service name for app-service-1"
  type        = string
  default     = "app-service-1"
}

variable "app_service_2_name" {
  description = "ECS service name for app-service-2"
  type        = string
  default     = "app-service-2"
}

variable "container_image" {
  description = "Container image for both services"
  type        = string
  default     = "public.ecr.aws/nginx/nginx:latest"
}

variable "container_port" {
  description = "Port the containers listen on"
  type        = number
  default     = 80
}

variable "rds_instance_identifier" {
  description = "RDS instance identifier"
  type        = string
  default     = "rds"
}

variable "rds_db_name" {
  description = "Initial database name"
  type        = string
  default     = "appdb"
}

variable "rds_username" {
  description = "Master username for PostgreSQL"
  type        = string
  default     = "dbadmin"
}

variable "rds_password" {
  description = "Master password for PostgreSQL"
  type        = string
  sensitive   = true
  default     = "ChangeMe123!"
}

variable "s3_bucket_name" {
  description = "Name of the private S3 bucket"
  type        = string
  default     = "s3-storage-bucket"
}
