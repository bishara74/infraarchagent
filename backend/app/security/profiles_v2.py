"""D-56 isolated contextual-v2. Never consulted by acceptance or readiness."""

import re
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

from app.domain.review import security_final
from app.security.addressing import refs
from app.security.instances import Instance, Instances, Ref, Unresolved
from app.security.profiles import Evidence, profile, static
from app.security.terraform import objects

LB = {"aws_lb", "aws_alb"}
LISTENER = {"aws_lb_listener", "aws_alb_listener"}
RULE = {
    "aws_security_group_rule",
    "aws_vpc_security_group_ingress_rule",
    "aws_vpc_security_group_egress_rule",
}
ATTACHED = {"security_groups", "vpc_security_group_ids", "security_group_ids"}


def port(value: Any) -> int | None:
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,5}", value):
        value = int(value)
    return value if type(value) is int and 1 <= value <= 65535 else None


def protocol(value: Any) -> str | None:
    return (
        value.strip().upper() if isinstance(value, str) and "${" not in value else None
    )


class EvidenceV2:
    def __init__(self, files: Mapping[str, str], *, legacy: Evidence | None = None):
        self.legacy = legacy if legacy is not None else Evidence(files)
        self.graph = Instances(dict(files), package=self.legacy.package)

    def public(self, lb: Instance) -> bool:
        return (
            lb.type in LB
            and self.graph.get(lb, "internal") is False
            and self.graph.get(lb, "load_balancer_type", "application")
            in {"application", "network"}
        )

    def listeners(self, lb: Instance) -> list[Instance]:
        if self.graph.unknown(lb.module, LISTENER):
            raise Unresolved()
        found = []
        for listener in self.graph.all(lb.module, LISTENER):
            owner = self.graph.linked(listener, "load_balancer_arn")
            if owner is None:
                raise Unresolved()
            if owner == lb:
                found.append(listener)
        return found

    def secure_lb(self, lb: Instance, require_http: bool = False) -> bool:
        if not self.public(lb):
            return False
        listeners = self.listeners(lb)
        if not listeners:
            return False
        kind = self.graph.get(lb, "load_balancer_type", "application")
        http = []
        https = []
        for listener in listeners:
            p = protocol(self.graph.get(listener, "protocol"))
            number = port(self.graph.get(listener, "port"))
            if number is None:
                return False
            if p == "HTTP" and kind == "application":
                http.append(listener)
                continue
            if p != ("TLS" if kind == "network" else "HTTPS"):
                return False
            certificate = listener.resource.body.get("certificate_arn")
            if not isinstance(certificate, str) or not certificate:
                return False
            if (
                kind == "network"
                and self.graph.get(listener, "ssl_policy")
                not in profile("contextual-v2")["nlb_tls12_policies"]
            ):
                return False
            https.append(listener)
        if not https or (require_http and not http):
            return False
        for listener in http:
            if port(self.graph.get(listener, "port")) != 80:
                return False
            actions = objects(self.graph.get(listener, "default_action", []))
            redirects = (
                objects(actions[0].get("redirect", []))
                if len(actions) == 1 and actions[0].get("type") == "redirect"
                else []
            )
            if (
                len(redirects) != 1
                or protocol(redirects[0].get("protocol")) != "HTTPS"
                or port(redirects[0].get("port")) != 443
                or redirects[0].get("status_code") not in {"HTTP_301", "HTTP_302"}
            ):
                return False
            if not any(port(self.graph.get(x, "port")) == 443 for x in https):
                return False
            rule_types = {"aws_lb_listener_rule", "aws_alb_listener_rule"}
            if self.graph.unknown(lb.module, rule_types):
                return False
            for rule in self.graph.all(lb.module, rule_types):
                linked = self.graph.linked(rule, "listener_arn")
                if linked is None or linked == listener:
                    return False
        return True

    def public_subnet(self, subnet: Instance) -> bool:
        graph = self.graph
        vpc = graph.linked(subnet, "vpc_id")
        if subnet.type != "aws_subnet" or vpc is None or vpc.type != "aws_vpc":
            return False
        associations = []
        for raw in graph.unknown(subnet.module, {"aws_route_table_association"}):
            # A separately unresolved private-subnet association cannot poison
            # an explicit public-subnet association whose identity is known.
            text = str(raw.body.get("subnet_id", ""))
            if not self.unrelated_subnet(text, subnet):
                return False
        for item in graph.all(subnet.module, {"aws_route_table_association"}):
            try:
                target = graph.get(item, "subnet_id")
            except Unresolved:
                text = str(item.resource.body.get("subnet_id", ""))
                if not self.unrelated_subnet(text, subnet):
                    return False
                continue
            if isinstance(target, Ref) and target.address == subnet.address:
                associations.append(item)
        if len(associations) > 1:
            return False
        tables = (
            [graph.linked(associations[0], "route_table_id")] if associations else []
        )
        if not associations:
            if graph.unknown(
                subnet.module,
                {"aws_main_route_table_association", "aws_default_route_table"},
            ):
                return False
            for item in graph.all(
                subnet.module,
                {"aws_main_route_table_association", "aws_default_route_table"},
            ):
                if (
                    item.type == "aws_main_route_table_association"
                    and graph.linked(item, "vpc_id") == vpc
                ):
                    tables.append(graph.linked(item, "route_table_id"))
                elif item.type == "aws_default_route_table" and graph.get(
                    item, "default_route_table_id"
                ) == Ref(vpc.module, vpc.address, "default_route_table_id"):
                    tables.append(item)
        if len(tables) != 1 or tables[0] is None:
            return False
        table = tables[0]
        if (
            table.type != "aws_default_route_table"
            and graph.linked(table, "vpc_id") != vpc
        ):
            return False
        routes = objects(graph.get(table, "route", []))
        for raw in graph.unknown(subnet.module, {"aws_route"}):
            match = re.fullmatch(
                r"\$\{(aws_(?:default_)?route_table\.[\w-]+)"
                r"(?:\[[^\[\]]+\])?\.id\}",
                str(raw.body.get("route_table_id", "")),
            )
            if not match or match[1] == table.resource.address:
                return False
        for item in graph.all(subnet.module, {"aws_route"}):
            linked = graph.linked(item, "route_table_id")
            if linked is None:
                return False
            if linked == table:
                routes.append(
                    {
                        k: graph.get(item, k)
                        for k in (
                            "gateway_id",
                            "cidr_block",
                            "destination_cidr_block",
                            "ipv6_cidr_block",
                            "destination_ipv6_cidr_block",
                        )
                    }
                )
        defaults: set[str] = set()
        public = False
        for route in routes:
            destination = route.get("cidr_block") or route.get("destination_cidr_block")
            ipv6 = route.get("ipv6_cidr_block") or route.get(
                "destination_ipv6_cidr_block"
            )
            if destination != "0.0.0.0/0" and ipv6 != "::/0":
                continue
            identity = "0.0.0.0/0" if destination == "0.0.0.0/0" else "::/0"
            if identity in defaults:
                return False
            defaults.add(identity)
            gateway = route.get("gateway_id")
            if not isinstance(gateway, Ref):
                continue
            igw = graph.find(gateway.module, gateway.address)
            if (
                igw
                and igw.type == "aws_internet_gateway"
                and graph.linked(igw, "vpc_id") == vpc
            ):
                public = True
        return public

    @staticmethod
    def unrelated_subnet(expression: str, subnet: Instance) -> bool:
        match = re.fullmatch(
            r"\$\{(aws_subnet\.[\w-]+)(?:\[[^\[\]]+\])?\.id\}", expression
        )
        return bool(match and match[1] != subnet.resource.address)

    def consumers(self, group: Instance) -> list[Instance]:
        graph = self.graph

        def fields(body: Any) -> list[Any]:
            if isinstance(body, dict):
                return [v for k, v in body.items() if k in ATTACHED] + [
                    v
                    for k, child in body.items()
                    if k not in ATTACHED
                    for v in fields(child)
                ]
            return (
                [v for child in body for v in fields(child)]
                if isinstance(body, list)
                else []
            )

        for resource in graph.package.resources:
            if (
                resource.module == group.module
                and resource.type
                not in RULE | {"aws_security_group", "aws_default_security_group"}
                and fields(resource.body)
                and graph.expanded.get((resource.module, resource.address)) is None
            ):
                raise Unresolved()
        found = []
        for item in graph.all(group.module):
            if item.type in RULE | {"aws_security_group", "aws_default_security_group"}:
                continue  # Source/peer rule references are not ENI attachments.
            for raw in fields(item.resource.body):
                value = graph.value(raw, item.module, item.env)
                resolved = refs(value)
                if not isinstance(value, list) or len(resolved) != len(value):
                    raise Unresolved()
                if any(
                    r.address == group.address and r.module == group.module
                    for r in resolved
                ):
                    if not self.public(item) or (
                        graph.get(item, "load_balancer_type", "application")
                        == "network"
                        and not self.secure_lb(item)
                    ):
                        return []
                    found.append(item)
        return found

    def condition(self, name: str, item: Instance) -> bool:
        graph = self.graph
        if name in {"log_target", "log_target_encryption"}:
            return static(item.resource) and self.legacy.condition(name, item.resource)
        if name == "public_subnet":
            return self.public_subnet(item)
        if name == "public_lb_redirect":
            return self.secure_lb(item)
        group = (
            item
            if item.type == "aws_security_group"
            else graph.linked(item, "security_group_id")
        )
        if group is None or group.type != "aws_security_group":
            return False
        consumers = self.consumers(group)
        if not consumers:
            return False
        if name == "public_lb_egress":
            return (
                item.type != "aws_security_group_rule"
                or graph.get(item, "type") == "egress"
            )
        if name == "public_lb_http":
            rules = objects(graph.get(group, "ingress", []))
            if graph.unknown(group.module, RULE):
                return False
            for other in graph.all(group.module, RULE):
                if graph.linked(other, "security_group_id") == group and (
                    other.type == "aws_vpc_security_group_ingress_rule"
                    or graph.get(other, "type") == "ingress"
                ):
                    rules.append(
                        {
                            k: graph.get(other, k)
                            for k in (
                                "from_port",
                                "to_port",
                                "protocol",
                                "ip_protocol",
                                "cidr_blocks",
                                "cidr_ipv4",
                                "type",
                            )
                        }
                    )
            if item != group:
                own = {
                    k: graph.get(item, k)
                    for k in (
                        "from_port",
                        "to_port",
                        "protocol",
                        "ip_protocol",
                        "cidr_blocks",
                        "cidr_ipv4",
                        "type",
                    )
                }
                if item.type == "aws_security_group_rule" and own["type"] != "ingress":
                    return False
                if (port(own["from_port"]), port(own["to_port"])) != (80, 80):
                    return False
                rules.append(own)
            exact = False
            for rule in rules:
                if rule.get("cidr_ipv4") != "0.0.0.0/0" and "0.0.0.0/0" not in rule.get(
                    "cidr_blocks", []
                ):
                    continue
                lo, hi = port(rule.get("from_port")), port(rule.get("to_port"))
                if (
                    lo is None
                    or hi is None
                    or protocol(rule.get("protocol") or rule.get("ip_protocol"))
                    not in {"TCP", "6"}
                ):
                    return False
                if lo <= 80 <= hi:
                    if (lo, hi) != (80, 80):
                        return False
                    exact = True
            return exact and all(
                self.secure_lb(lb, require_http=True) for lb in consumers
            )
        return False


def assess_v2(
    package: Mapping[str, Any],
    files: Mapping[str, str],
    legacy: dict[str, Any],
    *,
    evidence: Evidence | None = None,
) -> dict[str, Any]:
    view = EvidenceV2(files, legacy=evidence)
    final = security_final(package.get("security_report"))
    findings = final.get("remaining_blocking", [])
    findings = findings if isinstance(findings, list) else []
    exceptions = []
    for finding in findings:
        module = str(PurePosixPath(finding.get("file_path", "")).parent)
        address = finding.get("resource", "")
        items = [
            item
            for item in view.graph.all(module)
            if item.address == address
            or ("[" not in address and item.resource.address == address)
        ]
        if not items:
            continue
        for entry in profile("contextual-v2")["entries"]:
            if finding.get("rule_id") not in entry["checkov_ids"] + entry["trivy_ids"]:
                continue
            try:
                matched = all(
                    item.type in entry["resource_types"]
                    and view.condition(entry["condition"], item)
                    for item in items
                )
            except (Unresolved, ValueError, TypeError, KeyError, AttributeError):
                matched = False
            if matched:
                exceptions.append(
                    {
                        "rule_id": finding["rule_id"],
                        "file_path": finding.get("file_path"),
                        "resource": address,
                        "classification": "excepted",
                        "entry_id": entry["id"],
                        "justification": entry["justification"],
                    }
                )
                break
    known = isinstance(final.get("remaining_blocking"), list)
    observed = known and (
        final.get("outcome") == "clean"
        or final.get("outcome") == "exhausted"
        and bool(findings)
    )
    valid = (package.get("validation_report") or {}).get("summary", {}).get(
        "result"
    ) == "valid"
    passed = observed and valid and len(findings) == len(exceptions)
    if not final and package.get("status") == "checks_passed":
        passed = True  # Same legacy clean-scan compatibility as strict/v1.
    return {
        "checks_passed": passed,
        "remaining_blocking": legacy["strict"]["remaining_blocking"] - len(exceptions),
        "excepted": exceptions,
        "approval": "experimental; supervisor approval required",
    }
