# Shared naming and tags used across all resources
locals {
  name_prefix = var.project_name

  common_tags = {
    Project     = var.project_name
    ManagedBy   = "terraform"
    Environment = "prod"
  }

  app_services = {
    "app-service-1" = {
      image = var.app_service_1_image
    }
    "app-service-2" = {
      image = var.app_service_2_image
    }
  }
}
