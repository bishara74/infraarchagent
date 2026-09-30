# Private S3 bucket for static assets with encryption, versioning, logging and public access block
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "s3_storage" {
  bucket = "${local.name_prefix}-s3-storage-${random_id.bucket_suffix.hex}"
  tags   = merge(local.common_tags, { Name = "${local.name_prefix}-s3-storage" })
}

resource "aws_s3_bucket" "access_logs" {
  bucket = "${local.name_prefix}-s3-access-logs-${random_id.bucket_suffix.hex}"
  tags   = merge(local.common_tags, { Name = "${local.name_prefix}-s3-access-logs" })
}

resource "aws_s3_bucket_public_access_block" "access_logs" {
  bucket                  = aws_s3_bucket.access_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_ownership_controls" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_logging" "s3_storage" {
  bucket        = aws_s3_bucket.s3_storage.id
  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "s3-storage-access-logs/"
}

resource "aws_s3_bucket_versioning" "s3_storage" {
  bucket = aws_s3_bucket.s3_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_storage" {
  bucket = aws_s3_bucket.s3_storage.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "s3_storage" {
  bucket                  = aws_s3_bucket.s3_storage.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "s3_storage_tls_only" {
  bucket = aws_s3_bucket.s3_storage.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.s3_storage.arn,
        "${aws_s3_bucket.s3_storage.arn}/*"
      ]
      Condition = {
        Bool = { "aws:SecureTransport" = "false" }
      }
    }]
  })
}
