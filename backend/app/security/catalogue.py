"""D-46: scanner-targeted secure defaults, schema checked before emission."""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from app.domain.models import Violation
from app.security.addressing import repair_addressing
from app.security.terraform import (
    TerraformPackage,
    edit_resource,
    objects,
    subnet_intent,
)


@dataclass(frozen=True)
class Control:
    name: str
    rules: tuple[str, ...]
    types: tuple[str, ...]
    change: str
    justification: str


CATALOGUE = (
    Control(
        "deletion",
        ("CKV_AWS_293", "AWS-0177"),
        ("aws_db_instance",),
        "deletion_protection=true",
        "Prevent accidental database deletion",
    ),
    Control(
        "iam_auth",
        ("CKV_AWS_161", "AWS-0176"),
        ("aws_db_instance",),
        "iam_database_authentication_enabled=true",
        "Add IAM authentication for supported engines",
    ),
    Control(
        "storage",
        ("CKV_AWS_16", "AWS-0080"),
        ("aws_db_instance",),
        "storage_encrypted=true",
        "Encrypt database storage without replacing a configured key",
    ),
    Control(
        "db_logs",
        ("CKV_AWS_129",),
        ("aws_db_instance",),
        "enabled_cloudwatch_logs_exports=engine logs",
        "Export supported engine logs",
    ),
    Control(
        "insights",
        ("CKV_AWS_353", "AWS-0133"),
        ("aws_db_instance",),
        "performance_insights_enabled=true",
        "Enable supported database performance diagnostics",
    ),
    Control(
        "monitoring",
        ("CKV_AWS_118",),
        ("aws_db_instance",),
        "monitoring_interval=60 with existing role",
        "Enable enhanced monitoring with a supplied role",
    ),
    Control(
        "imds",
        ("CKV_AWS_79", "AWS-0028", "AWS-0130"),
        ("aws_instance",),
        "metadata_options.http_tokens=required",
        "Require authenticated instance metadata requests",
    ),
    Control(
        "ebs",
        ("CKV_AWS_8", "AWS-0131"),
        ("aws_instance", "aws_launch_configuration"),
        "root_block_device/ebs_block_device.encrypted=true",
        "Encrypt attached block storage",
    ),
    Control(
        "volume",
        ("CKV_AWS_3", "AWS-0026"),
        ("aws_ebs_volume",),
        "encrypted=true",
        "Encrypt standalone block storage",
    ),
    Control(
        "subnet",
        ("CKV_AWS_130", "AWS-0164"),
        ("aws_subnet",),
        "map_public_ip_on_launch=false on proven private subnets",
        "Avoid unintended public instance addresses",
    ),
    Control(
        "tls",
        ("CKV_AWS_103",),
        ("aws_lb_listener",),
        "ssl_policy=ELBSecurityPolicy-TLS13-1-2-2021-06 on HTTPS/TLS",
        "Require TLS 1.2 or newer",
    ),
    Control(
        "eks_logs",
        ("CKV_AWS_38", "AWS-0038"),
        ("aws_eks_cluster",),
        "enabled_cluster_log_types=api,audit,authenticator,controllerManager,scheduler",
        "Capture all control-plane audit streams",
    ),
)
DB_LOGS = {
    "postgres": ["postgresql", "upgrade"],
    "mysql": ["audit", "error", "general", "slowquery"],
    "mariadb": ["audit", "error", "general", "slowquery"],
}
EKS_LOGS = ["api", "audit", "authenticator", "controllerManager", "scheduler"]


def _literal(value: Any) -> bool:
    if isinstance(value, str):
        return "${" not in value and "%{" not in value
    if isinstance(value, list):
        return all(_literal(v) for v in value)
    if isinstance(value, dict):
        return all(_literal(v) for v in value.values())
    return value is None or isinstance(value, (bool, int, float))


def _updates(name: str, body: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    if name in {"iam_auth", "db_logs", "insights"} and (
        not isinstance(body.get("engine"), str) or body["engine"] not in DB_LOGS
    ):
        return {}, "context: unsupported or unresolved database engine"
    booleans = {
        "deletion": "deletion_protection",
        "iam_auth": "iam_database_authentication_enabled",
        "storage": "storage_encrypted",
        "insights": "performance_insights_enabled",
        "volume": "encrypted",
        "subnet": "map_public_ip_on_launch",
    }
    if name in booleans:
        field = booleans[name]
        old = body.get(field)
        if old is not None and type(old) is not bool:
            return {}, "context: unresolved expression"
        return {field: name != "subnet"}, None
    if name in {"db_logs", "eks_logs"}:
        field = (
            "enabled_cloudwatch_logs_exports"
            if name == "db_logs"
            else "enabled_cluster_log_types"
        )
        old = body.get(field, [])
        if not isinstance(old, list) or not all(
            isinstance(v, str) and _literal(v) for v in old
        ):
            return {}, "context: unresolved expression"
        return {
            field: sorted(
                set(old)
                | set(DB_LOGS[body["engine"]] if name == "db_logs" else EKS_LOGS)
            )
        }, None
    if name == "monitoring":
        if not body.get("monitoring_role_arn"):
            return {}, "context: monitoring role required"
        interval = body.get("monitoring_interval", 0)
        if type(interval) is not int:
            return {}, "context: unresolved expression"
        return {"monitoring_interval": interval if interval > 0 else 60}, None
    if name == "tls":
        if not isinstance(body.get("protocol"), str) or body["protocol"] not in {
            "HTTPS",
            "TLS",
        }:
            return {}, "context: TLS listener and certificate required"
        old = body.get("ssl_policy", "")
        if not _literal(old):
            return {}, "context: unresolved expression"
        if isinstance(old, str) and (
            "TLS13-1-2" in old or "TLS13-1-3" in old or "TLS-1-2" in old
        ):
            return {}, "already_secure"
        return {"ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06"}, None
    if name == "imds":
        old = objects(body.get("metadata_options", []))
        if "metadata_options" in body and len(old) != 1:
            return {}, "context: unresolved metadata block"
        nested = dict(old[0]) if old else {}
        if not _literal(nested.get("http_tokens")):
            return {}, "context: unresolved expression"
        nested["http_tokens"] = "required"
        return {"metadata_options": [nested]}, None
    if name == "ebs":
        changes = {}
        for field in ("root_block_device", "ebs_block_device"):
            entries = objects(body.get(field, []))
            if field in body and not entries:
                return {}, "context: unresolved block devices"
            if field == "root_block_device" and not entries:
                entries = [{}]
            if any(not _literal(v.get("encrypted")) for v in entries):
                return {}, "context: unresolved expression"
            if entries:
                changes[field] = [{**v, "encrypted": True} for v in entries]
        return changes, None
    return {}, "not_applicable"


def autofix(
    files: dict[str, str], findings: list[Violation]
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    current = dict(files)
    records: list[dict[str, Any]] = []
    targets = {
        (str(PurePosixPath(f.file_path).parent), f.resource.split("[", 1)[0])
        for f in findings
        if f.blocking and f.rule_id in {"CKV_AWS_130", "AWS-0164"}
    }
    current, subnet_records = repair_addressing(current, targets)
    for subnet_record in subnet_records:
        subnet_record["rule_ids"] = sorted(
            {
                f.rule_id
                for f in findings
                if f.blocking
                and f.resource.split("[", 1)[0] == subnet_record["resource"]
                and str(PurePosixPath(f.file_path).parent)
                == str(PurePosixPath(subnet_record["file"]).parent)
            }
        )
    records.extend(subnet_records)
    seen = set()
    for finding in sorted(findings, key=lambda f: (f.file_path, f.resource, f.rule_id)):
        if not finding.blocking:
            continue
        for control in CATALOGUE:
            if (
                control.name == "subnet"
                and (
                    str(PurePosixPath(finding.file_path).parent),
                    finding.resource.split("[", 1)[0],
                )
                in targets
            ):
                # New consumer evidence supersedes only this repair; v1 keeps
                # its original routing predicates and historical assessment.
                if not any(
                    r.get("resource") == finding.resource.split("[", 1)[0]
                    and r.get("control") == "subnet_consumers"
                    for r in records
                ):
                    records.append(
                        {
                            "file": finding.file_path,
                            "resource": finding.resource,
                            "control": "subnet_consumers",
                            "rule_ids": [finding.rule_id],
                            "status": "skipped",
                            "reason": "context: subnet consumers unresolved or inherit IP",
                        }
                    )
                continue
            key = (finding.file_path, finding.resource, control.name)
            if finding.rule_id not in control.rules or key in seen:
                continue
            seen.add(key)
            package = TerraformPackage(current)
            module = str(PurePosixPath(finding.file_path).parent)
            resource = package.get(module, finding.resource)
            record: dict[str, Any] = {
                "rule_ids": sorted(
                    {
                        f.rule_id
                        for f in findings
                        if f.blocking
                        and f.resource == finding.resource
                        and f.file_path == finding.file_path
                        and f.rule_id in control.rules
                    }
                ),
                "resource": finding.resource,
                "file": finding.file_path,
                "control": control.name,
                "status": "skipped",
            }
            if (
                resource is None
                or resource.path != finding.file_path
                or resource.type not in control.types
            ):
                record["reason"] = "context: resource unresolved"
            elif any(k in resource.body for k in ("count", "for_each", "dynamic")):
                record["reason"] = "context: resource instance unresolved"
            else:
                schema = package.schema(resource)
                updates, reason = _updates(control.name, resource.body)
                if control.name == "subnet":
                    intent = subnet_intent(package, resource)
                    if intent != "private":
                        reason = (
                            "context: public subnet"
                            if intent == "public"
                            else "context: subnet routing unresolved"
                        )
                if reason:
                    record["reason"] = reason
                elif not schema:
                    record["reason"] = "context: provider schema unavailable"
                else:
                    candidate = edit_resource(current, resource, updates, schema)
                    if candidate == current or all(
                        resource.body.get(k) == v for k, v in updates.items()
                    ):
                        record["reason"] = (
                            "already_secure"
                            if all(
                                resource.body.get(k) == v for k, v in updates.items()
                            )
                            else "context: schema unsupported"
                        )
                    else:
                        current = candidate
                        record.update(
                            status="proposed",
                            reason="secure_default",
                            provider_version=package.version(module),
                        )
            records.append(record)
    return current, records


def guidance(types: set[str], limit: int = 1500) -> str:
    lines: list[str] = []
    for control in CATALOGUE:
        selected = sorted(types.intersection(control.types))
        if selected:
            line = f"{','.join(selected)}: {control.change}."
            if len("\n".join([*lines, line])) <= limit:
                lines.append(line)
    return "\n".join(lines)
