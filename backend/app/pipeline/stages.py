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
        raise RuntimeError("validation stage is unavailable in this build")
