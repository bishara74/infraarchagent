resource "aws_s3_bucket" "public" {
  bucket = "infraarch-vulnerable-example"
}

resource "aws_s3_bucket_acl" "public" {
  bucket = aws_s3_bucket.public.id
  acl    = "public-read"
}

resource "aws_db_instance" "db" {
  identifier          = "infraarch-db"
  engine              = "postgres"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  username            = "admin"
  password            = var.db_password
  storage_encrypted   = false
  publicly_accessible = true
}

resource "aws_security_group" "ssh" {
  name = "infraarch-ssh"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_policy" "wildcard" {
  name   = "infraarch-wildcard"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}

variable "db_password" {
  type      = string
  sensitive = true
}
