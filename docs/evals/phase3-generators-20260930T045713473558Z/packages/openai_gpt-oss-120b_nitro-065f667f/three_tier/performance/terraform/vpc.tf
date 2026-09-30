# Data source for AZs
data "aws_availability_zones" "available" {}

# Export subnet IDs for other modules
output "public_subnet_ids" {
  value = module.vpc.public_subnets
}

output "private_subnet_ids" {
  value = module.vpc.private_subnets
}