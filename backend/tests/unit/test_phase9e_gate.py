"""FR-G-02/FR-V-03: targeted repairs, early parsing and warm initialization."""

import json
from copy import deepcopy

import pytest

from app.domain.plan import DeploymentPlan
from app.pipeline.demo_stub import DEMO_PLAN
from app.scanners.runner import ToolFailure, ToolResult
from app.validation.engine import ValidationEngine
from app.validation.gate import GenerationGate, syntax_checks
from app.validation.idioms import repair_idioms
from app.validation.workspace import ValidationWorkspace

pytestmark = pytest.mark.req("FR-G-02", "FR-V-03", "NFR-01", "PR-05")


def test_idioms_preserve_scope_and_are_idempotent():
    source = """resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id
  ingress { # intended empty
  }
  egress {}
}
resource "aws_security_group" "other" { ingress {} }
resource "aws_flow_log" "main" {
  log_format = "${version} $${account-id} ${var.custom} ${unknown}"
}
"""
    files = {"terraform/main.tf": source, "README.md": "${version}"}
    repaired, records = repair_idioms(files)
    assert len(records) == 3
    assert (
        'resource "aws_security_group" "other" { ingress {} }'
        in repaired["terraform/main.tf"]
    )
    assert (
        '"$${version} $${account-id} ${var.custom} ${unknown}"'
        in repaired["terraform/main.tf"]
    )
    assert repaired["README.md"] == "${version}"
    assert repair_idioms(repaired) == (repaired, [])


def test_idioms_heredoc_nonempty_rules_and_json():
    files = {
        "terraform/main.tf": """resource "aws_default_security_group" "x" {
 ingress { from_port = 80 }
}
resource "aws_flow_log" "x" {
 log_format = <<EOF
${version} ${srcaddr}
EOF
}
""",
        "terraform/other.tf.json": json.dumps(
            {
                "resource": {
                    "aws_default_security_group": {
                        "json": {"vpc_id": "keep", "ingress": [{}], "egress": [{}]}
                    },
                    "aws_flow_log": {
                        "json": {"log_format": "${version} ${var.custom}"}
                    },
                }
            }
        ),
    }
    repaired, records = repair_idioms(files)
    assert "ingress { from_port = 80 }" in repaired["terraform/main.tf"]
    assert "$${version} $${srcaddr}" in repaired["terraform/main.tf"]
    resource = json.loads(repaired["terraform/other.tf.json"])["resource"]
    assert resource["aws_default_security_group"]["json"] == {"vpc_id": "keep"}
    assert resource["aws_flow_log"]["json"]["log_format"] == "$${version} ${var.custom}"
    assert repair_idioms(repaired) == (repaired, [])
    assert len(records) == 3


@pytest.mark.parametrize(
    "path,content",
    [
        ("terraform/main.tf", "resource {"),
        ("k8s/app.yaml", "a: ["),
        ("monitoring/grafana/app.json", "{"),
        ("helm/app/values.json", "{"),
    ],
)
def test_all_type_syntax_failures(path, content):
    assert syntax_checks({path: content})[0].file_path == path
    assert not syntax_checks({path: content, "README.md": "text"}, {"README.md"})


def test_multi_document_yaml_is_parsed():
    assert not syntax_checks({"k8s/app.yaml": "a: 1\n---\nb: 2\n"})
    assert syntax_checks({"k8s/app.yaml": "a: 1\n---\nb: [\n"})


class Runner:
    def __init__(self, fail_init=False):
        self.calls = []
        self.fail_init = fail_init

    async def run_command(self, tool, args, root, **kwargs):
        self.calls.append((tool, args, root, kwargs))
        if tool == "terraform":
            if args[1] == "init":
                return ToolResult(
                    "", "syntax" if self.fail_init else "", int(self.fail_init), 0.0
                )
            if args[1] == "validate":
                return ToolResult('{"valid":true,"diagnostics":[]}', "", 0, 0.0)
            return ToolResult("", "", 0, 0.0)
        raise ToolFailure(tool, "not_installed")


def plan():
    value = deepcopy(DEMO_PLAN)
    value["file_types"] = ["terraform"]
    return DeploymentPlan.model_validate(value)


def engine(tmp_path, runner):
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    (mirror / "test_linux_amd64.zip").touch()
    return ValidationEngine(runner, mirror=mirror, versions={})


async def test_workspace_reuses_init_and_invalidates_only_dependencies(tmp_path):
    runner = Runner()
    validator = engine(tmp_path, runner)
    workspace = ValidationWorkspace()
    files = {
        "terraform/main.tf": (
            'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }\n'
        )
    }
    try:
        with workspace.activate():
            await validator.validate(plan(), files)
            await validator.validate(
                plan(), {**files, "terraform/variables.tf": 'variable "x" {}\n'}
            )
            await validator.validate(
                plan(),
                {
                    "terraform/main.tf": files["terraform/main.tf"].replace(
                        "10.0", "10.1"
                    )
                },
            )
            assert sum(args[1] == "init" for _, args, _, _ in runner.calls) == 1
            assert [m["init_reused"] for m in workspace.terraform_metrics] == [
                False,
                True,
                True,
            ]
            await validator.validate(
                plan(),
                {
                    **files,
                    "terraform/providers.tf": (
                        "terraform { required_providers { "
                        'aws = { version = "5.100.0" } } }\n'
                    ),
                },
            )
            assert sum(args[1] == "init" for _, args, _, _ in runner.calls) == 2
            assert (
                len({str(kw["environment_dir"]) for _, _, _, kw in runner.calls}) == 1
            )
    finally:
        root = workspace.root
        workspace.close()
    assert not root.exists()


async def test_failed_init_is_not_reused_and_gate_records_it(tmp_path):
    runner = Runner(fail_init=True)
    validator = engine(tmp_path, runner)
    workspace = ValidationWorkspace()
    files = {"terraform/main.tf": 'resource "aws_vpc" "main" {}\n'}
    try:
        with workspace.activate():
            gate = GenerationGate(validator)
            first = await gate.run(plan(), files)
            await gate.run(plan(), files)
        assert not workspace.initialized
        assert sum(args[1] == "init" for _, args, _, _ in runner.calls) == 2
        assert (
            first.metrics["terraform"][0]["init_outcome"]
            == "missing_required_providers"
        )
    finally:
        workspace.close()
