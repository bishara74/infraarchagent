import json
from typing import Any

import pytest

from app.agents.generators.base import (
    GeneratorDeadlineExceeded,
    GeneratorIncompletePackage,
    GeneratorLLMFailure,
)
from app.agents.generators.cost import CostGeneratorAgent
from app.agents.generators.performance import PerformanceGeneratorAgent
from app.agents.generators.security import SecurityGeneratorAgent
from app.domain.directive_checks import check_directive
from app.domain.enums import Variant
from app.domain.models import IaCPackage
from app.domain.plan import DeploymentPlan, FileType
from app.llm.base import LLMResponse, RetryPolicy
from app.llm.errors import LLMPermanentError
from app.llm.stub import StubAdapter


class FakeClock:
    def __init__(self) -> None:
        self.now_value = 0.0

    def now(self) -> float:
        return self.now_value


def plan(*file_types: str) -> DeploymentPlan:
    return DeploymentPlan.model_validate(
        {
            "cloud_provider": "aws",
            "services": [{"name": "web", "aws_service": "ECS", "purpose": "Serve"}],
            "dependencies": [],
            "network": {
                "public_services": ["web"],
                "private_services": [],
                "ingress": [],
                "notes": "VPC",
            },
            "storage": [],
            "file_types": ["terraform", *file_types],
            "ambiguities": [],
        }
    )


def agent(
    *responses: str | LLMResponse | BaseException,
    clock: FakeClock | None = None,
) -> CostGeneratorAgent:
    return CostGeneratorAgent(
        StubAdapter(
            policy=RetryPolicy(30, 3, 150, 0, 100),
            script=responses,
        ),
        deadline_seconds=150,
        attempt_timeout=120,
        max_output_tokens=32000,
        max_package_attempts=2,
        clock=clock.now if clock else FakeClock().now,
    )


def reply(files: dict[str, str], notes: str = "design") -> str:
    return json.dumps({"files": files, "notes": notes})


@pytest.mark.req("FR-G-01", "FR-G-02")
async def test_valid_first_package_has_variant_metrics_and_notes() -> None:
    generator = agent(LLMResponse(reply({"terraform/main.tf": "resource {}"}), 5, 9))
    package = await generator.generate(plan())
    assert isinstance(package, IaCPackage)
    assert package.variant is Variant.COST
    assert package.files == {"terraform/main.tf": "resource {}"}
    assert generator.last_run is not None
    assert generator.last_run.package_attempts == 1
    assert generator.last_run.total_llm_attempts == 1
    assert generator.last_run.input_tokens == 5
    assert generator.last_run.output_tokens == 9
    assert generator.last_run.notes == "design"
    assert generator.last_run.notes_length == 6
    assert generator.last_run.structure_error_counts == (0,)
    assert "resource {}" not in repr(generator.last_run)


@pytest.mark.req("FR-G-02", "FR-A-05")
async def test_missing_type_then_complete_uses_paths_without_contents() -> None:
    first = {"terraform/main.tf": "PRIVATE_PREVIOUS_CONTENT"}
    second = {**first, "k8s/web.yaml": "apiVersion: v1"}
    generator = agent(reply(first), reply(second))
    package = await generator.generate(plan("kubernetes"))
    assert "k8s/web.yaml" in package.files
    assert generator.last_run is not None
    assert generator.last_run.structure_error_counts[0] > 0
    prompts = generator.llm_adapter.prompts
    assert len(prompts) == 2
    assert "missing kubernetes files" in prompts[1]
    assert "terraform/main.tf" in prompts[1]
    assert "PRIVATE_PREVIOUS_CONTENT" not in prompts[1]


@pytest.mark.req("FR-G-02")
async def test_incomplete_twice_and_unsafe_path_are_structural() -> None:
    generator = agent(reply({"terraform/main.tf": "x"}), reply({"../x": "bad"}))
    with pytest.raises(GeneratorIncompletePackage) as caught:
        await generator.generate(plan("helm"))
    assert caught.value.missing_types == (FileType.TERRAFORM, FileType.HELM)
    assert any("unsafe" in error for error in caught.value.last_errors)
    assert len(generator.llm_adapter.prompts) == 2


@pytest.mark.req("PR-05")
async def test_expired_budget_makes_no_second_call() -> None:
    clock = FakeClock()

    class AdvancingStub(StubAdapter):
        async def send_prompt(
            self,
            prompt: str,
            *,
            system: str | None = None,
            max_output_tokens: int,
            timeout: float,
        ) -> LLMResponse:
            response = await super().send_prompt(
                prompt,
                system=system,
                max_output_tokens=max_output_tokens,
                timeout=timeout,
            )
            clock.now_value += 149.5
            return response

    generator = CostGeneratorAgent(
        AdvancingStub(script=[reply({"terraform/main.tf": "x"})]),
        deadline_seconds=150,
        attempt_timeout=120,
        max_output_tokens=32000,
        max_package_attempts=2,
        clock=clock.now,
    )
    with pytest.raises(GeneratorDeadlineExceeded):
        await generator.generate(plan("helm"))
    assert len(generator.llm_adapter.prompts) == 1


@pytest.mark.req("PR-05")
async def test_generator_forwards_adapter_overrides() -> None:
    class RecordingStub(StubAdapter):
        async def complete_json(self, prompt: str, **kwargs: Any) -> Any:
            self.options = kwargs
            return await super().complete_json(prompt, **kwargs)

    stub = RecordingStub(script=[reply({"terraform/main.tf": "x"})])
    generator = CostGeneratorAgent(
        stub,
        deadline_seconds=150,
        attempt_timeout=120,
        max_output_tokens=32000,
        max_package_attempts=2,
    )
    await generator.generate(plan())
    assert stub.options["attempt_timeout"] == 120
    assert stub.options["max_output_tokens"] == 32000


@pytest.mark.req("FR-A-05", "NFR-01")
async def test_typed_plan_and_safe_llm_failure() -> None:
    generator = agent(LLMPermanentError("CANARY-should-not-leak"))
    with pytest.raises(TypeError):
        await generator.generate("raw description")  # type: ignore[arg-type]
    with pytest.raises(GeneratorLLMFailure) as caught:
        await generator.generate(plan())
    assert "CANARY" not in str(caught.value)
    assert caught.value.category == "llm_failure"


@pytest.mark.req("FR-G-02")
async def test_schema_invalid_reply_is_corrected() -> None:
    generator = agent(
        json.dumps({"files": {"terraform/main.tf": 4}, "extra": 1}),
        reply({"terraform/main.tf": "x"}),
    )
    package = await generator.generate(plan())
    assert package.files == {"terraform/main.tf": "x"}
    assert "extra" in generator.llm_adapter.prompts[1]
    assert "terraform/main.tf" in generator.llm_adapter.prompts[1]


@pytest.mark.req("FR-G-03")
async def test_directive_failure_does_not_trigger_correction() -> None:
    generator = agent(reply({"terraform/main.tf": 'instance_type = "m5.large"'}))
    deployment = plan()
    package = await generator.generate(deployment)
    checks = check_directive(generator.variant, package.files, deployment)
    assert any(not check.passed for check in checks)
    assert len(generator.llm_adapter.prompts) == 1


@pytest.mark.req("PR-05")
async def test_valid_return_near_budget_is_accepted() -> None:
    clock = FakeClock()

    class AdvancingStub(StubAdapter):
        async def send_prompt(
            self,
            prompt: str,
            *,
            system: str | None = None,
            max_output_tokens: int,
            timeout: float,
        ) -> LLMResponse:
            response = await super().send_prompt(
                prompt,
                system=system,
                max_output_tokens=max_output_tokens,
                timeout=timeout,
            )
            clock.now_value += 149.5
            return response

    generator = CostGeneratorAgent(
        AdvancingStub(script=[reply({"terraform/main.tf": "x"})]),
        deadline_seconds=150,
        attempt_timeout=120,
        max_output_tokens=32000,
        max_package_attempts=2,
        clock=clock.now,
    )
    assert (await generator.generate(plan())).variant is Variant.COST


@pytest.mark.req("FR-G-01", "FR-G-03", "FR-G-04", "FR-G-05")
def test_subclasses_declare_only_variant_and_directive() -> None:
    for cls in (CostGeneratorAgent, PerformanceGeneratorAgent, SecurityGeneratorAgent):
        own_public = {name for name in vars(cls) if not name.startswith("_")}
        assert own_public == {"variant", "optimisation_directive"}
        assert "generate" not in vars(cls)
