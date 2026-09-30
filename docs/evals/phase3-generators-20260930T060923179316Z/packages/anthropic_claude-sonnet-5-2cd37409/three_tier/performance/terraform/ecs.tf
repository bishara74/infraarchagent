# ECS Fargate cluster and services for app-service-1 and app-service-2
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_iam_role" "ecs_execution" {
  name = "${var.project_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "${var.project_name}-ecs-task-s3-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
      Resource = [aws_s3_bucket.storage.arn, "${aws_s3_bucket.storage.arn}/*"]
    }]
  })
}

resource "aws_cloudwatch_log_group" "app_service_1" {
  name              = "/ecs/${var.project_name}/app-service-1"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "app_service_2" {
  name              = "/ecs/${var.project_name}/app-service-2"
  retention_in_days = 30
}

locals {
  app_services = {
    "app-service-1" = {
      image         = var.app_service_1_image
      log_group     = aws_cloudwatch_log_group.app_service_1.name
      target_group  = aws_lb_target_group.app_service_1.arn
    }
    "app-service-2" = {
      image         = var.app_service_2_image
      log_group     = aws_cloudwatch_log_group.app_service_2.name
      target_group  = aws_lb_target_group.app_service_2.arn
    }
  }
}

resource "aws_ecs_task_definition" "app" {
  for_each                 = local.app_services
  family                   = "${var.project_name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.app_cpu
  memory                   = var.app_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = each.key
    image     = each.value.image
    essential = true
    portMappings = [{
      containerPort = var.app_container_port
      protocol      = "tcp"
    }]
    environment = [
      { name = "DB_HOST", value = aws_db_instance.rds.address },
      { name = "DB_NAME", value = var.db_name },
      { name = "S3_BUCKET", value = aws_s3_bucket.storage.bucket }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = each.value.log_group
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = each.key
      }
    }
  }])
}

resource "aws_ecs_service" "app" {
  for_each        = local.app_services
  name            = each.key
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app[each.key].arn
  desired_count   = var.app_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private_app[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = each.value.target_group
    container_name   = each.key
    container_port   = var.app_container_port
  }

  depends_on = [aws_lb_listener.http]
}
