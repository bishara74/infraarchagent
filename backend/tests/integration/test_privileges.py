from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.repositories.runs import RunRepository
from app.domain.enums import LLMProvider


@pytest.mark.req("NFR-01")
async def test_app_role_least_privilege(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    app, _ = db_engines
    for statement in (
        "DELETE FROM pipeline_runs",
        "UPDATE agent_events SET message = 'changed'",
        "DELETE FROM agent_events",
        "TRUNCATE agent_events, generated_packages, pipeline_runs",
        "TRUNCATE generated_packages",
        "TRUNCATE agent_events",
    ):
        with pytest.raises(DBAPIError) as denied:
            async with app.begin() as connection:
                await connection.execute(text(statement))
        assert denied.value.orig.sqlstate == "42501"
    async with app.begin() as connection:
        await connection.execute(text("DELETE FROM generated_packages"))


async def test_app_identity_insert_does_not_need_sequence_grant(
    db_session: AsyncSession,
) -> None:
    run = await RunRepository(db_session).create("AWS web app", LLMProvider.STUB, 3)
    result = await db_session.execute(
        text(
            "INSERT INTO agent_events "
            "(event_id, run_id, agent_name, new_state, timestamp) "
            "VALUES (:event_id, :run_id, 'orchestrator', 'running', :now) "
            "RETURNING seq"
        ),
        {"event_id": uuid4(), "run_id": run.run_id, "now": datetime.now(UTC)},
    )
    assert result.scalar_one() >= 1


async def test_restrict_blocks_owner_run_delete(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    _, owner = db_engines
    run = await RunRepository(db_session).create("AWS web app", LLMProvider.STUB, 3)
    await db_session.commit()
    async with owner.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO agent_events "
                "(event_id, run_id, agent_name, new_state, timestamp) "
                "VALUES (:event_id, :run_id, 'orchestrator', 'running', :now)"
            ),
            {"event_id": uuid4(), "run_id": run.run_id, "now": datetime.now(UTC)},
        )
    with pytest.raises(IntegrityError):
        async with owner.begin() as connection:
            await connection.execute(
                text("DELETE FROM pipeline_runs WHERE run_id = :run_id"),
                {"run_id": run.run_id},
            )
