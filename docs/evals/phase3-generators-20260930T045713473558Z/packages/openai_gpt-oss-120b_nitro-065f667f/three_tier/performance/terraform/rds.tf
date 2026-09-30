# Managed PostgreSQL instance
resource "aws_db_subnet_group" "rds" {
  name       = "${var.project_name}-rds-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_rds_cluster" "postgres" {
  cluster_identifier = "${var.project_name}-rds"
  engine             = "aurora-postgresql"
  engine_version     = "13.9"
  master_username    = var.db_username
  master_password    = var.db_password
  backup_retention_period = 7
  skip_final_snapshot = true
  db_subnet_group_name = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  storage_encrypted = true
  apply_immediately = true
  engine_mode = "provisioned"
  scaling_configuration {
    auto_pause = false
    min_capacity = 2
    max_capacity = 8
  }
  availability_zones = data.aws_availability_zones.available.names
}