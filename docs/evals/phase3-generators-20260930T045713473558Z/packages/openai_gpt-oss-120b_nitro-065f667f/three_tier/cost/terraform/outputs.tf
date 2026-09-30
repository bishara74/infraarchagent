# Exported outputs
output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.alb.dns_name
}

output "rds_endpoint" {
  description = "RDS endpoint address"
  value       = aws_db_instance.postgres.endpoint
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.app_bucket.arn
}
