# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""The Playwright cancellation barrier requires explicit stub test mode."""

import pytest

from app.domain.enums import LLMProvider
from app.pipeline.demo_stub import PipelineDemoStub
from tests.e2e_server import configure_cancel_barrier
from tests.unit.test_config import _settings


@pytest.mark.req("FR-UI-02")
@pytest.mark.parametrize(
    ("bootstrap", "provider"),
    [(None, LLMProvider.STUB), ("0", LLMProvider.STUB), ("1", LLMProvider.OPENAI)],
)
def test_e2e_cancel_barrier_is_off_by_default(monkeypatch, bootstrap, provider):
    if bootstrap is None:
        monkeypatch.delenv("INFRAARCH_TEST_BOOTSTRAP", raising=False)
    else:
        monkeypatch.setenv("INFRAARCH_TEST_BOOTSTRAP", bootstrap)
    send = PipelineDemoStub.send_prompt
    configure_cancel_barrier(_settings(llm_provider=provider))
    assert PipelineDemoStub.send_prompt is send
