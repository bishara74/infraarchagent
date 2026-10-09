"""Assemble safe results; HTTP and database statements stay at their boundaries."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.schemas import MissingVariant, PackageResult, ResultsResponse, RunResult
from app.core.config import Settings
from app.core.safety import PublicDataSafety
from app.db.repositories.results import ResultsRepository
from app.domain.archive import package_zip, readiness_document
from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.domain.plan import DeploymentPlan
from app.domain.review import package_presentation
from app.domain.states import is_downloadable
from app.pipeline.review import ReviewError


class ResultsService:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], settings: Settings
    ) -> None:
        self.sessions = sessions
        self.safety = PublicDataSafety(settings)

    async def download(self, run_id: UUID, variant: Variant) -> tuple[bytes, str]:
        async with self.sessions() as session:
            repository = ResultsRepository(session)
            snapshot = await repository.snapshot(run_id)
            row = (
                next(
                    (item for item in snapshot.packages if item.variant == variant),
                    None,
                )
                if snapshot
                else None
            )
            if row is None or PackageStatus(row.status) == PackageStatus.FAILED:
                raise ReviewError(404, "not_found", "Package not found.")
            status = PackageStatus(row.status)
            if not is_downloadable(status):
                raise ReviewError(
                    409, "not_downloadable", "Package does not have a readiness label."
                )
            label = await repository.label_event(run_id, variant, status)
        assert snapshot is not None
        readiness = readiness_document(
            run_id=run_id,
            variant=variant,
            status=status,
            model=snapshot.run.model,
            labelled_at=label.timestamp if label else None,
            review_action=label.payload.get("review_action") if label else None,
            feedback=row.review_feedback,
            security_report=row.security_report,
            validation_report=row.validation_report,
        )
        archive = package_zip(self.safety.value(row.files), self.safety.text(readiness))
        return (
            archive,
            f"infraarch-{str(run_id)[:8]}-{variant.value}-{status.value}.zip",
        )

    async def results(self, run_id: UUID) -> ResultsResponse | None:
        async with self.sessions() as session:
            snapshot = await ResultsRepository(session).snapshot(run_id)
        if snapshot is None:
            return None
        row = snapshot.run
        run_status = RunStatus(row.status)
        packages = []
        missing = []
        order = {variant.value: index for index, variant in enumerate(Variant)}
        for item in sorted(snapshot.packages, key=lambda item: order[item.variant]):
            status = PackageStatus(item.status)
            if status == PackageStatus.FAILED:
                missing.append(
                    MissingVariant(
                        variant=Variant(item.variant),
                        error=self.safety.text(
                            item.error or "package generation failed"
                        ),
                    )
                )
            elif status != PackageStatus.GENERATING and item.files:
                packages.append(
                    PackageResult(
                        variant=Variant(item.variant),
                        status=status,
                        iteration_count=item.iteration_count,
                        **self.safety.value(
                            {
                                "error": item.error,
                                "files": item.files,
                                "original_files": item.original_files,
                                "security_report": item.security_report,
                                "validation_report": item.validation_report,
                                "review_feedback": item.review_feedback,
                                **package_presentation(
                                    run_status,
                                    status,
                                    item.files,
                                    item.security_report,
                                    item.validation_report,
                                    item.error,
                                ),
                            }
                        ),
                    )
                )
        return ResultsResponse(
            run=RunResult(
                id=row.run_id,
                status=run_status,
                input_text=self.safety.text(row.input_text),
                start_time=row.start_time,
                end_time=row.end_time,
                provider=LLMProvider(row.llm_provider),
                model=row.model,
                max_iterations=row.max_iterations,
                error_message=self.safety.value(row.error_message),
            ),
            plan=DeploymentPlan.model_validate(self.safety.value(snapshot.plan))
            if snapshot.plan is not None
            else None,
            packages=packages,
            missing_variants=missing,
        )
