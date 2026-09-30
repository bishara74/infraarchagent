# Private S3 bucket for static assets
resource "aws_s3_bucket" "static" {
  bucket = "${var.project_name}-static-assets"
  acl    = "private"
  force_destroy = true
}

resource "aws_s3_bucket_policy" "static" {
  bucket = aws_s3_bucket.static.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        AWS = aws_iam_role.ecs_task_execution.arn
      },
      Action = ["s3:GetObject", "s3:PutObject"],
      Resource = "${aws_s3_bucket.static.arn}/*"
    }]
  })
}