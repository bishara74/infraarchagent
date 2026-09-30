# RDS relational database (rds-db) with multi-AZ for HA
resource "aws_db_subnet_group" "rds_db" {
  name       = "rds-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "rds_db" {
  name   = "rds-db-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "rds_db" {
  identifier              = "rds-db"
  engine                  = "postgres"
  engine_version          = "15.4"
  instance_class          = var.db_instance_class
  allocated_storage       = 100
  max_allocated_storage   = 500
  storage_type            = "gp3"
  db_name                 = var.db_name
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.rds_db.name
  vpc_security_group_ids  = [aws_security_group.rds_db.id]
  multi_az                = true
  backup_retention_period = 7
  skip_final_snapshot     = true
  storage_encrypted       = true
  performance_insights_enabled = true
}
