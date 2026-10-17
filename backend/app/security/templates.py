"""D-46 supporting resources. Every candidate still needs all acceptance guards."""

import json
from pathlib import PurePosixPath
from typing import Any

from app.domain.models import Violation
from app.security.terraform import (
    Resource,
    TerraformPackage,
    edit_resource,
    fields_supported,
    objects,
)
from app.validation.provider_schema import DEFAULT_INDEX
from app.validation.schema_context import index_for

TEMPLATE_RULES = {
    "kms": {
        "CKV_AWS_145",
        "AWS-0132",
        "CKV_AWS_158",
        "AWS-0017",
        "CKV_AWS_354",
        "AWS-0027",
    },
    "access_logs": {"CKV_AWS_18", "AWS-0089", "CKV_AWS_91"},
    "flow_logs": {"CKV2_AWS_11", "AWS-0178"},
    "monitoring": {"CKV_AWS_118"},
}
TEMPLATE_TYPES = {
    "kms": {
        "aws_s3_bucket",
        "aws_s3_bucket_server_side_encryption_configuration",
        "aws_cloudwatch_log_group",
        "aws_db_instance",
        "aws_ebs_volume",
    },
    "access_logs": {"aws_s3_bucket", "aws_lb"},
    "flow_logs": {"aws_vpc"},
    "monitoring": {"aws_db_instance"},
}


class TemplateUnavailable(ValueError):
    """Fixed, safe context reason; never contains configuration values."""


def requests(files: dict[str, str], findings: list[Violation]) -> list[tuple[str, str]]:
    package = TerraformPackage(files)
    result = set()
    for f in findings:
        if not f.blocking:
            continue
        module = str(PurePosixPath(f.file_path).parent)
        resource = package.get(module, f.resource)
        if resource is not None:
            for kind, rules in TEMPLATE_RULES.items():
                if f.rule_id in rules and resource.type in TEMPLATE_TYPES[kind]:
                    result.add((module, kind))
    return sorted(result)


class Builder:
    def __init__(self, files: dict[str, str], module: str):
        self.files, self.module = dict(files), module
        self.package = TerraformPackage(files)
        version = self.package.version(module)
        if not version or not self.package.module_safe(module):
            raise TemplateUnavailable("context: module/schema unresolved")
        self.index = index_for("aws", version, DEFAULT_INDEX)
        if not self.index.available:
            raise TemplateUnavailable("context: provider schema unavailable")
        self.new: dict[str, Any] = {}
        self.data: dict[str, Any] = {}

    def existing(self, typ: str) -> list[Resource]:
        return sorted(
            (
                r
                for r in self.package.resources
                if r.module == self.module and r.type == typ
            ),
            key=lambda r: r.address,
        )

    def add(self, typ: str, name: str, body: dict[str, Any]) -> str:
        schema = self.index.resource_schema(typ)
        if (
            not schema
            or not fields_supported(body, schema)
            or self.index.required_missing(typ, body)
        ):
            raise TemplateUnavailable("context: template schema unsupported")
        if self.package.get(self.module, typ + "." + name):
            raise TemplateUnavailable("context: supporting resource name conflict")
        previous = self.new.setdefault(typ, {}).get(name)
        if previous is not None and previous != body:
            raise TemplateUnavailable("context: conflicting template resources")
        self.new[typ][name] = body
        return typ + "." + name

    def identity(self) -> None:
        for typ in ("aws_caller_identity", "aws_region", "aws_partition"):
            schema = self.index.resource_schema(typ, data_source=True)
            if schema is None:
                raise TemplateUnavailable("context: identity schema unavailable")
            # Reuse only the exact generated declaration; never replace user data.
            for doc in self.package.documents.documents.values():
                if str(PurePosixPath(doc.path).parent) != self.module:
                    continue
                raw = doc.data.get("data", {}) if isinstance(doc.data, dict) else {}
                for entry in raw if isinstance(raw, list) else [raw]:
                    if typ in entry and "infraarch_security" in entry[typ]:
                        if entry[typ]["infraarch_security"]:
                            raise TemplateUnavailable(
                                "context: identity declaration conflict"
                            )
                        break
                else:
                    continue
                break
            else:
                self.data[typ] = {"infraarch_security": {}}

    def edit(
        self,
        target: Resource,
        updates: dict[str, Any],
        dependencies: tuple[str, ...] = (),
    ) -> None:
        if any(k in target.body for k in ("count", "for_each", "dynamic", "provider")):
            raise TemplateUnavailable("context: resource/provider instance unresolved")
        if dependencies:
            old = target.body.get("depends_on", [])
            if not isinstance(old, list) or not all(isinstance(v, str) for v in old):
                raise TemplateUnavailable("context: dependencies unresolved")
            updates = {
                **updates,
                "depends_on": sorted(
                    set(dependencies)
                    | {
                        v[2:-1] if v.startswith("${") and v.endswith("}") else v
                        for v in old
                    }
                ),
            }
        schema = self.package.schema(target)
        if not schema or not fields_supported(updates, schema):
            raise TemplateUnavailable("context: target schema unsupported")
        # Refresh the body if another template link already edited this resource.
        current = TerraformPackage(self.files).get(self.module, target.address)
        if current is None:
            raise TemplateUnavailable("context: target unresolved")
        if all(current.body.get(k) == v for k, v in updates.items()):
            return
        self.files = edit_resource(self.files, current, updates, schema)

    def key(self) -> str:
        keys = self.existing("aws_kms_key")
        for existing_key in keys:
            if (
                existing_key.body.get("enable_key_rotation") is True
                and existing_key.body.get("is_enabled", True) is True
                and existing_key.body.get("key_usage", "ENCRYPT_DECRYPT")
                == "ENCRYPT_DECRYPT"
                and existing_key.body.get(
                    "customer_master_key_spec", "SYMMETRIC_DEFAULT"
                )
                == "SYMMETRIC_DEFAULT"
                and not any(
                    k in existing_key.body for k in ("count", "for_each", "provider")
                )
            ):
                return existing_key.address
        if keys:
            raise TemplateUnavailable("context: existing KMS key incompatible")
        if "infraarch_security" in self.new.get("aws_kms_key", {}):
            return "aws_kms_key.infraarch_security"
        self.identity()
        account = "${data.aws_caller_identity.infraarch_security.account_id}"
        partition = "${data.aws_partition.infraarch_security.partition}"
        region = "${data.aws_region.infraarch_security.name}"
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AccountAdministration",
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:{partition}:iam::{account}:root"},
                    "Action": "kms:*",
                    "Resource": "*",
                },
                {
                    "Sid": "ScopedLogEncryption",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "logs."
                        + region
                        + ".${data.aws_partition.infraarch_security.dns_suffix}"
                    },
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey",
                    ],
                    "Resource": "*",
                    "Condition": {
                        "ArnLike": {
                            "kms:EncryptionContext:aws:logs:arn": (
                                f"arn:{partition}:logs:{region}:{account}:"
                                "log-group:/infraarch/vpc-flow-*"
                            )
                        }
                    },
                },
            ],
        }
        key = self.add(
            "aws_kms_key",
            "infraarch_security",
            {
                "description": "Infrastructure security encryption",
                "enable_key_rotation": True,
                "deletion_window_in_days": 30,
                "policy": json.dumps(policy),
            },
        )
        self.add(
            "aws_kms_alias",
            "infraarch_security",
            {
                "name_prefix": "alias/infraarch-security-",
                "target_key_id": "${" + key + ".key_id}",
            },
        )
        return key

    def kms(self, targets: list[Resource]) -> None:
        key = self.key()
        for target in targets:
            if target.type == "aws_s3_bucket":
                configs = [
                    r
                    for r in self.existing(
                        "aws_s3_bucket_server_side_encryption_configuration"
                    )
                    if r.body.get("bucket")
                    in {
                        "${" + target.address + ".id}",
                        "${" + target.address + ".bucket}",
                    }
                ]
                if target.body.get("server_side_encryption_configuration"):
                    raise TemplateUnavailable(
                        "context: inline bucket encryption requires migration"
                    )
                body = self.encryption_rules(
                    configs[0].body if len(configs) == 1 else {}, key
                )
                if len(configs) == 1:
                    self.edit(configs[0], body)
                elif not configs:
                    self.add(
                        "aws_s3_bucket_server_side_encryption_configuration",
                        "infraarch_" + target.name,
                        {"bucket": "${" + target.address + ".id}", **body},
                    )
                else:
                    raise TemplateUnavailable(
                        "context: encryption association ambiguous"
                    )
            elif target.type == "aws_s3_bucket_server_side_encryption_configuration":
                if self.package.resolve(self.module, target.body.get("bucket")) is None:
                    raise TemplateUnavailable("context: bucket association unresolved")
                self.edit(target, self.encryption_rules(target.body, key))
            elif target.type == "aws_cloudwatch_log_group":
                name = target.body.get("name")
                if not isinstance(name, str) or "${" in name or "%{" in name:
                    raise TemplateUnavailable("context: log-group name unresolved")
                self.grant_log_key(key, name)
                self.preserve_key(target.body.get("kms_key_id"), key)
                self.edit(target, {"kms_key_id": "${" + key + ".arn}"})
            elif target.type == "aws_db_instance":
                if target.body.get("performance_insights_enabled") is not True:
                    raise TemplateUnavailable(
                        "context: Performance Insights not enabled"
                    )
                self.preserve_key(
                    target.body.get("performance_insights_kms_key_id"), key
                )
                self.edit(
                    target, {"performance_insights_kms_key_id": "${" + key + ".arn}"}
                )
            elif target.type == "aws_ebs_volume":
                self.preserve_key(target.body.get("kms_key_id"), key)
                self.edit(
                    target, {"encrypted": True, "kms_key_id": "${" + key + ".arn}"}
                )

    @staticmethod
    def preserve_key(value: Any, key: str) -> None:
        if value not in (None, "", "alias/aws/s3", "${" + key + ".arn}"):
            raise TemplateUnavailable("context: existing encryption key preserved")

    def encryption_rules(self, body: dict[str, Any], key: str) -> dict[str, Any]:
        rules = objects(body.get("rule", [{}]))
        if len(rules) != 1 or "dynamic" in rules[0]:
            raise TemplateUnavailable("context: encryption rule unresolved")
        defaults = objects(
            rules[0].get("apply_server_side_encryption_by_default", [{}])
        )
        if len(defaults) != 1:
            raise TemplateUnavailable("context: encryption default unresolved")
        self.preserve_key(defaults[0].get("kms_master_key_id"), key)
        return {
            "rule": [
                {
                    **rules[0],
                    "apply_server_side_encryption_by_default": [
                        {
                            **defaults[0],
                            "sse_algorithm": "aws:kms",
                            "kms_master_key_id": "${" + key + ".arn}",
                        }
                    ],
                }
            ]
        }

    def grant_log_key(self, key: str, name: str) -> None:
        self.identity()
        existing = self.package.get(self.module, key)
        body = (
            existing.body if existing else self.new["aws_kms_key"]["infraarch_security"]
        )
        policy = json.loads(body.get("policy", "{}"))
        if not isinstance(policy.get("Statement"), list):
            raise TemplateUnavailable("context: existing KMS policy unresolved")
        service = (
            "logs.${data.aws_region.infraarch_security.name}."
            "${data.aws_partition.infraarch_security.dns_suffix}"
        )
        arn = (
            "arn:${data.aws_partition.infraarch_security.partition}:logs:"
            "${data.aws_region.infraarch_security.name}:"
            "${data.aws_caller_identity.infraarch_security.account_id}:log-group:"
        )
        statement = {
            "Effect": "Allow",
            "Principal": {"Service": service},
            "Action": [
                "kms:Encrypt",
                "kms:Decrypt",
                "kms:ReEncrypt*",
                "kms:GenerateDataKey*",
                "kms:DescribeKey",
            ],
            "Resource": "*",
            "Condition": {
                "ArnEquals": {"kms:EncryptionContext:aws:logs:arn": arn + name}
            },
        }
        if statement not in policy["Statement"]:
            policy["Statement"].append(statement)
        if existing:
            self.edit(existing, {"policy": json.dumps(policy)})
        else:
            body["policy"] = json.dumps(policy)

    def access_logs(self, targets: list[Resource]) -> None:
        buckets = self.existing("aws_s3_bucket")
        existing_logs = [r for r in buckets if r.name == "infraarch_access_logs"]
        if existing_logs:
            # Reusing the generated destination is safe only when its complete
            # configuration remains available; never overwrite modified support.
            bucket = existing_logs[0].address
            configs = self.existing(
                "aws_s3_bucket_server_side_encryption_configuration"
            )
            if not any(
                r.name == "infraarch_access_logs"
                and objects(r.body.get("rule", []))
                == [
                    {
                        "apply_server_side_encryption_by_default": [
                            {"sse_algorithm": "AES256"}
                        ]
                    }
                ]
                for r in configs
            ):
                raise TemplateUnavailable(
                    "context: existing log destination incompatible"
                )
        else:
            bucket = self.add(
                "aws_s3_bucket",
                "infraarch_access_logs",
                {"bucket_prefix": "infraarch-access-", "force_destroy": False},
            )
            self.add(
                "aws_s3_bucket_public_access_block",
                "infraarch_access_logs",
                {
                    "bucket": "${" + bucket + ".id}",
                    **{
                        k: True
                        for k in (
                            "block_public_acls",
                            "block_public_policy",
                            "ignore_public_acls",
                            "restrict_public_buckets",
                        )
                    },
                },
            )
            self.add(
                "aws_s3_bucket_versioning",
                "infraarch_access_logs",
                {
                    "bucket": "${" + bucket + ".id}",
                    "versioning_configuration": [{"status": "Enabled"}],
                },
            )
            self.add(
                "aws_s3_bucket_server_side_encryption_configuration",
                "infraarch_access_logs",
                {
                    "bucket": "${" + bucket + ".id}",
                    "rule": [
                        {
                            "apply_server_side_encryption_by_default": [
                                {"sse_algorithm": "AES256"}
                            ]
                        }
                    ],
                },
            )
        self.identity()
        account = "${data.aws_caller_identity.infraarch_security.account_id}"
        statements: list[dict[str, Any]] = [
            {
                "Sid": "RequireTLS",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": ["${" + bucket + ".arn}", "${" + bucket + ".arn}/*"],
                "Condition": {"Bool": {"aws:SecureTransport": "false"}},
            }
        ]
        for target in targets:
            if target.address == bucket:
                continue
            if target.type == "aws_lb" and target.body.get(
                "load_balancer_type", "application"
            ) not in {"application", "network"}:
                raise TemplateUnavailable("context: unsupported load balancer")
            prefix = ("s3/" if target.type == "aws_s3_bucket" else "alb/") + target.name
            principal = (
                "logging.s3.amazonaws.com"
                if target.type == "aws_s3_bucket"
                else "logdelivery.elasticloadbalancing.amazonaws.com"
            )
            suffix = (
                "/*" if target.type == "aws_s3_bucket" else "/AWSLogs/" + account + "/*"
            )
            condition = {"StringEquals": {"aws:SourceAccount": account}}
            if target.type == "aws_s3_bucket":
                condition["ArnLike"] = {
                    "aws:SourceArn": "${" + target.address + ".arn}"
                }
            elif target.body.get("load_balancer_type") == "network":
                if not any(
                    r.module == self.module
                    and r.type == "aws_lb_listener"
                    and r.body.get("load_balancer_arn")
                    == "${" + target.address + ".arn}"
                    and r.body.get("protocol") == "TLS"
                    for r in self.package.resources
                ):
                    raise TemplateUnavailable("context: network LB needs TLS listener")
                principal = "delivery.logs.amazonaws.com"
                condition["ArnLike"] = {
                    "aws:SourceArn": (
                        "arn:${data.aws_partition.infraarch_security.partition}:logs:"
                        "${data.aws_region.infraarch_security.name}:" + account + ":*"
                    )
                }
                statements.append(
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": principal},
                        "Action": "s3:GetBucketAcl",
                        "Resource": "${" + bucket + ".arn}",
                        "Condition": {k: dict(v) for k, v in condition.items()},
                    }
                )
                condition["StringEquals"]["s3:x-amz-acl"] = "bucket-owner-full-control"
            statements.append(
                {
                    "Effect": "Allow",
                    "Principal": {"Service": principal},
                    "Action": "s3:PutObject",
                    "Resource": "${" + bucket + ".arn}/" + prefix + suffix,
                    "Condition": condition,
                }
            )
        policy = "aws_s3_bucket_policy.infraarch_access_logs"
        policy_body = {
            "bucket": "${" + bucket + ".id}",
            "policy": json.dumps({"Version": "2012-10-17", "Statement": statements}),
        }
        old_policy = self.package.get(self.module, policy)
        if old_policy:
            old = json.loads(old_policy.body.get("policy", "{}"))
            # Only extend known statements, preserving other access restrictions.
            old_statements = old.get("Statement", [])
            if not isinstance(old_statements, list):
                raise TemplateUnavailable("context: log bucket policy unresolved")
            for statement in statements:
                if statement not in old_statements:
                    old_statements.append(statement)
            self.edit(
                old_policy, {"policy": json.dumps({**old, "Statement": old_statements})}
            )
        else:
            self.add("aws_s3_bucket_policy", "infraarch_access_logs", policy_body)
        for target in targets:
            if target.address == bucket:
                continue
            if target.type == "aws_s3_bucket":
                configs = [
                    r
                    for r in self.existing("aws_s3_bucket_logging")
                    if r.body.get("bucket") == "${" + target.address + ".id}"
                ]
                body = {
                    "bucket": "${" + target.address + ".id}",
                    "target_bucket": "${" + bucket + ".id}",
                    "target_prefix": "s3/" + target.name + "/",
                }
                if configs or target.body.get("logging"):
                    raise TemplateUnavailable(
                        "context: existing access logging requires review"
                    )
                self.add(
                    "aws_s3_bucket_logging",
                    "infraarch_" + target.name,
                    {**body, "depends_on": [policy]},
                )
            else:
                if target.body.get("access_logs"):
                    raise TemplateUnavailable(
                        "context: existing access logging requires review"
                    )
                self.edit(
                    target,
                    {
                        "access_logs": [
                            {
                                "bucket": "${" + bucket + ".id}",
                                "prefix": "alb/" + target.name,
                                "enabled": True,
                            }
                        ]
                    },
                    (policy,),
                )

    def flow_logs(self, targets: list[Resource]) -> None:
        configured = {
            r.body.get("vpc_id")
            for r in self.existing("aws_flow_log")
            if isinstance(r.body.get("vpc_id"), str)
        }
        targets = [t for t in targets if "${" + t.address + ".id}" not in configured]
        if not targets:
            return
        existing_group = self.package.get(
            self.module, "aws_cloudwatch_log_group.infraarch_vpc_flow"
        )
        if existing_group:
            existing_role = self.package.get(
                self.module, "aws_iam_role.infraarch_vpc_flow"
            )
            existing_policy = self.package.get(
                self.module, "aws_iam_role_policy.infraarch_vpc_flow"
            )
            if (
                existing_role is None
                or existing_policy is None
                or existing_group.body.get("retention_in_days", 0) < 365
                or existing_group.body.get("name_prefix") != "/infraarch/vpc-flow-"
                or not self.package.resolve(
                    self.module, existing_group.body.get("kms_key_id")
                )
            ):
                raise TemplateUnavailable("context: flow-log support incompatible")
            trust = json.loads(existing_role.body.get("assume_role_policy", "{}"))
            if not any(
                s.get("Principal") == {"Service": "vpc-flow-logs.amazonaws.com"}
                and s.get("Action") == "sts:AssumeRole"
                for s in trust.get("Statement", [])
            ):
                raise TemplateUnavailable("context: flow-log trust unresolved")
            for target in targets:
                self.add(
                    "aws_flow_log",
                    "infraarch_" + target.name,
                    {
                        "vpc_id": "${" + target.address + ".id}",
                        "traffic_type": "ALL",
                        "log_destination_type": "cloud-watch-logs",
                        "log_destination": "${" + existing_group.address + ".arn}",
                        "iam_role_arn": "${" + existing_role.address + ".arn}",
                        "depends_on": [existing_policy.address],
                    },
                )
            return
        key = self.key()
        group = self.add(
            "aws_cloudwatch_log_group",
            "infraarch_vpc_flow",
            {
                "name_prefix": "/infraarch/vpc-flow-",
                "retention_in_days": 365,
                "kms_key_id": "${" + key + ".arn}",
            },
        )
        role = self.add(
            "aws_iam_role",
            "infraarch_vpc_flow",
            {
                "name_prefix": "infraarch-flow-",
                "assume_role_policy": json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
                                "Action": "sts:AssumeRole",
                                "Condition": {
                                    "StringEquals": {
                                        "aws:SourceAccount": (
                                            "${data.aws_caller_identity."
                                            "infraarch_security.account_id}"
                                        )
                                    }
                                },
                            }
                        ],
                    }
                ),
            },
        )
        self.identity()
        policy = self.add(
            "aws_iam_role_policy",
            "infraarch_vpc_flow",
            {
                "name_prefix": "infraarch-flow-",
                "role": "${" + role + ".id}",
                "policy": json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents",
                                    "logs:DescribeLogStreams",
                                ],
                                "Resource": "${" + group + ".arn}:*",
                            },
                            {
                                "Effect": "Allow",
                                "Action": ["logs:DescribeLogGroups"],
                                "Resource": "*",
                            },
                        ],
                    }
                ),
            },
        )
        for target in targets:
            self.add(
                "aws_flow_log",
                "infraarch_" + target.name,
                {
                    "vpc_id": "${" + target.address + ".id}",
                    "traffic_type": "ALL",
                    "log_destination_type": "cloud-watch-logs",
                    "log_destination": "${" + group + ".arn}",
                    "iam_role_arn": "${" + role + ".arn}",
                    "depends_on": [policy],
                },
            )

    def monitoring(self, targets: list[Resource]) -> None:
        roles = [
            r
            for r in self.existing("aws_iam_role")
            if r.name == "infraarch_rds_monitoring"
        ]
        if roles:
            role = roles[0].address
            existing_attachment = self.package.get(
                self.module, "aws_iam_role_policy_attachment.infraarch_rds_monitoring"
            )
            trust = json.loads(roles[0].body.get("assume_role_policy", "{}"))
            if existing_attachment is None or not any(
                s.get("Principal") == {"Service": "monitoring.rds.amazonaws.com"}
                and s.get("Action") == "sts:AssumeRole"
                for s in trust.get("Statement", [])
            ):
                raise TemplateUnavailable("context: monitoring role incompatible")
            for target in targets:
                if target.body.get("monitoring_role_arn") not in (
                    None,
                    "${" + role + ".arn}",
                ):
                    raise TemplateUnavailable("context: existing role preserved")
                self.edit(
                    target,
                    {
                        "monitoring_role_arn": "${" + role + ".arn}",
                        "monitoring_interval": target.body.get("monitoring_interval")
                        or 60,
                    },
                    (existing_attachment.address,),
                )
            return
        self.identity()
        role = self.add(
            "aws_iam_role",
            "infraarch_rds_monitoring",
            {
                "name_prefix": "infraarch-rds-monitor-",
                "assume_role_policy": json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "monitoring.rds.amazonaws.com"
                                },
                                "Action": "sts:AssumeRole",
                            }
                        ],
                    }
                ),
            },
        )
        attachment = self.add(
            "aws_iam_role_policy_attachment",
            "infraarch_rds_monitoring",
            {
                "role": "${" + role + ".name}",
                "policy_arn": (
                    "arn:${data.aws_partition.infraarch_security.partition}:"
                    "iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
                ),
            },
        )
        for target in targets:
            if target.body.get("monitoring_role_arn"):
                raise TemplateUnavailable(
                    "context: existing monitoring role requires review"
                )
            self.edit(
                target,
                {
                    "monitoring_role_arn": "${" + role + ".arn}",
                    "monitoring_interval": 60,
                },
                (attachment,),
            )

    def finish(self) -> dict[str, str]:
        if not self.new and not self.data:
            return self.files
        path = self.module + "/security_support.tf.json"
        data = json.loads(self.files.get(path, "{}"))
        if not isinstance(data, dict):
            raise TemplateUnavailable("context: support file conflict")
        for kind, additions in (("resource", self.new), ("data", self.data)):
            for typ, named in additions.items():
                for name, body in named.items():
                    dest = data.setdefault(kind, {}).setdefault(typ, {})
                    if name in dest and dest[name] != body:
                        raise TemplateUnavailable("context: support file conflict")
                    dest[name] = body
        return {**self.files, path: json.dumps(data, indent=2) + "\n"}


def build_template(
    files: dict[str, str], findings: list[Violation], module: str, kind: str
) -> tuple[dict[str, str], dict[str, Any]]:
    record: dict[str, Any] = {
        "template": kind,
        "module": module,
        "status": "skipped",
        "introduced_findings": [],
    }
    package = TerraformPackage(files)
    targets = {
        f.resource: package.get(module, f.resource)
        for f in findings
        if f.blocking
        and f.rule_id in TEMPLATE_RULES[kind]
        and str(PurePosixPath(f.file_path).parent) == module
    }
    selected = [
        r for r in targets.values() if r is not None and r.type in TEMPLATE_TYPES[kind]
    ]
    if not selected:
        record["reason"] = "context: no linked resource"
        return files, record
    record["resources"] = sorted(r.address for r in selected)
    try:
        if any(
            any(k in r.body for k in ("count", "for_each", "dynamic", "provider"))
            for r in selected
        ):
            raise TemplateUnavailable("context: resource/provider instance unresolved")
        builder = Builder(files, module)
        getattr(builder, kind)(selected)
        candidate = builder.finish()
        record.update(
            status="proposed" if candidate != files else "skipped",
            reason="supporting_resources" if candidate != files else "already_secure",
        )
        return candidate, record
    except TemplateUnavailable as error:
        record["reason"] = str(error)
        return files, record
    except (ValueError, TypeError, KeyError):
        # Never expose raw parser/configuration exceptions.
        record["reason"] = "context: supporting template unavailable"
        return files, record
