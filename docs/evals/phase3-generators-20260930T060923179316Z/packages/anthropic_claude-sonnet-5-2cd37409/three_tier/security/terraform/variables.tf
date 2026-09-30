# Input variables with safe non-secret defaults
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

variable "private_app_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_db_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.4.0/24", "10.0.5.0/24"]
}

variable "availability_zone" {
  type    = string
  default = "us-east-1a"
}

variable "availability_zone_secondary" {
  type    = string
  default = "us-east-1b"
}

variable "project_name" {
  type    = string
  default = "three-tier-app"
}

variable "db_engine_version" {
  type    = string
  default = "13.13"
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

variable "app_service_1_image" {
  type    = string
  default = "public.ecr.aws/nginx/nginx:latest"
}

variable "app_service_2_image" {
  type    = string
  default = "public.ecr.aws/nginx/nginx:latest"
}

variable "app_container_port" {
  type    = number
  default = 8080
}

variable "app_cpu" {
  type    = number
  default = 256
}

variable "app_memory" {
  type    = number
  default = 512
}

variable "app_desired_count" {
  type    = number
  default = 1
}
