"""Turn one accepted description into a validated AWS deployment plan."""

import time
from collections.abc import Callable
from dataclasses import dataclass

from app.agents.budget import AgentBudget
from app.agents.prompts.architect import (
    ARCHITECT_PROMPT_VERSION,
    ARCHITECT_SYSTEM_PROMPT,
    build_user_prompt,
)
from app.domain.input_rules import validate_request_text
from app.domain.plan import DeploymentPlan, plan_validation_errors
from app.llm.base import LLMAdapter
from app.llm.errors import LLMDeadlineExceeded, LLMPermanentError, LLMRetryExhausted


class ArchitectError(Exception):
    category = "architect_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ArchitectDeadlineExceeded(ArchitectError):
    category = "deadline"

    def __init__(self) -> None:
        super().__init__("Architecture planning exceeded its time limit.")


class ArchitectInvalidPlan(ArchitectError):
    category = "invalid_plan"

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors[:10])
        super().__init__(
            "Architecture planning could not produce a valid deployment plan."
        )


class ArchitectLLMFailure(ArchitectError):
    category = "llm_failure"

    def __init__(self, llm_category: str) -> None:
        self.llm_category = llm_category
        super().__init__(
            "Architecture planning could not reach the language model successfully."
        )


@dataclass(frozen=True)
class ArchitectRunInfo:
    plan_attempts: int
    total_llm_attempts: int | None
    elapsed_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    prompt_version: str
    validation_error_counts: tuple[int, ...]


class ArchitectAgent:
    def __init__(
        self,
        llm_adapter: LLMAdapter,
        *,
        deadline_seconds: float,
        max_plan_attempts: int = 3,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_plan_attempts < 1:
            raise ValueError("max_plan_attempts must be positive")
        self.llm_adapter = llm_adapter
        self.deadline_seconds = deadline_seconds
        self.max_plan_attempts = max_plan_attempts
        self._clock = clock
        self._text: str | None = None
        self._last_run: ArchitectRunInfo | None = None

    def parse_input(self, text: str) -> None:
        self._text = None
        self._text = validate_request_text(text)

    @property
    def last_run(self) -> ArchitectRunInfo | None:
        return self._last_run

    async def generate_plan(self) -> DeploymentPlan:
        if self._text is None:
            raise RuntimeError("parse_input must be called before generate_plan")
        budget = AgentBudget(self.deadline_seconds, clock=self._clock)
        self._last_run = None
        previous_errors: list[str] | None = None
        previous_output: dict[str, object] | None = None
        plan_attempts = 0
        llm_attempts: int | None = 0
        input_tokens: int | None = 0
        output_tokens: int | None = 0
        error_counts: list[int] = []
        try:
            for _ in range(self.max_plan_attempts):
                user_prompt = build_user_prompt(
                    self._text, previous_errors, previous_output
                )
                remaining = budget.remaining()
                if remaining < 1:
                    raise ArchitectDeadlineExceeded()
                plan_attempts += 1
                try:
                    result = await self.llm_adapter.complete_json(
                        user_prompt,
                        system=ARCHITECT_SYSTEM_PROMPT,
                        deadline=remaining,
                    )
                except LLMDeadlineExceeded as error:
                    if llm_attempts is not None:
                        llm_attempts += error.attempts
                    input_tokens = output_tokens = None
                    if remaining <= self.llm_adapter.policy.deadline:
                        raise ArchitectDeadlineExceeded() from None
                    raise ArchitectLLMFailure("deadline") from None
                except LLMRetryExhausted as error:
                    if llm_attempts is not None:
                        llm_attempts += error.attempts
                    input_tokens = output_tokens = None
                    raise ArchitectLLMFailure(error.last_category) from None
                except LLMPermanentError as error:
                    llm_attempts = None  # This Phase 1 error has no attempt count.
                    input_tokens = output_tokens = None
                    raise ArchitectLLMFailure(error.category) from None
                if llm_attempts is not None:
                    llm_attempts += result.attempts
                response = result.response
                input_tokens = (
                    input_tokens + response.input_tokens
                    if input_tokens is not None and response.input_tokens is not None
                    else None
                )
                output_tokens = (
                    output_tokens + response.output_tokens
                    if output_tokens is not None and response.output_tokens is not None
                    else None
                )
                errors = plan_validation_errors(result.data)
                error_counts.append(len(errors))
                if not errors:
                    return DeploymentPlan.model_validate(result.data)
                previous_errors = errors
                previous_output = result.data
            raise ArchitectInvalidPlan(previous_errors or [])
        finally:
            self._last_run = ArchitectRunInfo(
                plan_attempts=plan_attempts,
                total_llm_attempts=llm_attempts,
                elapsed_seconds=budget.elapsed(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                prompt_version=ARCHITECT_PROMPT_VERSION,
                validation_error_counts=tuple(error_counts),
            )
