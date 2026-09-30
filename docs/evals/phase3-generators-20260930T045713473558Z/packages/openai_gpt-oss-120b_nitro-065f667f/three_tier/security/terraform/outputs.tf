# Exported values
output "vpc_id" {
  description = "VPC identifier"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "Public DNS name of the ALB"
  value       = aws_lb.alb.dns_name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "s3_bucket_arn" {
  description = "ARN of the private S3 bucket"
  value       = aws_s3_bucket.static_assets.arn
}
