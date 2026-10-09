"""D-38 durable TIMESTAMPTZ recovery without retry-start events."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.domain.enums import PackageStatus, Variant
from app.main import create_app
from tests.integration.test_pipeline_review import pending_app, state


@pytest.mark.req("FR-S-09", "FR-P-04")
@pytest.mark.parametrize(
    "stage",
    [
        "remediating",
        "scanning",
        "scan_clean",
        "scan_exhausted",
        "validating",
        "valid",
        "invalid",
        "validation_error",
    ],
)
async def test_startup_recovers_timestamp_marked_retry_without_event(db_engines, stage):
    engine, _ = db_engines
    app, run_id = await pending_app(engine)
    async with app.state.session_factory() as session:
        async with session.begin():
            await app.state.writer.review_action(
                session, run_id, Variant.COST, "retry", "Fix"
            )
    # No retry acceptance event was written: simulate the state/event crash window.
    path = {
        "remediating": [],
        "scanning": ["scanning"],
        "scan_clean": ["scanning", "scan_clean"],
        "scan_exhausted": ["scan_exhausted"],
        "validating": ["scanning", "scan_clean", "validating"],
        "valid": ["scanning", "scan_clean", "validating", "valid"],
        "invalid": ["scanning", "scan_clean", "validating", "invalid"],
        "validation_error": [
            "scanning",
            "scan_clean",
            "validating",
            "validation_error",
        ],
    }[stage]
    for target in path:
        await app.state.writer.package_transition(
            run_id, Variant.COST, PackageStatus(target), message="fixture"
        )
    _, before = await state(app, run_id)
    assert before.review_retry_started_at.tzinfo is not None
    recovered_app = create_app(get_settings(), engine)
    async with recovered_app.router.lifespan_context(recovered_app):
        run, row = await state(recovered_app, run_id)
        assert run.status == "partial_success"
        assert row.status == "pending_review" and row.review_retry_started_at is None
        assert row.error == "review retry interrupted by server restart"
        assert row.review_feedback == "Fix" and row.files == before.files
    events = await recovered_app.state.event_log.list_after(run_id, None)
    count = len(events)
    async with recovered_app.router.lifespan_context(recovered_app):
        assert (
            len(await recovered_app.state.event_log.list_after(run_id, None)) == count
        )


@pytest.mark.req("FR-P-03", "FR-S-09")
async def test_unmarked_automated_recovery_unchanged(db_engines):
    app, run_id = await pending_app(db_engines[0], terminal=False)
    # Ordinary automated rows are NULL and keep their package state during run recovery.
    async with app.router.lifespan_context(app):
        run, row = await state(app, run_id)
        assert (
            run.status == "failed"
            and run.error_message == "interrupted by server restart"
        )
        assert row.status == "pending_review" and row.review_retry_started_at is None


@pytest.mark.req("NFR-01", "FR-S-09")
async def test_marker_column_timestamp_and_app_update_grant(db_engines):
    app, run_id = await pending_app(db_engines[0])
    _, row = await state(app, run_id)
    assert row.review_retry_started_at is None
    timestamp = datetime.now(UTC)
    async with db_engines[0].begin() as connection:
        await connection.execute(
            text(
                "UPDATE generated_packages SET review_retry_started_at=:started "
                "WHERE run_id=:run_id"
            ),
            {"started": timestamp, "run_id": run_id},
        )
        result = await connection.execute(
            text(
                "SELECT data_type, is_nullable, column_default "
                "FROM information_schema.columns WHERE table_name='generated_packages' "
                "AND column_name='review_retry_started_at'"
            )
        )
        assert result.one() == ("timestamp with time zone", "YES", None)
    _, row = await state(app, run_id)
    assert row.review_retry_started_at == timestamp
    async with app.state.session_factory() as session:
        assert await PackageRepository(session).list_review_retries() == [
            (run_id, Variant.COST)
        ]
