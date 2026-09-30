# Input variables with sensible defaults
variable "aws_region" {
  default = "us-east-1"
}

variable "cluster_name" {
  default = "eks-cluster"
}

variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

variable "node_instance_type" {
  default = "m5.xlarge"
}

variable "node_desired_capacity" {
  default = 3
}

variable "node_min_capacity" {
  default = 3
}

variable "node_max_capacity" {
  default = 10
}

variable "db_instance_class" {
  default = "db.r6g.xlarge"
}

variable "db_name" {
  default = "rdsdb"
}

variable "db_username" {
  default = "appadmin"
}

variable "db_password" {
  default = "ChangeMe12345!"
  sensitive = true
}
