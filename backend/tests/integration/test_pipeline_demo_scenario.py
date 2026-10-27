"""FR-UI-07: deterministic validation-only review and real-agent repair."""

import asyncio

import pytest

from app.agents.validator import ValidatorAgent
from app.core.config import get_settings
from app.domain.enums import LLMProvider
from app.main import create_app
from app.validation.engine import ValidationEngine
from tests.integration.test_pipeline_api import _empty_scanner
from tests.integration.test_pipeline_review import client_for
from tests.unit.test_validation_engine import Clean, mirror


@pytest.mark.req("FR-V-01", "FR-S-08", "FR-S-09", "FR-UI-07", "NFR-01")
async def test_review_demo_retries_to_ready_and_preserves_audit(db_engines, tmp_path):
    app = create_app(
        get_settings().model_copy(update={"pipeline_demo_scenario": "review"}),
        db_engines[0],
    )
    app.state.runner.factory.scanner = _empty_scanner(6)
    app.state.runner.validation_stage = ValidatorAgent(
        ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={}),
        app.state.session_factory,
    )
    async with app.router.lifespan_context(app), client_for(app) as client:
        accepted = await client.post(
            "/api/pipeline/run",
            json={"text": "Deploy an AWS web service", "config": {"provider": "stub"}},
        )
        assert accepted.status_code == 202
        run_id = accepted.json()["run_id"]
        await asyncio.gather(*app.state.runner.tasks.values())
        url = f"/api/pipeline/{run_id}/results"
        before = (await client.get(url)).json()
        assert before["run"]["status"] == "partial_success"
        assert [p["status"] for p in before["packages"]] == [
            "checks_passed",
            "checks_passed",
            "pending_review",
        ]
        package = before["packages"][2]
        assert package["review_reasons"] == ["validation_failed"]
        assert package["retry_targets"] == ["terraform/main.tf"]
        retry = await client.post(
            f"/api/pipeline/{run_id}/packages/security/review",
            json={"action": "retry", "feedback": "Declare the missing local."},
        )
        assert retry.status_code == 202
        await asyncio.gather(*app.state.runner.tasks.values())
        after = (await client.get(url)).json()
        assert {k: v for k, v in after["run"].items() if k != "lessons"} == {
            k: v for k, v in before["run"].items() if k != "lessons"
        }
        previous_calls = {c["call_id"]: c for c in before["run"]["lessons"]["calls"]}
        current_calls = {c["call_id"]: c for c in after["run"]["lessons"]["calls"]}
        assert all(current_calls[key] == value for key, value in previous_calls.items())
        new_calls = [c for key, c in current_calls.items() if key not in previous_calls]
        assert new_calls and all(
            c["role"] == "fixer" and not c["enabled"] for c in new_calls
        )
        assert after["run"]["lessons"]["used_lesson_ids"] == []
        assert after["packages"][:2] == before["packages"][:2]
        fixed = after["packages"][2]
        assert fixed["status"] == "checks_passed"
        assert fixed["retry_in_progress"] is False
        assert fixed["original_files"] == package["original_files"]
        assert fixed["validation_report"]["summary"]["result"] == "valid"
        assert fixed["security_report"]["sessions"][-1]["kind"] == "review_retry"
        assert (
            await client.get(f"/api/pipeline/{run_id}/download/security")
        ).status_code == 200


@pytest.mark.req("NFR-01")
async def test_review_demo_warns_for_real_default_provider(db_engines, caplog):
    app = create_app(
        get_settings().model_copy(
            update={
                "llm_provider": LLMProvider.OPENAI,
                "pipeline_demo_scenario": "review",
            }
        ),
        db_engines[0],
    )
    async with app.router.lifespan_context(app):
        pass
    assert "PIPELINE_DEMO_SCENARIO=review is ignored for non-stub runs" in caplog.text
