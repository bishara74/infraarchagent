"""FR-S-02: all secure defaults, versions, idempotence and context skips."""

import json

import pytest

from app.domain.models import Violation
from app.security.catalogue import CATALOGUE, autofix
from app.security.terraform import TerraformPackage, subnet_intent
from app.validation.gate import syntax_checks


def package(version, resource_type, body, extra=None):
    resources = {resource_type: {"target": body}}
    resources.update(extra or {})
    return {
        "terraform/main.tf.json": json.dumps(
            {
                "terraform": {
                    "required_providers": {
                        "aws": {"source": "hashicorp/aws", "version": "=" + version}
                    }
                },
                "resource": resources,
            }
        )
    }


def finding(rule, typ, path="terraform/main.tf.json"):
    return Violation(
        rule_id=rule,
        file_path=path,
        resource=typ + ".target",
        message="synthetic",
        tool="checkov",
        blocking=True,
    )


def control_body(name):
    return {
        "deletion": {},
        "iam_auth": {"engine": "postgres"},
        "storage": {},
        "db_logs": {"engine": "postgres"},
        "insights": {"engine": "postgres"},
        "monitoring": {"monitoring_role_arn": "${aws_iam_role.monitor.arn}"},
        "imds": {},
        "ebs": {},
        "volume": {},
        "subnet": {"vpc_id": "${aws_vpc.main.id}", "map_public_ip_on_launch": True},
        "tls": {"protocol": "HTTPS", "ssl_policy": "ELBSecurityPolicy-2016-08"},
        "eks_logs": {"enabled_cluster_log_types": ["api"]},
    }[name]


@pytest.mark.req("FR-S-02", "FR-V-03")
@pytest.mark.parametrize("version", ["5.100.0", "6.68.0"])
@pytest.mark.parametrize("control", CATALOGUE, ids=lambda c: c.name)
def test_every_catalogue_entry_is_schema_supported_and_idempotent(version, control):
    extra = (
        {
            "aws_route_table": {"private": {}},
            "aws_route_table_association": {
                "private": {
                    "subnet_id": "${aws_subnet.target.id}",
                    "route_table_id": "${aws_route_table.private.id}",
                }
            },
        }
        if control.name == "subnet"
        else None
    )
    files = package(version, control.types[0], control_body(control.name), extra)
    for rule in control.rules:
        fixes = [finding(rule, control.types[0])]
        candidate, records = autofix(files, fixes)
        assert candidate != files
        assert records[0]["status"] == "proposed"
        assert records[0]["provider_version"] == version
        assert not syntax_checks(candidate)
        assert autofix(candidate, fixes)[0] == candidate


@pytest.mark.req("FR-S-02")
@pytest.mark.parametrize(
    "target", ["private", "public", "nat", "unknown", "missing", "main", "default"]
)
@pytest.mark.parametrize("standalone", [False, True])
def test_route_derived_subnet_intent(target, standalone):
    extra = {
        "aws_route_table": {"table": {}},
        "aws_vpc": {"main": {}},
        "aws_internet_gateway": {"igw": {}},
        "aws_nat_gateway": {"nat": {}},
    }
    route = (
        {}
        if target in {"private", "main", "default", "missing"}
        else {
            "cidr_block": "0.0.0.0/0",
            "nat_gateway_id"
            if target == "nat"
            else "gateway_id": "${aws_nat_gateway.nat.id}"
            if target == "nat"
            else "${var.gateway}"
            if target == "unknown"
            else "${aws_internet_gateway.igw.id}",
        }
    )
    if route:
        if standalone:
            extra["aws_route"] = {
                "route": {**route, "route_table_id": "${aws_route_table.table.id}"}
            }
        else:
            extra["aws_route_table"]["table"]["route"] = [route]
    if target == "main":
        extra["aws_main_route_table_association"] = {
            "main": {
                "vpc_id": "${aws_vpc.main.id}",
                "route_table_id": "${aws_route_table.table.id}",
            }
        }
    elif target == "default":
        extra["aws_default_route_table"] = {
            "main": {"default_route_table_id": "${aws_vpc.main.default_route_table_id}"}
        }
    elif target != "missing":
        extra["aws_route_table_association"] = {
            "association": {
                "subnet_id": "${aws_subnet.target.id}",
                "route_table_id": "${aws_route_table.table.id}",
            }
        }
    files = package("5.100.0", "aws_subnet", control_body("subnet"), extra)
    p = TerraformPackage(files)
    subnet = p.get("terraform", "aws_subnet.target")
    expected = (
        "public"
        if target == "public"
        else "unresolvable"
        if target in {"unknown", "missing"}
        else "private"
    )
    assert subnet_intent(p, subnet) == expected
    candidate, records = autofix(files, [finding("AWS-0164", "aws_subnet")])
    assert (candidate != files) == (expected == "private")
    if expected == "public":
        assert records[0]["reason"] == "context: public subnet"


@pytest.mark.req("FR-S-02", "NFR-01")
@pytest.mark.parametrize(
    "name,body",
    [
        ("iam_auth", {"engine": "oracle-ee"}),
        ("insights", {"engine": "${var.engine}"}),
        ("tls", {"protocol": "HTTP"}),
        ("monitoring", {}),
        ("storage", {"storage_encrypted": "${var.encrypt}"}),
        ("imds", {"metadata_options": [{"http_tokens": "${var.tokens}"}]}),
        ("ebs", {"root_block_device": [{"encrypted": "${var.encrypted}"}]}),
        (
            "db_logs",
            {"engine": "postgres", "enabled_cloudwatch_logs_exports": "${var.logs}"},
        ),
        ("eks_logs", {"enabled_cluster_log_types": "${var.logs}"}),
        ("deletion", {"count": 2}),
        ("volume", {"encrypted": "${var.encrypted}"}),
    ],
)
def test_context_conflicts_skip(name, body):
    control = next(c for c in CATALOGUE if c.name == name)
    files = package("6.68.0", control.types[0], body)
    candidate, records = autofix(files, [finding(control.rules[0], control.types[0])])
    assert candidate == files and records[0]["status"] == "skipped"


@pytest.mark.req("FR-S-02")
def test_hcl_edit_preserves_unrelated_source_and_only_flagged_resource():
    files = {
        "terraform/main.tf": """# preserve header
resource "aws_db_instance" "target" {
  engine = "postgres"
  # retain this key
  kms_key_id = var.key
  storage_encrypted = false
}
resource "aws_db_instance" "other" { storage_encrypted = false }
"""
    }
    v = finding("AWS-0080", "aws_db_instance", "terraform/main.tf")
    candidate, _ = autofix(files, [v])
    assert "# retain this key\n  kms_key_id = var.key" in candidate[v.file_path]
    assert '"other" { storage_encrypted = false }' in candidate[v.file_path]
    assert not syntax_checks(candidate)
    assert autofix(candidate, [v])[0] == candidate
    assert autofix(files, [v.model_copy(update={"blocking": False})])[0] == files
