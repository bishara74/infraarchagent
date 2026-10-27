"""NFR-01/FR-S-01/02: refused file reads are blocking evidence, never executed."""

import json
from unittest.mock import AsyncMock

import pytest

from app.domain.enums import Variant
from app.scanners.runner import ProcessToolRunner, ToolFailure, ToolResult
from app.scanners.scan import Scanner

pytestmark = pytest.mark.req("NFR-01", "FR-S-01", "FR-S-02", "FR-V-03")


def files(expression):
    return {
        "terraform/main.tf": 'resource "aws_lambda_function" "api" {\n'
        " filename = var.lambda_zip_path\n"
        f" source_code_hash = {expression}\n"
        '}\nvariable "lambda_zip_path" {}\n'
    }


class SafeRunner:
    """Keep the actual process boundary for Terraform; record other scanners."""

    async def run(self, tool, root):
        if tool == "terraform":
            return await ProcessToolRunner(5).run(tool, root)
        return ToolResult(
            json.dumps({"passed": 0, "failed": 0, "resource_count": 0})
            if tool == "checkov"
            else '{"Results": []}',
            "",
            0,
            0,
        )


@pytest.mark.parametrize("variant", list(Variant))
@pytest.mark.parametrize(
    "expression",
    [
        "filebase64sha256(var.lambda_zip_path)",
        'filesha256("/synthetic-outside-file")',
        'file("\\u002fsynthetic-outside-file")',
    ],
)
async def test_refusal_is_blocking_and_never_launches(monkeypatch, variant, expression):
    # Dynamic hashing is copied structurally from final scenario 3, all three errors.
    launch = AsyncMock(side_effect=AssertionError("refused read launched"))
    monkeypatch.setattr("asyncio.create_subprocess_exec", launch)
    source = files(expression)
    original = dict(source)
    result = await Scanner(SafeRunner()).scan(source, variant)
    assert len(result.violations) == 1
    finding = result.violations[0]
    assert finding.rule_id == "TERRAFORM_FILE_INPUT" and finding.blocking
    assert finding.severity.value == "CRITICAL"
    assert finding.file_path == "terraform/main.tf"
    assert result.tool_status["terraform"] == "file_input_blocked"
    assert not result.syntax_limited
    assert source == original
    assert "/synthetic-outside-file" not in finding.message
    launch.assert_not_called()


async def test_unsubstantiated_refusal_stays_a_tool_error():
    class Runner(SafeRunner):
        async def run(self, tool, root):
            if tool == "terraform":
                raise ToolFailure(tool, "unsafe_file_input")
            return await super().run(tool, root)

    with pytest.raises(ToolFailure, match="unsafe_file_input"):
        await Scanner(Runner()).scan({"terraform/main.tf": "# no read\n"}, Variant.COST)


async def test_other_tool_failures_are_not_reclassified():
    class Runner:
        async def run(self, tool, root):
            raise ToolFailure(tool, "timeout")

    with pytest.raises(ToolFailure, match="timeout"):
        await Scanner(Runner()).scan(
            files("filebase64sha256(var.lambda_zip_path)"), Variant.COST
        )
