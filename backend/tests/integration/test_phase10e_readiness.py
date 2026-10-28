"""FR-S-02/03/07: persisted final evidence is replaced after review retries."""

from dataclasses import replace

import pytest

from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus as P
from app.domain.enums import Variant
from app.pipeline.readiness import final_readiness
from tests.integration.test_security_agent import setup
from tests.unit.test_phase10b_conformance import files, plan

pytestmark = pytest.mark.req("FR-S-02", "FR-S-03", "FR-S-07")


async def test_final_readiness_uses_immutable_original_and_clears_retry_conflict(
    db_engines,
):
    engine, _ = db_engines
    ctx, _ = await setup(engine)
    ctx = replace(ctx, plan=plan())
    sessions = make_session_factory(engine)
    original = files()
    flipped = files({"internal": True})
    async with sessions() as session, session.begin():
        await PackageRepository(session).save_automatic_repairs(
            ctx.run_id, Variant.SECURITY, original_files=original, files=flipped
        )
    assert (
        await final_readiness(sessions, ctx, Variant.SECURITY, P.SCAN_CLEAN, P.VALID)
        == P.PENDING_REVIEW
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row.original_files == original and row.files == flipped
        assert row.validation_report["plan_conformance"]["conflicts"]
    # An unchanged retry still sees the Generator baseline, not retry-start files.
    assert (
        await final_readiness(sessions, ctx, Variant.SECURITY, P.SCAN_CLEAN, P.VALID)
        == P.PENDING_REVIEW
    )
    async with sessions() as session, session.begin():
        await PackageRepository(session).save_automatic_repairs(
            ctx.run_id, Variant.SECURITY, original_files=flipped, files=original
        )
    assert (
        await final_readiness(sessions, ctx, Variant.SECURITY, P.SCAN_CLEAN, P.VALID)
        == P.CHECKS_PASSED
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row.original_files == original
        assert not row.validation_report["plan_conformance"]["conflicts"]


async def test_missing_generator_original_only_records_information(db_engines):
    engine, _ = db_engines
    ctx, _ = await setup(engine)
    sessions = make_session_factory(engine)
    ctx = replace(ctx, plan=plan())
    assert (
        await final_readiness(sessions, ctx, Variant.SECURITY, P.SCAN_CLEAN, P.VALID)
        == P.CHECKS_PASSED
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row.original_files is None
        assert row.validation_report["plan_conformance"]["notes"]


@pytest.mark.req("NFR-01")
async def test_final_assessment_redacts_canary_before_persistence(
    db_engines, canary_key, monkeypatch
):
    import json

    from app.core.safety import PublicDataSafety
    from app.domain.conformance import PlanConflict, PlanConformanceAssessment

    engine, _ = db_engines
    ctx, _ = await setup(engine)
    sessions = make_session_factory(engine)
    canary = canary_key.llm_api_key.get_secret_value()
    evidence = PlanConformanceAssessment(
        notes=[
            PlanConflict(
                service="edge",
                resource="aws_lb." + canary,
                property="internal",
                expected="public",
                assessment="unknown",
                message=canary,
            )
        ]
    )
    monkeypatch.setattr(
        "app.pipeline.readiness.assess_plan_conformance", lambda *args: evidence
    )
    assert (
        await final_readiness(
            sessions,
            ctx,
            Variant.SECURITY,
            P.SCAN_CLEAN,
            P.VALID,
            safety=PublicDataSafety(canary_key),
        )
        == P.CHECKS_PASSED
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert canary not in json.dumps(row.validation_report)
