"""Typed event payloads and the public SSE wire format."""

import json
from enum import StrEnum
from typing import Any

from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.events.publisher import EventRecord


class EventKind(StrEnum):
    RUN_STATUS = "run_status"
    AGENT_STATE = "agent_state"
    PLAN_CREATED = "plan_created"
    PACKAGE_STATUS = "package_status"
    PACKAGE_GENERATED = "package_generated"
    STAGE_NOTICE = "stage_notice"


def run_status_payload() -> dict[str, Any]:
    return {"kind": EventKind.RUN_STATUS}


def agent_state_payload(variant: Variant | None = None) -> dict[str, Any]:
    return {
        "kind": EventKind.AGENT_STATE,
        "variant": variant.value if variant else None,
    }


def plan_created_payload(plan: DeploymentPlan) -> dict[str, Any]:
    return {"kind": EventKind.PLAN_CREATED, "plan": plan.model_dump(mode="json")}


def package_status_payload(variant: Variant) -> dict[str, Any]:
    return {"kind": EventKind.PACKAGE_STATUS, "variant": variant.value}


def package_generated_payload(
    variant: Variant, files: dict[str, str], metrics: dict[str, Any], notes: str | None
) -> dict[str, Any]:
    return {
        "kind": EventKind.PACKAGE_GENERATED,
        "variant": variant.value,
        "file_count": len(files),
        "total_chars": sum(len(value) for value in files.values()),
        "paths": sorted(files),
        "notes": notes[:1000] if notes is not None else None,
        "metrics": metrics,
    }


def stage_notice_payload(
    variant: Variant, notice: str, metrics: dict[str, Any] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "kind": EventKind.STAGE_NOTICE,
        "variant": variant.value,
        "notice": notice,
    }
    if metrics:
        payload.update(metrics)
    return payload


def event_status(record: EventRecord, legacy_status: str | None = None) -> str:
    if record.new_state == "not_production_ready":
        return "rejected"
    if record.new_state != "production_ready":
        return record.new_state
    if (
        record.payload.get("review_action") == "approve"
        or record.previous_state == "pending_review"
    ):
        return "engineer_approved"
    # Only the migrated current row can establish an automatic legacy result.
    return legacy_status or "pending_review"


def to_sse(record: EventRecord, *, legacy_status: str | None = None) -> str:
    kind = EventKind(record.payload["kind"])
    data: dict[str, Any] = {
        "seq": record.seq,
        "kind": kind.value,
        "agent": record.agent_name.value,
        "status": event_status(record, legacy_status),
        "previous_status": record.previous_state,
        "message": record.message,
        "variant": record.payload.get("variant"),
        "timestamp": record.timestamp.isoformat(),
        "payload": dict(record.payload),
    }
    if record.new_state in {"production_ready", "not_production_ready"}:
        data["payload"]["legacy_label_interpretation"] = (
            "Historical label mapped to "
            + data["status"]
            + "; original immutable event retained."
        )
    encoded = json.dumps(data, ensure_ascii=False)
    return f"id: {record.seq}\nevent: {kind.value}\ndata: {encoded}\n\n"
