# EFS shared storage (efs-storage) for microservice-a and microservice-b
resource "aws_security_group" "efs_storage" {
  name   = "efs-storage-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
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

resource "aws_efs_file_system" "efs_storage" {
  creation_token = "efs-storage"
  encrypted      = true
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"
  tags = { Name = "efs-storage" }
}

resource "aws_efs_mount_target" "efs_storage" {
  count           = length(aws_subnet.private)
  file_system_id  = aws_efs_file_system.efs_storage.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.efs_storage.id]
}
