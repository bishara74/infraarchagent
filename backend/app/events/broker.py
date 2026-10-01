"""Single-process, per-run live event fan-out."""

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from app.events.publisher import EventRecord


class Subscription:
    def __init__(self, queue_size: int) -> None:
        self.queue: asyncio.Queue[EventRecord | None] = asyncio.Queue(queue_size)
        self.overflowed = False

    def __aiter__(self) -> AsyncIterator[EventRecord]:
        return self._events()

    async def _events(self) -> AsyncIterator[EventRecord]:
        while not self.overflowed:
            record = await self.queue.get()
            if record is None or self.overflowed:
                break
            yield record


class InMemoryBroker:
    def __init__(self, queue_size: int = 1000) -> None:
        if queue_size < 1:
            raise ValueError("queue size must be positive")
        self.queue_size = queue_size
        self._subscribers: dict[UUID, set[Subscription]] = defaultdict(set)

    @asynccontextmanager
    async def subscribe(self, run_id: UUID) -> AsyncIterator[Subscription]:
        subscription = Subscription(self.queue_size)
        self._subscribers[run_id].add(subscription)
        try:
            yield subscription
        finally:
            self._subscribers[run_id].discard(subscription)
            if not self._subscribers[run_id]:
                del self._subscribers[run_id]

    async def publish(self, record: EventRecord) -> None:
        for subscriber in tuple(self._subscribers.get(record.run_id, ())):
            if subscriber.overflowed:
                continue
            try:
                subscriber.queue.put_nowait(record)
            except asyncio.QueueFull:
                subscriber.overflowed = True
                while not subscriber.queue.empty():
                    subscriber.queue.get_nowait()
                subscriber.queue.put_nowait(None)
