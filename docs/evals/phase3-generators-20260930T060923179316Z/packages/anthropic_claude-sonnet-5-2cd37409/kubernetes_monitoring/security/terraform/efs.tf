# Encrypted EFS file system for shared microservice storage
resource "aws_kms_key" "efs" {
  description         = "KMS key for EFS encryption"
  enable_key_rotation = true
  tags                = local.common_tags
}

resource "aws_efs_file_system" "efs_storage" {
  creation_token = "${local.name_prefix}-efs-storage"
  encrypted      = true
  kms_key_id     = aws_kms_key.efs.arn

  tags = merge(local.common_tags, { Name = local.storage.efs })
}

resource "aws_efs_mount_target" "efs_storage" {
  count           = length(aws_subnet.private)
  file_system_id  = aws_efs_file_system.efs_storage.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.efs.id]
}
