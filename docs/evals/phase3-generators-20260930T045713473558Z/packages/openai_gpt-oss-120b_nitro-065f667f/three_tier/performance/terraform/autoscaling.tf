# Application Auto Scaling for each ECS service
resource "aws_appautoscaling_target" "app1" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app1.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "app1_cpu" {
  name               = "${var.project_name}-app1-cpu-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.app1.resource_id
  scalable_dimension = aws_appautoscaling_target.app1.scalable_dimension
  service_namespace  = aws_appautoscaling_target.app1.service_namespace
  target_tracking_scaling_policy_configuration {
    target_value       = 50.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_out_cooldown  = 60
    scale_in_cooldown   = 300
  }
}

resource "aws_appautoscaling_target" "app2" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app2.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "app2_cpu" {
  name               = "${var.project_name}-app2-cpu-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.app2.resource_id
  scalable_dimension = aws_appautoscaling_target.app2.scalable_dimension
  service_namespace  = aws_appautoscaling_target.app2.service_namespace
  target_tracking_scaling_policy_configuration {
    target_value       = 50.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_out_cooldown = 60
    scale_in_cooldown  = 300
  }
}