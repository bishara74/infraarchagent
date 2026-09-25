from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.domain.paths import UnsafePathError
from app.domain.states import IllegalTransition


@pytest.mark.req("FR-G-07")
async def test_repository_round_trip(db_session: AsyncSession) -> None:
    runs = RunRepository(db_session)
    packages = PackageRepository(db_session)
    run = await runs.create("a simple AWS web application", LLMProvider.STUB, 3)
    await runs.set_status(run.run_id, RunStatus.RUNNING)
    await packages.create(run.run_id, Variant.COST)
    await packages.save_files(run.run_id, Variant.COST, {"main.tf": "resource {}"})
    await packages.set_status(run.run_id, Variant.COST, PackageStatus.GENERATED)
    run_id = run.run_id
    await db_session.commit()
    db_session.expire_all()

    found = await runs.get(run_id)
    assert found is not None and found.status == RunStatus.RUNNING
    assert found.start_time.tzinfo is not None
    assert found.start_time.utcoffset().total_seconds() == 0
    listed = await packages.list_for_run(run_id)
    assert len(listed) == 1
    assert listed[0].files == {"main.tf": "resource {}"}
    assert listed[0].created_at.tzinfo is not None
    assert listed[0].created_at.utcoffset().total_seconds() == 0
    with pytest.raises(UnsafePathError):
        await packages.save_files(run_id, Variant.COST, {"../bad": "oops"})


async def test_illegal_repository_transitions_leave_rows_unchanged(
    db_session: AsyncSession,
) -> None:
    runs = RunRepository(db_session)
    packages = PackageRepository(db_session)
    run = await runs.create("a simple AWS web application", LLMProvider.STUB, 3)
    await packages.create(run.run_id, Variant.COST)
    with pytest.raises(IllegalTransition):
        await runs.set_status(run.run_id, RunStatus.SUCCESS)
    with pytest.raises(IllegalTransition):
        await packages.set_status(
            run.run_id, Variant.COST, PackageStatus.SCAN_EXHAUSTED
        )
    assert (await runs.get(run.run_id)).status == RunStatus.CREATED  # type: ignore[union-attr]
    assert (
        await packages.get(run.run_id, Variant.COST)
    ).status == PackageStatus.GENERATING  # type: ignore[union-attr]


@pytest.mark.parametrize(
    "terminal", [RunStatus.SUCCESS, RunStatus.PARTIAL_SUCCESS, RunStatus.FAILED]
)
async def test_repository_terminal_run_status_is_frozen(
    db_session: AsyncSession, terminal: RunStatus
) -> None:
    runs = RunRepository(db_session)
    run = await runs.create("a simple AWS web application", LLMProvider.STUB, 3)
    await runs.set_status(run.run_id, RunStatus.RUNNING)
    await runs.set_status(run.run_id, terminal)
    for target in RunStatus:
        with pytest.raises(IllegalTransition):
            await runs.set_status(run.run_id, target)
    current = await runs.get(run.run_id)
    assert current is not None and current.status == terminal
    assert current.end_time is not None and current.end_time.tzinfo is not None


async def test_invalid_status_rejected_by_check(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    _, owner = db_engines
    async with owner.begin() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(
                text(
                    "INSERT INTO pipeline_runs "
                    "(run_id, input_text, status, start_time, "
                    "llm_provider, max_iterations) "
                    "VALUES (:id, 'x', 'impossible', :now, 'stub', 3)"
                ),
                {"id": uuid4(), "now": datetime.now(UTC)},
            )


async def test_locked_transitions_refresh_stale_session_state(
    db_engines: tuple[AsyncEngine, AsyncEngine], db_session: AsyncSession
) -> None:
    app, _ = db_engines
    runs = RunRepository(db_session)
    packages = PackageRepository(db_session)
    run = await runs.create("AWS web app", LLMProvider.STUB, 3)
    await packages.create(run.run_id, Variant.COST)
    run_id = run.run_id
    await db_session.commit()

    assert (await runs.get(run_id)).status == RunStatus.CREATED  # type: ignore[union-attr]
    assert (await packages.get(run_id, Variant.COST)).status == PackageStatus.GENERATING  # type: ignore[union-attr]
    async with make_session_factory(app)() as other_session:
        await RunRepository(other_session).set_status(run_id, RunStatus.RUNNING)
        await PackageRepository(other_session).set_status(
            run_id, Variant.COST, PackageStatus.GENERATED
        )
        await other_session.commit()

    completed = await runs.set_status(run_id, RunStatus.SUCCESS)
    assert completed.status == RunStatus.SUCCESS
    assert (
        await packages.set_status(run_id, Variant.COST, PackageStatus.SCANNING)
    ).status == PackageStatus.SCANNING
