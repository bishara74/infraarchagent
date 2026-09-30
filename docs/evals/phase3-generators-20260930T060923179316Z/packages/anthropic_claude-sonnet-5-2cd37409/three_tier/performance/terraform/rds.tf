# Multi-AZ PostgreSQL RDS instance in private data tier
resource "aws_db_subnet_group" "rds" {
  name       = "${var.project_name}-rds-subnet-group"
  subnet_ids = aws_subnet.private_db[*].id

  tags = { Name = "${var.project_name}-rds-subnet-group" }
}

resource "aws_db_instance" "rds" {
  identifier             = "rds-storage"
  engine                 = "postgres"
  engine_version         = var.db_engine_version
  instance_class         = var.db_instance_class
  allocated_storage      = 100
  max_allocated_storage  = 500
  storage_type           = "gp3"
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az               = true
  storage_encrypted      = true
  backup_retention_period = 7
  skip_final_snapshot    = true
  deletion_protection    = false
  performance_insights_enabled = true

  tags = { Name = "rds-storage" }
}
