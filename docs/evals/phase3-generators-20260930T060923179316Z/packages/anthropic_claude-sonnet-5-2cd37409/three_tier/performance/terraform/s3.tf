# Private S3 bucket for static assets with encryption and versioning
resource "aws_s3_bucket" "storage" {
  bucket = "${var.project_name}-s3-storage-${data.aws_caller_identity.current.account_id}"

  tags = { Name = "s3-storage" }
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_public_access_block" "storage" {
  bucket                  = aws_s3_bucket.storage.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "storage" {
  bucket = aws_s3_bucket.storage.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
