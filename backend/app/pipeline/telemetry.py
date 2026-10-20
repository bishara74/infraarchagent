"""Collect stage diagnostics and persist only through EventLog."""

import asyncio
import inspect
import sys
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from app.core.deadlines import bounded_phase
from app.core.telemetry import Collector, current, safe_records, scope
from app.domain.enums import AgentName, AgentState

P = ParamSpec("P")
T = TypeVar("T")


async def publish(writer: Any, run_id: Any) -> None:
    collector = current.get()
    if collector is None:
        return
    async with collector.lock:
        await _publish(writer, run_id, collector)


async def _publish(writer: Any, run_id: Any, collector: Collector) -> None:
    pending = collector.pending()
    # Batch at stage/iteration boundaries, never add a transaction per tool.
    for offset in range(0, len(pending), 24):
        batch = pending[offset : offset + 24]
        async with bounded_phase("event_publication"):
            await writer.event_log.append(
                run_id,
                AgentName.ORCHESTRATOR,
                AgentState.RUNNING,
                message="runtime telemetry",
                payload={
                    "kind": "stage_notice",
                    "notice": "runtime telemetry",
                    "telemetry": safe_records(batch),
                },
            )
        collector.published.update(r["id"] for r in batch)


def traced(
    phase: str, role: str
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]
]:
    def decorate(
        function: Callable[P, Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        signature = inspect.signature(function)

        @wraps(function)
        async def call(*args: P.args, **kwargs: P.kwargs) -> T:
            bound = signature.bind(*args, **kwargs).arguments
            owner: Any = args[0]
            ctx: Any = bound.get("ctx")
            generator = bound.get("generator")
            variant = bound.get("variant", getattr(generator, "variant", None))
            run_id = getattr(ctx, "run_id", getattr(owner, "run_id", None))
            writer = getattr(ctx, "writer", getattr(owner, "writer", None))
            token = (
                current.set(Collector())
                if current.get() is None and hasattr(writer, "event_log")
                else None
            )
            selected_role = "generator_" + str(variant) if role == "generator" else role
            publication_end = None
            if token is not None and function.__name__ == "_loop" and ctx is not None:
                options = bound.get("kwargs", {})
                allowance = (
                    60.0
                    if options.get("kind") == "review_retry"
                    else owner.settings.security_deadline_seconds
                )
                publication_end = (
                    options.get("iteration_started", ctx.clock()) + allowance
                )
            iteration = bound.get("iteration_index", 0)
            if function.__name__ == "_fix_iteration":
                # Focus selection uses zero-based indices; published fix passes
                # and telemetry use the existing one-based iteration number.
                iteration += 1
            try:
                with scope(
                    run_id=str(run_id) if run_id else None,
                    variant=str(variant) if variant is not None else None,
                    phase=bound.get("phase", phase),
                    role=selected_role,
                    iteration=iteration,
                ):
                    return await function(*args, **kwargs)
            finally:
                if token is not None:
                    try:
                        if (
                            writer is not None
                            and run_id is not None
                            and sys.exc_info()[0] is None
                        ):
                            budget = bound.get("budget")
                            remaining = (
                                budget.remaining()
                                if budget is not None
                                else publication_end - ctx.clock()
                                if publication_end is not None
                                else None
                            )
                            if remaining is None:
                                await publish(writer, run_id)
                            elif remaining > 0:
                                try:
                                    async with asyncio.timeout(remaining):
                                        await publish(writer, run_id)
                                except TimeoutError:
                                    # Reporting never creates a fresh allowance.
                                    pass
                    finally:
                        current.reset(token)

        return call

    return decorate
