# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
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
    message_prefix: str | None = None,
) -> PackageStatus:
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, variant)
        if row is None:
            raise LookupError("package not found")
        original_files, files = row.original_files, row.files
    assessment = assess_plan_conformance(ctx.plan, original_files, files)
    if safety is not None:
        assessment = PlanConformanceAssessment.model_validate(
            safety.value(assessment.model_dump(mode="json"))
        )
    target = readiness_after_validation(
        scan, validation, plan_conformance_conflict=bool(assessment.conflicts)
    )
    async with ctx.writer.event_log.transaction(ctx.run_id) as transaction:
        repository = PackageRepository(transaction.session)
        row = await repository.get_for_update(ctx.run_id, variant)
        if row is None:
            raise LookupError("package not found")
        if row.original_files != original_files or row.files != files:
            raise RuntimeError("package files changed during final assessment")
        await repository.save_plan_conformance(row, assessment)
        if message_prefix is not None:
            await ctx.writer.package_transition_in(
                transaction, variant, target, message=f"{message_prefix} {target.value}"
            )
    return target
