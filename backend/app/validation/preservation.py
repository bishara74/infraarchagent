"""Reject deleting existing security controls instead of repairing their syntax."""

from pathlib import Path
from typing import Any

from app.validation.documents import PackageDocuments, blocks

CONTROL_FIELDS = frozenset(
    {
        "encrypted",
        "kms_key_id",
        "storage_encrypted",
        "root_block_device",
        "metadata_options",
        "server_side_encryption_configuration",
        "logging",
        "logging_config",
        "access_logs",
        "versioning",
        "replication_configuration",
        "public_access_block",
        "enabled_cloudwatch_logs_exports",
        "enable_logging",
        "vpc_config",
        "encryption_config",
        "block_public_acls",
        "block_public_policy",
        "ignore_public_acls",
        "restrict_public_buckets",
        "drop_invalid_header_fields",
        "deletion_protection",
        "backup_retention_period",
        "log_format",
        "log_destination",
        "iam_role_arn",
    }
)
CONTROL_TYPES = (
    "security_group",
    "flow_log",
    "cloudtrail",
    "kms",
    "policy",
    "public_access_block",
    "replication",
    "versioning",
    "encryption",
    "logging",
    "waf",
    "backup",
    "guardduty",
)
MIGRATIONS = {
    "replication_configuration": "aws_s3_bucket_replication_configuration",
    "server_side_encryption_configuration": (
        "aws_s3_bucket_server_side_encryption_configuration"
    ),
    "versioning": "aws_s3_bucket_versioning",
    "logging": "aws_s3_bucket_logging",
}


def resources(files: dict[str, str]) -> dict[tuple[str, ...], dict[str, Any]]:
    return {
        (str(Path(doc.path).parent), *labels): body
        for doc in PackageDocuments.parse(files).documents.values()
        if not doc.parse_error
        for labels, body in blocks(doc.data, "resource")
    }


def removes_security_controls(
    before: dict[str, str], candidate: dict[str, str]
) -> bool:
    original, proposed = resources(before), resources(candidate)
    replacements = {a: body for a, body in proposed.items() if a not in original}
    for address, body in original.items():
        current = proposed.get(address)
        protected = any(token in address[-2] for token in CONTROL_TYPES) or bool(
            CONTROL_FIELDS & body.keys()
        )
        if current is None:
            if protected:
                renamed = next(
                    (
                        a
                        for a, replacement in replacements.items()
                        if a[:2] == address[:2] and body.keys() <= replacement.keys()
                    ),
                    None,
                )
                if renamed is not None:
                    replacements.pop(renamed)
                    continue
                return True
            continue
        for field in CONTROL_FIELDS & (body.keys() - current.keys()):
            replacement = (
                MIGRATIONS.get(field) if address[-2] == "aws_s3_bucket" else None
            )
            if replacement and any(
                a[-2] == replacement
                and a[0] == address[0]
                and f"{address[-2]}.{address[-1]}." in str(v.get("bucket", ""))
                for a, v in proposed.items()
            ):
                continue
            return True
    return False
