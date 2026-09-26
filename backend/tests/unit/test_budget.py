import pytest

from app.agents.budget import AgentBudget
from app.llm.base import LLMResponse, RetryPolicy
from app.llm.errors import LLMDeadlineExceeded, LLMTransientError
from app.llm.stub import StubAdapter


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.value

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds


@pytest.mark.req("FR-A-04", "PR-05")
def test_budget_counts_elapsed_time() -> None:
    clock = FakeClock()
    budget = AgentBudget(150, clock=clock.now)
    assert budget.remaining() == 150
    clock.value = 100
    assert budget.elapsed() == 100
    assert budget.remaining() == 50
    clock.value = 151
    assert budget.expired() and budget.remaining() == 0


@pytest.mark.req("FR-A-04", "PR-05")
async def test_shorter_deadline_caps_attempts_and_backoff() -> None:
    clock = FakeClock()
    adapter = StubAdapter(
        policy=RetryPolicy(30, 3, 150, 10, 100),
        script=[LLMTransientError("rate_limit", retry_after=8), '{"ok":true}'],
        sleep=clock.sleep,
        clock=clock.now,
    )
    with pytest.raises(LLMDeadlineExceeded) as captured:
        await adapter.complete_json("x", deadline=5)
    assert captured.value.attempts == 1
    assert clock.sleeps == []
    assert len(adapter.prompts) == 1

    clock = FakeClock()
    adapter = StubAdapter(
        policy=RetryPolicy(30, 3, 150, 0, 100),
        script=[(6, LLMResponse('{"ok":true}'))],
        sleep=clock.sleep,
        clock=clock.now,
    )
    with pytest.raises(LLMDeadlineExceeded):
        await adapter.complete_json("x", deadline=5)
    assert clock.value == 6  # Fake sleep advances its clock; completion is refused.


@pytest.mark.req("FR-A-04", "PR-05")
async def test_none_keeps_policy_deadline() -> None:
    clock = FakeClock()
    adapter = StubAdapter(
        policy=RetryPolicy(30, 3, 150, 0, 100),
        script=['{"ok":true}'],
        sleep=clock.sleep,
        clock=clock.now,
    )
    assert (await adapter.complete_json("x", deadline=None)).data == {"ok": True}
