"""Pluggable package stages; the Phase 4 production scanner is unavailable."""

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

UNAVAILABLE_MESSAGE = "security scanning is not available in this build"


@dataclass(frozen=True)
class StageContext:
    run_id: UUID
    writer: PipelineStateWriter
    plan: DeploymentPlan
    clock: Callable[[], float] = time.monotonic


class SecurityStage(Protocol):
    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus: ...


class ValidationStage(Protocol):
    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus: ...


class UnavailableSecurityStage:
    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.SECURITY,
            AgentState.RUNNING,
            message="security stage started",
            variant=variant,
        )
        await ctx.writer.package_transition(
            ctx.run_id,
            variant,
            PackageStatus.SCANNING,
            message="security stage started",
        )
        await ctx.writer.event_log.append(
            ctx.run_id,
            AgentName.SECURITY,
            PackageStatus.SCANNING,
            message=UNAVAILABLE_MESSAGE,
            payload=stage_notice_payload(variant, UNAVAILABLE_MESSAGE),
        )
        await ctx.writer.package_transition(
            ctx.run_id,
            variant,
            PackageStatus.SCAN_ERROR,
            message=UNAVAILABLE_MESSAGE,
            error=UNAVAILABLE_MESSAGE,
        )
        await ctx.writer.agent_state(
            ctx.run_id,
            AgentName.SECURITY,
            AgentState.FAILED,
            previous=AgentState.RUNNING,
            message=UNAVAILABLE_MESSAGE,
            variant=variant,
        )
        return PackageStatus.SCAN_ERROR


class UnavailableValidationStage:
    async def run(
        self, ctx: StageContext, variant: Variant, package: IaCPackage
    ) -> PackageStatus:
        raise RuntimeError("validation stage is unavailable in this build")
