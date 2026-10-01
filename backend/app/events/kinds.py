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


def stage_notice_payload(variant: Variant, notice: str) -> dict[str, Any]:
    return {"kind": EventKind.STAGE_NOTICE, "variant": variant.value, "notice": notice}


def to_sse(record: EventRecord) -> str:
    kind = EventKind(record.payload["kind"])
    data = {
        "seq": record.seq,
        "kind": kind.value,
        "agent": record.agent_name.value,
        "status": record.new_state,
        "previous_status": record.previous_state,
        "message": record.message,
        "variant": record.payload.get("variant"),
        "timestamp": record.timestamp.isoformat(),
        "payload": dict(record.payload),
    }
    encoded = json.dumps(data, ensure_ascii=False)
    return f"id: {record.seq}\nevent: {kind.value}\ndata: {encoded}\n\n"
