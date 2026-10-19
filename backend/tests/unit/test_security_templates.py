"""FR-S-02/03: bounded supporting resources with no acceptance exemptions."""

import json

import pytest

from app.domain.models import Violation
from app.security.templates import build_template
from app.security.terraform import TerraformPackage
from app.validation.documents import blocks
from app.validation.gate import syntax_checks


def read_support(files):
    package = TerraformPackage(files)
    resources = {}
    data = {}
    for resource in package.resources:
        if resource.path.endswith("/security_support.tf"):
            resources.setdefault(resource.type, {})[resource.name] = resource.body
    for doc in package.documents.documents.values():
        for labels, body in blocks(doc.data, "data"):
            data.setdefault(labels[0], {}).update(body)
    return {"resource": resources, "data": data}


def template_input(version, kind):
    typ, body, rule = {
        "kms": ("aws_s3_bucket", {}, "CKV_AWS_145"),
        "access_logs": ("aws_s3_bucket", {}, "CKV_AWS_18"),
        "flow_logs": ("aws_vpc", {"cidr_block": "10.0.0.0/16"}, "AWS-0178"),
        "monitoring": (
            "aws_db_instance",
            {
                "engine": "postgres",
                "instance_class": "db.t3.micro",
                "allocated_storage": 20,
            },
            "CKV_AWS_118",
        ),
    }[kind]
    files = {
        "terraform/main.tf.json": json.dumps(
            {
                "terraform": {
                    "required_providers": {
                        "aws": {"source": "hashicorp/aws", "version": "=" + version}
                    }
                },
                "resource": {typ: {"target": body}},
            }
        )
    }
    v = Violation(
        rule_id=rule,
        resource=typ + ".target",
        file_path="terraform/main.tf.json",
        message="synthetic",
        tool="checkov",
        blocking=True,
    )
    return files, [v]


@pytest.mark.req("FR-S-02", "FR-V-03")
@pytest.mark.parametrize("version", ["5.100.0", "6.68.0"])
@pytest.mark.parametrize("kind", ["kms", "access_logs", "flow_logs", "monitoring"])
def test_templates_both_schemas_parse_and_do_not_duplicate(version, kind):
    files, findings = template_input(version, kind)
    candidate, record = build_template(files, findings, "terraform", kind)
    assert record["status"] == "proposed", record
    assert candidate != files and not syntax_checks(candidate)
    second, _ = build_template(candidate, findings, "terraform", kind)
    assert second == candidate
    support = read_support(candidate)["resource"]
    assert all(
        len(values) == 1
        for typ, values in support.items()
        if typ
        in {
            "aws_kms_key",
            "aws_kms_alias",
            "aws_cloudwatch_log_group",
            "aws_iam_role",
            "aws_s3_bucket",
        }
    )
    if kind == "access_logs":
        assert "aws_kms_key" not in support
        assert (
            support["aws_s3_bucket_server_side_encryption_configuration"][
                "infraarch_access_logs"
            ]["rule"][0]["apply_server_side_encryption_by_default"][0]["sse_algorithm"]
            == "AES256"
        )
        assert "aws_s3_bucket_logging" in support
        assert "infraarch_access_logs" not in support["aws_s3_bucket_logging"]


@pytest.mark.req("FR-S-02")
@pytest.mark.parametrize("kind", ["kms", "access_logs", "flow_logs", "monitoring"])
def test_templates_skip_unknown_provider_and_do_not_change_input(kind):
    files, findings = template_input("6.68.0", kind)
    original = dict(files)
    data = json.loads(files["terraform/main.tf.json"])
    target = next(iter(data["resource"].values()))["target"]
    target["provider"] = "aws.other"
    files = {"terraform/main.tf.json": json.dumps(data)}
    candidate, record = build_template(files, findings, "terraform", kind)
    assert candidate == files and record["status"] == "skipped"
    assert original != files


@pytest.mark.req("FR-S-02")
def test_existing_compatible_key_reused_and_collision_skips():
    files, findings = template_input("6.68.0", "kms")
    data = json.loads(files["terraform/main.tf.json"])
    data["resource"]["aws_kms_key"] = {"existing": {"enable_key_rotation": True}}
    files["terraform/main.tf.json"] = json.dumps(data)
    candidate, record = build_template(files, findings, "terraform", "kms")
    assert record["status"] == "proposed"
    support = read_support(candidate)
    assert "aws_kms_key" not in support["resource"]
    assert "aws_kms_key.existing.arn" in candidate["terraform/security_support.tf"]
    data["resource"]["aws_kms_key"]["existing"]["enable_key_rotation"] = False
    files["terraform/main.tf.json"] = json.dumps(data)
    assert build_template(files, findings, "terraform", "kms")[0] == files


@pytest.mark.req("FR-S-02")
def test_load_balancer_delivery_policy_and_dependency():
    files, findings = template_input("5.100.0", "access_logs")
    data = json.loads(files["terraform/main.tf.json"])
    data["resource"] = {"aws_lb": {"target": {"load_balancer_type": "application"}}}
    files["terraform/main.tf.json"] = json.dumps(data)
    findings = [
        findings[0].model_copy(
            update={"resource": "aws_lb.target", "rule_id": "CKV_AWS_91"}
        )
    ]
    candidate, record = build_template(files, findings, "terraform", "access_logs")
    assert record["status"] == "proposed", record
    target = json.loads(candidate["terraform/main.tf.json"])["resource"]["aws_lb"][
        "target"
    ]
    assert target["depends_on"] == ["aws_s3_bucket_policy.infraarch_access_logs"]
    assert (
        "logdelivery.elasticloadbalancing.amazonaws.com"
        in candidate["terraform/security_support.tf"]
    )


@pytest.mark.req("FR-S-02", "NFR-01")
def test_support_file_name_conflict_is_safe():
    files, findings = template_input("5.100.0", "kms")
    files["terraform/security_support.tf.json"] = "[]"
    assert build_template(files, findings, "terraform", "kms")[0] == files


@pytest.mark.req("FR-S-02")
@pytest.mark.parametrize("kind", ["kms", "access_logs", "flow_logs", "monitoring"])
def test_template_support_reused_for_second_flagged_resource(kind):
    files, findings = template_input("6.68.0", kind)
    candidate, _ = build_template(files, findings, "terraform", kind)
    data = json.loads(candidate["terraform/main.tf.json"])
    typ = findings[0].resource.split(".")[0]
    data["resource"][typ]["second"] = dict(data["resource"][typ]["target"])
    if kind == "monitoring":
        data["resource"][typ]["second"].pop("monitoring_role_arn", None)
        data["resource"][typ]["second"].pop("depends_on", None)
    candidate["terraform/main.tf.json"] = json.dumps(data)
    second_finding = findings[0].model_copy(update={"resource": typ + ".second"})
    second, record = build_template(candidate, [second_finding], "terraform", kind)
    assert record["status"] == "proposed", record
    support = read_support(second)["resource"]
    assert all(
        len(support.get(t, {})) <= 1
        for t in (
            "aws_kms_key",
            "aws_kms_alias",
            "aws_iam_role",
            "aws_cloudwatch_log_group",
        )
    )


@pytest.mark.req("FR-S-02", "FR-V-03")
@pytest.mark.parametrize("version", ["5.100.0", "6.68.0"])
@pytest.mark.parametrize(
    "typ,body,rule,field",
    [
        (
            "aws_cloudwatch_log_group",
            {"name": "/app/service", "retention_in_days": 365},
            "AWS-0017",
            "kms_key_id",
        ),
        (
            "aws_db_instance",
            {"engine": "postgres", "performance_insights_enabled": True},
            "CKV_AWS_354",
            "performance_insights_kms_key_id",
        ),
        (
            "aws_ebs_volume",
            {"availability_zone": "us-east-1a", "encrypted": True},
            "AWS-0027",
            "kms_key_id",
        ),
        (
            "aws_s3_bucket_server_side_encryption_configuration",
            {
                "bucket": "${aws_s3_bucket.source.id}",
                "rule": [
                    {
                        "apply_server_side_encryption_by_default": [
                            {"sse_algorithm": "AES256"}
                        ]
                    }
                ],
            },
            "AWS-0132",
            "rule",
        ),
    ],
)
def test_kms_links_all_supported_resource_types(version, typ, body, rule, field):
    files, _ = template_input(version, "kms")
    data = json.loads(files["terraform/main.tf.json"])
    data["resource"] = {typ: {"target": body}}
    if typ == "aws_s3_bucket_server_side_encryption_configuration":
        data["resource"]["aws_s3_bucket"] = {"source": {}}
    files["terraform/main.tf.json"] = json.dumps(data)
    findings = [
        Violation(
            rule_id=rule,
            resource=typ + ".target",
            file_path="terraform/main.tf.json",
            message="synthetic",
            tool="trivy",
            blocking=True,
        )
    ]
    candidate, record = build_template(files, findings, "terraform", "kms")
    assert record["status"] == "proposed", record
    target = json.loads(candidate["terraform/main.tf.json"])["resource"][typ]["target"]
    assert "aws_kms_key.infraarch_security.arn" in json.dumps(target[field])
    assert build_template(candidate, findings, "terraform", "kms")[0] == candidate
    if typ == "aws_cloudwatch_log_group":
        policy = read_support(candidate)["resource"]["aws_kms_key"][
            "infraarch_security"
        ]["policy"]
        assert "/app/service" in policy and "ArnEquals" in policy


@pytest.mark.req("FR-S-02", "NFR-01")
def test_kms_template_preserves_bucket_key_configuration_and_existing_keys():
    files, findings = template_input("6.68.0", "kms")
    data = json.loads(files["terraform/main.tf.json"])
    data["resource"]["aws_s3_bucket_server_side_encryption_configuration"] = {
        "existing": {
            "bucket": "${aws_s3_bucket.target.id}",
            "rule": [
                {
                    "bucket_key_enabled": True,
                    "apply_server_side_encryption_by_default": [
                        {"sse_algorithm": "AES256"}
                    ],
                }
            ],
        }
    }
    files["terraform/main.tf.json"] = json.dumps(data)
    candidate, record = build_template(files, findings, "terraform", "kms")
    assert record["status"] == "proposed", record
    rule = json.loads(candidate["terraform/main.tf.json"])["resource"][
        "aws_s3_bucket_server_side_encryption_configuration"
    ]["existing"]["rule"][0]
    assert rule["bucket_key_enabled"] is True
    data["resource"]["aws_s3_bucket_server_side_encryption_configuration"]["existing"][
        "rule"
    ][0]["apply_server_side_encryption_by_default"][0][
        "kms_master_key_id"
    ] = "${var.existing_key}"
    files["terraform/main.tf.json"] = json.dumps(data)
    assert build_template(files, findings, "terraform", "kms")[0] == files


@pytest.mark.req("FR-S-03")
async def test_template_introduced_blocker_is_rejected_and_identified():
    from app.agents.budget import AgentBudget
    from app.domain.enums import Variant
    from app.scanners.scan import ScanResult
    from app.security.acceptance import CandidateGuard

    files, findings = template_input("6.68.0", "access_logs")
    candidate, _ = build_template(files, findings, "terraform", "access_logs")
    new = findings[0].model_copy(
        update={
            "resource": "aws_s3_bucket.infraarch_access_logs",
            "file_path": "terraform/security_support.tf.json",
        }
    )

    class Verifier:
        async def checks(self, source):
            return []

    class Scanner:
        async def scan(self, source, variant):
            return ScanResult([*findings, new], {})

    record = {"terraform_verification_seconds": 0, "security_verification_seconds": 0}
    result = await CandidateGuard(
        Verifier(), Scanner(), Variant.SECURITY, AgentBudget(60), record
    ).evaluate(files, candidate, [], ScanResult(findings, {}))
    assert result.reason == "new_blocking_findings"
    assert result.introduced == [
        {
            "rule_id": "CKV_AWS_18",
            "file": "terraform/security_support.tf.json",
            "resource": "aws_s3_bucket.infraarch_access_logs",
        }
    ]
