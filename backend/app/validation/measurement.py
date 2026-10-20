"""Explicit descriptive stage timings, published only through EventLog."""

from typing import Any

from app.domain.enums import AgentName, PackageStatus, Variant
from app.events.kinds import stage_notice_payload
from app.pipeline.stages import StageContext
from app.pipeline.telemetry import publish
from app.validation.workspace import current_workspace

STAGES = frozenset(
    {
        "deterministic_repairs",
        "generation_gate",
        "initial_validation",
        "validation_repair_round",
        "post_security_validation",
        "final_validation",
        "final_security_scan",
        "security_iteration_verification",
    }
)


def initialization_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "init_seconds": sum(float(r.get("init_seconds", 0)) for r in records),
        "validate_seconds": sum(float(r.get("validate_seconds", 0)) for r in records),
        "init_runs": sum(
            r.get("init_outcome") == "initialized"
            or (r.get("init_seconds", 0) > 0 and not r.get("init_reused"))
            for r in records
        ),
        "init_reused": sum(bool(r.get("init_reused")) for r in records),
        "reinitializations": sum(
            r.get("reinitialization_reason") == "dependencies_changed" for r in records
        ),
    }


async def publish_measurement(
    ctx: StageContext,
    variant: Variant,
    stage: str,
    seconds: float,
    *,
    phase: str = "",
    **extra: Any,
) -> dict[str, Any]:
    if stage not in STAGES:
        raise ValueError("unknown measurement stage")
    record = {
        "stage": stage,
        "duration_seconds": max(0.0, seconds),
        "phase": phase,
        **extra,
    }
    workspace = current_workspace()
    if workspace is not None:
        workspace.measurements.append(record)
    agent = (
        AgentName(f"generator_{variant.value}")
        if phase == "generation"
        else AgentName.SECURITY
        if stage in {"security_iteration_verification", "final_security_scan"}
        else AgentName.VALIDATOR
    )
    await ctx.writer.event_log.append(
        ctx.run_id,
        agent,
        PackageStatus.GENERATING
        if phase == "generation"
        else PackageStatus.SCANNING
        if agent == AgentName.SECURITY
        else PackageStatus.VALIDATING,
        message="stage measurement",
        payload=stage_notice_payload(
            variant, "stage measurement", {"measurement": record}
        ),
    )
    await publish(ctx.writer, ctx.run_id)
    return record
