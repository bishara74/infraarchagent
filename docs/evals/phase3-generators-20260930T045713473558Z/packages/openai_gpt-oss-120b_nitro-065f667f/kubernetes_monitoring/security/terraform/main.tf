# Terraform main configuration
terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.region
}

provider "kubernetes" {
  host                   = aws_eks_cluster.eks.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.eks.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.eks.token
}

# VPC
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  tags = { Name = "${var.cluster_name}-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.cluster_name}-igw" }
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  tags = { Name = "${var.cluster_name}-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = { Name = "${var.cluster_name}-private-${count.index}" }
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public[0].id
  tags = { Name = "${var.cluster_name}-nat" }
}

resource "aws_eip" "nat_eip" {
  vpc = true
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "${var.cluster_name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
  tags = { Name = "${var.cluster_name}-private-rt" }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security Groups
resource "aws_security_group" "alb_sg" {
  name        = "${var.cluster_name}-alb-sg"
  description = "Allow inbound HTTPS from the internet"
  vpc_id      = aws_vpc.this.id
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.cluster_name}-alb-sg" }
}

resource "aws_security_group" "node_sg" {
  name        = "${var.cluster_name}-node-sg"
  description = "Node communication"
  vpc_id      = aws_vpc.this.id
  ingress {
    description = "All traffic from within SG"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }
  ingress {
    description = "Ingress from ALB"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.cluster_name}-node-sg" }
}

# IAM roles for EKS
resource "aws_iam_role" "eks_cluster" {
  name = "${var.cluster_name}-cluster-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "eks.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_AmazonEKSClusterPolicy" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role_policy_attachment" "eks_cluster_AmazonEKSVPCResourceController" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
}

resource "aws_iam_role" "eks_node" {
  name = "${var.cluster_name}-node-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "ec2.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_node_AmazonEKSWorkerNodePolicy" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "eks_node_AmazonEC2ContainerRegistryReadOnly" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "eks_node_AmazonEKS_CNI_Policy" {
  role       = aws_iam_role.eks_node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

# EKS Cluster
resource "aws_eks_cluster" "eks" {
  name    = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn
  version = "1.30"
  vpc_config {
    subnet_ids = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
    security_group_ids = [aws_security_group.node_sg.id]
    endpoint_private_access = true
    endpoint_public_access  = false
  }
  tags = { Name = var.cluster_name }
}

data "aws_eks_cluster_auth" "eks" {
  name = aws_eks_cluster.eks.name
}

resource "aws_eks_node_group" "workers" {
  cluster_name    = aws_eks_cluster.eks.name
  node_group_name = "workers"
  node_role       = aws_iam_role.eks_node.arn
  subnet_ids      = aws_subnet.private[*].id
  scaling_config {
    desired_size = var.node_desired_size
    max_size     = var.node_desired_size + 1
    min_size     = var.node_desired_size - 1
  }
  instance_types = [var.node_instance_type]
  remote_access {
    ec2_ssh_key = "${var.cluster_name}-key"
  }
  tags = { Name = "${var.cluster_name}-workers" }
}

# EFS file system for shared storage
resource "aws_efs_file_system" "efs" {
  encrypted = true
  tags = { Name = "${var.cluster_name}-efs" }
}

resource "aws_efs_mount_target" "private_a" {
  file_system_id = aws_efs_file_system.efs.id
  subnet_id      = aws_subnet.private[0].id
  security_groups = [aws_security_group.node_sg.id]
}

resource "aws_efs_mount_target" "private_b" {
  file_system_id = aws_efs_file_system.efs.id
  subnet_id      = aws_subnet.private[1].id
  security_groups = [aws_security_group.node_sg.id]
}

# RDS PostgreSQL instance (encrypted, private)
resource "random_password" "rds_master" {
  length  = 16
  special = false
}

resource "aws_db_subnet_group" "rds_subnet" {
  name       = "${var.cluster_name}-rds-subnet"
  subnet_ids = aws_subnet.private[*].id
  tags = { Name = "${var.cluster_name}-rds-subnet" }
}

resource "aws_db_instance" "postgres" {
  identifier         = "${var.cluster_name}-postgres"
  engine             = "postgres"
  engine_version     = "15"
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  db_subnet_group_name = aws_db_subnet_group.rds_subnet.name
  vpc_security_group_ids = [aws_security_group.node_sg.id]
  username           = "admin"
  password           = random_password.rds_master.result
  skip_final_snapshot = true
  storage_encrypted   = true
  publicly_accessible = false
  tags = { Name = "${var.cluster_name}-postgres" }
}

# S3 bucket for logs with public access block
resource "aws_s3_bucket" "logs" {
  bucket = "${var.cluster_name}-logs-${random_id.bucket_suffix.hex}"
  force_destroy = true
  tags = { Name = "${var.cluster_name}-logs" }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_public_access_block" "logs_block" {
  bucket = aws_s3_bucket.logs.id
  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls  = true
  restrict_public_buckets = true
}

# Enable VPC flow logs for auditability
resource "aws_cloudwatch_log_group" "vpc_flow" {
  name = "/aws/vpc/flow-logs/${var.cluster_name}"
  retention_in_days = 90
}

resource "aws_flow_log" "vpc" {
  iam_role_arn    = aws_iam_role.flow_log_role.arn
  log_group_name  = aws_cloudwatch_log_group.vpc_flow.name
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.this.id
}

resource "aws_iam_role" "flow_log_role" {
  name = "${var.cluster_name}-flowlog-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "vpc-flow-logs.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "flow_log" {
  name = "${var.cluster_name}-flowlog-policy"
  role = aws_iam_role.flow_log_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = ["logs:CreateLogStream", "logs:PutLogEvents"],
      Resource = "*"
    }]
  })
}
