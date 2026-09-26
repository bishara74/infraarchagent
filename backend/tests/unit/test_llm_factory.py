import httpx2
import pytest

from app.core.config import Settings
from app.llm import factory as factory_module
from app.llm.anthropic import AnthropicAdapter
from app.llm.base import RetryPolicy
from app.llm.errors import LLMConfigurationError
from app.llm.factory import build_adapter
from app.llm.openai import OpenAIAdapter
from app.llm.stub import StubAdapter


def settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "postgresql+asyncpg://app:secret@localhost/db",
        "migration_database_url": "postgresql+asyncpg://owner:secret@localhost/db",
        "test_database_url": "postgresql+asyncpg://app:secret@localhost/test",
        "test_migration_database_url": "postgresql+asyncpg://owner:secret@localhost/test",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.mark.req("FR-I-04", "NFR-03")
def test_factory_selects_provider_and_overrides_model_and_policy() -> None:
    configured = settings(
        llm_provider="anthropic", llm_model="configured", llm_api_key="placeholder"
    )
    policy = RetryPolicy(240, 1, 240, 0, 12000)
    anthropic = build_adapter(configured)
    assert isinstance(anthropic, AnthropicAdapter)
    assert anthropic.model == "configured"
    assert anthropic.policy.max_attempts == 3
    openai = build_adapter(
        configured, provider="openai", model="override", policy=policy
    )
    assert isinstance(openai, OpenAIAdapter)
    assert openai.model == "override"
    assert openai.policy is policy


@pytest.mark.req("FR-I-04", "NFR-03")
async def test_stub_needs_neither_key_nor_model() -> None:
    adapter = build_adapter(settings())
    assert isinstance(adapter, StubAdapter)
    assert (await adapter.complete_json("x")).data["files"] == {"stub.txt": "ok"}


@pytest.mark.req("FR-I-04")
def test_real_provider_requires_key_and_model() -> None:
    with pytest.raises(LLMConfigurationError, match="LLM_MODEL"):
        build_adapter(settings(), provider="anthropic")
    with pytest.raises(LLMConfigurationError, match="LLM_API_KEY"):
        build_adapter(settings(), provider="openai", model="test")
    with pytest.raises(LLMConfigurationError, match="LLM_PROVIDER"):
        build_adapter(settings(), provider="unknown")


@pytest.mark.req("FR-I-04", "NFR-03")
@pytest.mark.parametrize(
    "base_url,expected_url",
    [
        (None, "https://api.openai.com/v1/chat/completions"),
        (
            "https://groq.test/openai/v1",
            "https://groq.test/openai/v1/chat/completions",
        ),
    ],
)
async def test_factory_base_url_reaches_openai_request(
    base_url: str | None,
    expected_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(
            200,
            json={
                "id": "chatcmpl_test",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": '{"ok":true}'},
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            },
        )

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        real_adapter = OpenAIAdapter

        def adapter_with_mock(
            model: str, policy: RetryPolicy, key: str, *, base_url: str | None
        ) -> OpenAIAdapter:
            return real_adapter(
                model, policy, key, http_client=client, base_url=base_url
            )

        monkeypatch.setattr(factory_module, "OpenAIAdapter", adapter_with_mock)
        adapter = build_adapter(
            settings(
                llm_provider="openai",
                llm_model="test-model",
                llm_api_key="placeholder",
                llm_base_url=base_url,
            )
        )
        assert (await adapter.complete_json("prompt")).data == {"ok": True}
    assert len(requests) == 1
    assert str(requests[0].url) == expected_url
