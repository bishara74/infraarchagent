# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Commit each transition with its audit event.

The transaction closes the crash gap between state and event. SSE replay
recovers a committed event if the process stops before publishing it.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deadlines import deadline_bound
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import AgentName, AgentState, PackageStatus, RunStatus, Variant
from app.domain.states import cancellation_fails_package
from app.events.kinds import (
    agent_state_payload,
    package_status_payload,
    run_status_payload,
)
from app.events.log import EventLog, RunEventTransaction


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
        """Update the package inside the caller's locked acceptance transaction."""
        return await PackageRepository(session).review_action(
            run_id, variant, action, feedback
        )

    async def review_event(
        self,
        transaction: RunEventTransaction,
        variant: Variant,
        target: PackageStatus,
        previous: PackageStatus,
        *,
        action: str,
        reasons: list[str],
        decision: dict[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            **package_status_payload(variant),
            "review_action": action,
            "review_reasons": reasons,
            "review_decision": decision,
        }
        await transaction.append(
            AgentName.ORCHESTRATOR,
            target,
            previous,
            f"engineer review {action}",
            payload,
            event_id=UUID(decision["decision_id"])
            if decision and decision.get("decision_id")
            else None,
        )

    async def abort_review_retry(
        self, run_id: UUID, variant: Variant, *, reason: str
    ) -> None:
        async with self.event_log.transaction(run_id) as transaction:
            changes = await PackageRepository(transaction.session).abort_review_retry(
                run_id, variant, reason
            )
            for previous, target in changes:
                await transaction.append(
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
        async with self.event_log.transaction(run_id) as transaction:
            await self.run_transition_in(
                transaction, target, message=message, error_message=error_message
            )

    async def run_transition_in(
        self,
        transaction: RunEventTransaction,
        target: RunStatus,
        *,
        message: str,
        error_message: str | None = None,
    ) -> None:
        _, previous = await RunRepository(transaction.session).transition_status(
            transaction.run_id, target, error_message=error_message
        )
        await transaction.append(
            AgentName.ORCHESTRATOR,
            target,
            previous,
            message,
            run_status_payload(),
        )

    @deadline_bound("closing_state_event")
    async def package_transition(
        self,
        run_id: UUID,
        variant: Variant,
        target: PackageStatus,
        *,
        message: str,
        error: str | None = None,
    ) -> None:
        async with self.event_log.transaction(run_id) as transaction:
            await self.package_transition_in(
                transaction, variant, target, message=message, error=error
            )

    async def package_transition_in(
        self,
        transaction: RunEventTransaction,
        variant: Variant,
        target: PackageStatus,
        *,
        message: str,
        error: str | None = None,
        cancelling: bool = False,
    ) -> None:
        _, previous = await PackageRepository(transaction.session).transition_status(
            transaction.run_id, variant, target, error=error, cancelling=cancelling
        )
        await transaction.append(
            AgentName.ORCHESTRATOR,
            target,
            previous,
            message,
            package_status_payload(variant),
        )

    async def cancel_run(self, run_id: UUID, identity: str) -> None:
        message = f"cancelled by {identity}"
        async with self.event_log.transaction(run_id) as transaction:
            rows = await PackageRepository(transaction.session).list_for_run(run_id)
            for row in rows:
                if cancellation_fails_package(PackageStatus(row.status)):
                    await self.package_transition_in(
                        transaction,
                        Variant(row.variant),
                        PackageStatus.FAILED,
                        message="cancelled by user",
                        error="cancelled by user",
                        cancelling=True,
                    )
            await self.run_transition_in(
                transaction, RunStatus.CANCELLED, message=message, error_message=message
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
        transaction: RunEventTransaction | None = None,
    ) -> None:
        payload = agent_state_payload(variant)
        if metrics is not None:
            payload["metrics"] = metrics
        if failure_category is not None:
            payload["failure_category"] = failure_category
        if transaction is None:
            await self.event_log.append(
                run_id, agent_name, state, previous, message, payload
            )
        else:
            await transaction.append(agent_name, state, previous, message, payload)
