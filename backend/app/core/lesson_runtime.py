"""Single-process lesson dispatch ownership and sticky revocation.

The normal disabled path has no installed hook. Only eligible Architect and
Generator adapters register one; the kill switch detaches it synchronously
under the same short gate used to authorize an outbound transport task.
"""

import asyncio
from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.repositories.lessons import LessonRepository
from app.domain.enums import AgentName, AgentState
from app.domain.lessons import content_hash, render_lessons
from app.domain.run_config import RunConfig
from app.events.log import EventLog
from app.llm.base import LLMAdapter


class LessonRuntime:
    def __init__(self, sessions: async_sessionmaker[AsyncSession], events: EventLog):
        self.sessions, self.events = sessions, events
        self.gate = asyncio.Lock()
        self.enabled: bool | None = None
        self.generation = 0
        self.adapters: dict[UUID, set[LLMAdapter]] = defaultdict(set)
        self.revoked: set[UUID] = set()

    def disable(self) -> None:
        self.enabled = False
        self.generation += 1
        for run_id, adapters in self.adapters.items():
            self.revoked.add(run_id)
            for adapter in adapters:
                adapter.lesson_hook = None
                adapter.lesson_gate = None
                adapter.lesson_provenance = self.unused("disabled_during_run")

    def synchronize(self, control: dict[str, Any]) -> None:
        self.enabled = control["enabled"]
        self.generation = max(self.generation, control["disable_generation"])

    @staticmethod
    def unused(reason: str) -> dict[str, Any]:
        return {
            "enabled": False,
            "set_version": 0,
            "set_hash": content_hash([]),
            "lesson_ids": [],
            "block_hash": None,
            "self_approved": False,
            "reason": reason,
        }

    def bind(self, adapter: LLMAdapter, config: RunConfig, role: str) -> None:
        snapshot = config.lessons
        reason = (snapshot or {}).get("reason", "unconfigured")
        adapter.lesson_provenance = self.unused(reason)
        if (
            not snapshot
            or not snapshot.get("lessons_enabled")
            or config.lesson_run_id is None
        ):
            return
        run_id = config.lesson_run_id
        if (
            self.enabled is False
            or run_id in self.revoked
            or snapshot["disable_generation"] < self.generation
        ):
            adapter.lesson_provenance = self.unused("disabled_during_run")
            return
        if content_hash(snapshot["entries"]) != snapshot["set_hash"]:
            adapter.lesson_provenance = self.unused("invalid_snapshot")
            return
        block, selected = render_lessons(snapshot["entries"], role)
        if not block:
            adapter.lesson_provenance = self.unused("no_applicable_lessons")
            return
        self.generation = max(self.generation, snapshot["disable_generation"])
        self.adapters[run_id].add(adapter)
        adapter.lesson_provenance = self.unused("not_dispatched")

        async def prepare(prompt: str, call_id: str) -> tuple[str, dict[str, Any]]:
            # Called under gate by the adapter. No disable can interleave between
            # this check, the durable use record and transport authorization.
            try:
                async with self.sessions() as session, session.begin():
                    control = await LessonRepository(session).control()
                    permitted = (
                        control.runtime_enabled
                        and control.disable_generation == snapshot["disable_generation"]
                    )
                if not permitted:
                    self.disable()
                    return prompt, self.unused("disabled_during_run")
                used_rows = [
                    row for row in snapshot["entries"] if row["id"] in selected
                ]
                usage = {
                    "enabled": True,
                    "set_version": snapshot["set_version"],
                    "set_hash": snapshot["set_hash"],
                    "lesson_ids": selected,
                    "block_hash": content_hash(block),
                    "self_approved": any(row["self_approved"] for row in used_rows),
                    "reason": "used",
                }
                await self.events.append(
                    run_id,
                    AgentName.ORCHESTRATOR,
                    AgentState.RUNNING,
                    message="advisory lessons authorized for model attempt",
                    payload={
                        "kind": "stage_notice",
                        "notice": "lesson use",
                        "role": role,
                        "call_id": call_id,
                        "lessons": usage,
                    },
                )
                return prompt + "\n" + block, usage
            except asyncio.CancelledError:
                raise
            except Exception:
                # Failing to prove eligibility/use provenance fails closed. Never
                # return exception text or the source prompt in a diagnostic.
                self.revoked.add(run_id)
                for bound in self.adapters.get(run_id, set()):
                    bound.lesson_hook = None
                    bound.lesson_gate = None
                    bound.lesson_provenance = self.unused("eligibility_unavailable")
                return prompt, self.unused("eligibility_unavailable")

        adapter.lesson_hook = prepare
        adapter.lesson_gate = self.gate

    def release(self, run_id: UUID) -> None:
        for adapter in self.adapters.pop(run_id, set()):
            adapter.lesson_hook = None
            adapter.lesson_gate = None
        self.revoked.discard(run_id)
