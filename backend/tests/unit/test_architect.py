import json
from typing import Any

import pytest

from app.agents.architect import (
    ArchitectAgent,
    ArchitectDeadlineExceeded,
    ArchitectInvalidPlan,
    ArchitectLLMFailure,
)
from app.domain.input_rules import NoInfrastructureIntentError
from app.llm.base import LLMResponse, LLMResult, RetryPolicy
from app.llm.errors import LLMTransientError
from app.llm.stub import StubAdapter


def plan(*, ambiguous: bool = False) -> dict[str, Any]:
    return {
        "cloud_provider": "aws",
        "services": [
            {"name": "web", "aws_service": "ECS Fargate", "purpose": "Serve a web app"}
        ],
        "dependencies": [],
        "network": {
            "public_services": ["web"],
            "private_services": [],
            "ingress": ["HTTPS"],
            "notes": "VPC",
        },
        "storage": [],
        "file_types": ["terraform"],
        "ambiguities": (
            [
                {
                    "topic": "runtime",
                    "detail": "Unspecified",
                    "assumption": "Container runtime",
                }
            ]
            if ambiguous
            else []
        ),
    }


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def now(self) -> float:
        return self.value

    async def sleep(self, seconds: float) -> None:
        self.value += seconds


class RecordingStub(StubAdapter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.deadlines: list[float | None] = []

    async def complete_json(
        self, prompt: str, *, system: str | None = None, deadline: float | None = None
    ) -> LLMResult:
        self.deadlines.append(deadline)
        return await super().complete_json(prompt, system=system, deadline=deadline)


@pytest.mark.req("FR-A-01", "FR-A-02")
async def test_valid_first_attempt_and_metrics() -> None:
    adapter = StubAdapter(script=[LLMResponse(json.dumps(plan()), 11, 20)])
    agent = ArchitectAgent(adapter, deadline_seconds=150)
    agent.parse_input("build a web app")
    result = await agent.generate_plan()
    assert result.services[0].name == "web"
    assert agent.last_run is not None
    assert agent.last_run.plan_attempts == agent.last_run.total_llm_attempts == 1
    assert (agent.last_run.input_tokens, agent.last_run.output_tokens) == (11, 20)
    assert agent.last_run.validation_error_counts == (0,)


@pytest.mark.req("FR-A-01", "FR-A-03")
async def test_invalid_plan_is_corrected_with_exact_error() -> None:
    invalid = plan()
    invalid["dependencies"] = [
        {"source": "web", "target": "missing", "description": "wrong"}
    ]
    adapter = StubAdapter(
        script=[json.dumps(invalid), json.dumps(plan(ambiguous=True))]
    )
    agent = ArchitectAgent(adapter, deadline_seconds=150)
    agent.parse_input("build a web app")
    result = await agent.generate_plan()
    assert result.ambiguities[0].topic == "runtime"
    assert "dependencies.0.target: unknown service 'missing'" in adapter.prompts[1]
    assert agent.last_run is not None
    assert agent.last_run.validation_error_counts == (1, 0)


@pytest.mark.req("FR-A-01")
async def test_three_invalid_plans_raise_safe_error() -> None:
    invalid = plan()
    invalid["file_types"] = []
    adapter = StubAdapter(script=[json.dumps(invalid)] * 3)
    agent = ArchitectAgent(adapter, deadline_seconds=150)
    agent.parse_input("build a web app")
    with pytest.raises(ArchitectInvalidPlan) as captured:
        await agent.generate_plan()
    assert captured.value.errors == ("file_types: terraform is required",)
    assert agent.last_run is not None and agent.last_run.plan_attempts == 3


@pytest.mark.req("FR-A-04", "PR-05")
async def test_retry_exhaustion_stops_plan_attempts() -> None:
    adapter = StubAdapter(
        policy=RetryPolicy(30, 3, 150, 0, 100), script=[LLMTransientError()] * 3
    )
    agent = ArchitectAgent(adapter, deadline_seconds=150)
    agent.parse_input("build a web app")
    with pytest.raises(ArchitectLLMFailure):
        await agent.generate_plan()
    assert agent.last_run is not None
    assert agent.last_run.plan_attempts == 1
    assert agent.last_run.total_llm_attempts == 3


@pytest.mark.req("FR-A-04", "PR-05")
async def test_remaining_budget_is_passed_to_next_plan_attempt() -> None:
    clock = FakeClock()
    invalid = plan()
    invalid["file_types"] = []
    adapter = RecordingStub(
        policy=RetryPolicy(150, 1, 150, 0, 100),
        script=[(100, json.dumps(invalid)), json.dumps(plan())],
        sleep=clock.sleep,
        clock=clock.now,
    )
    agent = ArchitectAgent(adapter, deadline_seconds=150, clock=clock.now)
    agent.parse_input("build a web app")
    await agent.generate_plan()
    assert adapter.deadlines == [150, 50]


@pytest.mark.req("FR-A-04", "PR-05")
async def test_exhausted_budget_starts_no_second_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    invalid = plan()
    invalid["file_types"] = []
    adapter = StubAdapter(
        policy=RetryPolicy(150, 1, 150, 0, 100),
        script=[json.dumps(invalid), json.dumps(plan())],
        clock=clock.now,
    )

    def slow_validation(data: dict[str, Any]) -> list[str]:
        clock.value = 150
        return ["file_types: terraform is required"]

    monkeypatch.setattr("app.agents.architect.plan_validation_errors", slow_validation)
    agent = ArchitectAgent(adapter, deadline_seconds=150, clock=clock.now)
    agent.parse_input("build a web app")
    with pytest.raises(ArchitectDeadlineExceeded):
        await agent.generate_plan()
    assert len(adapter.prompts) == 1


@pytest.mark.req("FR-A-04", "PR-05")
async def test_nearly_exhausted_budget_starts_no_second_call() -> None:
    clock = FakeClock()
    invalid = plan()
    invalid["file_types"] = []
    adapter = StubAdapter(
        policy=RetryPolicy(150, 1, 150, 0, 100),
        script=[(149.5, json.dumps(invalid)), (1, json.dumps(plan()))],
        sleep=clock.sleep,
        clock=clock.now,
    )
    agent = ArchitectAgent(adapter, deadline_seconds=150, clock=clock.now)
    agent.parse_input("build a web app")
    with pytest.raises(ArchitectDeadlineExceeded):
        await agent.generate_plan()
    assert len(adapter.prompts) == 1


@pytest.mark.req("FR-A-04", "PR-05")
async def test_valid_plan_returned_just_before_deadline_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    adapter = StubAdapter(
        policy=RetryPolicy(150, 1, 150, 0, 100),
        script=[(149.5, json.dumps(plan()))],
        sleep=clock.sleep,
        clock=clock.now,
    )
    from app.domain.plan import plan_validation_errors

    def slow_validation(data: dict[str, Any]) -> list[str]:
        clock.value = 151
        return plan_validation_errors(data)

    monkeypatch.setattr("app.agents.architect.plan_validation_errors", slow_validation)
    agent = ArchitectAgent(adapter, deadline_seconds=150, clock=clock.now)
    agent.parse_input("build a web app")
    assert (await agent.generate_plan()).services[0].name == "web"


@pytest.mark.req("FR-I-02")
async def test_parse_input_required_and_intent_rejection_never_calls_adapter() -> None:
    adapter = StubAdapter(script=[json.dumps(plan())])
    agent = ArchitectAgent(adapter, deadline_seconds=150)
    with pytest.raises(RuntimeError):
        await agent.generate_plan()
    with pytest.raises(NoInfrastructureIntentError):
        agent.parse_input("tell me a joke about cats")
    assert adapter.prompts == []
