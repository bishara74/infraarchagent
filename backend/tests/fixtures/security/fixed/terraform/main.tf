resource "aws_kms_key" "data" {
  description         = "Encrypt S3 and RDS data"
  enable_key_rotation = true
}

resource "aws_s3_bucket" "private" {
  bucket = "infraarch-private-example"
}

resource "aws_s3_bucket_public_access_block" "private" {
  bucket                  = aws_s3_bucket.private.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "private" {
  bucket = aws_s3_bucket.private.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
  }
}

resource "aws_s3_bucket_versioning" "private" {
  bucket = aws_s3_bucket.private.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_logging" "private" {
  bucket        = aws_s3_bucket.private.id
  target_bucket = var.audit_bucket_id
  target_prefix = "access/"
}

resource "aws_s3_bucket_replication_configuration" "private" {
  bucket = aws_s3_bucket.private.id
  role   = var.replication_role_arn
  rule {
    id     = "replicate"
    status = "Enabled"
    destination { bucket = var.replica_bucket_arn }
  }
}

resource "aws_db_instance" "db" {
  identifier                   = "infraarch-db"
  engine                       = "postgres"
  instance_class               = "db.t3.micro"
  allocated_storage            = 20
  username                     = "admin"
  password                     = var.db_password
  storage_encrypted            = true
  kms_key_id                   = aws_kms_key.data.arn
  publicly_accessible          = false
  multi_az                     = true
  monitoring_interval          = 60
  monitoring_role_arn          = var.monitoring_role_arn
  performance_insights_enabled = true
  performance_insights_kms_key_id = aws_kms_key.data.arn
  backup_retention_period      = 7
  deletion_protection          = true
  iam_database_authentication_enabled = true
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
}

resource "aws_security_group" "app" {
  name = "infraarch-app"
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}

resource "aws_iam_policy" "limited" {
  name   = "infraarch-limited"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["s3:GetObject"], Resource = "arn:aws:s3:::infraarch-private-example/*" }]
  })
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "monitoring_role_arn" { type = string }
variable "audit_bucket_id" { type = string }
variable "replication_role_arn" { type = string }
variable "replica_bucket_arn" { type = string }
