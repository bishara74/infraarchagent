"""FR-S-02: threshold and variant exemptions keep all findings visible."""

import pytest

from app.domain.enums import Severity, Variant
from app.domain.models import Violation
from app.security.policy import CHECKOV_SEVERITY, classify

BUCKET = 'resource "aws_s3_bucket" "example" {}\n'
ENCRYPTION = """resource "aws_s3_bucket_server_side_encryption_configuration" "enc" {
  bucket = aws_s3_bucket.example.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
"""


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
            finding("AWS-0088", "trivy", "HIGH"),
            finding("AWS-0099", "trivy", "LOW"),
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
        [item], Variant.COST, {"terraform/main.tf": BUCKET + ENCRYPTION}
    )[0].blocking
    assert classify(
        [item], Variant.SECURITY, {"terraform/main.tf": BUCKET + ENCRYPTION}
    )[0].blocking


@pytest.mark.req("FR-S-02", "NFR-01")
@pytest.mark.parametrize(
    "extra",
    [
        {"README.md": "# AES256"},
        {"terraform/comment.tf": "# AES256\n"},
        {"terraform/comment.tf": 'locals { text = "AES256" }\n'},
        {
            "terraform/other.tf": ENCRYPTION.replace("example", "other")
            + BUCKET.replace("example", "other")
        },
        {"terraform/unknown.tf": ENCRYPTION.replace('"AES256"', "var.algorithm")},
        {
            "terraform/unknown.tf": ENCRYPTION.replace(
                "aws_s3_bucket.example.id", "var.bucket"
            )
        },
        {"terraform/invalid.tf": 'resource "incomplete" {'},
    ],
)
def test_r2_unrelated_or_unresolvable_evidence_stays_blocking(extra):
    assert classify(
        [finding("CKV_AWS_145")], Variant.COST, {"terraform/main.tf": BUCKET, **extra}
    )[0].blocking


@pytest.mark.req("FR-S-02")
@pytest.mark.parametrize("cross_file", [False, True])
def test_r2_exact_bucket_encryption(cross_file):
    files = {"terraform/main.tf": BUCKET}
    if cross_file:
        files["terraform/encryption.tf"] = ENCRYPTION
    else:
        files["terraform/main.tf"] += ENCRYPTION
    assert not classify([finding("CKV_AWS_145")], Variant.COST, files)[0].blocking
    files["terraform/duplicate.tf"] = ENCRYPTION.replace('"example" {', '"duplicate" {')
    assert classify([finding("CKV_AWS_145")], Variant.COST, files)[0].blocking


@pytest.mark.req("FR-S-02")
def test_r2_tf_json_and_module_isolation():
    import json

    files = {
        "terraform/main.tf": BUCKET,
        "terraform/encryption.tf.json": json.dumps(
            {
                "resource": {
                    "aws_s3_bucket_server_side_encryption_configuration": {
                        "encryption": {
                            "bucket": "${aws_s3_bucket.example.id}",
                            "rule": [
                                {
                                    "apply_server_side_encryption_by_default": [
                                        {"sse_algorithm": "AES256"}
                                    ]
                                }
                            ],
                        }
                    }
                }
            }
        ),
    }
    assert not classify([finding("CKV_AWS_145")], Variant.COST, files)[0].blocking
    files["terraform/child/encryption.tf.json"] = files.pop(
        "terraform/encryption.tf.json"
    )
    assert classify([finding("CKV_AWS_145")], Variant.COST, files)[0].blocking
