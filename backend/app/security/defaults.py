"""D-56 guarded backup retention and unused VPC default security groups."""

from typing import Any

from app.security.addressing import COMPUTE, refs
from app.security.instances import Instance, Instances, Unresolved
from app.security.templates import Builder, TemplateUnavailable
from app.security.terraform import edit_resource


def default_group_unused(
    graph: Instances, vpc: Instance, group: Instance | None
) -> bool:
    if vpc.module in graph.unsafe or graph.unknown(vpc.module, COMPUTE):
        return False
    if any(
        scope == vpc.module and value is None
        for (scope, _), value in graph.expanded.items()
    ):
        return False
    for item in graph.all(vpc.module):
        if item.type in {"aws_security_group", "aws_default_security_group"}:
            continue
        if item.type in {
            "aws_security_group_rule",
            "aws_vpc_security_group_ingress_rule",
            "aws_vpc_security_group_egress_rule",
        }:
            if group and graph.linked(item, "security_group_id") == group:
                return False
            continue
        body = item.resource.body
        try:
            infrastructure = {
                "aws_vpc",
                "aws_subnet",
                "aws_route_table",
                "aws_route",
                "aws_route_table_association",
                "aws_internet_gateway",
                "aws_nat_gateway",
                "aws_flow_log",
                "aws_db_subnet_group",
                "aws_elasticache_subnet_group",
                "aws_eks_cluster",
                "aws_eks_node_group",
                "aws_lb",
                "aws_alb",
                "aws_main_route_table_association",
                "aws_default_route_table",
            }
            if item.type not in infrastructure | COMPUTE | {
                "aws_db_instance",
                "aws_rds_cluster",
            } and any(
                k in body
                for k in (
                    "vpc_id",
                    "subnet_id",
                    "subnet_ids",
                    "subnet_group_name",
                    "db_subnet_group_name",
                    "cache_subnet_group_name",
                    "vpc_config",
                )
            ):
                return False
            fields = [
                k
                for k in (
                    "vpc_security_group_ids",
                    "security_group_ids",
                    "security_groups",
                )
                if k in body
            ]
            networks = (
                graph.get(item, "network_configuration", [])
                if "network_configuration" in body
                else []
            )
            configs = graph.get(item, "vpc_config", []) if "vpc_config" in body else []
            attachments = [graph.get(item, k) for k in fields]
            attachments.extend(n.get("security_groups") for n in networks)
            attachments.extend(n.get("security_group_ids") for n in configs)
            if (
                item.type
                in {
                    "aws_instance",
                    "aws_launch_configuration",
                    "aws_launch_template",
                    "aws_db_instance",
                    "aws_rds_cluster",
                    "aws_network_interface",
                }
                and not attachments
            ):
                return False
            if item.type == "aws_ecs_service" and not networks:
                return False
            if (
                item.type in {"aws_lb", "aws_alb"}
                and graph.get(item, "load_balancer_type", "application")
                == "application"
                and not attachments
            ):
                return False
            for value in attachments:
                resolved = refs(value)
                if (
                    not resolved
                    or not isinstance(value, list)
                    or len(resolved) != len(value)
                ):
                    return False
                if any(
                    r.attribute not in {"id", "arn", "name"}
                    or graph.find(r.module, r.address) is None
                    or not any(
                        sg.address == r.address and sg.module == r.module
                        for sg in graph.all(vpc.module, {"aws_security_group"})
                    )
                    or (group and r.address == group.address)
                    or r.address == vpc.address
                    for r in resolved
                ):
                    return False
            if "launch_template" in body or "launch_configuration" in body:
                # Custom/external launch settings may hide default-group use.
                return False
        except (Unresolved, TypeError, AttributeError):
            return False
    return True


def repair_defaults(
    files: dict[str, str], targets: set[tuple[str, str]] | None = None
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    graph = Instances(files)
    result, records = dict(files), []
    for resource in graph.package.resources:
        if targets is not None and (resource.module, resource.address) not in targets:
            continue
        if resource.type in {"aws_db_instance", "aws_rds_cluster"}:
            old = resource.body.get("backup_retention_period", 0)
            if type(old) is not int or old >= 7 or old < 0:
                continue
            schema = graph.package.schema(resource)
            if not schema:
                continue
            candidate = edit_resource(
                result, resource, {"backup_retention_period": 7}, schema
            )
            if candidate != result:
                records.append(
                    {
                        "file": resource.path,
                        "resource": resource.address,
                        "control": "backup_retention",
                        "status": "proposed",
                        "reason": "seven_day_retention",
                    }
                )
                result = candidate
        elif resource.type == "aws_vpc":
            vpc = graph.find(resource.module, resource.address)
            if vpc is None:
                continue
            groups = [
                g
                for g in graph.all(resource.module, {"aws_default_security_group"})
                if graph.linked(g, "vpc_id") == vpc
            ]
            if len(groups) > 1 or not default_group_unused(
                graph, vpc, groups[0] if groups else None
            ):
                continue
            try:
                builder = Builder(result, resource.module)
                if groups:
                    group = groups[0].resource
                    if (
                        group.body.get("ingress") == []
                        and group.body.get("egress") == []
                    ):
                        continue
                    builder.edit(group, {"ingress": [], "egress": []})
                else:
                    builder.add(
                        "aws_default_security_group",
                        "infraarch_default_" + resource.name,
                        {
                            "vpc_id": "${" + resource.address + ".id}",
                            "ingress": [],
                            "egress": [],
                        },
                    )
                candidate = builder.finish()
            except TemplateUnavailable:
                continue
            if candidate != result:
                result = candidate
                records.append(
                    {
                        "file": resource.path,
                        "resource": resource.address,
                        "control": "default_group",
                        "status": "proposed",
                        "reason": "proven_unused_default_group",
                    }
                )
    return result, records
