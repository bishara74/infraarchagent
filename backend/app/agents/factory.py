"""Construct agents with resolved run settings and the shared LLM factory."""

from app.agents.architect import ArchitectAgent
from app.core.config import Settings
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
