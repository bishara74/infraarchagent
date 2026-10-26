"""FR-UI-06/07: synthetic demo uses actual pipeline/review/lesson services."""

import httpx
import pytest

from app.agents.validator import ValidatorAgent
from app.core.config import get_settings
from app.domain.enums import LLMProvider
from app.main import create_app
from app.validation.engine import ValidationEngine
from scripts.phase10_demo import seed
from tests.integration.test_pipeline_api import _empty_scanner
from tests.unit.test_validation_engine import Clean, mirror

pytestmark = pytest.mark.req("FR-UI-06", "FR-UI-07", "NFR-01", "UC-08")


async def test_demo_has_all_labels_categories_approved_lesson_and_history(
    db_engines, tmp_path
):
    app = create_app(
        get_settings().model_copy(
            update={
                "llm_provider": LLMProvider.STUB,
                "pipeline_demo_scenario": "review",
                "lessons_admin_direct_activation": True,
                "api_key": None,
            }
        ),
        db_engines[0],
    )
    app.state.runner.factory.scanner = _empty_scanner(128)
    app.state.runner.validation_stage = ValidatorAgent(
        ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={}),
        app.state.session_factory,
    )
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1",
            headers={"Origin": "http://127.0.0.1"},
        ) as client,
    ):
        response = await client.post(
            "/api/auth/setup",
            json={"username": "demo-admin", "password": "phase10-demo-password"},
        )
        assert response.status_code == 200
        result = await seed(client, interval=0)
        assert result["synthetic"] is True and result["provider"] == "stub"
        labels = {label for row in result["runs"] for label in row["labels"].values()}
        assert labels == {
            "checks_passed",
            "pending_review",
            "engineer_approved",
            "rejected",
        }
        lesson = (await client.get(f"/api/lessons/{result['lesson_id']}")).json()[
            "lesson"
        ]
        assert lesson["approval"] == "admin_direct" and lesson["status"] == "approved"
        history = (await client.get("/api/reviews/history")).json()
        assert {row["category"] for row in history["items"]} == {
            "accepted_risk",
            "operability",
        }
        assert all("password" not in row for row in result["runs"])
