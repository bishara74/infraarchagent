"""D-63: bounded exposure preservation, independent of scanner policy.

D-66 uses final retained-file detection rather than candidate rejection.
Unknown exposure is informational and never establishes deployment correctness.
"""

import json
import re
from dataclasses import asdict, is_dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any, Literal

from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.security.instances import Instances, Ref, Unresolved
from app.security.terraform import Resource, objects, subnet_intent
from app.validation.documents import blocks
from app.validation.provider_schema import provider_requirements

if TYPE_CHECKING:
    from app.domain.conformance import PlanConformanceAssessment

LB = {"aws_lb", "aws_alb", "aws_elb"}
SERVICE_TYPES = {
    "alb": LB,
    "elb": LB,
    "nlb": LB,
    "loadbalancer": LB,
    "applicationloadbalancer": LB,
    "networkloadbalancer": LB,
    "elasticloadbalancing": LB,
    "elasticloadbalancingv2": LB,
    "apigateway": {"aws_api_gateway_rest_api", "aws_apigatewayv2_api"},
    "apigatewayrest": {"aws_api_gateway_rest_api"},
    "apigatewayv2": {"aws_apigatewayv2_api"},
    "cloudfront": {"aws_cloudfront_distribution"},
    "ec2": {"aws_instance", "aws_launch_template", "aws_launch_configuration"},
    "ecs": {"aws_ecs_service"},
    "fargate": {"aws_ecs_service"},
    "rds": {"aws_db_instance", "aws_rds_cluster_instance", "aws_rds_cluster"},
    "aurora": {"aws_rds_cluster", "aws_rds_cluster_instance"},
    "eks": {"aws_eks_cluster"},
    "lambda": {"aws_lambda_function_url"},
    "s3": {"aws_s3_bucket"},
}
EXPOSURE = {
    "acl",
    "policy",
    "internal",
    "scheme",
    "publicly_accessible",
    "associate_public_ip_address",
    "endpoint_configuration",
    "disable_execute_api_endpoint",
    "enabled",
    "authorization_type",
    "vpc_config",
    "network_configuration",
}
PLACEMENT = {
    "subnets",
    "subnet_ids",
    "subnet_id",
    "subnet_mapping",
    "db_subnet_group_name",
    "network_configuration",
    "vpc_config",
    "vpc_id",
}
INGRESS = {
    "security_groups",
    "security_group_ids",
    "vpc_security_group_ids",
    "ingress",
    "listener",
    "origin",
    "default_cache_behavior",
    "ordered_cache_behavior",
}
SUPPORT = {
    "aws_subnet": {
        "vpc_id",
        "map_public_ip_on_launch",
        "availability_zone",
        "availability_zone_id",
    },
    "aws_route_table_association": {"subnet_id", "route_table_id"},
    "aws_main_route_table_association": {"vpc_id", "route_table_id"},
    "aws_default_route_table": {"default_route_table_id", "route"},
    "aws_route_table": {"vpc_id", "route"},
    "aws_route": {
        "route_table_id",
        "destination_cidr_block",
        "destination_ipv6_cidr_block",
        "gateway_id",
        "nat_gateway_id",
        "network_interface_id",
        "transit_gateway_id",
        "vpc_peering_connection_id",
        "egress_only_gateway_id",
    },
    "aws_internet_gateway": {"vpc_id"},
    "aws_nat_gateway": {"subnet_id", "connectivity_type"},
    "aws_eip": {"instance", "network_interface", "domain"},
    "aws_vpc": {"cidr_block", "ipv6_cidr_block"},
    "aws_db_subnet_group": {"subnet_ids", "name"},
    "aws_security_group": {"ingress", "vpc_id"},
    "aws_default_security_group": {"ingress", "vpc_id"},
    "aws_security_group_rule": {
        "type",
        "security_group_id",
        "from_port",
        "to_port",
        "protocol",
        "cidr_blocks",
        "ipv6_cidr_blocks",
        "source_security_group_id",
        "self",
    },
    "aws_vpc_security_group_ingress_rule": {
        "security_group_id",
        "from_port",
        "to_port",
        "ip_protocol",
        "cidr_ipv4",
        "cidr_ipv6",
        "referenced_security_group_id",
    },
    "aws_lb_listener": {"load_balancer_arn", "port", "protocol", "default_action"},
    "aws_alb_listener": {"load_balancer_arn", "port", "protocol", "default_action"},
    "aws_lb_listener_rule": {"listener_arn", "condition", "action"},
    "aws_alb_listener_rule": {"listener_arn", "condition", "action"},
    "aws_s3_bucket_policy": {"bucket", "policy"},
    "aws_s3_bucket_public_access_block": {
        "bucket",
        "block_public_acls",
        "block_public_policy",
        "ignore_public_acls",
        "restrict_public_buckets",
    },
}
REVERSE = {
    "aws_instance": {"aws_eip": "instance"},
    "aws_subnet": {"aws_route_table_association": "subnet_id"},
    "aws_route_table": {"aws_route": "route_table_id"},
    "aws_default_route_table": {"aws_route": "route_table_id"},
    "aws_security_group": {
        "aws_security_group_rule": "security_group_id",
        "aws_vpc_security_group_ingress_rule": "security_group_id",
    },
    "aws_lb": {
        "aws_lb_listener": "load_balancer_arn",
        "aws_alb_listener": "load_balancer_arn",
    },
    "aws_alb": {
        "aws_lb_listener": "load_balancer_arn",
        "aws_alb_listener": "load_balancer_arn",
    },
    "aws_lb_listener": {"aws_lb_listener_rule": "listener_arn"},
    "aws_alb_listener": {"aws_alb_listener_rule": "listener_arn"},
    "aws_s3_bucket": {
        "aws_s3_bucket_policy": "bucket",
        "aws_s3_bucket_public_access_block": "bucket",
    },
}
NETWORK_TYPES = set(SUPPORT) | set().union(*SERVICE_TYPES.values())


def label(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower()).removeprefix("aws")


def canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        default=lambda v: (
            asdict(v) if is_dataclass(v) and not isinstance(v, type) else str(v)
        ),
    )


def fields(resource: Resource, names: set[str]) -> dict[str, Any]:
    return {
        k: v
        for k, v in resource.body.items()
        if k in names | {"count", "for_each", "provider", "dynamic"}
    }


def named(resource: Resource, name: str) -> bool:
    return label(name) in {
        label(resource.name),
        label(str(resource.body.get("name", ""))),
        label(str(resource.body.get("tags", {}).get("Name", "")))
        if isinstance(resource.body.get("tags"), dict)
        else "",
    }


class View:
    def __init__(self, files: dict[str, str]):
        self.graph = Instances(files)
        self.resources = {
            (r.module, r.address): r for r in self.graph.package.resources
        }

    def bind(self, name: str, types: set[str], unique: bool) -> Resource | None:
        candidates = [r for r in self.resources.values() if r.type in types]
        matches = [r for r in candidates if named(r, name)]
        return (
            matches[0]
            if len(matches) == 1
            else candidates[0]
            if not matches and unique and len(candidates) == 1
            else None
        )

    def value(self, resource: Resource, key: str, default: Any = None) -> Any:
        instances = self.graph.expand(resource.module, resource.address)
        entries = (
            list(instances.values())
            if isinstance(instances, dict)
            else instances
            if isinstance(instances, list)
            else [instances]
        )
        if len(entries) != 1:
            raise Unresolved()
        return self.graph.get(entries[0], key, default)

    def value_or_unknown(self, resource: Resource, key: str) -> str:
        try:
            return canonical(self.value(resource, key))
        except (Unresolved, TypeError, ValueError, KeyError):
            return "unknown"

    def projection(self, resource: Resource, names: set[str]) -> dict[str, Any]:
        """Follow configured references and reverse network attachments only."""
        result: dict[str, Any] = {}
        pending = [(resource, names)]
        seen: set[tuple[str, str]] = set()
        # Auto-addressing belongs to the instance's own subnet, never to a
        # public subnet reached through its NAT egress route.
        address_subnet = (
            self.graph.package.resolve(resource.module, resource.body.get("subnet_id"))
            if resource.type
            in {"aws_instance", "aws_launch_template", "aws_launch_configuration"}
            else None
        )
        while pending:
            item, selected = pending.pop()
            key = item.module, item.address
            if key in seen:
                continue
            seen.add(key)
            body = fields(
                item,
                selected | SUPPORT.get(item.type, set())
                if key == (resource.module, resource.address)
                else selected,
            )
            if item.type == "aws_subnet" and not (
                names == EXPOSURE
                and resource.type
                in {"aws_instance", "aws_launch_template", "aws_launch_configuration"}
                and (address_subnet is None or item == address_subnet)
            ):
                # EC2 auto-addressing is not subnet routing or an ECS/EKS/LB
                # endpoint control. Keep it on possible EC2 exposure paths.
                body.pop("map_public_ip_on_launch", None)
            if (
                key == (resource.module, resource.address)
                and names == EXPOSURE
                and resource.type == "aws_instance"
                and "associate_public_ip_address" not in resource.body
                and "subnet_id" in resource.body
            ):
                body["subnet_id"] = resource.body["subnet_id"]
            result[canonical(key)] = body
            # Resolve dependency *identity* recursively, never deployment inputs.
            expressions = re.findall(r"\b(?:local|var)\.[\w-]+", canonical(body))
            reference_values = [body]
            dependencies: set[str] = set()
            while expressions:
                expression = expressions.pop()
                if expression in dependencies:
                    continue
                dependencies.add(expression)
                prefix, name = expression.split(".", 1)
                for doc in self.graph.package.documents.documents.values():
                    if str(PurePosixPath(doc.path).parent) != item.module:
                        continue
                    if prefix == "var":
                        definitions = [
                            definition
                            for labels, definition in blocks(doc.data, "variable")
                            if labels == (name,)
                        ]
                    else:
                        definitions = (
                            [
                                definition[name]
                                for definition in objects(doc.data.get("locals", []))
                                if name in definition
                            ]
                            if isinstance(doc.data, dict)
                            else []
                        )
                    for definition in definitions:
                        reference_values.append(definition)
                        result[canonical((item.module, expression))] = definition
                        expressions.extend(
                            re.findall(
                                r"\b(?:local|var)\.[\w-]+", canonical(definition)
                            )
                        )
            for doc in self.graph.package.documents.documents.values():
                if str(PurePosixPath(doc.path).parent) == item.module and isinstance(
                    doc.data, dict
                ):
                    for kind in ("terraform", "provider"):
                        if kind in doc.data:
                            result[canonical((item.module, doc.path, kind))] = doc.data[
                                kind
                            ]
            for address in re.findall(
                r"\baws_[\w]+\.[\w-]+", canonical(reference_values)
            ):
                linked = self.resources.get((item.module, address))
                if linked and linked.type in SUPPORT:
                    pending.append((linked, SUPPORT[linked.type]))
            for kind, owner_field in REVERSE.get(item.type, {}).items():
                if names == PLACEMENT and kind not in {
                    "aws_route_table_association",
                    "aws_route",
                }:
                    continue
                for linked in self.resources.values():
                    if linked.module == item.module and linked.type == kind:
                        if kind == "aws_eip" and not any(
                            linked.body.get(field) is not None
                            for field in ("instance", "network_interface")
                        ):
                            continue
                        raw = str(linked.body.get(owner_field, ""))
                        if item.address in re.findall(
                            r"\baws_[\w]+\.[\w-]+", raw
                        ) or not re.search(r"\baws_[\w]+\.[\w-]+", raw):
                            pending.append((linked, SUPPORT[kind]))
            if item.type == "aws_subnet":
                # A changed main-table association affects implicit subnet routes.
                for linked in self.resources.values():
                    if linked.module == item.module and linked.type in {
                        "aws_main_route_table_association",
                        "aws_default_route_table",
                    }:
                        pending.append((linked, SUPPORT[linked.type]))
        if resource.module in self.graph.unsafe:
            for doc in self.graph.package.documents.documents.values():
                if str(PurePosixPath(doc.path).parent) == resource.module:
                    if doc.parse_error:
                        result[canonical((doc.path, "unparseable"))] = doc.source
                    elif isinstance(doc.data, dict) and "module" in doc.data:
                        result[canonical((doc.path, "module"))] = doc.data["module"]
            # Parsing/external modules make changed network evidence unverifiable.
            result["unresolved_module"] = True
        return result

    def exposure(self, resource: Resource) -> str:
        try:
            if resource.type in LB:
                provider = provider_requirements(
                    self.graph.package.documents, resource.module
                ).get("aws", {})
                if provider.get("source", "hashicorp/aws") not in {
                    "hashicorp/aws",
                    "registry.terraform.io/hashicorp/aws",
                }:
                    return "unknown"
                internal = self.value(
                    resource, "internal", False if resource.type != "aws_elb" else None
                )
                scheme = self.value(resource, "scheme")
                if scheme is not None:
                    return {"internet-facing": "public", "internal": "private"}.get(
                        scheme, "unknown"
                    )
                return (
                    "private"
                    if internal is True
                    else "public"
                    if internal is False
                    else "unknown"
                )
            if resource.type in {"aws_db_instance", "aws_rds_cluster_instance"}:
                flag = self.value(resource, "publicly_accessible", False)
                return (
                    "public"
                    if flag is True
                    else "private"
                    if flag is False
                    else "unknown"
                )
            if resource.type == "aws_instance":
                if any(
                    r.type == "aws_eip"
                    and resource.address in str(r.body.get("instance", ""))
                    for r in self.resources.values()
                    if r.module == resource.module
                ):
                    return "public"
                flag = self.value(resource, "associate_public_ip_address")
                return (
                    "public"
                    if flag is True
                    else "private"
                    if flag is False
                    else "unknown"
                )
            if resource.type == "aws_ecs_service":
                values = objects(self.value(resource, "network_configuration", []))
                flags = [v.get("assign_public_ip", False) for v in values]
                return (
                    "public"
                    if flags and all(v is True for v in flags)
                    else "private"
                    if flags and all(v is False for v in flags)
                    else "unknown"
                )
            if resource.type == "aws_eks_cluster":
                values = objects(self.value(resource, "vpc_config", []))
                flags = [v.get("endpoint_public_access", True) for v in values]
                return (
                    "public"
                    if flags and all(v is True for v in flags)
                    else "private"
                    if flags and all(v is False for v in flags)
                    else "unknown"
                )
            if resource.type == "aws_api_gateway_rest_api":
                configs = objects(self.value(resource, "endpoint_configuration", []))
                types = {v for c in configs for v in c.get("types", [])}
                if (
                    self.value(resource, "disable_execute_api_endpoint", False)
                    is not False
                ):
                    return "unknown"
                return (
                    "private"
                    if types == {"PRIVATE"}
                    else "public"
                    if types and types <= {"EDGE", "REGIONAL"}
                    else "unknown"
                )
            if resource.type == "aws_apigatewayv2_api":
                return (
                    "public"
                    if self.value(resource, "disable_execute_api_endpoint", False)
                    is False
                    else "unknown"
                )
            if resource.type == "aws_cloudfront_distribution":
                return (
                    "public" if self.value(resource, "enabled") is True else "unknown"
                )
            if resource.type == "aws_s3_bucket":
                acl = self.value(resource, "acl", "private")
                if acl in {"public-read", "public-read-write", "authenticated-read"}:
                    return "public"
                return "unknown"  # ACLs alone cannot prove effective policy privacy.
            if resource.type == "aws_lambda_function_url":
                return (
                    "public"
                    if self.value(resource, "authorization_type") in {"NONE", "AWS_IAM"}
                    else "unknown"
                )
        except (Unresolved, TypeError, ValueError, KeyError):
            pass
        return "unknown"

    def subnet_intent(self, subnet: Resource) -> str:
        package = self.graph.package
        intent = subnet_intent(package, subnet)
        if intent != "public":
            return intent
        tables = [
            package.resolve(subnet.module, r.body.get("route_table_id"))
            for r in package.resources
            if r.module == subnet.module
            and r.type == "aws_route_table_association"
            and package.resolve(subnet.module, r.body.get("subnet_id")) == subnet
        ]
        if not tables:
            vpc = package.resolve(subnet.module, subnet.body.get("vpc_id"))
            tables = [
                package.resolve(subnet.module, r.body.get("route_table_id"))
                for r in package.resources
                if r.module == subnet.module
                and r.type == "aws_main_route_table_association"
                and package.resolve(subnet.module, r.body.get("vpc_id")) == vpc
                and vpc is not None
            ]
        if len(tables) != 1 or tables[0] is None:
            return "unresolvable"
        table = tables[0]
        routes = objects(table.body.get("route", [])) + [
            r.body
            for r in package.resources
            if r.module == subnet.module
            and r.type == "aws_route"
            and package.resolve(subnet.module, r.body.get("route_table_id")) == table
        ]
        for route in routes:
            if not any(
                route.get(k) == v
                for k, v in (
                    ("cidr_block", "0.0.0.0/0"),
                    ("destination_cidr_block", "0.0.0.0/0"),
                    ("ipv6_cidr_block", "::/0"),
                    ("destination_ipv6_cidr_block", "::/0"),
                )
            ):
                continue
            igw = package.resolve(subnet.module, route.get("gateway_id"))
            if igw and igw.type == "aws_internet_gateway":
                vpc = package.resolve(subnet.module, subnet.body.get("vpc_id"))
                if (
                    vpc is not None
                    and package.resolve(subnet.module, igw.body.get("vpc_id")) == vpc
                    and package.resolve(subnet.module, table.body.get("vpc_id")) == vpc
                ):
                    return "public"
        return "unresolvable"

    def placement(self, resource: Resource) -> str:
        try:
            values = [self.value(resource, k) for k in PLACEMENT if k in resource.body]

            def references(value: Any) -> list[Ref]:
                if isinstance(value, Ref):
                    return [value]
                if isinstance(value, dict):
                    return [r for v in value.values() for r in references(v)]
                return (
                    [r for v in value for r in references(v)]
                    if isinstance(value, (list, tuple))
                    else []
                )

            subnets = [
                self.resources.get((r.module, r.address))
                for v in values
                for r in references(v)
                if r.address.startswith("aws_subnet.")
            ]
            groups = [
                self.resources.get((r.module, r.address))
                for v in values
                for r in references(v)
                if r.address.startswith("aws_db_subnet_group.")
            ]
            for group in groups:
                if group:
                    subnets.extend(
                        self.resources.get((r.module, r.address))
                        for r in references(self.value(group, "subnet_ids"))
                    )
            if not subnets or any(s is None for s in subnets):
                return "unknown"
            intents = {self.subnet_intent(s) for s in subnets if s}
            return (
                next(iter(intents))
                if len(intents) == 1 and "unresolvable" not in intents
                else "unknown"
            )
        except (Unresolved, TypeError, ValueError, KeyError):
            return "unknown"


def changed_path(
    old: View,
    new: View,
    original: Resource,
    updated: Resource,
    selected: set[str],
) -> bool:
    if old.projection(original, selected) == new.projection(updated, selected):
        return False
    if selected in (EXPOSURE, PLACEMENT):
        previous = (
            old.exposure(original) if selected == EXPOSURE else old.placement(original)
        )
        actual = (
            new.exposure(updated) if selected == EXPOSURE else new.placement(updated)
        )
        # Equal unknowns prove nothing about changed expressions/dependencies.
        if previous != "unknown" and previous == actual:
            return False
    return True


def unresolved_changed(old: View, new: View, types: set[str], name: str) -> bool:
    """Compare possible service roots, never arbitrary policy-bearing resources.

    Known ambiguous types keep every compatible root. An unsupported type has
    no type-wide binding: only an exact named network resource supplies a path.
    An absent binding is not a package-wide veto or a conformance certificate.
    """

    def possible(resource: Resource) -> bool:
        return resource.type in types or (
            not types
            and named(resource, name)
            and (
                resource.type in NETWORK_TYPES
                or bool(
                    resource.body.keys()
                    & (PLACEMENT | INGRESS | (EXPOSURE - {"policy", "enabled"}))
                )
            )
        )

    roots = {key for key, resource in old.resources.items() if possible(resource)}
    # A new unrelated logging/support resource cannot become the binding of an
    # existing ambiguous service. References from existing roots still traverse
    # new attachments. With no baseline roots, keep new possible bindings closed.
    no_baseline_roots = not roots
    roots.update(
        key
        for key, resource in new.resources.items()
        if possible(resource) and (no_baseline_roots or named(resource, name))
    )
    for key in roots:
        original, updated = old.resources.get(key), new.resources.get(key)
        if original is None or updated is None:
            return True
        if any(
            changed_path(old, new, original, updated, selected)
            for selected in (EXPOSURE, PLACEMENT, INGRESS)
        ):
            return True
    return False


def plan_regressions(
    plan: DeploymentPlan,
    before: dict[str, str],
    candidate: dict[str, str],
    targeted: list[Violation] | tuple[Violation, ...] = (),
) -> list[dict[str, Any]]:
    if before == candidate:
        return []
    old, new = View(before), View(candidate)
    results: list[dict[str, Any]] = []
    for service in plan.services:
        expected = (
            "public"
            if service.name in plan.network.public_services
            else "private"
            if service.name in plan.network.private_services
            else None
        )
        if expected is None:
            continue
        types = SERVICE_TYPES.get(label(service.aws_service), set())
        unique = (
            sum(
                bool(types & SERVICE_TYPES.get(label(s.aws_service), set()))
                for s in plan.services
            )
            == 1
        )
        original = old.bind(service.name, types, unique)
        updated = (
            new.resources.get((original.module, original.address))
            if original
            else new.bind(service.name, types, unique)
        )

        def record(
            prop: str,
            unknown: bool = False,
            *,
            resource: Resource | None = original or updated,
            service_name: str = service.name,
            intent: str = expected,
            related_resources: list[str] | None = None,
        ) -> None:
            results.append(
                {
                    "service": service_name,
                    "resource": resource.address if resource else "unresolved",
                    "file_path": resource.path if resource else None,
                    "property": prop,
                    "expected": intent,
                    "assessment": "unknown" if unknown else "regression",
                    "related_resources": related_resources or [],
                    "targeted_findings": [
                        {
                            "rule_id": v.rule_id,
                            "resource": v.resource,
                            "file_path": v.file_path,
                        }
                        for v in targeted
                        if v.resource.split("[", 1)[0]
                        in [
                            resource.address if resource else "unresolved",
                            *(related_resources or []),
                        ]
                    ],
                    "rule_ids": sorted(
                        {
                            v.rule_id
                            for v in targeted
                            if resource is None
                            or v.file_path == resource.path
                            or v.resource.split("[", 1)[0] in (related_resources or [])
                        }
                    ),
                }
            )

        if original is None or updated is None:
            changed = unresolved_changed(old, new, types, service.name)
            if changed:
                record("service_binding", original is None)
            continue
        for prop, selected in [
            ("exposure", EXPOSURE),
            ("subnets", PLACEMENT),
            ("ingress", INGRESS),
        ]:
            a, b = old.projection(original, selected), new.projection(updated, selected)
            if a == b or not changed_path(old, new, original, updated, selected):
                continue
            related = sorted(
                {
                    json.loads(key)[1]
                    for key in a.keys() | b.keys()
                    if key.startswith("[")
                    and len(json.loads(key)) >= 2
                    and str(json.loads(key)[1]).startswith("aws_")
                }
            )
            if prop == "exposure":
                actual = new.exposure(updated)
                if actual != expected:
                    record(prop, actual == "unknown", related_resources=related)
            elif prop == "subnets":
                actual = new.placement(updated)
                if actual != expected:
                    record(prop, actual == "unknown", related_resources=related)
            elif plan.network.ingress:
                # Existing ingress is a conservative lower bound when natural-
                # language rules cannot be uniquely bound. Additions are safe
                # only for public services; private exposure never broadens.
                preserved = all(k in b and v == b[k] for k, v in a.items())
                if not preserved or expected == "private":
                    record(
                        prop,
                        any("${" in canonical(v) for v in b.values()),
                        related_resources=related,
                    )
    return results


def assess_plan_conformance(
    plan: DeploymentPlan,
    original_files: dict[str, str] | None,
    retained_files: dict[str, str],
) -> "PlanConformanceAssessment":
    """D-66: detect final regressions; uncertainty never rejects a repair.

    The Generator original is the comparison baseline, including on retries.
    The historical change detector remains available for offline comparisons;
    it is no longer an acceptance gate.
    """
    from app.domain.conformance import PlanConflict, PlanConformanceAssessment

    result = PlanConformanceAssessment()
    old = View(original_files or {})
    new = View(retained_files)

    def observation(
        service: str,
        resource: Resource | None,
        prop: str,
        expected: Literal["public", "private"],
        confirmed: bool,
        detail: str,
    ) -> None:
        row = PlanConflict(
            service=service,
            resource=resource.address if resource else "unresolved",
            file_path=resource.path if resource else None,
            property=prop,
            expected=expected,
            assessment="regression" if confirmed else "unknown",
            message=re.sub(
                r"[\x00-\x1f\x7f]",
                " ",
                f"{service}: {resource.address if resource else 'unresolved'} "
                f"{prop} — {detail}; plan requires {expected} exposure.",
            )[:500],
        )
        (result.conflicts if confirmed else result.notes).append(row)

    for service in plan.services:
        expected: Literal["public", "private"] | None = (
            "public"
            if service.name in plan.network.public_services
            else "private"
            if service.name in plan.network.private_services
            else None
        )
        if expected is None:
            continue
        types = SERVICE_TYPES.get(label(service.aws_service), set())
        unique = (
            sum(
                bool(types & SERVICE_TYPES.get(label(s.aws_service), set()))
                for s in plan.services
            )
            == 1
        )
        original = old.bind(service.name, types, unique)
        updated = new.bind(service.name, types, unique)
        if original is None or updated is None:
            # No guessed identity, including renamed or ambiguous roots.
            observation(
                service.name,
                updated or original,
                "service_binding",
                expected,
                False,
                "original or retained service binding is unavailable or ambiguous",
            )
            continue
        for prop, selected in (("exposure", EXPOSURE), ("subnets", PLACEMENT)):
            previous = (
                old.exposure(original)
                if prop == "exposure"
                else old.placement(original)
            )
            actual = (
                new.exposure(updated) if prop == "exposure" else new.placement(updated)
            )
            if (
                prop == "exposure"
                and updated.type == "aws_cloudfront_distribution"
                and new.value_or_unknown(updated, "enabled") == "false"
            ):
                actual = "disabled"
            before_projection = old.projection(original, selected)
            after_projection = new.projection(updated, selected)
            # EIP domain/vpc schema migration is not a placement change.
            if selected == PLACEMENT:
                for projection in (before_projection, after_projection):
                    for key, body in projection.items():
                        if key.startswith("[") and isinstance(body, dict):
                            identity = json.loads(key)
                            if len(identity) == 2 and str(identity[1]).startswith(
                                "aws_eip."
                            ):
                                body.pop("domain", None)
            if before_projection == after_projection:
                continue
            if previous == actual and actual != "unknown":
                continue
            if actual == expected:
                continue
            # A subnet's classification alone cannot prove a private service
            # became public (for example an EC2 instance with no public IP).
            if prop == "subnets" and expected == "private":
                continue
            confirmed = (
                previous == expected
                and actual in {"public", "private", "disabled"}
                and actual != expected
            )
            if prop == "exposure":
                changed = [
                    k
                    for k in sorted(EXPOSURE)
                    if old.value_or_unknown(original, k)
                    != new.value_or_unknown(updated, k)
                ]
                prop = ", ".join(changed) or "exposure"
            observation(
                service.name,
                updated,
                prop,
                expected,
                confirmed,
                f"changed from {previous} to {actual}",
            )
        if expected == "public" and plan.network.ingress:
            previous_paths, old_unknown = ingress_paths(old, original)
            current_paths, new_unknown = ingress_paths(new, updated)
            lost = [
                p
                for p in previous_paths
                if not any(path_covers(q, p) for q in current_paths)
            ]
            if lost:
                observation(
                    service.name,
                    updated,
                    "listener/ingress",
                    expected,
                    any(p[0] not in new_unknown for p in lost),
                    "original required listener or ingress path "
                    "was removed or narrowed",
                )
            elif (old_unknown or new_unknown) and old.projection(
                original, INGRESS
            ) != new.projection(updated, INGRESS):
                observation(
                    service.name,
                    updated,
                    "listener/ingress",
                    expected,
                    False,
                    "changed ingress path could not be verified",
                )
    return result


IngressPath = tuple[str, str, int, int, str]


def ingress_paths(view: View, root: Resource) -> tuple[list[IngressPath], set[str]]:
    """Resolved configured ingress only; never infer semantics from plan prose.

    Plan ingress makes original literal paths the bounded preservation baseline.
    Equivalent renamed resources and broader replacement paths remain eligible.
    """
    paths: list[IngressPath] = []
    unknown: set[str] = set()
    projection = view.projection(root, INGRESS)
    attached = [r for key, r in view.resources.items() if canonical(key) in projection]
    for resource in attached:
        keys = (
            ["listener"]
            if resource.type == "aws_elb"
            else ["ingress"]
            if resource.type in {"aws_security_group", "aws_default_security_group"}
            else [None]
            if resource.type
            in {
                "aws_lb_listener",
                "aws_alb_listener",
                "aws_security_group_rule",
                "aws_vpc_security_group_ingress_rule",
            }
            else []
        )
        for key in keys:
            listener = resource.type in {
                "aws_lb_listener",
                "aws_alb_listener",
                "aws_elb",
            }
            kind = "listener" if listener else "ingress"
            try:
                bodies = (
                    objects(view.value(resource, key, []))
                    if key
                    else [
                        {
                            k: view.value(resource, k)
                            for k in {
                                "type",
                                "protocol",
                                "ip_protocol",
                                "port",
                                "from_port",
                                "to_port",
                                "cidr_blocks",
                                "ipv6_cidr_blocks",
                                "cidr_ipv4",
                                "cidr_ipv6",
                                "source_security_group_id",
                                "referenced_security_group_id",
                            }
                            if k in resource.body
                        }
                    ]
                )
                for body in bodies:
                    if (
                        resource.type == "aws_security_group_rule"
                        and body.get("type") != "ingress"
                    ):
                        continue
                    listener = resource.type in {
                        "aws_lb_listener",
                        "aws_alb_listener",
                        "aws_elb",
                    }
                    protocol = str(
                        body.get(
                            "protocol",
                            body.get("ip_protocol", body.get("lb_protocol", "tcp")),
                        )
                    ).lower()
                    if listener and protocol in {"http", "https", "tls"}:
                        protocol = "tcp"
                    protocol = {"6": "tcp", "17": "udp"}.get(protocol, protocol)
                    start = body.get("port", body.get("lb_port", body.get("from_port")))
                    end = body.get("to_port", start)
                    if protocol == "-1":
                        start, end = 0, 65535
                    if not isinstance(start, int) or not isinstance(end, int):
                        unknown.add(kind)
                        continue
                    sources = (
                        ["listener"]
                        if listener
                        else [
                            *body.get("cidr_blocks", []),
                            *body.get("ipv6_cidr_blocks", []),
                            *[
                                body[k]
                                for k in (
                                    "cidr_ipv4",
                                    "cidr_ipv6",
                                    "source_security_group_id",
                                    "referenced_security_group_id",
                                )
                                if body.get(k)
                            ],
                        ]
                    )
                    if not sources:
                        unknown.add(kind)
                    for source in sources:
                        if not isinstance(source, str) or "${" in source:
                            unknown.add(kind)
                        else:
                            paths.append(
                                (
                                    "listener" if listener else "ingress",
                                    protocol,
                                    start,
                                    end,
                                    source,
                                )
                            )
            except (Unresolved, TypeError, ValueError, KeyError):
                unknown.add(kind)
    return paths, unknown


def path_covers(candidate: IngressPath, original: IngressPath) -> bool:
    from ipaddress import ip_network

    kind, protocol, start, end, source = original
    if (
        candidate[0] != kind
        or candidate[1] not in {protocol, "-1"}
        or candidate[2] > start
        or candidate[3] < end
    ):
        return False
    if candidate[4] == source:
        return True
    try:
        old_network, new_network = ip_network(source), ip_network(candidate[4])
        return (
            old_network.version == new_network.version
            and int(new_network.network_address) <= int(old_network.network_address)
            and int(old_network.broadcast_address) <= int(new_network.broadcast_address)
        )
    except ValueError:
        return False
