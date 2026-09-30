# Input variables with cost-conscious defaults
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "private_app_subnet_cidr" {
  type    = string
  default = "10.0.2.0/24"
}

variable "private_db_subnet_cidr" {
  type    = string
  default = "10.0.3.0/24"
}

variable "private_db_subnet_cidr_2" {
  type    = string
  default = "10.0.4.0/24"
}

variable "availability_zone" {
  type    = string
  default = "us-east-1a"
}

variable "availability_zone_2" {
  type    = string
  default = "us-east-1b"
}

variable "db_engine_version" {
  type    = string
  default = "13"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "db_username" {
  type    = string
  default = "appadmin"
}

variable "db_password" {
  type      = string
  default   = "ChangeMe123!"
  sensitive = true
}

variable "container_image" {
  type    = string
  default = "nginx:latest"
}

variable "container_port" {
  type    = number
  default = 80
}

variable "fargate_cpu" {
  type    = number
  default = 256
}

variable "fargate_memory" {
  type    = number
  default = 512
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "bucket_name" {
  type    = string
  default = "app-static-assets-bucket-demo"
}

variable "project_name" {
  type    = string
  default = "three-tier-app"
}
