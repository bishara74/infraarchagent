"""Live broker isolation, fan-out, ordering, and bounded overflow."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.enums import AgentName
from app.events.broker import InMemoryBroker
from app.events.publisher import EventRecord


def record(run_id: object, seq: int) -> EventRecord:
    return EventRecord(
        uuid4(),
        seq,
        run_id,
        AgentName.ORCHESTRATOR,
        None,
        "running",
        datetime.now(UTC),
        None,
        {"kind": "run_status"},
    )  # type: ignore[arg-type]


@pytest.mark.req("FR-P-04")
async def test_broker_fanout_isolation_and_order() -> None:
    broker = InMemoryBroker(3)
    first = uuid4()
    second = uuid4()
    async with (
        broker.subscribe(first) as a,
        broker.subscribe(first) as b,
        broker.subscribe(second) as c,
    ):
        await broker.publish(record(first, 1))
        await broker.publish(record(first, 2))
        await broker.publish(record(second, 3))
        assert [await a.queue.get(), await a.queue.get()]
        assert [await b.queue.get(), await b.queue.get()]
        assert (await c.queue.get()).seq == 3  # type: ignore[union-attr]
        assert c.queue.empty()


@pytest.mark.req("FR-P-04")
async def test_broker_overflow_ends_only_slow_subscriber() -> None:
    broker = InMemoryBroker(1)
    run_id = uuid4()
    async with broker.subscribe(run_id) as slow, broker.subscribe(run_id) as fast:
        await broker.publish(record(run_id, 1))
        assert (await fast.queue.get()).seq == 1  # type: ignore[union-attr]
        await broker.publish(record(run_id, 2))
        assert slow.overflowed
        assert [item async for item in slow] == []
        assert (await fast.queue.get()).seq == 2  # type: ignore[union-attr]
