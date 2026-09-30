# Key outputs for verification and integration
output "alb_dns_name" {
  value = aws_lb.alb.dns_name
}

output "rds_endpoint" {
  value = aws_db_instance.rds.address
}

output "s3_bucket_name" {
  value = aws_s3_bucket.s3_storage.bucket
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}
