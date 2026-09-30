# EFS shared storage mounted by microservice-a and microservice-b
resource "aws_efs_file_system" "efs_storage" {
  creation_token = "efs-storage"
  encrypted      = true
  tags           = merge(local.common_tags, { Name = "efs-storage" })
}

resource "aws_efs_mount_target" "efs_storage" {
  count           = length(aws_subnet.private)
  file_system_id  = aws_efs_file_system.efs_storage.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.efs.id]
}
