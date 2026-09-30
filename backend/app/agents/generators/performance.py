"""Performance strategy for the shared generator template."""

from app.agents.generators.base import GeneratorAgent
from app.domain.enums import Variant


class PerformanceGeneratorAgent(GeneratorAgent):
    variant = Variant.PERFORMANCE
    optimisation_directive = (
        "Optimise for performance. Prefer larger instance classes, multi_az = true "
        "for relational databases, autoscaling via an ASG with scaling policies "
        "and/or a Kubernetes HorizontalPodAutoscaler, multiple replicas, caching "
        "when the plan has a cache, and load balancing across Availability Zones. "
        "Configure autoscaling for every application service: a "
        "HorizontalPodAutoscaler for each Kubernetes Deployment, Application "
        "Auto Scaling (aws_appautoscaling_target and aws_appautoscaling_policy) "
        "for each ECS service, and scaling policies for any EC2 Auto Scaling "
        "group."
    )
