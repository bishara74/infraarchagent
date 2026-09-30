# Encrypted RDS PostgreSQL instance in private subnets
resource "random_password" "rds" {
  length           = 20
  special          = true
  override_special = "!#$%&*()-_=+[]{}"
}

resource "aws_secretsmanager_secret" "rds" {
  name = "${local.name_prefix}-rds-db-credentials"
}

resource "aws_secretsmanager_secret_version" "rds" {
  secret_id = aws_secretsmanager_secret.rds.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.rds.result
  })
}

resource "aws_db_subnet_group" "rds" {
  name       = "${local.name_prefix}-rds-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  tags       = merge(local.common_tags, { Name = "${local.name_prefix}-rds-db-subnet-group" })
}

resource "aws_kms_key" "rds" {
  description         = "KMS key for RDS storage encryption"
  enable_key_rotation = true
  tags                = local.common_tags
}

resource "aws_db_instance" "rds_db" {
  identifier                 = "${local.name_prefix}-rds-db"
  engine                     = "postgres"
  engine_version             = "15.5"
  instance_class             = var.db_instance_class
  allocated_storage          = 20
  storage_encrypted          = true
  kms_key_id                 = aws_kms_key.rds.arn
  db_name                    = var.db_name
  username                   = var.db_username
  password                   = random_password.rds.result
  db_subnet_group_name       = aws_db_subnet_group.rds.name
  vpc_security_group_ids     = [aws_security_group.rds.id]
  publicly_accessible        = false
  multi_az                   = false
  backup_retention_period    = 7
  deletion_protection        = true
  skip_final_snapshot        = false
  final_snapshot_identifier  = "${local.name_prefix}-rds-db-final-snapshot"
  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = merge(local.common_tags, { Name = local.storage.rds })
}
