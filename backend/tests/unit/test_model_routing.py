"""FR-P-04 shared metadata lookup cases; request IDs stay separate."""

import json
from pathlib import Path

import pytest

from app.domain.model_catalogue import catalogue_id

CASES = json.loads(
    (
        Path(__file__).parents[3] / "frontend/src/test/fixtures/model-routing.json"
    ).read_text()
)


@pytest.mark.req("FR-P-04", "FR-UI-01")
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_shared_routing_metadata(case):
    assert catalogue_id(case["provider"], case["id"]) == case["catalog_id"]


@pytest.mark.req("FR-P-04", "FR-UI-01")
async def test_resolver_uses_base_evidence_and_preserves_request_id():
    from unittest.mock import AsyncMock

    from app.core.config import Settings
    from app.core.model_selection import ModelSelectionService
    from app.domain.run_config import RunConfig

    service = ModelSelectionService(None, Settings(_env_file=None), {})
    service.catalog = AsyncMock(
        return_value={
            "provider": "openrouter",
            "credential_id": None,
            "defaults": {},
            "models": [
                {
                    "id": "openai/model",
                    "structured_output": True,
                    "reasoning": True,
                    "thinking_modes": ["low"],
                }
            ],
        }
    )
    config = RunConfig.model_validate(
        {
            "agent_models": {
                "architect": {"model": "openai/model:nitro", "thinking_mode": "low"}
            }
        }
    )
    resolved = await service.resolve(config, interactive=True)
    assert resolved.resolved_agents["architect"].model == "openai/model:nitro"
    assert resolved.resolved_agents["architect"].thinking_mode == "low"
