"""Versioned local severity policy; Checkov Community JSON has no severity data."""

from collections.abc import Mapping, Sequence

from app.domain.enums import Severity, Variant
from app.domain.models import Violation

SECURITY_POLICY_VERSION = "1"
BLOCKING_SEVERITIES = frozenset({Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM})

# Sources: Checkov 3.3.21 `--list` check names and the equivalent tfsec
# v1.28.14 rule severity where available. The mapping is deliberately curated;
# unknown Checkov rules are visible as advisory until a human reviews them.
CHECKOV_SEVERITY: dict[str, Severity] = {
    # S3 access, encryption, replication, and logging.
    "CKV2_AWS_65": Severity.HIGH,
    "CKV_AWS_18": Severity.MEDIUM,
    "CKV_AWS_21": Severity.MEDIUM,
    "CKV_AWS_144": Severity.MEDIUM,
    "CKV_AWS_145": Severity.MEDIUM,
    "CKV_AWS_19": Severity.HIGH,
    "CKV_AWS_20": Severity.HIGH,
    "CKV_AWS_53": Severity.HIGH,
    "CKV_AWS_54": Severity.HIGH,
    "CKV_AWS_55": Severity.HIGH,
    "CKV_AWS_56": Severity.HIGH,
    # RDS and network exposure.
    "CKV_AWS_16": Severity.HIGH,
    "CKV_AWS_17": Severity.HIGH,
    "CKV_AWS_118": Severity.MEDIUM,
    "CKV_AWS_129": Severity.MEDIUM,
    "CKV_AWS_133": Severity.MEDIUM,
    "CKV_AWS_157": Severity.MEDIUM,
    "CKV_AWS_161": Severity.MEDIUM,
    "CKV_AWS_293": Severity.MEDIUM,
    "CKV_AWS_353": Severity.MEDIUM,
    "CKV_AWS_354": Severity.MEDIUM,
    "CKV_AWS_24": Severity.HIGH,
    "CKV_AWS_260": Severity.MEDIUM,
    "CKV_AWS_130": Severity.MEDIUM,
    "CKV2_AWS_12": Severity.HIGH,
    # IAM, storage, transport, and audit.
    "CKV_AWS_40": Severity.HIGH,
    "CKV_AWS_111": Severity.HIGH,
    "CKV_AWS_108": Severity.HIGH,
    "CKV_AWS_3": Severity.HIGH,
    "CKV_AWS_8": Severity.HIGH,
    "CKV_AWS_146": Severity.HIGH,
    "CKV_AWS_2": Severity.HIGH,
    "CKV_AWS_103": Severity.MEDIUM,
    "CKV_AWS_378": Severity.HIGH,
    "CKV2_AWS_20": Severity.HIGH,
    "CKV2_AWS_11": Severity.MEDIUM,
    "CKV_AWS_37": Severity.MEDIUM,
    "CKV_AWS_38": Severity.HIGH,
    "CKV_AWS_39": Severity.HIGH,
    "CKV_AWS_58": Severity.HIGH,
    "CKV_AWS_91": Severity.MEDIUM,
    # Kubernetes workload boundaries and resource limits.
    "CKV_K8S_10": Severity.MEDIUM,
    "CKV_K8S_11": Severity.MEDIUM,
    "CKV_K8S_12": Severity.MEDIUM,
    "CKV_K8S_13": Severity.MEDIUM,
    "CKV_K8S_16": Severity.HIGH,
    "CKV_K8S_17": Severity.HIGH,
    "CKV_K8S_20": Severity.HIGH,
    "CKV_K8S_23": Severity.HIGH,
    "CKV_K8S_40": Severity.MEDIUM,
    "CKV_K8S_14": Severity.MEDIUM,
    # Dockerfile runtime user and image pinning.
    "CKV_DOCKER_7": Severity.MEDIUM,
    "CKV_DOCKER_8": Severity.HIGH,
}

# The check is still reported; only its blocking classification changes.
VARIANT_EXEMPTIONS: dict[tuple[Variant, str], str] = {
    (
        Variant.COST,
        "CKV_AWS_144",
    ): "cross-region replication conflicts with minimal cost",
    (
        Variant.PERFORMANCE,
        "CKV_AWS_144",
    ): "cross-region replication is outside same-region latency goals",
    (Variant.COST, "CKV_AWS_157"): "single-AZ database is the cost directive",
    (Variant.COST, "CKV_AWS_118"): "enhanced monitoring adds cost",
    (Variant.COST, "CKV_AWS_353"): "Performance Insights adds cost",
    (Variant.COST, "CKV_AWS_354"): "Performance Insights adds cost",
    (
        Variant.COST,
        "aws-rds-enable-performance-insights",
    ): "Performance Insights adds cost",
    (
        Variant.COST,
        "aws-rds-enable-enhanced-monitoring",
    ): "enhanced monitoring adds cost",
    (Variant.COST, "CKV_AWS_145"): "SSE-AES256 is present; KMS adds cost",
}


def classify(
    violations: Sequence[Violation],
    variant: Variant,
    files: Mapping[str, str] | None = None,
) -> list[Violation]:
    """Classify every scanner record without dropping cross-tool duplicates."""
    has_aes256 = files is not None and any(
        "AES256" in content for content in files.values()
    )
    result: list[Violation] = []
    for violation in violations:
        severity = (
            CHECKOV_SEVERITY.get(violation.rule_id, Severity.UNKNOWN)
            if violation.tool == "checkov"
            else violation.severity
        )
        exemption = VARIANT_EXEMPTIONS.get((variant, violation.rule_id))
        if violation.rule_id == "CKV_AWS_145" and not has_aes256:
            exemption = None
        reason = (
            f"variant_exemption:{exemption}"
            if exemption
            else "unmapped_checkov"
            if violation.tool == "checkov" and severity == Severity.UNKNOWN
            else "low_severity"
            if severity == Severity.LOW
            else None
        )
        result.append(
            violation.model_copy(
                update={
                    "severity": severity,
                    "blocking": severity in BLOCKING_SEVERITIES and reason is None,
                    "advisory_reason": reason,
                }
            )
        )
    return result
