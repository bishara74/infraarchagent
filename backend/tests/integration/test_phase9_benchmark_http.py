"""Public HTTP harness against a real PostgreSQL-backed stub pipeline."""

import httpx
import pytest

from app.core.config import get_settings
from app.main import create_app
from scripts.benchmark import Harness
from tests.integration.test_pipeline_orchestrator import FakeSecurity, FakeValidation


@pytest.mark.req("PR-01", "PR-03", "PR-05", "NFR-01")
async def test_harness_runs_public_stub_api_and_concurrent_cohort(db_engines, tmp_path):
    settings = get_settings().model_copy(update={"llm_api_key": None, "api_key": None})
    app = create_app(settings, db_engines[0])
    app.state.runner.security_stage = FakeSecurity()
    app.state.runner.validation_stage = FakeValidation()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test", timeout=30
    ) as client:
        harness = Harness(client, base_url="http://test", output=tmp_path, timeout=30)
        await harness.pr01(1)
        await harness.pr03()
    assert len(harness.rows) == 5
    assert all(
        row["complete"] and row["provider"] == row["model"] == "stub"
        for row in harness.rows
    )
    assert all(row["run_status"] == "success" for row in harness.rows)
    cohort = [row for row in harness.rows if row.get("role") == "cohort"]
    assert len(cohort) == 3 and all(row["ratio_to_baseline"] > 0 for row in cohort)
    assert all(row["pr01_reference_count"] == 1 for row in cohort)
    assert all(row["cost_attribution"] == "not attributed" for row in cohort)
    assert {row["agent"] for row in harness.agent_rows} >= {
        "architect",
        "generator_cost",
        "generator_performance",
        "generator_security",
        "security_iteration",
    }
    assert all(
        "sk-" not in path.read_text() for path in tmp_path.rglob("*") if path.is_file()
    )
