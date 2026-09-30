"""Report-only regex heuristics; Phase 5 Checkov determines real security findings.

These checks are deliberately approximate. They inspect Terraform and Kubernetes
text but do not parse either language or reject a generated package.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.enums import Variant
from app.domain.package_layout import classify_path
from app.domain.plan import DeploymentPlan, FileType, StorageKind


@dataclass(frozen=True)
class DirectiveCheck:
    name: str
    passed: bool
    detail: str


def _has_relational_db(plan: DeploymentPlan) -> bool:
    return any(storage.kind is StorageKind.RELATIONAL_DB for storage in plan.storage)


def _uses(plan: DeploymentPlan, name: str) -> bool:
    return any(name in item.aws_service.casefold() for item in plan.services) or any(
        name in item.aws_service.casefold() for item in plan.storage
    )


def _check(name: str, passed: bool, success: str, failure: str) -> DirectiveCheck:
    return DirectiveCheck(name, passed, success if passed else failure)


def _cost(terraform: str) -> list[DirectiveCheck]:
    sizes = re.findall(
        r"\b(?:instance_type|instance_class)\s*=\s*[\"']([^\"']+)[\"']",
        terraform,
        re.IGNORECASE,
    )
    small = re.compile(r"(?:db\.)?t(?:2|3|3a|4g)\.(?:micro|small)\Z", re.I)
    bad = [size for size in sizes if not small.fullmatch(size)]
    multi_az = bool(re.search(r"\bmulti_az\s*=\s*true\b", terraform, re.I))
    return [
        _check(
            "small instance classes",
            not bad,
            f"All {len(sizes)} explicit instance classes are micro or small.",
            f"Found {len(bad)} larger or unknown instance classes.",
        ),
        _check(
            "single-AZ preference",
            not multi_az,
            "No multi_az = true setting found.",
            "Found multi_az = true.",
        ),
    ]


def _performance(
    terraform: str, kubernetes: str, plan: DeploymentPlan
) -> list[DirectiveCheck]:
    checks: list[DirectiveCheck] = []
    if _has_relational_db(plan):
        multi_az = bool(re.search(r"\bmulti_az\s*=\s*true\b", terraform, re.I))
        checks.append(
            _check(
                "relational DB multi-AZ",
                multi_az,
                "Found multi_az = true for a plan with a relational DB.",
                "Plan has a relational DB but no multi_az = true setting was found.",
            )
        )
    scaling = bool(
        re.search(
            r"\baws_(?:autoscaling_group|appautoscaling_[a-z_]+)\b",
            terraform,
            re.I,
        )
        or re.search(r"\bHorizontalPodAutoscaler\b", kubernetes)
    )
    checks.append(
        _check(
            "autoscaling construct",
            scaling,
            "Found Terraform autoscaling or a Kubernetes HPA.",
            "No Terraform autoscaling construct or Kubernetes HPA found.",
        )
    )
    return checks


def _open_ingress_blocks(terraform: str) -> list[str]:
    blocks = re.findall(r"\bingress\s*\{([^{}]*)\}", terraform, re.I | re.S)
    rules = re.findall(
        r'resource\s+"(aws_(?:vpc_security_group_ingress_rule|security_group_rule))"'
        r'\s+"[^"]+"\s*\{([^{}]*)\}',
        terraform,
        re.I | re.S,
    )
    blocks.extend(
        body
        for kind, body in rules
        if kind.casefold() == "aws_vpc_security_group_ingress_rule"
        or re.search(r'\btype\s*=\s*"ingress"', body, re.I)
    )
    return blocks


def _security(terraform: str, plan: DeploymentPlan) -> list[DirectiveCheck]:
    checks: list[DirectiveCheck] = []
    if _uses(plan, "rds"):
        encrypted = bool(
            re.search(r"\bstorage_encrypted\s*=\s*true\b", terraform, re.I)
        )
        checks.append(
            _check(
                "RDS storage encryption",
                encrypted,
                "Found storage_encrypted = true.",
                "Plan uses RDS but storage_encrypted = true was not found.",
            )
        )
    if _uses(plan, "s3"):
        encryption = bool(
            re.search(
                r"\b(?:aws_s3_bucket_server_side_encryption_configuration|"
                r"server_side_encryption_configuration)\b",
                terraform,
                re.I,
            )
        )
        block = "aws_s3_bucket_public_access_block" in terraform
        checks.extend(
            (
                _check(
                    "S3 encryption",
                    encryption,
                    "Found an S3 server-side encryption configuration.",
                    "Plan uses S3 but no server-side encryption configuration "
                    "was found.",
                ),
                _check(
                    "S3 public access block",
                    block,
                    "Found an S3 public access block.",
                    "Plan uses S3 but no public access block was found.",
                ),
            )
        )
    open_blocks = [
        block for block in _open_ingress_blocks(terraform) if "0.0.0.0/0" in block
    ]
    bad_ingress = [
        block
        for block in open_blocks
        if not (
            re.search(r"\bfrom_port\s*=\s*443\b", block)
            and re.search(r"\bto_port\s*=\s*443\b", block)
        )
    ]
    checks.append(
        _check(
            "public ingress port",
            not bad_ingress,
            "No broad ingress found outside port 443.",
            "Found 0.0.0.0/0 ingress on a port other than 443.",
        )
    )
    wildcard_actions = bool(
        re.search(r"\bactions\s*=\s*\[[^\]]*[\"']\*[\"']", terraform, re.I | re.S)
        or re.search(r'"Action"\s*:\s*(?:"\*"|\[[^\]]*"\*")', terraform, re.I | re.S)
        or re.search(r'\bAction\s*=\s*"\*"', terraform, re.I)
    )
    checks.append(
        _check(
            "IAM wildcard actions",
            not wildcard_actions,
            "No wildcard IAM action was found.",
            "Found an IAM action wildcard.",
        )
    )
    return checks


def check_directive(
    variant: Variant, files: Mapping[str, str], plan: DeploymentPlan
) -> list[DirectiveCheck]:
    terraform = "\n".join(
        content
        for path, content in files.items()
        if classify_path(path) is FileType.TERRAFORM
    )
    kubernetes = "\n".join(
        content
        for path, content in files.items()
        if classify_path(path) is FileType.KUBERNETES
    )
    if variant is Variant.COST:
        return _cost(terraform)
    if variant is Variant.PERFORMANCE:
        return _performance(terraform, kubernetes, plan)
    if variant is Variant.SECURITY:
        return _security(terraform, plan)
    raise ValueError("unknown optimisation variant")
