import asyncio
import random
from typing import Any

import pytest

from app.llm.base import (
    LLMAdapter,
    LLMResponse,
    RetryPolicy,
    extract_json_object,
)
from app.llm.errors import (
    LLMDeadlineExceeded,
    LLMPermanentError,
    LLMResponseFormatError,
    LLMRetryExhausted,
    LLMTransientError,
    parse_retry_after,
)
from app.llm.stub import StubAdapter


class FakeClock:
    def __init__(self) -> None:
        self.time = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.time

    async def sleep(self, duration: float) -> None:
        self.sleeps.append(duration)
        self.time += duration


@pytest.mark.req("NFR-03", "FR-I-04")
async def test_minimal_adapter_uses_concrete_retry_wrapper() -> None:
    class MinimalAdapter(LLMAdapter):
        async def send_prompt(
            self,
            prompt: str,
            *,
            system: str | None = None,
            max_output_tokens: int,
            timeout: float,
        ) -> LLMResponse:
            step = self.steps.pop(0)
            self.timeouts.append(timeout)
            if isinstance(step, BaseException):
                raise step
            return step

        def parse_response(self, response: LLMResponse) -> dict[str, Any]:
            return extract_json_object(response.text)

    clock = FakeClock()
    adapter = MinimalAdapter(
        "test",
        RetryPolicy(30, 3, 150, 1, 100),
        sleep=clock.sleep,
        clock=clock.now,
        rng=random.Random(0),
    )
    adapter.steps = [LLMTransientError(), LLMResponse('{"ok":true}')]
    adapter.timeouts = []
    result = await adapter.complete_json("prompt")
    assert result.data == {"ok": True}
    assert result.attempts == 2
    assert adapter.timeouts == [30, 30]
    assert 0 <= clock.sleeps[0] <= 1


@pytest.mark.req("NFR-03")
async def test_success_invalid_json_and_truncation() -> None:
    clock = FakeClock()
    policy = RetryPolicy(30, 3, 150, 0, 100)
    first = StubAdapter(
        policy=policy, script=['{"ok":1}'], sleep=clock.sleep, clock=clock.now
    )
    assert (await first.complete_json("first")).attempts == 1
    adapter = StubAdapter(
        policy=policy,
        script=[
            "not JSON",
            LLMResponse('{"ok":0}', stop_reason="max_tokens"),
            '{"ok":2}',
        ],
        sleep=clock.sleep,
        clock=clock.now,
    )
    assert (await adapter.complete_json("retry")).attempts == 3
    assert adapter.prompts == ["retry"] * 3


@pytest.mark.req("NFR-03")
async def test_invalid_json_then_valid_json_succeeds_on_second_attempt() -> None:
    adapter = StubAdapter(
        policy=RetryPolicy(30, 3, 150, 0, 100),
        script=["not JSON", '{"ok":true}'],
    )
    assert (await adapter.complete_json("x")).attempts == 2


@pytest.mark.req("FR-A-04", "PR-05")
async def test_attempt_timeout_then_success() -> None:
    adapter = StubAdapter(
        policy=RetryPolicy(0.005, 2, 1, 0, 100),
        script=[(0.1, '{"late":true}'), '{"ok":true}'],
    )
    assert (await adapter.complete_json("x")).attempts == 2


@pytest.mark.req("FR-A-04", "PR-05")
async def test_retry_exhaustion_and_permanent_failure() -> None:
    clock = FakeClock()
    policy = RetryPolicy(30, 3, 150, 0, 100)
    exhausted = StubAdapter(
        policy=policy,
        script=[LLMTransientError()] * 3,
        sleep=clock.sleep,
        clock=clock.now,
    )
    with pytest.raises(LLMRetryExhausted) as captured:
        await exhausted.complete_json("x")
    assert captured.value.attempts == 3
    assert captured.value.last_category == "transient"
    permanent = StubAdapter(
        policy=policy,
        script=[LLMPermanentError("request"), '{"ok":true}'],
        sleep=clock.sleep,
        clock=clock.now,
    )
    with pytest.raises(LLMPermanentError):
        await permanent.complete_json("x")
    assert len(permanent.prompts) == 1
    assert clock.sleeps == []


@pytest.mark.req("FR-A-04", "PR-05")
async def test_deadline_clips_second_attempt_and_prevents_third() -> None:
    class TimeoutAdapter(LLMAdapter):
        async def send_prompt(
            self,
            prompt: str,
            *,
            system: str | None = None,
            max_output_tokens: int,
            timeout: float,
        ) -> LLMResponse:
            self.timeouts.append(timeout)
            await self._sleep(timeout)
            raise TimeoutError

        def parse_response(self, response: LLMResponse) -> dict[str, Any]:
            return extract_json_object(response.text)

    for deadline in (150, 40):
        clock = FakeClock()
        adapter = TimeoutAdapter(
            "test",
            RetryPolicy(30, 3, deadline, 1, 100),
            sleep=clock.sleep,
            clock=clock.now,
            rng=random.Random(0),
        )
        adapter.timeouts = []
        with pytest.raises((LLMRetryExhausted, LLMDeadlineExceeded)):
            await adapter.complete_json("x")
        assert clock.time <= deadline
        if deadline == 40:
            assert len(adapter.timeouts) == 2
            assert 0 < adapter.timeouts[1] < 10


@pytest.mark.req("FR-A-04", "PR-05")
async def test_backoff_does_not_cross_deadline() -> None:
    clock = FakeClock()
    adapter = StubAdapter(
        policy=RetryPolicy(1, 3, 0.1, 100, 100),
        script=[LLMTransientError()] * 3,
        sleep=clock.sleep,
        clock=clock.now,
        rng=random.Random(0),
    )
    with pytest.raises(LLMDeadlineExceeded):
        await adapter.complete_json("x")
    assert clock.time == 0.1
    assert len(adapter.prompts) == 1


@pytest.mark.req("NFR-03")
async def test_cancellation_is_not_retried() -> None:
    adapter = StubAdapter(script=[asyncio.CancelledError()])
    with pytest.raises(asyncio.CancelledError):
        await adapter.complete_json("x")
    assert len(adapter.prompts) == 1


@pytest.mark.req("NFR-03")
async def test_exhausted_stub_script_is_safe_and_not_retried() -> None:
    adapter = StubAdapter(script=[])
    with pytest.raises(LLMPermanentError, match="stub_script_exhausted"):
        await adapter.complete_json("x")
    assert len(adapter.prompts) == 1


@pytest.mark.req("NFR-03")
@pytest.mark.parametrize(
    "source,expected",
    [
        (' {"a":1} ', {"a": 1}),
        ('```json\n{"a":1}\n```', {"a": 1}),
        ('  ```\n{"a":1}\n```  ', {"a": 1}),
    ],
)
def test_extract_json_accepts_one_object(source: str, expected: dict[str, Any]) -> None:
    assert extract_json_object(source) == expected


@pytest.mark.req("NFR-03")
@pytest.mark.parametrize(
    "source",
    [
        "",
        "[]",
        "42",
        "null",
        "broken",
        'before {"a":1}',
        '{"a":1} after',
        "```json\n{}\n```\n```json\n{}\n```",
    ],
)
def test_extract_json_rejects_non_object_or_extra_text(source: str) -> None:
    with pytest.raises(LLMResponseFormatError):
        extract_json_object(source)


@pytest.mark.req("FR-A-04", "PR-05")
@pytest.mark.parametrize(
    "header,expected",
    [
        (None, None),
        ("", None),
        ("soon", None),
        ("nan", None),
        ("inf", None),
        ("-1", None),
        ("20", 20.0),
        ("0.5", 0.5),
    ],
)
def test_retry_after_parses_only_nonnegative_finite_seconds(
    header: str | None, expected: float | None
) -> None:
    assert parse_retry_after(header) == expected
