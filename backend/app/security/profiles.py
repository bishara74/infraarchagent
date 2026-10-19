"""Secondary resource-specific assessments. Never used by strict acceptance."""

import json
from collections.abc import Iterator, Mapping
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, cast

from app.domain.review import security_final
from app.security.encryption import aes256_buckets
from app.security.terraform import (
    Resource,
    TerraformPackage,
    objects,
    reference,
    subnet_intent,
)
from app.validation.documents import blocks

PROFILE_IDS = ("strict", "contextual-v1")
LB_TYPES = {"aws_lb", "aws_alb"}
LISTENERS = {"aws_lb_listener", "aws_alb_listener"}
RULES = {
    "aws_security_group_rule",
    "aws_vpc_security_group_ingress_rule",
    "aws_vpc_security_group_egress_rule",
}
ATTACHMENTS = {
    "security_groups",
    "vpc_security_group_ids",
    "security_group_id",
    "source_security_group_id",
    "referenced_security_group_id",
}


@lru_cache
def profile(identifier: str) -> dict[str, Any]:
    if identifier not in PROFILE_IDS:
        raise ValueError("unknown policy profile")
    return cast(
        dict[str, Any],
        json.loads(
            (Path(__file__).with_name("profiles") / f"{identifier}.json").read_text()
        ),
    )


def static(resource: Resource) -> bool:
    def dynamic(value: Any) -> bool:
        if isinstance(value, dict):
            return any(
                k in {"count", "for_each", "dynamic", "provider"} or dynamic(v)
                for k, v in value.items()
            )
        return isinstance(value, list) and any(dynamic(v) for v in value)

    return not dynamic(resource.body)


def values(value: Any) -> Iterator[Any]:
    if isinstance(value, dict):
        for v in value.values():
            yield from values(v)
    elif isinstance(value, list):
        for v in value:
            yield from values(v)
    else:
        yield value


class Evidence:
    def __init__(self, files: Mapping[str, str]):
        self.package = TerraformPackage(dict(files))
        self.aes256 = aes256_buckets(files)

    def linked(self, resource: Resource, field: str) -> Resource | None:
        linked = self.package.resolve(resource.module, resource.body.get(field))
        return linked if linked and static(linked) else None

    def log_target(self, bucket: Resource) -> bool:
        if bucket.type != "aws_s3_bucket":
            return False
        for source in self.package.resources:
            if source.module != bucket.module or not static(source):
                continue
            if source.type == "aws_s3_bucket_logging":
                owner = self.linked(source, "bucket")
                target = self.linked(source, "target_bucket")
                if (
                    owner
                    and owner.type == "aws_s3_bucket"
                    and owner.address != bucket.address
                    and target == bucket
                ):
                    return True
            if source.type == "aws_s3_bucket" and source.address != bucket.address:
                for logging in objects(source.body.get("logging", [])):
                    target = self.package.resolve(
                        source.module, logging.get("target_bucket")
                    )
                    if target == bucket:
                        return True
        return False

    def public(self, lb: Resource) -> bool:
        return (
            lb.type in LB_TYPES
            and static(lb)
            and lb.body.get("internal") is False
            and lb.body.get("load_balancer_type", "application") == "application"
        )

    def redirect(self, lb: Resource) -> bool:
        if not self.public(lb):
            return False
        listeners = []
        for r in self.package.resources:
            if r.module != lb.module or r.type not in LISTENERS:
                continue
            if self.linked(r, "load_balancer_arn") is None:
                return False
            if self.linked(r, "load_balancer_arn") == lb:
                if not static(r):
                    return False
                if r.body.get("protocol") not in {"HTTP", "HTTPS"}:
                    return False
                listeners.append(r)
        https = any(
            r.body.get("port") == 443
            and r.body.get("protocol") == "HTTPS"
            and r.body.get("certificate_arn")
            for r in listeners
        )
        http = [r for r in listeners if r.body.get("protocol") == "HTTP"]
        if not https or not http:
            return False
        for r in http:
            actions = objects(r.body.get("default_action", []))
            if (
                r.body.get("port") != 80
                or len(actions) != 1
                or actions[0].get("type") != "redirect"
            ):
                return False
            redirects = objects(actions[0].get("redirect", []))
            if (
                len(redirects) != 1
                or redirects[0].get("protocol") != "HTTPS"
                or str(redirects[0].get("port")) != "443"
                or redirects[0].get("status_code") not in {"HTTP_301", "HTTP_302"}
            ):
                return False
            for rule in self.package.resources:
                if rule.module == lb.module and rule.type in {
                    "aws_lb_listener_rule",
                    "aws_alb_listener_rule",
                }:
                    listener = self.linked(rule, "listener_arn")
                    if listener is None or listener == r:
                        return False
        return True

    def owner(self, resource: Resource) -> Resource | None:
        if resource.type == "aws_security_group":
            return resource
        owner = (
            self.linked(resource, "security_group_id")
            if resource.type in RULES
            else None
        )
        return owner if owner and owner.type == "aws_security_group" else None

    def consumers(self, group: Resource) -> list[Resource]:
        # Local/external modules may hide consumers; never infer exclusivity.
        if any(
            blocks(d.data, "module") for d in self.package.documents.documents.values()
        ):
            return []
        found = []
        for r in self.package.resources:
            if r.module != group.module:
                continue
            if r.type in RULES and not static(r):
                return []
            for key, body in self._attachments(r.body):
                if r.type in RULES and key == "security_group_id":
                    continue
                refs = [reference(v) for v in values(body)]
                if any(v is None for v in refs):
                    return []
            if any(reference(v) == group.address for v in values(r.body)):
                if r.type in RULES and self.owner(r) == group:
                    continue
                if r == group:
                    return []
                if not self.public(r) or group.address not in {
                    reference(v) for v in values(r.body.get("security_groups", []))
                }:
                    return []
                found.append(r)
        return found

    @staticmethod
    def _attachments(value: Any) -> Iterator[tuple[str, Any]]:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ATTACHMENTS:
                    yield key, child
                else:
                    yield from Evidence._attachments(child)
        elif isinstance(value, list):
            for child in value:
                yield from Evidence._attachments(child)

    def public_subnet(self, subnet: Resource) -> bool:
        if (
            subnet.type != "aws_subnet"
            or subnet_intent(self.package, subnet) != "public"
        ):
            return False
        vpc = self.linked(subnet, "vpc_id")
        if vpc is None:
            return False
        associations = [
            r
            for r in self.package.resources
            if r.module == subnet.module
            and r.type == "aws_route_table_association"
            and self.linked(r, "subnet_id") == subnet
        ]
        if len(associations) > 1:
            return False
        tables = (
            [self.linked(associations[0], "route_table_id")]
            if associations
            else [
                self.linked(r, "route_table_id")
                if r.type == "aws_main_route_table_association"
                else r
                for r in self.package.resources
                if r.module == subnet.module
                and static(r)
                and (
                    r.type == "aws_main_route_table_association"
                    and self.linked(r, "vpc_id") == vpc
                    or r.type == "aws_default_route_table"
                    and r.body.get("default_route_table_id")
                    == "${" + vpc.address + ".default_route_table_id}"
                )
            ]
        )
        if len(tables) != 1 or tables[0] is None:
            return False
        table = tables[0]
        default_of_vpc = (
            table.type == "aws_default_route_table"
            and table.body.get("default_route_table_id")
            == "${" + vpc.address + ".default_route_table_id}"
        )
        if not default_of_vpc and self.linked(table, "vpc_id") != vpc:
            return False
        routes = objects(table.body.get("route", [])) + [
            r.body
            for r in self.package.resources
            if r.module == subnet.module
            and r.type == "aws_route"
            and static(r)
            and self.linked(r, "route_table_id") == table
        ]
        for route in routes:
            gateway = self.package.resolve(subnet.module, route.get("gateway_id"))
            if (
                gateway
                and static(gateway)
                and gateway.type == "aws_internet_gateway"
                and self.linked(gateway, "vpc_id") == vpc
                and (
                    route.get("cidr_block") == "0.0.0.0/0"
                    or route.get("destination_cidr_block") == "0.0.0.0/0"
                    or route.get("ipv6_cidr_block") == "::/0"
                    or route.get("destination_ipv6_cidr_block") == "::/0"
                )
            ):
                return True
        return False

    def condition(self, name: str, r: Resource) -> bool:
        if name == "log_target_encryption":
            bucket = (
                self.linked(r, "bucket")
                if r.type == "aws_s3_bucket_server_side_encryption_configuration"
                else r
            )
            return bool(
                bucket
                and self.log_target(bucket)
                and (bucket.module, bucket.address) in self.aes256
            )
        if name == "log_target":
            return self.log_target(r)
        if name == "public_subnet":
            return self.public_subnet(r)
        if name == "public_lb_redirect":
            return self.redirect(r)
        group = self.owner(r)
        if group is None:
            return False
        consumers = self.consumers(group)
        if not consumers:
            return False
        if name == "public_lb_egress":
            return r.type != "aws_security_group_rule" or r.body.get("type") == "egress"
        if name == "public_lb_http":
            if r.type in RULES:
                own = r.body
                if (own.get("from_port"), own.get("to_port")) != (80, 80) or own.get(
                    "protocol", own.get("ip_protocol")
                ) not in {"tcp", "6"}:
                    return False
                if r.type == "aws_security_group_rule" and own.get("type") != "ingress":
                    return False
                if (
                    "0.0.0.0/0" not in own.get("cidr_blocks", [])
                    and own.get("cidr_ipv4") != "0.0.0.0/0"
                ):
                    return False
            ingress = objects(group.body.get("ingress", [])) + [
                x.body
                for x in self.package.resources
                if x.module == group.module
                and x.type in RULES
                and self.owner(x) == group
                and (
                    x.type == "aws_vpc_security_group_ingress_rule"
                    or x.body.get("type") == "ingress"
                )
            ]
            exact = False
            for rule in ingress:
                public = (
                    "0.0.0.0/0" in rule.get("cidr_blocks", [])
                    or rule.get("cidr_ipv4") == "0.0.0.0/0"
                )
                if not public:
                    continue
                lo, hi = rule.get("from_port"), rule.get("to_port")
                if (
                    not isinstance(lo, int)
                    or not isinstance(hi, int)
                    or rule.get("protocol", rule.get("ip_protocol")) not in {"tcp", "6"}
                ):
                    return False
                if lo <= 80 <= hi:
                    if (lo, hi) != (80, 80):
                        return False
                    exact = True
            return exact and all(self.redirect(lb) for lb in consumers)
        return False


def assess(
    package: Mapping[str, Any], files: Mapping[str, str] | None = None
) -> dict[str, Any]:
    final = security_final(package.get("security_report"))
    raw_findings = final.get("remaining_blocking")
    known_findings = isinstance(raw_findings, list)
    findings = raw_findings if isinstance(raw_findings, list) else []
    valid = (package.get("validation_report") or {}).get("summary", {}).get(
        "result"
    ) == "valid"
    clean = final.get("outcome") == "clean" and known_findings
    observed = clean or (
        final.get("outcome") == "exhausted" and known_findings and bool(findings)
    )
    if not final and package.get("status") == "checks_passed":
        observed = clean = valid = True
    strict: dict[str, Any] = {
        "checks_passed": clean and valid and not findings,
        "remaining_blocking": len(findings),
        "excepted": [],
    }
    evidence = Evidence(files or package.get("files") or {})
    exceptions = []
    for finding in findings:
        resource = evidence.package.get(
            str(PurePosixPath(finding.get("file_path", "")).parent),
            finding.get("resource", ""),
        )
        if resource is None or not static(resource):
            continue
        for entry in profile("contextual-v1")["entries"]:
            if (
                finding.get("rule_id") in entry["checkov_ids"] + entry["trivy_ids"]
                and resource.type in entry["resource_types"]
                and evidence.condition(entry["condition"], resource)
            ):
                exceptions.append(
                    {
                        "rule_id": finding["rule_id"],
                        "file_path": finding.get("file_path"),
                        "resource": resource.address,
                        "classification": "excepted",
                        "entry_id": entry["id"],
                        "justification": entry["justification"],
                    }
                )
                break
    return {
        "strict": strict,
        "contextual-v1": {
            "checks_passed": observed and valid and len(findings) == len(exceptions),
            "remaining_blocking": len(findings) - len(exceptions),
            "excepted": exceptions,
            "approval": "experimental; supervisor approval required",
        },
    }
