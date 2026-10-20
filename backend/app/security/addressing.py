"""D-56 public-IP defaults follow resolved consumers, not subnet names."""

from typing import Any

from app.security.instances import Instance, Instances, Ref, Unresolved
from app.security.terraform import edit_resource

COMPUTE = {
    "aws_instance",
    "aws_launch_template",
    "aws_launch_configuration",
    "aws_autoscaling_group",
    "aws_ecs_service",
    "aws_eks_node_group",
    "aws_network_interface",
    "aws_spot_instance_request",
    "aws_spot_fleet_request",
    "aws_eks_fargate_profile",
    "aws_ec2_fleet",
}


def refs(value: Any) -> list[Ref]:
    if isinstance(value, Ref):
        return [value]
    if isinstance(value, dict):
        return [r for v in value.values() for r in refs(v)]
    if isinstance(value, (list, tuple)):
        return [r for v in value for r in refs(v)]
    return []


def belongs(value: Any, subnet: Instance) -> bool:
    return any(
        r.module == subnet.module and r.address == subnet.address for r in refs(value)
    )


def safe_subnet(graph: Instances, subnet: Instance) -> bool:
    if subnet.module in graph.unsafe or graph.unknown(subnet.module, COMPUTE):
        return False
    harmless = {
        "aws_lb",
        "aws_alb",
        "aws_nat_gateway",
        "aws_db_subnet_group",
        "aws_eks_cluster",
        "aws_route_table_association",
        "aws_elasticache_subnet_group",
    }

    def network_fields(value: Any) -> bool:
        if isinstance(value, dict):
            return any(
                k
                in {
                    "subnet_id",
                    "subnet_ids",
                    "subnets",
                    "vpc_zone_identifier",
                    "network_interfaces",
                }
                or network_fields(v)
                for k, v in value.items()
            )
        return isinstance(value, list) and any(network_fields(v) for v in value)

    for resource in graph.package.resources:
        if (
            resource.module == subnet.module
            and resource.type not in COMPUTE | harmless
            and network_fields(resource.body)
        ):
            return False
    # A template's inherited address behavior may apply through an ASG. Only
    # explicit private templates are safe without tracing a deployment plan.
    for item in graph.all(subnet.module, COMPUTE):
        body = item.resource.body
        try:
            if item.type in {"aws_launch_template", "aws_launch_configuration"}:
                interfaces = graph.get(item, "network_interfaces", [])
                if interfaces:
                    if any(
                        type(i.get("associate_public_ip_address")) is not bool
                        for i in interfaces
                    ):
                        return False
                elif type(graph.get(item, "associate_public_ip_address")) is not bool:
                    return False
                continue
            if item.type == "aws_instance":
                if "network_interface" in body:
                    return False
                attached = graph.get(item, "subnet_id")
                if not isinstance(attached, Ref):
                    return False
                if (
                    belongs(attached, subnet)
                    and type(graph.get(item, "associate_public_ip_address")) is not bool
                ):
                    return False
            elif item.type == "aws_ecs_service":
                networks = graph.get(item, "network_configuration", [])
                for network in networks:
                    assigned = network.get("assign_public_ip", False)
                    if type(assigned) is not bool or not refs(
                        network.get("subnets", [])
                    ):
                        return False
                # awsvpc Fargate public addressing is explicit and independent
                # of the subnet's EC2 auto-assignment default.
                if not networks:
                    return False
            elif item.type == "aws_eks_node_group":
                attached = graph.get(item, "subnet_ids")
                if not refs(attached) or belongs(attached, subnet):
                    return False
            elif item.type == "aws_network_interface":
                if not isinstance(graph.get(item, "subnet_id"), Ref):
                    return False
            elif item.type == "aws_autoscaling_group":
                attached = graph.get(item, "vpc_zone_identifier")
                if not refs(attached):
                    return False
                if belongs(attached, subnet):
                    # Associated template checks above must be explicit; an
                    # unresolved/external launch configuration is not evidence.
                    linked = graph.linked(item, "launch_configuration")
                    templates = graph.get(item, "launch_template", [])
                    resolved_templates = [
                        graph.find(r.module, r.address)
                        for t in templates
                        for r in refs(t.get("id", t.get("name")))
                    ]
                    if not (
                        linked and linked.type == "aws_launch_configuration"
                    ) and not (
                        len(templates) == len(resolved_templates) == 1
                        and resolved_templates[0] is not None
                        and resolved_templates[0].type == "aws_launch_template"
                    ):
                        return False
            elif item.type in {"aws_eks_fargate_profile"}:
                if not refs(graph.get(item, "subnet_ids")):
                    return False
            else:
                return False
        except (Unresolved, TypeError, AttributeError):
            return False
    return True


def repair_addressing(
    files: dict[str, str],
    targets: set[tuple[str, str]] | None = None,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    graph = Instances(files)
    result, records = dict(files), []
    for resource in graph.package.resources:
        if targets is not None and (resource.module, resource.address) not in targets:
            continue
        if (
            resource.type != "aws_subnet"
            or resource.body.get("map_public_ip_on_launch") is not True
        ):
            continue
        instances = [
            i
            for i in graph.all(resource.module, {"aws_subnet"})
            if i.resource == resource
        ]
        schema = graph.package.schema(resource)
        if (
            not instances
            or not schema
            or not all(safe_subnet(graph, subnet) for subnet in instances)
        ):
            continue
        candidate = edit_resource(
            result, resource, {"map_public_ip_on_launch": False}, schema
        )
        if candidate != result:
            records.append(
                {
                    "file": resource.path,
                    "resource": resource.address,
                    "control": "subnet_consumers",
                    "status": "proposed",
                    "reason": "explicit_or_private_consumers",
                    "provider_version": graph.package.version(resource.module),
                }
            )
            result = candidate
    return result, records
