"""Persist each transition before its event.

A hard crash between the two transactions leaves correct state but no event.
The separate transactions are the Phase 4 trade-off; startup recovery settles
nonterminal runs and replay recovers events that were committed but not published.
"""

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
    ) -> None:
        await self.event_log.append(
            run_id,
            agent_name,
            state,
            previous,
            message,
            agent_state_payload(variant),
        )
