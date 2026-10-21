"""Architect, parallel generators, then per-package stages and settlement."""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, replace
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.architect import ArchitectError
from app.agents.budget import AgentBudget
from app.agents.factory import AgentFactory
from app.agents.generation_syntax import recover_generation_syntax
from app.agents.generators.base import GeneratorAgent, GeneratorError
from app.agents.remediation import validate_files
from app.agents.security.agent import SecurityAgent
from app.agents.validation_repair import ValidationRepair
from app.agents.validator import ValidatorAgent
from app.core.safety import PublicDataSafety
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import (
    AgentName,
    AgentState,
    LLMProvider,
    PackageStatus,
    RunStatus,
    Variant,
)
from app.domain.models import IaCPackage
from app.domain.plan import DeploymentPlan
from app.domain.run_config import RunConfig
from app.domain.states import classify_run, readiness_after_validation
from app.domain.validation import (
    DeterministicRepair,
    RemediationReport,
    ValidationReport,
)
from app.events.kinds import (
    package_generated_payload,
    package_status_payload,
    plan_created_payload,
)
from app.pipeline.stages import SecurityStage, StageContext, ValidationStage
from app.pipeline.state import PipelineStateWriter
from app.pipeline.telemetry import publish as publish_telemetry
from app.pipeline.telemetry import traced
from app.scanners.runner import ToolFailure
from app.security.generation import generation_context
from app.validation.gate import GateRepairEngine, GenerationGate
from app.validation.idioms import repair_idioms
from app.validation.measurement import initialization_metrics, publish_measurement
from app.validation.repairs import repair_declarations
from app.validation.syntax import native_syntax
from app.validation.workspace import ValidationWorkspace, current_workspace

logger = logging.getLogger(__name__)
GENERATOR_NAMES = {
    Variant.COST: AgentName.GENERATOR_COST,
    Variant.PERFORMANCE: AgentName.GENERATOR_PERFORMANCE,
    Variant.SECURITY: AgentName.GENERATOR_SECURITY,
}


class PipelineOrchestrator:
    def __init__(
        self,
        run_id: UUID,
        text: str,
        run_config: RunConfig,
        *,
        factory: AgentFactory,
        session_factory: async_sessionmaker[AsyncSession],
        writer: PipelineStateWriter,
        security_stage: SecurityStage | None,
        validation_stage: ValidationStage,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.run_id = run_id
        self.text = text
        self.run_config = run_config
        self.factory = factory
        self.safety = (
            PublicDataSafety(factory.settings) if hasattr(factory, "settings") else None
        )
        self.session_factory = session_factory
        self.writer = writer
        self.security_stage = security_stage
        self.validation_stage = validation_stage
        self.clock = clock
        self.workspaces: dict[Variant, ValidationWorkspace] = {}

    async def _generate(
        self, generator: GeneratorAgent, plan: object
    ) -> tuple[Variant, IaCPackage | None]:
        workspace = ValidationWorkspace()
        self.workspaces[generator.variant] = workspace
        with workspace.activate():
            if not isinstance(generator, GeneratorAgent):
                return await self._generate_inside(generator, plan)
            started = self.clock()
            try:
                async with asyncio.timeout(generator.deadline_seconds):
                    return await self._generate_inside(generator, plan)
            except TimeoutError:
                # The work reserve is not an additional publication allowance:
                # slow database/event writes share the same absolute deadline.
                if generator.last_run is not None:
                    elapsed = max(
                        generator.last_run.elapsed_seconds, self.clock() - started
                    )
                    generator._last_run = replace(
                        generator.last_run,
                        elapsed_seconds=elapsed,
                        deadline_exceeded=True,
                        overrun_seconds=max(0.0, elapsed - generator.deadline_seconds),
                    )
                current = await self._package_status(generator.variant)
                if current == PackageStatus.GENERATING:
                    await self._generation_failed(
                        generator.variant,
                        "package generation exceeded its time limit",
                        generator,
                        "deadline",
                    )
                else:
                    # Publication may already have committed GENERATED. Follow
                    # existing legal arrows rather than reverting that state.
                    await self.writer.package_transition(
                        self.run_id,
                        generator.variant,
                        PackageStatus.SCANNING,
                        message="generation publication exceeded its time limit",
                    )
                    await self.writer.package_transition(
                        self.run_id,
                        generator.variant,
                        PackageStatus.SCAN_ERROR,
                        message="generation publication exceeded its time limit",
                        error="generation deadline exceeded",
                    )
                    await self.writer.agent_state(
                        self.run_id,
                        GENERATOR_NAMES[generator.variant],
                        AgentState.FAILED,
                        previous=AgentState.RUNNING,
                        message="generator publication timed out",
                        variant=generator.variant,
                        metrics=self._generator_metrics(generator),
                        failure_category="deadline",
                    )
                return generator.variant, None

    async def _prepare_generation(
        self,
        generator: GeneratorAgent,
        plan: DeploymentPlan,
        package: IaCPackage,
        started: float,
        generation_budget: AgentBudget | None = None,
    ) -> IaCPackage:
        if not isinstance(self.validation_stage, ValidatorAgent):
            return package
        workspace = current_workspace()
        assert workspace is not None
        workspace.original_files = (
            self.safety.value(dict(package.files))
            if self.safety is not None
            else dict(package.files)
        )
        package = package.model_copy(update={"files": dict(workspace.original_files)})
        deterministic_started = self.clock()
        files, records = await repair_declarations(package.files)
        files, idioms = repair_idioms(files)
        context = generation_context(plan)
        metadata = RemediationReport(
            generator_schema_context_chars=context.schema_chars,
            **context.metrics(),
            deterministic_repairs=[
                DeterministicRepair.model_validate(r) for r in [*records, *idioms]
            ],
        )
        ctx = StageContext(self.run_id, self.writer, plan, self.clock)
        await publish_measurement(
            ctx,
            package.variant,
            "deterministic_repairs",
            self.clock() - deterministic_started,
            phase="generation",
            count=len(records) + len(idioms),
        )
        package = package.model_copy(update={"files": files})
        remaining = generator.deadline_seconds - max(
            self.clock() - started,
            generator.last_run.elapsed_seconds if generator.last_run else 0,
        )
        if generation_budget is not None:
            remaining = min(remaining, generation_budget.remaining())
        # Publication and restoration share the original generator allowance.
        remaining = max(0.0, remaining - 5.0)
        gate = GenerationGate(self.validation_stage.engine)
        if remaining <= 0:
            metadata = metadata.model_copy(
                update={
                    "generation_syntax": {
                        "path": "deadline",
                        "normalizations": [],
                        "rounds": [],
                        "regeneration": "deadline",
                        "skipped_steps": [
                            "syntax_round_1",
                            "syntax_round_2",
                            "regeneration",
                        ],
                    }
                }
            )
            workspace.gate = {
                "outcome": "deadline",
                "duration_seconds": 0.0,
                "failed_checks": [],
                "skipped_checks": [],
            }
        else:
            budget = AgentBudget(remaining, clock=self.clock)
            gate_started = self.clock()
            workspace.gate = {
                "outcome": "deadline",
                "duration_seconds": 0.0,
                "failed_checks": [],
                "skipped_checks": [],
            }
            try:
                async with asyncio.timeout(budget.remaining()):
                    security = (
                        self.security_stage
                        or self.factory.create_security_agent(self.run_config)
                    )
                    if isinstance(security, SecurityAgent):

                        async def regenerate(
                            feedback: list[dict[str, Any]],
                        ) -> dict[str, str]:
                            return (
                                await generator.regenerate(plan, feedback, budget)
                            ).files

                        recovered, recovery = await recover_generation_syntax(
                            package.files,
                            plan,
                            security.fix_agent,
                            budget,
                            redact=self.safety.value
                            if self.safety
                            else lambda value: value,
                            regenerate=regenerate,
                        )
                        recovery.update(
                            fixing_model=security.fixing_model,
                            fixing_provider=security.fixing_provider,
                            fixing_reasoning_effort=security.fixing_reasoning_effort,
                        )
                        metadata = metadata.model_copy(
                            update={"generation_syntax": recovery}
                        )
                        package = package.model_copy(update={"files": recovered})
                        actions = [a for r in recovery["rounds"] for a in r["actions"]]
                        if any(
                            a.get("failure_category") == "usage_limit" for a in actions
                        ):
                            await self.writer.event_log.append(
                                self.run_id,
                                AgentName("generator_" + package.variant.value),
                                PackageStatus.GENERATING,
                                message="Syntax repair usage limit reached.",
                                payload={
                                    "kind": "stage_notice",
                                    "variant": package.variant.value,
                                    "failure_category": "usage_limit",
                                },
                            )
                        if generator.last_run and actions:
                            updates: dict[str, Any] = {}
                            old_attempts = generator.last_run.total_llm_attempts
                            updates["total_llm_attempts"] = (
                                old_attempts + sum(a["llm_attempts"] for a in actions)
                                if old_attempts is not None
                                and all(a["llm_attempts"] is not None for a in actions)
                                else None
                            )
                            for field in (
                                "input_tokens",
                                "output_tokens",
                                "cached_input_tokens",
                            ):
                                old = getattr(generator.last_run, field)
                                updates[field] = (
                                    old + sum(a[field] for a in actions)
                                    if old is not None
                                    and all(a[field] is not None for a in actions)
                                    else None
                                )
                            generator._last_run = replace(generator.last_run, **updates)
                    repaired, declarations = await repair_declarations(package.files)
                    metadata = metadata.model_copy(
                        update={
                            "deterministic_repairs": [
                                *metadata.deterministic_repairs,
                                *(
                                    DeterministicRepair.model_validate(r)
                                    for r in declarations
                                ),
                            ]
                        }
                    )
                    package = package.model_copy(update={"files": repaired})
                    result = await gate.run(plan, package.files)
                    package = package.model_copy(update={"files": result.files})
                    workspace.gate = result.metrics
                    workspace.observe(
                        list(result.report.checks), "generated", package.files
                    )
                    demo = (
                        getattr(self.factory, "pipeline_demo_stub", False)
                        and self.factory.settings.pipeline_demo_scenario == "review"
                        and self.run_config.resolve(self.factory.settings).provider
                        == LLMProvider.STUB
                    )
                    if (
                        result.report.summary.result == "invalid"
                        and budget.remaining() >= 1
                        and not demo
                        and not await native_syntax(package.files)
                    ):
                        security = (
                            self.security_stage
                            or self.factory.create_security_agent(self.run_config)
                        )
                        if isinstance(security, SecurityAgent):
                            repair = ValidationRepair(security, GateRepairEngine(gate))
                            ctx = StageContext(
                                self.run_id, self.writer, plan, self.clock
                            )
                            package, _, metadata = await repair.run(
                                ctx,
                                package.variant,
                                package,
                                rounds=1,
                                budget=budget,
                                phase="generation",
                                metadata=metadata,
                                report=result.report,
                            )
                            repaired, declarations = await repair_declarations(
                                package.files
                            )
                            metadata = metadata.model_copy(
                                update={
                                    "deterministic_repairs": [
                                        *metadata.deterministic_repairs,
                                        *(
                                            DeterministicRepair.model_validate(r)
                                            for r in declarations
                                        ),
                                    ]
                                }
                            )
                            package = package.model_copy(update={"files": repaired})
                            result = await gate.run(plan, package.files)
                            package = package.model_copy(update={"files": result.files})
                            workspace.gate = result.metrics
            except TimeoutError:
                workspace.gate = {**(workspace.gate or {}), "outcome": "deadline"}
            finally:
                assert workspace.gate is not None
                workspace.gate["duration_seconds"] = self.clock() - gate_started
        await publish_measurement(
            ctx,
            package.variant,
            "generation_gate",
            float(workspace.gate.get("duration_seconds", 0)),
            phase="generation",
            outcome=workspace.gate.get("outcome", "unknown"),
            **initialization_metrics(workspace.terraform_metrics),
        )
        metadata = metadata.model_copy(
            update={
                "gate": workspace.gate,
                "measurements": list(workspace.measurements),
            }
        )
        return package.model_copy(
            update={
                "validation_report": {"remediation": metadata.model_dump(mode="json")}
            }
        )

    @traced("generation", "generator")
    async def _generate_inside(
        self, generator: GeneratorAgent, plan: object
    ) -> tuple[Variant, IaCPackage | None]:
        variant = generator.variant
        name = GENERATOR_NAMES[variant]
        started = self.clock()
        generation_budget = (
            AgentBudget(generator.deadline_seconds, clock=self.clock)
            if isinstance(generator, GeneratorAgent)
            else None
        )
        context_metrics = (
            generation_context(plan).metrics()
            if isinstance(plan, DeploymentPlan)
            else {}
        )
        await self.writer.agent_state(
            self.run_id,
            name,
            AgentState.RUNNING,
            message="generator started",
            variant=variant,
            metrics=context_metrics,
        )
        try:
            if isinstance(generator, GeneratorAgent) and isinstance(
                plan, DeploymentPlan
            ):
                assert generation_budget is not None
                work_budget = AgentBudget(
                    max(0.001, generation_budget.remaining() - 5.0), clock=self.clock
                )
                package = await generator.generate(plan, budget=work_budget)
            else:
                package = await generator.generate(plan)  # type: ignore[arg-type]
            if isinstance(generator, GeneratorAgent) and isinstance(
                plan, DeploymentPlan
            ):
                package = await self._prepare_generation(
                    generator, plan, package, started, generation_budget
                )
                if generator.last_run is not None:
                    elapsed = max(
                        generator.last_run.elapsed_seconds, self.clock() - started
                    )
                    generator._last_run = replace(
                        generator.last_run,
                        elapsed_seconds=elapsed,
                        deadline_exceeded=elapsed >= generator.deadline_seconds,
                        overrun_seconds=max(0.0, elapsed - generator.deadline_seconds),
                    )
            if self.safety is not None:
                package = package.model_copy(
                    update={"files": self.safety.value(package.files)}
                )
            async with self.session_factory() as session:
                async with session.begin():
                    await PackageRepository(session).save_files(
                        self.run_id, variant, package.files
                    )
                    workspace = current_workspace()
                    if workspace is not None and workspace.original_files is not None:
                        await PackageRepository(session).save_automatic_repairs(
                            self.run_id,
                            variant,
                            original_files=workspace.original_files,
                            files=package.files,
                        )
        except GeneratorError as error:
            await self._generation_failed(
                variant,
                str(error),
                generator,
                getattr(error, "llm_category", error.category),
            )
            return variant, None
        except Exception:
            logger.exception("generator %s failed for run %s", variant, self.run_id)
            await self._generation_failed(
                variant, "package generation failed", generator, "provider_error"
            )
            return variant, None
        await self.writer.package_transition(
            self.run_id, variant, PackageStatus.GENERATED, message="package generated"
        )
        info = generator.last_run
        metrics = self._generator_metrics(generator)
        await self.writer.event_log.append(
            self.run_id,
            name,
            PackageStatus.GENERATED,
            message="package files stored",
            payload=package_generated_payload(
                variant, package.files, metrics, info.notes if info else None
            ),
        )
        await self.writer.agent_state(
            self.run_id,
            name,
            AgentState.COMPLETED,
            previous=AgentState.RUNNING,
            message="generator completed",
            variant=variant,
            metrics=metrics,
        )
        return variant, package

    @staticmethod
    def _generator_metrics(generator: GeneratorAgent) -> dict[str, Any]:
        info = generator.last_run
        return (
            {
                "attempts": info.package_attempts,
                "llm_attempts": info.total_llm_attempts
                if info.total_llm_attempts is not None
                else len(info.attempt_details)
                if info.attempt_details
                else None,
                "elapsed_seconds": info.elapsed_seconds,
                "input_tokens": info.input_tokens,
                "output_tokens": info.output_tokens,
                "cached_input_tokens": info.cached_input_tokens,
                "prompt_version": info.prompt_version,
                "completeness": list(info.completeness),
                "llm_attempt_details": [asdict(item) for item in info.attempt_details],
                "deadline_exceeded": info.deadline_exceeded,
                "overrun_seconds": info.overrun_seconds,
            }
            if info
            else {}
        )

    async def _generation_failed(
        self,
        variant: Variant,
        message: str,
        generator: GeneratorAgent,
        failure_category: str,
    ) -> None:
        await self.writer.package_transition(
            self.run_id, variant, PackageStatus.FAILED, message=message, error=message
        )
        await self.writer.agent_state(
            self.run_id,
            GENERATOR_NAMES[variant],
            AgentState.FAILED,
            previous=AgentState.RUNNING,
            message=message,
            variant=variant,
            metrics=self._generator_metrics(generator),
            failure_category=failure_category,
        )

    async def _package_status(self, variant: Variant) -> PackageStatus:
        async with self.session_factory() as session:
            row = await PackageRepository(session).get(self.run_id, variant)
            if row is None:
                raise LookupError("package not found")
            return PackageStatus(row.status)

    async def _stage_error(
        self, variant: Variant, *, validation: bool
    ) -> PackageStatus:
        current = await self._package_status(variant)
        if validation:
            if current in {PackageStatus.SCAN_CLEAN, PackageStatus.SCAN_EXHAUSTED}:
                await self.writer.package_transition(
                    self.run_id,
                    variant,
                    PackageStatus.VALIDATING,
                    message="validation started",
                )
            await self.writer.package_transition(
                self.run_id,
                variant,
                PackageStatus.VALIDATION_ERROR,
                message="validation failed unexpectedly",
                error="validation failed",
            )
            return PackageStatus.VALIDATION_ERROR
        if current in {
            PackageStatus.GENERATED,
            PackageStatus.VALID,
            PackageStatus.INVALID,
            PackageStatus.VALIDATION_ERROR,
        }:
            await self.writer.package_transition(
                self.run_id,
                variant,
                PackageStatus.SCANNING,
                message="security stage started",
            )
        elif current == PackageStatus.REMEDIATING:
            await self.writer.package_transition(
                self.run_id,
                variant,
                PackageStatus.SCANNING,
                message="security stage could not complete",
            )
        await self.writer.package_transition(
            self.run_id,
            variant,
            PackageStatus.SCAN_ERROR,
            message="security stage failed unexpectedly",
            error="security stage failed",
        )
        return PackageStatus.SCAN_ERROR

    async def _post_generation(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        workspace = self.workspaces.get(variant)
        if workspace is None:
            return await self._post_generation_inside(ctx, variant, package)
        with workspace.activate():
            return await self._post_generation_inside(ctx, variant, package)

    @traced("post_generation", "fixer")
    async def _post_generation_inside(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        stage = self.security_stage or self.factory.create_security_agent(
            self.run_config
        )
        repair = None
        repair_budget = None
        metadata = RemediationReport.model_validate(
            (package.validation_report or {}).get("remediation") or {}
        )
        workspace = current_workspace()
        original_files = dict(
            workspace.original_files
            if workspace and workspace.original_files is not None
            else package.files
        )
        demo_review = (
            getattr(self.factory, "pipeline_demo_stub", False)
            and self.factory.settings.pipeline_demo_scenario == "review"
            and self.run_config.resolve(self.factory.settings).provider
            == LLMProvider.STUB
        )
        if (
            isinstance(stage, SecurityAgent)
            and isinstance(self.validation_stage, ValidatorAgent)
            and not demo_review
        ):
            repair = ValidationRepair(stage, self.validation_stage.engine)
            repair_budget = AgentBudget(
                self.factory.settings.validation_deadline_seconds, clock=ctx.clock
            )
            files, records = await repair_declarations(package.files)
            metadata = metadata.model_copy(
                update={
                    "deterministic_repairs": [
                        *metadata.deterministic_repairs,
                        *(DeterministicRepair.model_validate(r) for r in records),
                    ]
                }
            )
            package = package.model_copy(update={"files": files})
            await ctx.writer.package_transition(
                ctx.run_id,
                variant,
                PackageStatus.VALIDATING,
                message="validation preflight started",
            )
            try:
                package, report, metadata = await repair.run(
                    ctx,
                    variant,
                    package,
                    rounds=self.factory.settings.validation_repair_max_rounds,
                    budget=repair_budget,
                    phase="before_security",
                    metadata=metadata,
                )
            except Exception:
                logger.exception(
                    "validation preflight failed for run %s variant %s",
                    self.run_id,
                    variant,
                )
                report = ValidationReport.build(
                    [],
                    terraform_required=True,
                    abort_reason="internal_error",
                ).model_copy(update={"remediation": metadata})
            async with self.session_factory() as session:
                async with session.begin():
                    await PackageRepository(session).save_automatic_repairs(
                        self.run_id,
                        variant,
                        original_files=original_files,
                        files=package.files,
                    )
            await self.validation_stage.run(
                ctx, variant, package, prepared_report=report, already_validating=True
            )
        before_security_files = dict(package.files)
        try:
            scan = await stage.run(ctx, variant, package)
        except Exception:
            logger.exception(
                "security stage failed for run %s variant %s", self.run_id, variant
            )
            scan = await self._stage_error(variant, validation=False)
        if scan == PackageStatus.SCAN_ERROR:
            return scan
        async with self.session_factory() as session:
            remediated_row = await PackageRepository(session).get(self.run_id, variant)
            if remediated_row is None:
                raise LookupError("package not found")
            remediated_package = package.model_copy(
                update={
                    "files": dict(remediated_row.files),
                    "security_report": remediated_row.security_report,
                    "validation_report": remediated_row.validation_report,
                }
            )
        try:
            if repair is not None and repair_budget is not None:
                assert isinstance(self.validation_stage, ValidatorAgent)
                assert isinstance(stage, SecurityAgent)
                started_validation = time.monotonic()
                report = await validate_files(
                    self.validation_stage.engine, ctx.plan, remediated_package.files
                )
                await publish_measurement(
                    ctx,
                    variant,
                    "post_security_validation",
                    time.monotonic() - started_validation,
                    phase="after_security",
                )
                if (
                    remediated_package.files != before_security_files
                    and report.summary.result == "invalid"
                ):
                    remediated_package, report, metadata = await repair.run(
                        ctx,
                        variant,
                        remediated_package,
                        rounds=1,
                        budget=AgentBudget(
                            self.factory.settings.post_security_repair_deadline_seconds,
                            clock=ctx.clock,
                        ),
                        phase="after_security",
                        metadata=metadata,
                        report=report,
                    )
                # Final checks describe the same candidate, including rollback.
                remediated_package = remediated_package.model_copy(
                    update={"files": stage.safety.value(remediated_package.files)}
                )
                started_validation = time.monotonic()
                report = await validate_files(
                    self.validation_stage.engine, ctx.plan, remediated_package.files
                )
                await publish_measurement(
                    ctx,
                    variant,
                    "final_validation",
                    time.monotonic() - started_validation,
                )
                report = report.model_copy(update={"remediation": metadata})
                await self.writer.package_transition(
                    self.run_id,
                    variant,
                    PackageStatus.VALIDATING,
                    message="final validation and security verification",
                )
                async with self.session_factory() as session:
                    async with session.begin():
                        repository = PackageRepository(session)
                        await repository.save_automatic_repairs(
                            self.run_id,
                            variant,
                            original_files=original_files,
                            files=remediated_package.files,
                        )
                        await repository.save_validation_results(
                            self.run_id, variant, report
                        )
                scan = await stage.confirm_final(ctx, variant, remediated_package)
                validation = await self.validation_stage.run(
                    ctx,
                    variant,
                    remediated_package,
                    prepared_report=report,
                    already_validating=True,
                )
            else:
                validation = await self.validation_stage.run(
                    ctx, variant, remediated_package
                )
        except ToolFailure:
            return await self._stage_error(variant, validation=False)
        except Exception:
            logger.exception(
                "validation stage failed for run %s variant %s", self.run_id, variant
            )
            validation = await self._stage_error(variant, validation=True)
        target = readiness_after_validation(scan, validation)
        await self.writer.package_transition(
            self.run_id, variant, target, message=f"package {target.value}"
        )
        return target

    async def _run_core(self) -> RunStatus:
        await self.writer.run_transition(
            self.run_id, RunStatus.RUNNING, message="pipeline started"
        )
        architect = self.factory.create_architect(self.run_config)
        await self.writer.agent_state(
            self.run_id,
            AgentName.ARCHITECT,
            AgentState.RUNNING,
            message="architect started",
        )
        try:
            architect.parse_input(self.text)
            plan = await architect.generate_plan()
        except ArchitectError as error:
            await self.writer.agent_state(
                self.run_id,
                AgentName.ARCHITECT,
                AgentState.FAILED,
                previous=AgentState.RUNNING,
                message=str(error),
                failure_category=getattr(error, "llm_category", error.category),
            )
            await publish_telemetry(self.writer, self.run_id)
            await self.writer.run_transition(
                self.run_id,
                RunStatus.FAILED,
                message=str(error),
                error_message=str(error),
            )
            return RunStatus.FAILED
        await self.writer.agent_state(
            self.run_id,
            AgentName.ARCHITECT,
            AgentState.COMPLETED,
            previous=AgentState.RUNNING,
            message="architect completed",
        )
        await self.writer.event_log.append(
            self.run_id,
            AgentName.ARCHITECT,
            AgentState.COMPLETED,
            message="deployment plan created",
            payload=plan_created_payload(plan),
        )
        async with self.session_factory() as session:
            async with session.begin():
                repository = PackageRepository(session)
                for variant in Variant:
                    await repository.create(self.run_id, variant)
        for variant in Variant:
            await self.writer.event_log.append(
                self.run_id,
                AgentName.ORCHESTRATOR,
                PackageStatus.GENERATING,
                message="package generation queued",
                payload=package_status_payload(variant),
            )
        generators = self.factory.create_generators(self.run_config)
        results = await asyncio.gather(
            *(self._generate(generator, plan) for generator in generators),
            return_exceptions=True,
        )
        packages: dict[Variant, IaCPackage] = {}
        for result in results:
            if isinstance(result, BaseException):
                raise result
            variant, package = result
            if package is not None:
                packages[variant] = package
        if not packages:
            await publish_telemetry(self.writer, self.run_id)
            await self.writer.run_transition(
                self.run_id,
                RunStatus.FAILED,
                message="no package could be generated",
                error_message="no package could be generated",
            )
            return RunStatus.FAILED
        ctx = StageContext(
            self.run_id,
            self.writer,
            plan,
            self.clock,
            self.run_config.resolve(self.factory.settings).max_iterations
            if hasattr(self.factory, "settings")
            else self.run_config.max_iterations or 3,
        )
        await asyncio.gather(
            *(
                self._post_generation(ctx, variant, package)
                for variant, package in packages.items()
            )
        )
        async with self.session_factory() as session:
            rows = await PackageRepository(session).list_for_run(self.run_id)
        statuses = {Variant(row.variant): PackageStatus(row.status) for row in rows}
        target = classify_run(True, statuses)
        await publish_telemetry(self.writer, self.run_id)
        await self.writer.run_transition(
            self.run_id, target, message=f"pipeline {target.value}"
        )
        return target

    async def _fail_unexpected(self, message: str) -> None:
        await publish_telemetry(self.writer, self.run_id)
        async with self.session_factory() as session:
            row = await RunRepository(session).get(self.run_id)
        if row is not None and RunStatus(row.status) in {
            RunStatus.CREATED,
            RunStatus.RUNNING,
        }:
            await self.writer.run_transition(
                self.run_id,
                RunStatus.FAILED,
                message=message,
                error_message=message,
            )

    @traced("pipeline", "architect")
    async def run(self) -> RunStatus:
        try:
            return await self._run_core()
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(
                    asyncio.shield(
                        self._fail_unexpected("interrupted by server shutdown")
                    ),
                    timeout=5,
                )
            except Exception:
                logger.exception("could not settle cancelled run %s", self.run_id)
            raise
        except Exception:
            logger.exception("pipeline failed unexpectedly for run %s", self.run_id)
            try:
                await self._fail_unexpected("internal error; see server logs")
            except Exception:
                logger.exception("could not settle failed run %s", self.run_id)
            return RunStatus.FAILED
        finally:
            for workspace in self.workspaces.values():
                workspace.close()
