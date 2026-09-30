# Input variables
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Base name for all resources"
  type        = string
  default     = "exampleapp"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "container_image_1" {
  description = "Docker image for app-service-1"
  type        = string
  default     = "nginx:latest"
}

variable "container_image_2" {
  description = "Docker image for app-service-2"
  type        = string
  default     = "nginx:latest"
}

variable "desired_task_count" {
  description = "Desired number of tasks per service"
  type        = number
  default     = 2
}