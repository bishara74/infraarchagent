"""Context-local, source-free runtime observations. No database or file I/O."""

import asyncio
import inspect
import math
import time
from collections.abc import Callable, Coroutine, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, TypeVar
from uuid import UUID, uuid4

KINDS = {"llm", "tool", "scan", "verification", "partial_group", "cache"}
P = ParamSpec("P")
T = TypeVar("T")
OPERATIONS = {"checkov", "trivy", "terraform.init", "terraform.validate"}
TEXT_FIELDS = {
    "provider",
    "module",
    "model",
    "served_by",
    "outcome",
    "category",
    "format_reason",
    "operation",
    "phase",
    "role",
    "variant",
    "action",
    "request_style",
    "response_format",
    "requested_effort",
    "call_kind",
}
NUMBER_FIELDS = {
    "elapsed_seconds",
    "queue_seconds",
    "execution_seconds",
    "overrun_seconds",
}
INTEGER_FIELDS = {
    "attempt",
    "package_attempt",
    "iteration",
    "input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "cached_input_tokens",
    "response_characters",
}
ID_FIELDS = {"id", "call_id", "run_id", "parent_id"}
TIME_FIELDS = {"started_at", "finished_at", "execution_started_at"}
BOOL_FIELDS = {"executed", "completed", "deadline_exceeded"}


def safe_records(raw: object) -> list[dict[str, Any]]:
    """Re-allowlist observations at public/export/file boundaries."""
    from app.core.logging import RedactingFilter

    if not isinstance(raw, list):
        return []
    result = []
    seen: set[str] = set()
    redact = RedactingFilter().redact
    for item in raw:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("kind"), str)
            or item["kind"] not in KINDS
        ):
            continue
        clean: dict[str, Any] = {"kind": item["kind"]}
        for key, value in item.items():
            if value is None and key in (
                TEXT_FIELDS | NUMBER_FIELDS | INTEGER_FIELDS | ID_FIELDS | TIME_FIELDS
            ):
                clean[key] = None
            elif key in TEXT_FIELDS and isinstance(value, str):
                clean[key] = redact(value)[:128]
            elif key in NUMBER_FIELDS and type(value) in {int, float}:
                clean[key] = value if math.isfinite(value) and value >= 0 else None
            elif key in INTEGER_FIELDS:
                clean[key] = value if type(value) is int and value >= 0 else None
            elif key in BOOL_FIELDS and type(value) is bool:
                clean[key] = value
            elif key in ID_FIELDS and isinstance(value, str):
                try:
                    clean[key] = str(UUID(value))
                except ValueError:
                    clean[key] = None
            elif key in TIME_FIELDS and isinstance(value, str):
                try:
                    stamp = datetime.fromisoformat(value)
                    clean[key] = (
                        stamp.astimezone(UTC).isoformat() if stamp.tzinfo else None
                    )
                except ValueError:
                    clean[key] = None
        identity = clean.get("id")
        if identity:
            if identity in seen:
                continue
            seen.add(identity)
        result.append(clean)
    return result


@dataclass
class Collector:
    records: list[dict[str, Any]] = field(default_factory=list)
    published: set[str] = field(default_factory=set)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def pending(self) -> list[dict[str, Any]]:
        return [
            r
            for r in self.records
            if r.get("finished_at") and r["id"] not in self.published
        ]


current: ContextVar[Collector | None] = ContextVar("runtime_collector", default=None)
tags: ContextVar[dict[str, Any] | None] = ContextVar("runtime_tags", default=None)
# Nested semaphore wrappers contribute to the same invocation's queue time.
queue_wait: ContextVar[list[float] | None] = ContextVar("tool_queue_wait", default=None)
active_tool: ContextVar[dict[str, Any] | None] = ContextVar(
    "tool_invocation", default=None
)


@contextmanager
def scope(**values: Any) -> Iterator[None]:
    token = tags.set({**(tags.get() or {}), **values})
    try:
        yield
    finally:
        tags.reset(token)


def observe(record: dict[str, Any]) -> dict[str, Any]:
    value = {**(tags.get() or {}), **record}
    collector = current.get()
    if collector is not None:
        collector.records.append(value)
    return value


@contextmanager
def span(kind: str, **values: Any) -> Iterator[dict[str, Any]]:
    record = {
        "id": str(uuid4()),
        "kind": kind,
        "started_at": datetime.now(UTC).isoformat(),
        "completed": False,
        "executed": kind != "cache",
        **values,
    }
    started = time.monotonic()
    try:
        with scope(parent_id=record["id"]):
            yield record
        record.setdefault("outcome", "success")
        record["completed"] = True
    except asyncio.CancelledError:
        record["outcome"] = "cancelled"
        raise
    except TimeoutError:
        record["outcome"] = "timeout"
        raise
    except Exception as error:
        # Only locally defined categories, never exception messages.
        from app.scanners.runner import ToolFailure

        record["outcome"] = (
            error.category if isinstance(error, ToolFailure) else "error"
        )
        raise
    finally:
        record["elapsed_seconds"] = max(0.0, time.monotonic() - started)
        if kind == "tool":
            record["execution_seconds"] = (
                max(0.0, record["elapsed_seconds"] - record.get("queue_seconds", 0.0))
                if record["executed"]
                else 0.0
            )
        record["finished_at"] = datetime.now(UTC).isoformat()
        observe(record)


@contextmanager
def invocation(operation: str) -> Iterator[None]:
    """Wrap a runner call, including semaphore queues and cancellation cleanup."""
    if current.get() is None or active_tool.get() is not None:
        yield
        return
    waits: list[float] = []
    token = queue_wait.set(waits)
    try:
        with span(
            "tool",
            operation=operation,
            executed=False,
            attempt=(tags.get() or {}).get("attempt", 1),
        ) as record:
            tool_token = active_tool.set(record)
            try:
                yield
            finally:
                record["queue_seconds"] = sum(waits)
                active_tool.reset(tool_token)
    finally:
        queue_wait.reset(token)


def execution_started() -> None:
    record = active_tool.get()
    if record is not None:
        record["executed"] = True
        record["execution_started_at"] = datetime.now(UTC).isoformat()


def unevaluated_group(reason: str) -> None:
    stamp = datetime.now(UTC).isoformat()
    observe(
        {
            "kind": "partial_group",
            "id": str(uuid4()),
            "executed": False,
            "completed": False,
            "outcome": reason,
            "elapsed_seconds": None,
            "started_at": stamp,
            "finished_at": stamp,
        }
    )


def tool_observed(
    function: Callable[P, Coroutine[Any, Any, T]],
) -> Callable[P, Coroutine[Any, Any, T]]:
    signature = inspect.signature(function)

    @wraps(function)
    async def call(*parameters: P.args, **kwargs: P.kwargs) -> T:
        if current.get() is None:
            return await function(*parameters, **kwargs)
        bound = signature.bind(*parameters, **kwargs).arguments
        tool, args = bound["tool"], bound["args"]
        operation = (
            tool
            if tool in {"checkov", "trivy"}
            else (
                "terraform." + args[1] if tool == "terraform" and len(args) > 1 else ""
            )
        )
        if operation not in OPERATIONS:
            return await function(*parameters, **kwargs)
        with invocation(operation):
            return await function(*parameters, **kwargs)

    return call


def timed(
    kind: str,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]
]:
    def decorate(
        function: Callable[P, Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        signature = inspect.signature(function)

        @wraps(function)
        async def call(*args: P.args, **kwargs: P.kwargs) -> T:
            if current.get() is None:
                return await function(*args, **kwargs)
            arguments = signature.bind(*args, **kwargs).arguments
            values: dict[str, Any] = {
                k: arguments[k]
                for k in ("iteration", "attempt", "module")
                if k in arguments
            }
            owner = arguments.get("self")
            action = getattr(owner, "record", {}).get("verification_action")
            if action:
                values["action"] = action
            with scope(**values), span(kind):
                return await function(*args, **kwargs)

        return call

    return decorate


def interval_union(records: list[dict[str, Any]]) -> float:
    intervals = sorted(
        (
            datetime.fromisoformat(r["started_at"]).timestamp(),
            datetime.fromisoformat(r["finished_at"]).timestamp(),
        )
        for r in records
        if r.get("executed") and r.get("finished_at") and r.get("started_at")
    )
    total, end = 0.0, float("-inf")
    for start, stop in intervals:
        total += max(0.0, stop - max(start, end))
        end = max(end, stop)
    return total


def summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    tools = [r for r in records if r["kind"] == "tool"]
    groups = [r for r in records if r["kind"] == "partial_group"]
    return {
        "tool_invocations": len(tools),
        "tool_executions": sum(r.get("executed") is True for r in tools),
        "tool_invocation_seconds": sum(r.get("elapsed_seconds", 0) for r in tools),
        "tool_wall_seconds": interval_union([{**r, "executed": True} for r in tools]),
        "tool_queue_seconds": sum(r.get("queue_seconds", 0) for r in tools),
        "tool_execution_wall_seconds": interval_union(
            [
                {**r, "started_at": r.get("execution_started_at")}
                for r in tools
                if r.get("executed")
            ]
        ),
        "partial_groups_started": sum(r.get("executed") is True for r in groups),
        "partial_groups_completed": sum(r.get("completed") is True for r in groups),
        "partial_groups_interrupted": sum(
            r.get("executed") is True and not r.get("completed") for r in groups
        ),
        "partial_groups_unevaluated": sum(r.get("executed") is False for r in groups),
        "partial_group_seconds": sum(r.get("elapsed_seconds") or 0 for r in groups),
        "cache_reuses": sum(r["kind"] == "cache" for r in records),
    }
