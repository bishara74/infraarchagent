# Export useful values
output "alb_dns_name" {
  description = "DNS name of the public ALB"
  value       = aws_lb.alb.dns_name
}

output "rds_endpoint" {
  description = "RDS cluster endpoint"
  value       = aws_rds_cluster.postgres.endpoint
}

output "s3_bucket_name" {
  description = "Name of the private S3 bucket"
  value       = aws_s3_bucket.static.id
}