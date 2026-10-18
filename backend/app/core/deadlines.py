"""Private absolute deadlines shared by iteration work and finalization."""

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class DeadlineWindow:
    end: float
    clock: Callable[[], float]
    timings: dict[str, float] = field(default_factory=dict)

    def remaining(self) -> float:
        return max(0.0, self.end - self.clock())

    def check(self) -> None:
        if self.remaining() <= 0:
            raise TimeoutError


active_deadline: ContextVar[DeadlineWindow | None] = ContextVar(
    "iteration_deadline", default=None
)


@asynccontextmanager
async def bounded_phase(name: str) -> AsyncIterator[None]:
    window = active_deadline.get()
    if window is None:
        yield
        return
    window.check()
    started = time.monotonic()
    try:
        async with asyncio.timeout(window.remaining()):
            yield
            window.check()
    finally:
        window.timings[name] = (
            window.timings.get(name, 0.0) + time.monotonic() - started
        )


def deadline_bound(
    name: str,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    def decorate(function: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(function)
        async def call(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                async with bounded_phase(name):
                    return await function(*args, **kwargs)
            except Exception as error:
                # PostgreSQL can enforce the same bound before asyncio's
                # callback runs. Preserve the timeout classification.
                state = getattr(getattr(error, "orig", None), "sqlstate", None)
                if active_deadline.get() and state in {"57014", "55P03"}:
                    raise TimeoutError from None
                raise

        return call

    return decorate


@asynccontextmanager
async def iteration_window(
    end: float, clock: Callable[[], float], record: dict[str, Any]
) -> AsyncIterator[None]:
    window = DeadlineWindow(end, clock)
    token = active_deadline.set(window)
    try:
        async with bounded_phase("complete_iteration"):
            yield
    finally:
        record["deadline_timings"] = window.timings
        record["deadline_overrun_seconds"] = max(0.0, clock() - end)
        active_deadline.reset(token)
