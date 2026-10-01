"""Construct agents with resolved run settings and the shared LLM factory."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.architect import ArchitectAgent
from app.agents.generators.base import GeneratorAgent
from app.agents.generators.cost import CostGeneratorAgent
from app.agents.generators.performance import PerformanceGeneratorAgent
from app.agents.generators.security import SecurityGeneratorAgent
from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixAgent
from app.core.config import Settings
from app.domain.enums import LLMProvider, Variant
from app.domain.run_config import RunConfig
from app.llm.factory import build_adapter
from app.pipeline.demo_stub import PipelineDemoStub
from app.scanners.runner import ProcessToolRunner
from app.scanners.scan import Scanner


class AgentFactory:
    def __init__(
        self,
        settings: Settings,
        *,
        pipeline_demo_stub: bool = False,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        scanner: Scanner | None = None,
        scanner_versions: dict[str, str | None] | None = None,
    ) -> None:
        self.settings = settings
        self.pipeline_demo_stub = pipeline_demo_stub
        self.session_factory = session_factory
        self.scanner = scanner or Scanner(
            ProcessToolRunner(settings.scanner_timeout_seconds)
        )
        self.scanner_versions = scanner_versions or {}
        self.security_semaphore = asyncio.Semaphore(
            settings.security_max_parallel_fixes
        )

    def create_architect(self, run_config: RunConfig | None = None) -> ArchitectAgent:
        resolved = (run_config or RunConfig()).resolve(self.settings)
        adapter = build_adapter(
            self.settings,
            provider=resolved.provider,
            model=resolved.model,
        )
        if self.pipeline_demo_stub and resolved.provider == LLMProvider.STUB:
            adapter = PipelineDemoStub(None, adapter.policy)
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
        if self.pipeline_demo_stub and resolved.provider == LLMProvider.STUB:
            adapter = PipelineDemoStub(variant, adapter.policy)
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

    def create_security_agent(self, run_config: RunConfig) -> SecurityAgent:
        if self.session_factory is None:
            raise RuntimeError("security agent requires a database session factory")
        resolved = run_config.resolve(self.settings)
        provider = self.settings.security_fix_provider or resolved.provider
        model = self.settings.security_fix_model or resolved.model
        adapter = build_adapter(
            self.settings,
            provider=provider,
            model=model,
            reasoning_effort=self.settings.security_fix_reasoning_effort,
        )
        if self.pipeline_demo_stub and provider == LLMProvider.STUB:
            adapter = PipelineDemoStub(Variant.SECURITY, adapter.policy)
        return SecurityAgent(
            self.scanner,
            FixAgent(
                adapter,
                attempt_timeout=self.settings.fix_attempt_timeout_seconds,
                max_output_tokens=self.settings.fix_max_output_tokens,
            ),
            self.session_factory,
            self.settings,
            versions=self.scanner_versions,
            semaphore=self.security_semaphore,
            fixing_provider=adapter.provider,
            fixing_model=adapter.model,
            fixing_reasoning_effort=adapter.reasoning_effort,
        )
