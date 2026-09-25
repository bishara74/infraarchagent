"""Durable per-run event log.

For each run, commit order equals seq order across any number of writers,
provided every writer inserts through append(): the transaction-scoped
PostgreSQL advisory lock is acquired before the identity value is drawn.
Values increase but are not consecutive because other runs share the sequence.
Publish order equals seq order only per EventLog instance. The application
therefore owns exactly one instance per process, exposed through one accessor.
Phase 4 SSE filtering of seq <= last sent would drop a late-published event
if multiple instances in the same process published out of order.
"""

import asyncio
import json
import logging
import weakref
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import AgentEvent
from app.domain.enums import AgentName, AgentState, PackageStatus, RunStatus
from app.events.publisher import EventRecord, Publisher

logger = logging.getLogger(__name__)
STATE_VALUES = {
    item.value for enum in (RunStatus, PackageStatus, AgentState) for item in enum
}


class EventLog:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], publisher: Publisher
    ) -> None:
        self.session_factory = session_factory
        self.publisher = publisher
        self._locks: weakref.WeakValueDictionary[UUID, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )

    def _run_lock(self, run_id: UUID) -> asyncio.Lock:
        lock = self._locks.get(run_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[run_id] = lock
        return lock

    async def _acquire_advisory_lock(self, session: AsyncSession, run_id: UUID) -> None:
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:run_id, 0))"),
            {"run_id": str(run_id)},
        )

    async def _after_insert(self, record: EventRecord) -> None:
        """Internal no-op seam for deterministic transaction-order tests."""
        return None

    async def append(
        self,
        run_id: UUID,
        agent_name: AgentName,
        new_state: RunStatus | PackageStatus | AgentState | str,
        previous_state: RunStatus | PackageStatus | AgentState | str | None = None,
        message: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> EventRecord:
        if str(new_state) not in STATE_VALUES or (
            previous_state is not None and str(previous_state) not in STATE_VALUES
        ):
            raise ValueError("invalid event state")
        try:
            name = AgentName(agent_name)
        except ValueError as error:
            raise ValueError("invalid agent name") from error
        data = {} if payload is None else payload
        if not isinstance(data, dict):
            raise ValueError("event payload must be an object")
        try:
            encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).encode(
                "utf-8"
            )
        except (TypeError, ValueError) as error:
            raise ValueError("event payload must be JSON serialisable") from error
        if len(encoded) > 64 * 1024:
            raise ValueError("event payload exceeds 64 KB")

        event_id = uuid4()
        timestamp = datetime.now(UTC)
        async with self._run_lock(run_id):
            async with self.session_factory() as session:
                async with session.begin():
                    await self._acquire_advisory_lock(session, run_id)
                    result = await session.execute(
                        insert(AgentEvent)
                        .values(
                            event_id=event_id,
                            run_id=run_id,
                            agent_name=name,
                            previous_state=(
                                str(previous_state)
                                if previous_state is not None
                                else None
                            ),
                            new_state=str(new_state),
                            timestamp=timestamp,
                            message=message,
                            payload=data,
                        )
                        .returning(AgentEvent.event_id, AgentEvent.seq)
                    )
                    inserted_id, seq = result.one()
                    record = EventRecord(
                        event_id=inserted_id,
                        seq=seq,
                        run_id=run_id,
                        agent_name=name,
                        previous_state=(
                            str(previous_state) if previous_state is not None else None
                        ),
                        new_state=str(new_state),
                        timestamp=timestamp,
                        message=message,
                        payload=data,
                    )
                    await self._after_insert(record)
            try:
                await self.publisher.publish(record)
            except Exception:
                logger.exception("event publish failed for run %s seq %s", run_id, seq)
            return record

    async def list_after(
        self, run_id: UUID, after_seq: int | None
    ) -> list[EventRecord]:
        statement = select(AgentEvent).where(AgentEvent.run_id == run_id)
        if after_seq is not None:
            statement = statement.where(AgentEvent.seq > after_seq)
        statement = statement.order_by(AgentEvent.seq)
        async with self.session_factory() as session:
            rows = list(await session.scalars(statement))
        return [
            EventRecord(
                event_id=row.event_id,
                seq=row.seq,
                run_id=row.run_id,
                agent_name=AgentName(row.agent_name),
                previous_state=row.previous_state,
                new_state=row.new_state,
                timestamp=row.timestamp,
                message=row.message,
                payload=row.payload,
            )
            for row in rows
        ]
