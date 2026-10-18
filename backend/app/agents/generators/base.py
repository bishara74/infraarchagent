"""Template Method for one complete package, with bounded structural correction."""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from pydantic import ValidationError

from app.agents.budget import AgentBudget
from app.agents.generators.schema import (
    GeneratorOutput,
    generator_wire_schema,
    validate_generator_output,
)
from app.agents.prompts.generator import (
    GENERATOR_PROMPT_VERSION,
    build_system_prompt,
    build_user_prompt,
)
from app.core.config import StructuredOutput
from app.domain.enums import Variant
from app.domain.models import IaCPackage
from app.domain.package_layout import (
    completeness_diagnostics,
    package_structure_errors,
    required_types_missing,
)
from app.domain.plan import DeploymentPlan, FileType
from app.llm.base import LLMAdapter, LLMAttempt
from app.llm.errors import (
    LLMDeadlineExceeded,
    LLMPermanentError,
    LLMRetryExhausted,
    failure_message,
    safe_category,
)


class GeneratorError(Exception):
    category = "generator_error"

    def __init__(self, variant: Variant, message: str) -> None:
        self.variant = variant
        super().__init__(message)


class GeneratorDeadlineExceeded(GeneratorError):
    category = "deadline"

    def __init__(self, variant: Variant) -> None:
        super().__init__(
            variant, f"{variant.value} package generation exceeded its time limit."
        )


class GeneratorIncompletePackage(GeneratorError):
    category = "incomplete_package"

    def __init__(
        self, variant: Variant, missing_types: list[FileType], last_errors: list[str]
    ) -> None:
        self.missing_types = tuple(missing_types)
        self.last_errors = tuple(last_errors[:10])
        super().__init__(
            variant, f"{variant.value} generator did not produce a complete package."
        )


class GeneratorLLMFailure(GeneratorError):
    category = "llm_failure"

    def __init__(
        self, variant: Variant, llm_category: str, *, structured_output: bool = False
    ) -> None:
        self.llm_category = safe_category(llm_category)
        message = failure_message(self.llm_category)
        if structured_output and self.llm_category in {
            "request_rejected",
            "model_unavailable",
        }:
            message += " Set LLM_STRUCTURED_OUTPUT=json_object and retry."
        super().__init__(variant, message)


@dataclass(frozen=True)
class GeneratorRunInfo:
    package_attempts: int
    total_llm_attempts: int | None
    elapsed_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    prompt_version: str
    structure_error_counts: tuple[int, ...]
    notes: str | None
    notes_length: int
    file_count: int
    total_characters: int
    cached_input_tokens: int | None = None
    attempt_details: tuple[LLMAttempt, ...] = ()
    deadline_exceeded: bool = False
    overrun_seconds: float = 0.0
    completeness: tuple[dict[str, Any], ...] = ()


class GeneratorAgent(ABC):
    @property
    @abstractmethod
    def variant(self) -> Variant: ...

    @property
    @abstractmethod
    def optimisation_directive(self) -> str: ...

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        *,
        deadline_seconds: float,
        attempt_timeout: float,
        max_output_tokens: int,
        max_package_attempts: int,
        structured_output: StructuredOutput = "json_schema",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if attempt_timeout <= 0 or max_output_tokens < 1 or max_package_attempts < 1:
            raise ValueError("generator limits must be positive")
        self.llm_adapter = llm_adapter
        self.wire_files = (
            llm_adapter.supports_structured_output
            and structured_output == "json_schema"
        )
        llm_adapter.structured_output = structured_output
        llm_adapter.output_schema = generator_wire_schema() if self.wire_files else None
        self.output_validator = lambda data: validate_generator_output(
            data, wire_files=self.wire_files
        )
        self.deadline_seconds = deadline_seconds
        self.attempt_timeout = attempt_timeout
        self.max_output_tokens = max_output_tokens
        self.max_package_attempts = max_package_attempts
        self._clock = clock
        self._last_run: GeneratorRunInfo | None = None

    @property
    def last_run(self) -> GeneratorRunInfo | None:
        return self._last_run

    async def regenerate(
        self, plan: DeploymentPlan, feedback: list[dict[str, Any]], budget: AgentBudget
    ) -> IaCPackage:
        """One replacement candidate; reuse the caller's absolute deadline."""
        previous = self._last_run
        details: list[LLMAttempt] = []
        result = None
        try:
            async with asyncio.timeout(max(0.001, budget.remaining())):
                result = await self.llm_adapter.complete_json(
                    build_user_prompt(plan, [json.dumps(item) for item in feedback]),
                    system=build_system_prompt(
                        self.optimisation_directive,
                        max_output_tokens=self.max_output_tokens,
                        wire_files=self.wire_files,
                        plan=plan,
                    ),
                    deadline=budget.remaining(),
                    attempt_timeout=self.attempt_timeout,
                    max_output_tokens=self.max_output_tokens,
                    attempt_observer=details.append,
                    response_validator=self.output_validator,
                )
            output = GeneratorOutput.model_validate(result.data)
            errors = package_structure_errors(output.files, plan.file_types)
            if errors:
                raise GeneratorIncompletePackage(self.variant, [], errors)
            return IaCPackage(variant=self.variant, files=output.files)
        except (
            LLMDeadlineExceeded,
            LLMRetryExhausted,
            LLMPermanentError,
            TimeoutError,
            ValidationError,
        ):
            raise GeneratorError(
                self.variant, "syntax regeneration unavailable"
            ) from None
        finally:
            if previous is not None:

                def total(name: str) -> int | None:
                    old = getattr(previous, name)
                    value = getattr(result.response, name) if result else None
                    return (
                        old + value if old is not None and value is not None else None
                    )

                self._last_run = replace(
                    previous,
                    elapsed_seconds=max(previous.elapsed_seconds, budget.elapsed()),
                    deadline_exceeded=budget.expired(),
                    overrun_seconds=max(0.0, budget.elapsed() - self.deadline_seconds),
                    package_attempts=previous.package_attempts + 1,
                    total_llm_attempts=(
                        previous.total_llm_attempts + result.attempts
                        if previous.total_llm_attempts is not None and result
                        else None
                    ),
                    input_tokens=total("input_tokens"),
                    output_tokens=total("output_tokens"),
                    cached_input_tokens=total("cached_input_tokens"),
                    attempt_details=previous.attempt_details
                    + tuple(
                        replace(
                            d,
                            attempt=len(previous.attempt_details) + i,
                            package_attempt=previous.package_attempts + 1,
                        )
                        for i, d in enumerate(details, 1)
                    ),
                    completeness=previous.completeness
                    + (
                        {
                            "attempt": previous.package_attempts + 1,
                            "phase": "regeneration",
                            **completeness_diagnostics(
                                result.data["files"],
                                plan.file_types,
                                plan.services[0].name,
                            ),
                        },
                    )
                    if result
                    else previous.completeness
                    + (
                        {
                            "attempt": previous.package_attempts + 1,
                            "error_count": None,
                            "categories": {"no_candidate": 1},
                            "missing_types": [],
                            "missing_paths": [],
                        },
                    ),
                )

    async def generate(
        self, plan: DeploymentPlan, *, budget: AgentBudget | None = None
    ) -> IaCPackage:
        if not isinstance(plan, DeploymentPlan):
            raise TypeError("generate requires a DeploymentPlan")
        local_started = self._clock()
        budget = budget or AgentBudget(self.deadline_seconds, clock=self._clock)
        self._last_run = None
        previous_errors: list[str] | None = None
        previous_paths: list[str] | None = None
        previous_files: dict[str, str] = {}
        attempts = 0
        llm_attempts: int | None = 0
        input_tokens: int | None = 0
        output_tokens: int | None = 0
        cached_input_tokens: int | None = 0
        error_counts: list[int] = []
        notes: str | None = None
        file_count = total_characters = 0
        attempt_details: list[LLMAttempt] = []
        completeness: list[dict[str, Any]] = []

        def observe(attempt: LLMAttempt) -> None:
            attempt_details.append(
                replace(
                    attempt, attempt=len(attempt_details) + 1, package_attempt=attempts
                )
            )

        try:
            for _ in range(self.max_package_attempts):
                prompt = build_user_prompt(
                    plan,
                    previous_errors,
                    previous_paths,
                    completeness[-1] if completeness else None,
                )
                system = build_system_prompt(
                    self.optimisation_directive,
                    max_output_tokens=self.max_output_tokens,
                    wire_files=self.wire_files,
                    plan=plan,
                )
                remaining = budget.remaining()
                if remaining < 1:
                    raise GeneratorDeadlineExceeded(self.variant)
                attempts += 1
                try:
                    async with asyncio.timeout(remaining):
                        result = await self.llm_adapter.complete_json(
                            prompt,
                            system=system,
                            deadline=remaining,
                            attempt_timeout=self.attempt_timeout,
                            max_output_tokens=self.max_output_tokens,
                            attempt_observer=observe,
                            response_validator=self.output_validator,
                        )
                except TimeoutError:
                    llm_attempts = len(attempt_details)
                    input_tokens = output_tokens = cached_input_tokens = None
                    raise GeneratorDeadlineExceeded(self.variant) from None
                except LLMDeadlineExceeded as error:
                    if llm_attempts is not None:
                        llm_attempts += error.attempts
                    input_tokens = output_tokens = cached_input_tokens = None
                    if remaining <= self.llm_adapter.policy.deadline:
                        raise GeneratorDeadlineExceeded(self.variant) from None
                    raise GeneratorLLMFailure(self.variant, "deadline") from None
                except LLMRetryExhausted as error:
                    if llm_attempts is not None:
                        llm_attempts += error.attempts
                    input_tokens = output_tokens = cached_input_tokens = None
                    raise GeneratorLLMFailure(
                        self.variant, error.last_category
                    ) from None
                except LLMPermanentError as error:
                    llm_attempts = input_tokens = output_tokens = (
                        cached_input_tokens
                    ) = None
                    raise GeneratorLLMFailure(
                        self.variant,
                        error.category,
                        structured_output=self.wire_files,
                    ) from None
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
                cached_input_tokens = (
                    cached_input_tokens + response.cached_input_tokens
                    if cached_input_tokens is not None
                    and response.cached_input_tokens is not None
                    else None
                )
                try:
                    output = GeneratorOutput.model_validate(result.data)
                except ValidationError as error:
                    previous_errors = [
                        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                        for item in error.errors(include_input=False)
                    ]
                    previous_paths = (
                        list(result.data["files"])
                        if isinstance(result.data.get("files"), dict)
                        else []
                    )
                    previous_files = {}
                    diagnostic = completeness_diagnostics(
                        {}, plan.file_types, plan.services[0].name
                    )
                    diagnostic["categories"]["schema"] = len(previous_errors)
                    diagnostic["error_count"] = len(previous_errors)
                    completeness.append({"attempt": attempts, **diagnostic})
                else:
                    previous_files = output.files
                    previous_paths = list(output.files)
                    file_count = len(output.files)
                    total_characters = sum(
                        len(content) for content in output.files.values()
                    )
                    previous_errors = package_structure_errors(
                        output.files, plan.file_types
                    )
                    completeness.append(
                        {
                            "attempt": attempts,
                            **completeness_diagnostics(
                                output.files, plan.file_types, plan.services[0].name
                            ),
                        }
                    )
                    if not previous_errors:
                        notes = output.notes
                        error_counts.append(0)
                        return IaCPackage(variant=self.variant, files=output.files)
                error_counts.append(len(previous_errors))
            raise GeneratorIncompletePackage(
                self.variant,
                required_types_missing(previous_files, plan.file_types),
                previous_errors or [],
            )
        finally:
            if len(completeness) < attempts:
                completeness.append(
                    {
                        "attempt": attempts,
                        "error_count": None,
                        "categories": {"no_candidate": 1},
                        "missing_types": [],
                        "missing_paths": [],
                    }
                )
            elapsed = max(budget.elapsed(), self._clock() - local_started)
            deadline_exceeded = elapsed >= self.deadline_seconds
            overrun_seconds = max(0.0, elapsed - self.deadline_seconds)
            if attempt_details and deadline_exceeded:
                attempt_details[-1] = replace(
                    attempt_details[-1],
                    deadline_exceeded=True,
                    overrun_seconds=overrun_seconds,
                )
            self._last_run = GeneratorRunInfo(
                package_attempts=attempts,
                total_llm_attempts=llm_attempts,
                elapsed_seconds=elapsed,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_input_tokens=cached_input_tokens,
                prompt_version=GENERATOR_PROMPT_VERSION,
                structure_error_counts=tuple(error_counts),
                notes=notes,
                notes_length=len(notes) if notes is not None else 0,
                file_count=file_count,
                total_characters=total_characters,
                attempt_details=tuple(attempt_details),
                deadline_exceeded=deadline_exceeded,
                overrun_seconds=overrun_seconds,
                completeness=tuple(completeness),
            )
