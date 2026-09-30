# Input variables with sensible nonsecret defaults
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "three-tier-app"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_app_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "private_db_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.21.0/24", "10.0.22.0/24"]
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "db_engine_version" {
  type    = string
  default = "13.13"
}

variable "db_instance_class" {
  type    = string
  default = "db.r6g.large"
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
  default   = "ChangeMe123!Secure"
  sensitive = true
}

variable "app_service_1_image" {
  type    = string
  default = "nginx:latest"
}

variable "app_service_2_image" {
  type    = string
  default = "nginx:latest"
}

variable "app_container_port" {
  type    = number
  default = 8080
}

variable "app_desired_count" {
  type    = number
  default = 3
}

variable "app_cpu" {
  type    = number
  default = 512
}

variable "app_memory" {
  type    = number
  default = 1024
}

variable "app_max_capacity" {
  type    = number
  default = 10
}

variable "app_min_capacity" {
  type    = number
  default = 3
}
