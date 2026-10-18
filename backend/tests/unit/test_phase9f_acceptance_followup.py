"""FR-S-03/FR-V-03/NFR-01: corrective guard regressions."""

import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.agents.generators.security import SecurityGeneratorAgent
from app.agents.security.agent import SecurityAgent
from app.domain.enums import PackageStatus, Variant
from app.pipeline.orchestrator import PipelineOrchestrator
from tests.unit.test_security_partial import setup

pytestmark = pytest.mark.req("FR-S-03", "FR-V-03", "NFR-01")


async def test_deleted_variable_with_unchanged_consumer_is_rejected():
    files = {
        "terraform/main.tf": 'output "x" { value = var.name }',
        "terraform/variables.tf": 'variable "name" { default = "keep" }',
    }
    guard, checkpoint = setup(files)
    result = await guard.evaluate(
        files,
        {**files, "terraform/variables.tf": "\n"},
        await guard.checks(files),
        checkpoint.scan,
    )
    assert result.reason == "reference_regression"


async def test_equal_count_replacement_syntax_error_is_rejected():
    files = {"terraform/main.tf": 'output "x" { value = 1 description = "old" }'}
    guard, checkpoint = setup(files)
    candidate = {
        "terraform/main.tf": 'output "x" { value = 1 }\n'
        'output "y" { value = 2 description = "new" }'
    }
    result = await guard.evaluate(
        files, candidate, await guard.checks(files), checkpoint.scan
    )
    assert result.reason == "invalid_syntax"


async def test_publication_is_clipped_to_iteration_deadline(monkeypatch):
    security = object.__new__(SecurityAgent)
    entered = asyncio.Event()

    async def blocked(*args):
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(security, "_publish_iteration_inside", blocked)
    record = {"_iteration_deadline": 60.0}
    await security._publish_iteration(
        SimpleNamespace(clock=lambda: 59.9), Variant.SECURITY, record, 1, 0
    )
    assert entered.is_set() and record["publication_deadline"]
    assert "_iteration_deadline" not in record
    assert record["publication_seconds"] >= 0


@pytest.mark.req("FR-G-02", "PR-05")
@pytest.mark.parametrize("status", [PackageStatus.GENERATING, PackageStatus.GENERATED])
async def test_generator_publication_shares_absolute_deadline(status):
    generator = object.__new__(SecurityGeneratorAgent)
    generator.deadline_seconds = 0.01
    generator._last_run = None
    pipeline = object.__new__(PipelineOrchestrator)
    pipeline.clock = time.monotonic
    pipeline.workspaces = {}
    pipeline.run_id = "test"
    pipeline.writer = SimpleNamespace(
        package_transition=AsyncMock(), agent_state=AsyncMock()
    )
    pipeline._package_status = AsyncMock(return_value=status)
    pipeline._generation_failed = AsyncMock()

    async def blocked(*args):
        await asyncio.Event().wait()

    pipeline._generate_inside = blocked
    try:
        assert await pipeline._generate(generator, None) == (Variant.SECURITY, None)
        if status == PackageStatus.GENERATING:
            pipeline._generation_failed.assert_awaited_once()
        else:
            assert [
                call.args[2]
                for call in pipeline.writer.package_transition.await_args_list
            ] == [PackageStatus.SCANNING, PackageStatus.SCAN_ERROR]
            assert (
                pipeline.writer.agent_state.await_args.kwargs["failure_category"]
                == "deadline"
            )
    finally:
        for workspace in pipeline.workspaces.values():
            workspace.close()
