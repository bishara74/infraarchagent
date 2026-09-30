# Private, encrypted PostgreSQL RDS instance
resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_subnet_group" "rds" {
  name       = "${local.name_prefix}-rds-subnet-group"
  subnet_ids = aws_subnet.private_db[*].id
  tags       = merge(local.common_tags, { Name = "${local.name_prefix}-rds-subnet-group" })
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name       = "${local.name_prefix}-rds-credentials"
  kms_key_id = aws_kms_key.main.arn
  tags       = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
  })
}

resource "aws_db_instance" "rds" {
  identifier                          = "${local.name_prefix}-rds"
  engine                              = "postgres"
  engine_version                      = var.db_engine_version
  instance_class                      = var.db_instance_class
  allocated_storage                   = 20
  storage_type                        = "gp3"
  storage_encrypted                   = true
  kms_key_id                          = aws_kms_key.main.arn
  db_name                             = var.db_name
  username                            = var.db_username
  password                            = random_password.db_password.result
  db_subnet_group_name                = aws_db_subnet_group.rds.name
  vpc_security_group_ids              = [aws_security_group.rds.id]
  publicly_accessible                 = false
  multi_az                            = false
  backup_retention_period             = 7
  deletion_protection                 = true
  skip_final_snapshot                 = false
  final_snapshot_identifier           = "${local.name_prefix}-rds-final-snapshot"
  copy_tags_to_snapshot                = true
  iam_database_authentication_enabled = true
  enabled_cloudwatch_logs_exports      = ["postgresql", "upgrade"]
  auto_minor_version_upgrade           = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-rds" })
}
