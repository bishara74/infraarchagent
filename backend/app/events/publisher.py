"""Publisher contract; a live broker will replace NullPublisher in Phase 4."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.domain.enums import AgentName


@dataclass(frozen=True)
class EventRecord:
    event_id: UUID
    seq: int
    run_id: UUID
    agent_name: AgentName
    previous_state: str | None
    new_state: str
    timestamp: datetime
    message: str | None
    payload: Mapping[str, Any]


class Publisher(Protocol):
    async def publish(self, event: EventRecord) -> None: ...


class NullPublisher:
    async def publish(self, event: EventRecord) -> None:
        return None


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[EventRecord] = []

    async def publish(self, event: EventRecord) -> None:
        self.events.append(event)
