"""FR-S-07: assess persisted final files before initial or retry readiness."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.safety import PublicDataSafety
from app.db.repositories.packages import PackageRepository
from app.domain.conformance import PlanConformanceAssessment
from app.domain.enums import PackageStatus, Variant
from app.domain.states import readiness_after_validation
from app.pipeline.stages import StageContext
from app.security.plan_conformance import assess_plan_conformance


async def final_readiness(
    sessions: async_sessionmaker[AsyncSession],
    ctx: StageContext,
    variant: Variant,
    scan: PackageStatus,
    validation: PackageStatus,
    *,
    safety: PublicDataSafety | None = None,
) -> PackageStatus:
    async with sessions() as session, session.begin():
        repository = PackageRepository(session)
        row = await repository.get_for_update(ctx.run_id, variant)
        if row is None:
            raise LookupError("package not found")
        assessment = assess_plan_conformance(ctx.plan, row.original_files, row.files)
        if safety is not None:
            assessment = PlanConformanceAssessment.model_validate(
                safety.value(assessment.model_dump(mode="json"))
            )
        await repository.save_plan_conformance(row, assessment)
        return readiness_after_validation(
            scan, validation, plan_conformance_conflict=bool(assessment.conflicts)
        )
