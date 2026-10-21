"""FR-V-03: documented v6 equivalents preserve bindings and existing guards."""

import json
from types import SimpleNamespace

import pytest

from app.agents.budget import AgentBudget
from app.agents.deterministic import checked_one
from app.domain.enums import Variant
from app.validation.documents import PackageDocuments
from app.validation.equivalents import repair_equivalents
from app.validation.v6_equivalents import repair_v6_equivalents
from app.validation.workspace import ValidationWorkspace
from tests.unit.test_phase9i_deterministic import Engine, Scanner, Verifier, report
from tests.unit.test_secure_generation import plan

pytestmark = pytest.mark.req("FR-V-03", "FR-G-02", "NFR-01")


def provider(version="~> 6.68", source="hashicorp/aws"):
    return {
        "terraform/providers.tf": "terraform {\n required_providers {\n"
        ' aws = { source = "' + source + '", version = "' + version + '" }\n }\n}\n'
    }


@pytest.mark.parametrize("style", ["hcl", "json"])
def test_documented_equivalents_preserve_bindings_comments_and_idempotence(style):
    files = provider()
    if style == "hcl":
        files["terraform/main.tf"] = """# preserve this header
resource "aws_eip" "nat" { vpc = true } # preserve this comment
resource "aws_ssm_association" "one" {
  name = "AWS-RunShellScript"
  instance_id = var.instance_id # preserve target expression
  parameters = { commands = "echo test" }
}
resource "aws_cloudwatch_log_group" "flow" { name = "flow" }
resource "aws_flow_log" "flow" {
  log_group_name = aws_cloudwatch_log_group.flow.name
  traffic_type = "ALL"
}
"""
    else:
        files["terraform/main.tf.json"] = json.dumps(
            {
                "resource": {
                    "aws_eip": {"nat": {"vpc": True, "tags": {"Name": "KEEP"}}},
                    "aws_ssm_association": {
                        "one": {
                            "name": "AWS-RunShellScript",
                            "instance_id": "${var.instance_id}",
                            "parameters": {"commands": "echo test"},
                        }
                    },
                    "aws_cloudwatch_log_group": {"flow": {"name": "flow"}},
                    "aws_flow_log": {
                        "flow": {
                            "log_group_name": "${aws_cloudwatch_log_group.flow.name}",
                            "traffic_type": "ALL",
                        }
                    },
                }
            }
        )
    before = dict(files)
    result, records = repair_equivalents(files)
    assert files == before
    assert {r["kind"] for r in records} == {
        "eip_v6_domain",
        "ssm_v6_targets",
        "flow_log_v6_destination",
    }
    assert all(r["before_hash"] != r["after_hash"] for r in records)
    docs = PackageDocuments.parse(result)
    assert not any(d.parse_error for d in docs.documents.values())
    content = "".join(result.values())
    assert "domain" in content and "InstanceIds" in content
    assert "aws_cloudwatch_log_group.flow.arn" in content
    assert "echo test" in content
    if style == "hcl":
        assert (
            "# preserve this comment" in content
            and "# preserve target expression" in content
        )
        assert "values = [var.instance_id]" in content
    assert repair_equivalents(result) == (result, [])


@pytest.mark.parametrize(
    "version,source",
    [
        ("~> 5.100", "hashicorp/aws"),
        ("~> 7.0", "hashicorp/aws"),
        ("~> 6.68", "other/aws"),
        ("invalid", "hashicorp/aws"),
    ],
)
def test_v5_unknown_versions_and_custom_sources_are_untouched(version, source):
    files = {
        **provider(version, source),
        "terraform/main.tf": 'resource "aws_eip" "nat" { vpc = true }',
    }
    assert repair_v6_equivalents(files) == (files, [])


@pytest.mark.parametrize(
    "body", ["vpc = false", "vpc = var.vpc", 'vpc = true\n domain = "vpc"']
)
def test_eip_dynamic_false_and_conflicting_domain_skip(body):
    files = {
        **provider(),
        "terraform/main.tf": 'resource "aws_eip" "nat" {\n' + body + "\n}",
    }
    assert repair_v6_equivalents(files) == (files, [])


@pytest.mark.parametrize(
    "body",
    [
        'instance_id = "i-test"\n targets { key = "InstanceIds"\n'
        ' values = ["i-other"] }',
        "instance_id = null",
        'instance_id = "*"',
        'log_group_name = "literal-name"',
        "log_group_name = aws_cloudwatch_log_group.missing.name",
    ],
)
def test_ambiguous_targets_and_unbound_log_destinations_skip(body):
    typ = "aws_flow_log" if body.startswith("log_group") else "aws_ssm_association"
    files = {
        **provider(),
        "terraform/main.tf": f'resource "{typ}" "one" {{\n{body}\n}}',
    }
    assert repair_v6_equivalents(files) == (files, [])


def test_module_isolation_resolved_workspace_version_and_malformed_input():
    files = {
        **provider(),
        "terraform/main.tf": 'resource "aws_eip" "nat" { vpc = true }',
        "terraform/child/providers.tf": provider("~> 5.100")["terraform/providers.tf"],
        "terraform/child/main.tf": 'resource "aws_eip" "nat" { vpc = true }',
    }
    result, records = repair_v6_equivalents(files)
    assert (
        len(records) == 1
        and result["terraform/child/main.tf"] == files["terraform/child/main.tf"]
    )
    workspace = ValidationWorkspace()
    try:
        with workspace.activate():
            workspace.resolved["terraform"] = {"aws": "5.100.0"}
            assert repair_v6_equivalents(files) == (files, [])
    finally:
        workspace.close()
    files["terraform/broken.tf"] = "resource {"
    assert repair_v6_equivalents(files) == (files, [])


def test_duplicate_json_keys_and_duplicate_hcl_attributes_skip():
    files = {
        **provider(),
        "terraform/main.tf.json": '{"resource":{"aws_eip":{"nat":'
        '{"vpc":true,"vpc":true}}}}',
    }
    assert repair_v6_equivalents(files) == (files, [])
    files = {
        **provider(),
        "terraform/main.tf": 'resource "aws_eip" "nat" {\n vpc = true\n vpc = true\n}',
    }
    assert repair_v6_equivalents(files) == (files, [])


@pytest.mark.parametrize(
    "mode,failed,accepted",
    [
        ("clean", False, True),
        ("clean", True, False),
        ("new_blocker", False, False),
        ("unavailable", False, False),
    ],
)
async def test_v6_proposals_use_unchanged_validity_and_security_guards(
    mode, failed, accepted
):
    files = {
        **provider(),
        "terraform/main.tf": 'resource "aws_eip" "nat" { vpc = true }',
    }
    result, _, records = await checked_one(
        files,
        plan("EC2"),
        Variant.COST,
        report(True),
        Engine(failed),
        SimpleNamespace(scanner=Scanner(mode), terraform_verifier=Verifier()),
        AgentBudget(30),
        repair_v6_equivalents,
    )
    assert (result != files) is accepted
    assert records[0]["outcome"] == ("accepted" if accepted else "rejected")
