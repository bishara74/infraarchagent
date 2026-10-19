"""Public event payload and SSE framing contract."""

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.enums import AgentName, Variant
from app.events.kinds import package_generated_payload, to_sse
from app.events.publisher import EventRecord


@pytest.mark.req("FR-P-04", "FR-G-07")
def test_sse_frame_and_package_metadata_exclude_contents() -> None:
    payload = package_generated_payload(
        Variant.COST,
        {"terraform/main.tf": "SECRET CONTENT"},
        {"attempts": 1},
        "notes",
    )
    record = EventRecord(
        uuid4(),
        42,
        uuid4(),
        AgentName.GENERATOR_COST,
        "generating",
        "generated",
        datetime.now(UTC),
        "done",
        payload,
    )
    frame = to_sse(record)
    assert frame.startswith("id: 42\nevent: package_generated\ndata: ")
    data = json.loads(frame.split("data: ", 1)[1])
    assert data["status"] == "generated"
    assert data["previous_status"] == "generating"
    assert data["variant"] == "cost"
    assert data["payload"]["paths"] == ["terraform/main.tf"]
    assert "SECRET CONTENT" not in frame


@pytest.mark.req("FR-S-08", "FR-P-04")
@pytest.mark.parametrize(
    "previous,action,migrated,expected",
    [
        ("valid", None, "checks_passed", "checks_passed"),
        ("pending_review", "approve", "engineer_approved", "engineer_approved"),
        (None, None, "pending_review", "pending_review"),
        ("valid", None, None, "pending_review"),
    ],
)
def test_legacy_sse_mapping_discloses_evidence(previous, action, migrated, expected):
    record = EventRecord(
        uuid4(),
        1,
        uuid4(),
        AgentName.ORCHESTRATOR,
        previous,
        "production_ready",
        datetime.now(UTC),
        "historical",
        {"kind": "package_status", "variant": "cost", "review_action": action},
    )
    data = json.loads(to_sse(record, legacy_status=migrated).split("data: ", 1)[1])
    assert data["status"] == expected
    assert "Historical label mapped" in data["payload"]["legacy_label_interpretation"]
    assert "legacy_label_interpretation" not in record.payload
