"""Pluggable package stages and the Phase 5 validation placeholder."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.enums import AgentName, AgentState, PackageStatus, Variant
from app.domain.models import IaCPackage
from app.domain.plan import DeploymentPlan
from app.events.kinds import stage_notice_payload
from app.pipeline.state import PipelineStateWriter


@dataclass(frozen=True)
class StageContext:
    run_id: UUID
    writer: PipelineStateWriter
    plan: DeploymentPlan
    clock: Callable[[], float] = time.monotonic
    max_iterations: int = 3


class SecurityStage(Protocol):
    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus: ...


class ValidationStage(Protocol):
    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus: ...


class UnavailableValidationStage:
    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        message = "validation is not available in this build"
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.VALIDATOR,
            AgentState.RUNNING,
            message="validation started",
            variant=variant,
        )
        await ctx.writer.package_transition(
            ctx.run_id,
            variant,
            PackageStatus.VALIDATING,
            message="validation started",
        )
        await ctx.writer.event_log.append(
            ctx.run_id,
            AgentName.VALIDATOR,
            PackageStatus.VALIDATING,
            message=message,
            payload=stage_notice_payload(variant, message),
        )
        await ctx.writer.package_transition(
            ctx.run_id,
            variant,
            PackageStatus.VALIDATION_ERROR,
            message=message,
            error=message,
        )
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.VALIDATOR,
            AgentState.FAILED,
            previous=AgentState.RUNNING,
            message=message,
            variant=variant,
        )
        return PackageStatus.VALIDATION_ERROR
