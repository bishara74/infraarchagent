"""Plan-specific schema/security guidance inside the existing 6000-character cap."""

import json
import re
from dataclasses import dataclass
from typing import Any

from app.domain.plan import DeploymentPlan, StorageKind
from app.security.catalogue import guidance
from app.validation.schema_context import generator_schema_guidance

SERVICE_TYPES = {
    "ec2": {"aws_instance"},
    "eks": {"aws_eks_cluster"},
    "ecs": {"aws_ecs_service", "aws_ecs_task_definition"},
    "fargate": {"aws_ecs_service", "aws_ecs_task_definition"},
    "rds": {"aws_db_instance"},
    "s3": {"aws_s3_bucket"},
    "cloudfront": {
        "aws_cloudfront_distribution",
        "aws_cloudfront_origin_access_control",
    },
    "alb": {"aws_lb", "aws_lb_listener"},
    "elb": {"aws_lb", "aws_lb_listener"},
    "nlb": {"aws_lb", "aws_lb_listener"},
    "cloudwatch": {"aws_cloudwatch_log_group"},
}


def plan_resource_types(plan: DeploymentPlan) -> set[str]:
    types: set[str] = set()
    for service in plan.services:
        tokens = set(re.findall(r"[a-z0-9]+", service.aws_service.lower()))
        for token, selected in SERVICE_TYPES.items():
            if token in tokens:
                types.update(selected)
        if tokens & {"ec2", "eks", "ecs", "fargate", "rds", "alb", "elb", "nlb"}:
            types.update(
                {
                    "aws_vpc",
                    "aws_subnet",
                    "aws_security_group",
                    "aws_route_table",
                    "aws_route_table_association",
                    "aws_internet_gateway",
                }
            )
        if "load" in tokens and "balancer" in tokens:
            types.update({"aws_lb", "aws_lb_listener", "aws_subnet", "aws_vpc"})
    for storage in plan.storage:
        if storage.kind == StorageKind.OBJECT_STORAGE:
            types.add("aws_s3_bucket")
        elif storage.kind == StorageKind.RELATIONAL_DB:
            types.add("aws_db_instance")
        elif storage.kind == StorageKind.BLOCK_VOLUME:
            types.add("aws_ebs_volume")
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
    named: list[str] = []
    for aws_service in [s.aws_service for s in plan.services] + [
        s.aws_service for s in plan.storage
    ]:
        tokens = set(re.findall(r"[a-z0-9]+", aws_service.lower()))
        for token, selected in SERVICE_TYPES.items():
            if token in tokens:
                named.extend(sorted(selected))
        if {"load", "balancer"} <= tokens:
            named.extend(("aws_lb", "aws_lb_listener"))
    storage_types = {
        StorageKind.OBJECT_STORAGE: "aws_s3_bucket",
        StorageKind.RELATIONAL_DB: "aws_db_instance",
        StorageKind.BLOCK_VOLUME: "aws_ebs_volume",
    }
    named.extend(storage_types[s.kind] for s in plan.storage if s.kind in storage_types)
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
