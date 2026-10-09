"""Review tasks share capacity and shutdown ownership with automated runs."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domain.enums import Variant
from app.pipeline.review import ReviewService
from app.pipeline.runner import PipelineRunner
from tests.unit.test_config import _settings


@pytest.mark.req("FR-S-09", "PR-03")
async def test_retry_tasks_have_unique_ids_and_release_capacity_on_shutdown(
    monkeypatch,
):
    runner = PipelineRunner(
        capacity=2,
        factory=SimpleNamespace(settings=_settings()),
        session_factory=None,
        writer=None,
        security_stage=None,
        validation_stage=None,
    )
    entered = asyncio.Event()
    cancelled = []

    async def held(self, run_id, variant, target_files):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.append(variant)

    monkeypatch.setattr(ReviewService, "run_retry", held)
    run_id = uuid4()
    for variant in (Variant.COST, Variant.SECURITY):
        assert runner.reserve()
        runner.start_review_retry(run_id, variant, [])
    assert not runner.reserve() and len(runner.tasks) == 2
    await entered.wait()
    await runner.shutdown()
    assert set(cancelled) == {Variant.COST, Variant.SECURITY}
    assert runner.tasks == {} and runner._reserved == 0
