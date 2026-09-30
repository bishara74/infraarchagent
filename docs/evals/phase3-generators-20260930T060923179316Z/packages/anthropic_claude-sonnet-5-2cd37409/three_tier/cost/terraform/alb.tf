# Internet-facing ALB forwarding to app-service-1 and app-service-2 target groups
resource "aws_lb" "alb" {
  name               = "alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public.id, aws_subnet.private_db_2.id]

  tags = { Name = "alb" }
}

resource "aws_lb_target_group" "app_service_1" {
  name        = "app-service-1"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
    timeout             = 5
  }

  tags = { Name = "app-service-1" }
}

resource "aws_lb_target_group" "app_service_2" {
  name        = "app-service-2"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
    timeout             = 5
  }

  tags = { Name = "app-service-2" }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_service_1.arn
  }
}

resource "aws_lb_listener_rule" "app_service_2" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_service_2.arn
  }

  condition {
    path_pattern {
      values = ["/service2/*"]
    }
  }
}
