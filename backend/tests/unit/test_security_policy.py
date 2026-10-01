"""FR-S-02: threshold and variant exemptions keep all findings visible."""

import pytest

from app.domain.enums import Severity, Variant
from app.domain.models import Violation
from app.security.policy import CHECKOV_SEVERITY, classify


def finding(
    rule_id: str, tool: str = "checkov", severity: str = "UNKNOWN"
) -> Violation:
    return Violation.model_validate(
        {
            "rule_id": rule_id,
            "tool": tool,
            "severity": severity,
            "file_path": "terraform/main.tf",
            "resource": "aws_s3_bucket.example",
            "message": "finding",
        }
    )


@pytest.mark.req("FR-S-02")
def test_policy_threshold_unmapped_and_cross_tool_records() -> None:
    assert 40 <= len(CHECKOV_SEVERITY) <= 60
    records = classify(
        [
            finding("CKV_AWS_16"),
            finding("CKV_NEW_1"),
            finding("aws-s3-enable-bucket-encryption", "tfsec", "HIGH"),
            finding("aws-ec2-add-description", "tfsec", "LOW"),
        ],
        Variant.SECURITY,
    )
    assert [item.blocking for item in records] == [True, False, True, False]
    assert records[1].severity == Severity.UNKNOWN
    assert records[1].advisory_reason == "unmapped_checkov"
    assert records[3].advisory_reason == "low_severity"
    assert len(records) == 4


@pytest.mark.req("FR-S-02")
def test_exemptions_do_not_apply_to_security_variant_or_unencrypted_s3() -> None:
    item = finding("CKV_AWS_145")
    assert classify([item], Variant.COST)[0].blocking
    assert not classify(
        [item], Variant.COST, {"terraform/main.tf": 'sse_algorithm = "AES256"'}
    )[0].blocking
    assert classify(
        [item], Variant.SECURITY, {"terraform/main.tf": 'sse_algorithm = "AES256"'}
    )[0].blocking
