"""Persist each transition before its event.

A hard crash between the two transactions leaves correct state but no event.
The separate transactions are the Phase 4 trade-off; startup recovery settles
nonterminal runs and replay recovers events that were committed but not published.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import AgentName, AgentState, PackageStatus, RunStatus, Variant
from app.events.kinds import (
    agent_state_payload,
    package_status_payload,
    run_status_payload,
)
from app.events.log import EventLog


class PipelineStateWriter:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], event_log: EventLog
    ) -> None:
        self.session_factory = session_factory
        self.event_log = event_log

    async def review_action(
        self,
        session: AsyncSession,
        run_id: UUID,
        variant: Variant,
        action: str,
        feedback: str | None,
    ) -> PackageStatus:
        """Caller owns the locked acceptance transaction; event follows commit."""
        return await PackageRepository(session).review_action(
            run_id, variant, action, feedback
        )

    async def review_event(
        self,
        run_id: UUID,
        variant: Variant,
        target: PackageStatus,
        previous: PackageStatus,
        *,
        action: str,
        reasons: list[str],
    ) -> None:
        payload: dict[str, Any] = {
            **package_status_payload(variant),
            "review_action": action,
            "review_reasons": reasons,
        }
        await self.event_log.append(
            run_id,
            AgentName.ORCHESTRATOR,
            target,
            previous,
            f"engineer review {action}",
            payload,
        )

    async def abort_review_retry(
        self, run_id: UUID, variant: Variant, *, reason: str
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                changes = await PackageRepository(session).abort_review_retry(
                    run_id, variant, reason
                )
        for previous, target in changes:
            await self.event_log.append(
                run_id,
                AgentName.ORCHESTRATOR,
                target,
                previous,
                reason,
                {**package_status_payload(variant), "review_retry_aborted": True},
            )

    async def run_transition(
        self,
        run_id: UUID,
        target: RunStatus,
        *,
        message: str,
        error_message: str | None = None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                _, previous = await RunRepository(session).transition_status(
                    run_id, target, error_message=error_message
                )
        await self.event_log.append(
            run_id,
            AgentName.ORCHESTRATOR,
            target,
            previous,
            message,
            run_status_payload(),
        )

    async def package_transition(
        self,
        run_id: UUID,
        variant: Variant,
        target: PackageStatus,
        *,
        message: str,
        error: str | None = None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                _, previous = await PackageRepository(session).transition_status(
                    run_id, variant, target, error=error
                )
        await self.event_log.append(
            run_id,
            AgentName.ORCHESTRATOR,
            target,
            previous,
            message,
            package_status_payload(variant),
        )

    async def agent_state(
        self,
        run_id: UUID,
        agent_name: AgentName,
        state: AgentState,
        *,
        message: str,
        variant: Variant | None = None,
        previous: AgentState | None = None,
        metrics: dict[str, Any] | None = None,
        failure_category: str | None = None,
    ) -> None:
        payload = agent_state_payload(variant)
        if metrics is not None:
            payload["metrics"] = metrics
        if failure_category is not None:
            payload["failure_category"] = failure_category
        await self.event_log.append(
            run_id,
            agent_name,
            state,
            previous,
            message,
            payload,
        )
