"""FR-A-01 / PR-01 / NFR-01: explicit experiment configuration."""

from types import SimpleNamespace

import pytest

from scripts.run_phase9_benchmarks import architect_override

pytestmark = pytest.mark.req("FR-A-01", "PR-01", "NFR-01")


def test_architect_override_is_sparse_and_explicit():
    assert architect_override(SimpleNamespace()) == {}
    assert architect_override(
        SimpleNamespace(architect_model="test-only/model", architect_thinking="medium")
    ) == {
        "agent_models": {
            "architect": {"model": "test-only/model", "thinking_mode": "medium"}
        }
    }
    with pytest.raises(ValueError, match="explicit ARCHITECT_MODEL"):
        architect_override(SimpleNamespace(architect_thinking="medium"))
