"""Plan-specific schema/security guidance inside the existing 6000-character cap."""

import json
import re
from dataclasses import dataclass
from typing import Any

from app.domain.plan import DeploymentPlan, StorageKind
from app.security.catalogue import guidance
from app.validation.schema_context import generator_schema_guidance

NETWORK_TYPES = {
    "aws_vpc",
    "aws_subnet",
    "aws_security_group",
    "aws_route_table",
    "aws_route_table_association",
    "aws_internet_gateway",
}
REST_API_TYPES = {
    "aws_api_gateway_rest_api",
    "aws_api_gateway_resource",
    "aws_api_gateway_method",
    "aws_api_gateway_integration",
    "aws_api_gateway_deployment",
    "aws_api_gateway_stage",
}
HTTP_API_TYPES = {
    "aws_apigatewayv2_api",
    "aws_apigatewayv2_integration",
    "aws_apigatewayv2_route",
    "aws_apigatewayv2_deployment",
    "aws_apigatewayv2_stage",
}
SERVICE_TYPES = {
    "ec2": {"aws_instance"},
    "eks": {"aws_eks_cluster"},
    "ecs": {"aws_ecs_service", "aws_ecs_task_definition"},
    "fargate": {"aws_ecs_service", "aws_ecs_task_definition"},
    "rds": {"aws_db_instance"},
    "aurora": {"aws_rds_cluster", "aws_rds_cluster_instance"},
    "s3": {"aws_s3_bucket"},
    "cloudfront": {
        "aws_cloudfront_distribution",
        "aws_cloudfront_origin_access_control",
    },
    "alb": {"aws_lb", "aws_lb_listener"},
    "elb": {"aws_lb", "aws_lb_listener"},
    "nlb": {"aws_lb", "aws_lb_listener"},
    "cloudwatch": {"aws_cloudwatch_log_group"},
    "lambda": {"aws_lambda_function", "aws_lambda_permission", "aws_iam_role"},
    "apigateway": REST_API_TYPES | HTTP_API_TYPES,
    "apigateway_rest": REST_API_TYPES,
    "apigatewayv2": HTTP_API_TYPES,
    "dynamodb": {"aws_dynamodb_table"},
    "elasticache": {
        "aws_elasticache_cluster",
        "aws_elasticache_replication_group",
        "aws_elasticache_subnet_group",
    },
    "redis": {"aws_elasticache_replication_group", "aws_elasticache_subnet_group"},
    "acm": {"aws_acm_certificate", "aws_acm_certificate_validation"},
    "natgateway": {"aws_nat_gateway", "aws_eip"},
    "vpc": NETWORK_TYPES,
    "amp": {"aws_prometheus_workspace"},
    "amg": {"aws_grafana_workspace", "aws_iam_role"},
    "ebs": {"aws_ebs_volume"},
    "route53": {"aws_route53_zone", "aws_route53_record"},
    "sqs": {"aws_sqs_queue"},
    "sns": {"aws_sns_topic", "aws_sns_topic_subscription"},
    "msk": {"aws_msk_cluster"},
    "autoscaling": {"aws_autoscaling_group", "aws_launch_template"},
    "redshift": {"aws_redshift_cluster", "aws_redshift_subnet_group"},
}
# Match structured service labels at word boundaries, never request/purpose text.
SERVICE_ALIASES = {
    "elasticloadbalancing": "elb",
    "elasticloadbalancingv2": "elb",
    "elastic load balancing": "elb",
    "elastic load balancing v2": "elb",
    "application load balancer": "alb",
    "network load balancer": "nlb",
    "load balancer": "elb",
    "elastic compute cloud": "ec2",
    "elastic kubernetes service": "eks",
    "kubernetes": "eks",
    "k8s": "eks",
    "elastic container service": "ecs",
    "relational database service": "rds",
    "simple storage service": "s3",
    "cloud front": "cloudfront",
    "cloud watch": "cloudwatch",
    "api gateway": "apigateway",
    "api gateway rest": "apigateway_rest",
    "rest api gateway": "apigateway_rest",
    "apigateway rest": "apigateway_rest",
    "api gateway http": "apigatewayv2",
    "http api gateway": "apigatewayv2",
    "api gateway v2": "apigatewayv2",
    "apigateway http": "apigatewayv2",
    "apigateway v2": "apigatewayv2",
    "dynamo db": "dynamodb",
    "elasti cache": "elasticache",
    "certificate manager": "acm",
    "nat gateway": "natgateway",
    "virtual private cloud": "vpc",
    "elastic block store": "ebs",
    "route 53": "route53",
    "simple queue service": "sqs",
    "simple notification service": "sns",
    "kafka": "msk",
    "managed streaming for apache kafka": "msk",
    "auto scaling": "autoscaling",
    "managed prometheus": "amp",
    "managed service for prometheus": "amp",
    "managed grafana": "amg",
    "prometheus": "prometheus",
    "grafana": "grafana",
}
NETWORKED_SERVICES = {
    "ec2",
    "eks",
    "ecs",
    "fargate",
    "rds",
    "aurora",
    "alb",
    "elb",
    "nlb",
    "elasticache",
    "redis",
    "natgateway",
    "msk",
    "redshift",
    "autoscaling",
}
STORAGE_TYPES = {
    StorageKind.OBJECT_STORAGE: {"aws_s3_bucket"},
    StorageKind.RELATIONAL_DB: {"aws_db_instance"},
    StorageKind.NOSQL_DB: {"aws_dynamodb_table"},
    StorageKind.BLOCK_VOLUME: {"aws_ebs_volume"},
    StorageKind.CACHE: {
        "aws_elasticache_replication_group",
        "aws_elasticache_subnet_group",
    },
}


def service_keys(aws_service: str) -> set[str]:
    label = " " + " ".join(re.findall(r"[a-z0-9]+", aws_service.casefold())) + " "
    aliases = {**{k.replace("_", " "): k for k in SERVICE_TYPES}, **SERVICE_ALIASES}
    keys = {key for alias, key in aliases.items() if f" {alias} " in label}
    if keys & {"apigateway_rest", "apigatewayv2"}:
        keys.discard("apigateway")
    if "amp" in keys:
        keys.discard("prometheus")
    if "amg" in keys:
        keys.discard("grafana")
    if "aurora" in keys:
        keys.discard("rds")
    return keys


def service_resource_types(
    aws_service: str, *, hosting_types: set[str] | None = None
) -> set[str]:
    keys = service_keys(aws_service)
    types = {name for key in keys for name in SERVICE_TYPES.get(key, set())}
    if keys & {"prometheus", "grafana"}:
        types.update(hosting_types or set())
    return types


def hosting_resource_types(plan: DeploymentPlan) -> set[str]:
    """Self-hosted monitoring inherits only compute explicitly named in the plan."""
    return {
        name
        for service in plan.services
        for key in service_keys(service.aws_service) & {"ec2", "eks", "ecs", "fargate"}
        for name in SERVICE_TYPES[key]
    }


def _direct_resource_types(plan: DeploymentPlan) -> list[str]:
    named = []
    hosting = hosting_resource_types(plan)
    for service in plan.services:
        named.extend(
            sorted(service_resource_types(service.aws_service, hosting_types=hosting))
        )
    for storage in plan.storage:
        selected = service_resource_types(storage.aws_service)
        # A named storage service (e.g. Redshift) wins over a generic kind.
        named.extend(sorted(selected or STORAGE_TYPES.get(storage.kind, set())))
    return named


def plan_resource_types(plan: DeploymentPlan) -> set[str]:
    types = set(_direct_resource_types(plan))
    labels = [s.aws_service for s in plan.services] + [
        s.aws_service for s in plan.storage
    ]
    for label in labels:
        if service_keys(label) & NETWORKED_SERVICES:
            types.update(NETWORK_TYPES)
    return types


def supporting_guidance(types: set[str]) -> list[str]:
    lines = []
    if "aws_s3_bucket" in types:
        lines.append(
            "S3: associate encryption with each bucket; "
            "reuse one rotating KMS key/alias. "
            "Log destinations need public-access blocks, versioning and SSE-S3; "
            "add scoped delivery policies, never self-logging."
        )
    if "aws_lb" in types:
        lines.append(
            "LB: use an SSE-S3 log destination with "
            "service-specific delivery permissions; "
            "NLB logs require a TLS listener. Preserve listener/certificate intent."
        )
    if "aws_vpc" in types:
        lines.append(
            "VPC: flow logs need an encrypted CloudWatch group "
            "and scoped delivery role/policy. "
            "Resolve subnet route tables; preserve public subnet connectivity. "
            "Manage unused VPC default groups with explicit empty ingress/egress; "
            "preserve rules required by actual consumers."
        )
    if "aws_db_instance" in types:
        lines.append(
            "RDS: enhanced monitoring needs a "
            "monitoring.rds.amazonaws.com role/policy; "
            "use compatible engine features and preserve configured encryption keys. "
            "Keep at least seven days of backups, preserving longer retention."
        )
    if "aws_cloudwatch_log_group" in types:
        lines.append(
            "CloudWatch: KMS permissions must allow the regional Logs service "
            "for this group's encryption context."
        )
    return lines


def priority_resource_types(plan: DeploymentPlan) -> tuple[str, ...]:
    """Explicit plan services/storage precede inferred supporting infrastructure."""
    named = _direct_resource_types(plan)
    types = plan_resource_types(plan)
    return tuple(dict.fromkeys([*(n for n in named if n in types), *sorted(types)]))


@dataclass(frozen=True)
class GenerationContext:
    text: str
    schema_chars: int
    checklist_chars: int
    truncated: bool
    resource_types: tuple[str, ...]
    omitted_required: tuple[str, ...] = ()
    omitted_conditional: tuple[str, ...] = ()

    def metrics(self) -> dict[str, Any]:
        return {
            "generator_schema_only_context_chars": self.schema_chars,
            "generator_security_context_chars": self.checklist_chars,
            "generator_context_truncated": self.truncated,
            "generator_schema_context_overflow": bool(
                self.omitted_required or self.omitted_conditional
            ),
            "generator_schema_omitted_resource_types": {
                "required": list(self.omitted_required),
                "conditional_required": list(self.omitted_conditional),
            },
        }


def generation_context(plan: DeploymentPlan) -> GenerationContext:
    types = plan_resource_types(plan)
    priority = priority_resource_types(plan)
    budgeted = generator_schema_guidance(4500, resource_types=priority)
    schema = budgeted.text
    header = "\nSecurity checklist:\n"
    lines = [
        "Syntax: close quoted strings; use one block argument per line, no semicolons. "
        "Encode IAM policies with jsonencode() or a valid heredoc. "
        "Escape quotes (including PromQL) inside JSON strings."
    ] + supporting_guidance(types)
    supporting = "\n".join(lines)
    controls = guidance(types, max(0, 1500 - len(header) - len(supporting) - 1))
    checklist = header + supporting + ("\n" + controls if controls else "")
    checklist = checklist[:1500]
    entries = json.loads(schema or "[]")
    included = {e.get("type") for e in entries}
    all_controls = guidance(types, 10000)
    truncated = (
        bool(types - included)
        or any(e.get("truncated") for e in entries)
        or len(header + supporting + "\n" + all_controls) > 1500
    )
    return GenerationContext(
        schema + checklist,
        len(schema),
        len(checklist),
        truncated,
        priority,
        budgeted.omitted_required,
        budgeted.omitted_conditional,
    )
