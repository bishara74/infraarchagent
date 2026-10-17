"""FR-S-01/02: fix calls overlap and obey the shared concurrency cap."""

import asyncio
from typing import Any
from uuid import uuid4

import pytest

from app.agents.budget import AgentBudget
from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixProposal
from app.core.config import get_settings
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.pipeline.demo_stub import DEMO_PLAN
from app.pipeline.stages import StageContext


@pytest.mark.req("FR-S-02")
async def test_three_file_fixes_overlap_and_limit_active_calls() -> None:
    started = asyncio.Event()
    release = asyncio.Event()

    class WaitingFix:
        def __init__(self) -> None:
            self.active = 0
            self.peak = 0
            self.calls: list[str] = []

        async def propose(self, **kwargs: Any) -> FixProposal:
            path: str = kwargs["path"]
            self.calls.append(path)
            self.active += 1
            self.peak = max(self.peak, self.active)
            if len(self.calls) == 2:
                started.set()
            await release.wait()
            self.active -= 1
            return FixProposal(
                path, True, None, kwargs["files"][path] + "# fixed\n", {}, ()
            )

    fixer = WaitingFix()
    settings = get_settings()
    security = SecurityAgent(  # type: ignore[arg-type]
        None, fixer, None, settings, semaphore=asyncio.Semaphore(2)
    )
    plan = DeploymentPlan.model_validate(DEMO_PLAN)
    ctx = StageContext(uuid4(), None, plan)  # type: ignore[arg-type]
    files = {
        "terraform/module-a/a.tf": "# a\n",
        "terraform/module-b/b.tf": "# b\n",
        "terraform/module-c/c.tf": "# c\n",
        "terraform/untouched.tf": "# unchanged\n",
    }
    targets = {path: [] for path in files if path != "terraform/untouched.tf"}
    task = asyncio.create_task(
        security._fix_pass(
            ctx,
            Variant.SECURITY,
            files,
            targets,
            AgentBudget(30),
            feedback=None,
            validation_failures=[],
        )
    )
    await asyncio.wait_for(started.wait(), 2)
    assert len(fixer.calls) == 2
    assert fixer.peak == 2
    release.set()
    final, results, diff = await asyncio.wait_for(task, 2)
    assert len(fixer.calls) == 3
    assert all(item["accepted"] for item in results)
    assert final["terraform/untouched.tf"] == files["terraform/untouched.tf"]
    assert "untouched.tf" not in diff


@pytest.mark.req("FR-S-02", "FR-S-09")
async def test_shared_editable_context_is_serialized_and_refreshed():
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []

    class Fix:
        async def propose(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                entered.set()
                await release.wait()
            else:
                assert kwargs["files"]["terraform/a.tf"].endswith("# fixed\n")
            return FixProposal(
                kwargs["path"],
                True,
                None,
                kwargs["files"][kwargs["path"]] + "# fixed\n",
                {},
                (),
            )

    files = {"terraform/a.tf": "# a\n", "terraform/b.tf": "# b\n"}
    security = SecurityAgent(None, Fix(), None, get_settings())
    ctx = StageContext(uuid4(), None, DeploymentPlan.model_validate(DEMO_PLAN))
    task = asyncio.create_task(
        security._fix_pass(
            ctx,
            Variant.SECURITY,
            files,
            dict.fromkeys(files, []),
            AgentBudget(30),
            feedback=None,
            validation_failures=[],
        )
    )
    await asyncio.wait_for(entered.wait(), 2)
    assert len(calls) == 1
    release.set()
    await asyncio.wait_for(task, 2)
    assert len(calls) == 2


@pytest.mark.req("FR-S-02", "FR-S-09")
@pytest.mark.parametrize("review_order", [False, True])
async def test_review_category_order_keeps_automated_sorted_order(review_order):
    calls = []

    class Fix:
        async def propose(self, **kwargs):
            calls.append(kwargs["path"])
            return FixProposal(kwargs["path"], False, "no_changes", None, {}, ())

    security = SecurityAgent(
        None, Fix(), None, get_settings(), semaphore=asyncio.Semaphore(1)
    )
    ctx = StageContext(uuid4(), None, DeploymentPlan.model_validate(DEMO_PLAN))
    files = {"terraform/z.tf": "z", "terraform/a.tf": "a"}
    _, results, _ = await security._fix_pass(
        ctx,
        Variant.COST,
        files,
        {path: [] for path in files},
        AgentBudget(30),
        feedback=None,
        validation_failures=[],
        review_target_order=review_order,
    )
    assert calls == (list(files) if review_order else sorted(files))
    assert [result["file"] for result in results] == sorted(files)
