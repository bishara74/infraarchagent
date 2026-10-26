"""Read immutable review events independently of retained package payloads."""

from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentEvent
from app.domain.review_categories import CATEGORIES
from app.events.kinds import EventKind


class ReviewHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def read(
        self, filters: dict[str, Any], *, page: int | None = None
    ) -> tuple[list[Any], int]:
        await self.session.connection(
            execution_options={"isolation_level": "REPEATABLE READ"}
        )
        conditions = [
            AgentEvent.payload["kind"].astext == EventKind.PACKAGE_STATUS,
            AgentEvent.payload["review_action"].astext.in_(["approve", "reject"]),
        ]
        if category := filters.get("category"):
            column = AgentEvent.payload["review_decision"]["category"].astext
            conditions.append(
                or_(column.is_(None), ~column.in_(CATEGORIES))
                if category == "not_recorded"
                else column == category
            )
        if variant := filters.get("variant"):
            column = AgentEvent.payload["variant"].astext
            conditions.append(
                or_(column.is_(None), ~column.in_(["cost", "performance", "security"]))
                if variant == "not_recorded"
                else column == variant
            )
        if identity := filters.get("decision_id"):
            conditions.append(AgentEvent.event_id == UUID(identity))
        if rule := filters.get("blocking_rule"):
            conditions.append(
                AgentEvent.payload["review_action"].astext
                == filters.get("decision", "reject")
            )
            conditions.append(
                AgentEvent.payload["review_decision"][
                    "remaining_blocking_rules"
                ].contains([rule])
            )
        if decision := filters.get("decision"):
            conditions.append(AgentEvent.payload["review_action"].astext == decision)
        if start := filters.get("date_from"):
            conditions.append(
                AgentEvent.timestamp
                >= datetime.combine(date.fromisoformat(start), datetime.min.time(), UTC)
            )
        if end := filters.get("date_to"):
            end_date = date.fromisoformat(end)
            if end_date < date.max:
                conditions.append(
                    AgentEvent.timestamp
                    < datetime.combine(
                        end_date + timedelta(days=1), datetime.min.time(), UTC
                    )
                )
        total = int(
            await self.session.scalar(
                select(func.count()).select_from(AgentEvent).where(*conditions)
            )
            or 0
        )
        statement = (
            select(
                AgentEvent.event_id,
                AgentEvent.run_id,
                AgentEvent.payload["variant"].astext.label("variant"),
                AgentEvent.previous_state,
                AgentEvent.new_state,
                AgentEvent.payload["review_action"].astext.label("decision"),
                AgentEvent.payload["review_decision"].label("details"),
                AgentEvent.timestamp,
            )
            .where(*conditions)
            .order_by(AgentEvent.timestamp.desc(), AgentEvent.seq.desc())
        )
        if page is not None:
            statement = statement.limit(25).offset((page - 1) * 25)
        return list((await self.session.execute(statement)).mappings()), total
