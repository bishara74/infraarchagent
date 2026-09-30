# ECS cluster and task definitions
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-ecs-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Task definition shared base
locals "task_base" {
  cpu    = 512
  memory = 1024
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
}

resource "aws_ecs_task_definition" "app1" {
  family                   = "${var.project_name}-app1"
  cpu                      = local.task_base.cpu
  memory                   = local.task_base.memory
  network_mode             = local.task_base.network_mode
  requires_compatibilities = local.task_base.requires_compatibilities
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  container_definitions = jsonencode([
    {
      name  = "app-service-1",
      image = var.container_image_1,
      portMappings = [{ containerPort = 80, protocol = "tcp" }]
    }
  ])
}

resource "aws_ecs_task_definition" "app2" {
  family                   = "${var.project_name}-app2"
  cpu                      = local.task_base.cpu
  memory                   = local.task_base.memory
  network_mode             = local.task_base.network_mode
  requires_compatibilities = local.task_base.requires_compatibilities
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  container_definitions = jsonencode([
    {
      name  = "app-service-2",
      image = var.container_image_2,
      portMappings = [{ containerPort = 80, protocol = "tcp" }]
    }
  ])
}

# Services
resource "aws_ecs_service" "app1" {
  name            = "${var.project_name}-app1"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app1.arn
  desired_count   = var.desired_task_count
  launch_type     = "FARGATE"
  network_configuration {
    subnets         = module.vpc.private_subnets
    security_groups = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.app1.arn
    container_name   = "app-service-1"
    container_port   = 80
  }
}

resource "aws_ecs_service" "app2" {
  name            = "${var.project_name}-app2"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app2.arn
  desired_count   = var.desired_task_count
  launch_type     = "FARGATE"
  network_configuration {
    subnets         = module.vpc.private_subnets
    security_groups = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.app2.arn
    container_name   = "app-service-2"
    container_port   = 80
  }
}