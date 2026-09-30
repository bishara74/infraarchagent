# Key resource outputs
output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "rds_endpoint" {
  value = aws_db_instance.rds.endpoint
}

output "s3_bucket_name" {
  value = aws_s3_bucket.storage.bucket
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}
