"""Construct agents with resolved run settings and the shared LLM factory."""

from app.agents.architect import ArchitectAgent
from app.agents.generators.base import GeneratorAgent
from app.agents.generators.cost import CostGeneratorAgent
from app.agents.generators.performance import PerformanceGeneratorAgent
from app.agents.generators.security import SecurityGeneratorAgent
from app.core.config import Settings
from app.domain.enums import Variant
from app.domain.run_config import RunConfig
from app.llm.factory import build_adapter


class AgentFactory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_architect(self, run_config: RunConfig | None = None) -> ArchitectAgent:
        resolved = (run_config or RunConfig()).resolve(self.settings)
        adapter = build_adapter(
            self.settings,
            provider=resolved.provider,
            model=resolved.model,
        )
        return ArchitectAgent(
            adapter,
            deadline_seconds=self.settings.agent_deadline_seconds,
            max_plan_attempts=self.settings.architect_max_plan_attempts,
        )

    def create_generator(
        self, variant: Variant, run_config: RunConfig | None = None
    ) -> GeneratorAgent:
        classes: dict[
            Variant,
            type[CostGeneratorAgent]
            | type[PerformanceGeneratorAgent]
            | type[SecurityGeneratorAgent],
        ] = {
            Variant.COST: CostGeneratorAgent,
            Variant.PERFORMANCE: PerformanceGeneratorAgent,
            Variant.SECURITY: SecurityGeneratorAgent,
        }
        resolved = (run_config or RunConfig()).resolve(self.settings)
        adapter = build_adapter(
            self.settings, provider=resolved.provider, model=resolved.model
        )
        return classes[Variant(variant)](
            adapter,
            deadline_seconds=self.settings.generator_deadline_seconds,
            attempt_timeout=self.settings.generator_attempt_timeout_seconds,
            max_output_tokens=self.settings.generator_max_output_tokens,
            max_package_attempts=self.settings.generator_max_package_attempts,
        )

    def create_generators(
        self, run_config: RunConfig | None = None
    ) -> list[GeneratorAgent]:
        return [
            self.create_generator(variant, run_config)
            for variant in (Variant.COST, Variant.PERFORMANCE, Variant.SECURITY)
        ]
