import asyncio
import logging
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
    rate_limit_wait,
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


@pytest.mark.req("FR-A-04", "NFR-01")
@pytest.mark.parametrize(
    ("outcome", "step", "expected_error"),
    [
        ("success", '{"ok":true}', None),
        ("timeout", TimeoutError(), LLMRetryExhausted),
        ("cancelled", asyncio.CancelledError(), asyncio.CancelledError),
        ("transient", LLMTransientError("transient"), LLMRetryExhausted),
        ("rate_limit", LLMTransientError("rate_limit"), LLMRetryExhausted),
        ("server", LLMTransientError("server"), LLMRetryExhausted),
        ("connection", LLMTransientError("connection"), LLMRetryExhausted),
        ("invalid_json", "not JSON", LLMRetryExhausted),
        (
            "truncated",
            LLMResponse('{"ok":true}', stop_reason="max_tokens"),
            LLMRetryExhausted,
        ),
        ("deadline", LLMDeadlineExceeded(1, 0), LLMDeadlineExceeded),
        ("request", LLMPermanentError("request"), LLMPermanentError),
        ("unexpected", RuntimeError("hidden error text"), LLMPermanentError),
    ],
)
async def test_attempt_log_is_parseable_for_every_outcome(
    outcome: str,
    step: str | LLMResponse | BaseException,
    expected_error: type[BaseException] | None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.llm.base")
    adapter = StubAdapter(policy=RetryPolicy(30, 1, 150, 0, 100), script=[step])
    if expected_error is None:
        await adapter.complete_json("prompt", system="rules")
    else:
        with pytest.raises(expected_error):
            await adapter.complete_json("prompt", system="rules")
    lines = [
        record.getMessage()
        for record in caplog.records
        if record.name == "app.llm.base"
    ]
    assert len(lines) == 1
    assert "  " not in lines[0]
    parsed = dict(field.split("=", 1) for field in lines[0].split(" "))
    assert set(parsed) == {
        "provider",
        "model",
        "attempt",
        "outcome",
        "reasoning_effort",
        "latency",
        "input_tokens",
        "output_tokens",
        "prompt_chars",
        "system_chars",
        "retry_after",
        "rate_limit_headers",
    }
    assert parsed["outcome"] == outcome
    assert parsed["reasoning_effort"] == "unset"
    assert parsed["prompt_chars"] == "6"
    assert parsed["system_chars"] == "5"


@pytest.mark.req("PR-05")
async def test_per_call_overrides_and_none_keep_policy_defaults() -> None:
    class RecordingAdapter(StubAdapter):
        async def send_prompt(
            self,
            prompt: str,
            *,
            system: str | None = None,
            max_output_tokens: int,
            timeout: float,
        ) -> LLMResponse:
            self.calls.append((max_output_tokens, timeout))
            return await super().send_prompt(
                prompt,
                system=system,
                max_output_tokens=max_output_tokens,
                timeout=timeout,
            )

    adapter = RecordingAdapter(policy=RetryPolicy(30, 3, 150, 0, 100))
    adapter.calls = []
    await adapter.complete_json("x", attempt_timeout=120, max_output_tokens=32000)
    await adapter.complete_json("x", deadline=5, attempt_timeout=120)
    await adapter.complete_json("x", attempt_timeout=None, max_output_tokens=None)
    assert adapter.calls == [(32000, 120), (100, pytest.approx(5)), (100, 30)]


@pytest.mark.parametrize("override", [0, -1, float("inf"), float("nan")])
async def test_invalid_attempt_timeout_override(override: float) -> None:
    with pytest.raises(ValueError):
        await StubAdapter().complete_json("x", attempt_timeout=override)


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
        ("7.66s", 7.66),
        ("1m2.5s", 62.5),
        ("250ms", 0.25),
        ("1m", 60.0),
        ("20s", 20.0),
        ("1m2.5s-extra", None),
        ("1h", None),
        ("-1s", None),
        ("-1m2s", None),
    ],
)
def test_retry_after_parses_only_nonnegative_finite_seconds(
    header: str | None, expected: float | None
) -> None:
    assert parse_retry_after(header) == expected


@pytest.mark.req("FR-A-04", "PR-05")
def test_rate_limit_reset_fallback_and_priority() -> None:
    assert rate_limit_wait(
        {
            "retry-after": "7.66s",
            "x-ratelimit-reset-tokens": "1m2.5s",
            "x-ratelimit-reset-requests": "250ms",
        }
    ) == (
        7.66,
        (
            "retry-after",
            "x-ratelimit-reset-tokens",
            "x-ratelimit-reset-requests",
        ),
    )
    assert (
        rate_limit_wait(
            {
                "retry-after": "invalid",
                "x-ratelimit-reset-tokens": "1m2.5s",
                "x-ratelimit-reset-requests": "250ms",
            }
        )[0]
        == 62.5
    )
    assert (
        rate_limit_wait(
            {
                "x-ratelimit-reset-tokens": "bad",
                "x-ratelimit-reset-requests": "250ms",
            }
        )[0]
        == 0.25
    )
    assert (
        rate_limit_wait(
            {
                "retry-after": "bad",
                "x-ratelimit-reset-tokens": "nan",
                "x-ratelimit-reset-requests": "-2s",
            }
        )[0]
        is None
    )
