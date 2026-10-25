"""Assemble safe results; HTTP and database statements stay at their boundaries."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.schemas import MissingVariant, PackageResult, ResultsResponse, RunResult
from app.core.config import Settings
from app.core.safety import PublicDataSafety
from app.core.telemetry import safe_records
from app.db.models import AgentEvent, GeneratedPackage
from app.db.repositories.results import ResultsRepository, ResultsSnapshot
from app.domain.agent_selection import reported_selections
from app.domain.archive import bundle_zip, package_zip, readiness_document
from app.domain.enums import LLMProvider, PackageStatus, RunStatus, Variant
from app.domain.lessons import lesson_manifest
from app.domain.plan import DeploymentPlan
from app.domain.review import package_presentation
from app.domain.states import is_downloadable
from app.pipeline.review import ReviewError
from app.security.profiles import assess


def run_lessons(snapshot: ResultsSnapshot) -> dict[str, Any]:
    # Finished telemetry wins over its earlier dispatch authorization. Durable
    # authorizations preserve evidence if a process dies during transport.
    records = [
        *snapshot.telemetry,
        *[
            {
                "kind": "llm",
                "id": row.get("call_id"),
                "call_id": row.get("call_id"),
                "role": row.get("role"),
                "outcome": "authorized",
                "lesson_usage": row.get("lessons"),
            }
            for row in snapshot.lesson_uses
        ],
    ]
    return lesson_manifest(snapshot.run.lessons, safe_records(records))


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
            retried = (
                await repository.review_retry_before(run_id, variant, label.seq)
                if label
                else False
            )
        assert snapshot is not None
        return self._archive(run_id, variant, snapshot, row, label, retried)

    def _archive(
        self,
        run_id: UUID,
        variant: Variant,
        snapshot: ResultsSnapshot,
        row: GeneratedPackage,
        label: AgentEvent | None,
        retried: bool,
    ) -> tuple[bytes, str]:
        status = PackageStatus(row.status)
        lessons = run_lessons(snapshot)
        readiness = readiness_document(
            run_id=run_id,
            variant=variant,
            status=status,
            model=snapshot.run.model,
            agent_models=snapshot.run.agent_models,
            labelled_at=label.timestamp if label else None,
            review_action=label.payload.get("review_action") if label else None,
            feedback=row.review_feedback,
            security_report=row.security_report,
            validation_report=row.validation_report,
            files=row.files,
            retried=retried,
            decision=row.review_decision,
            policy_profile=snapshot.run.policy_profile or "strict",
            assessments=assess(
                {
                    "security_report": row.security_report,
                    "validation_report": row.validation_report,
                    "files": row.files,
                }
            ),
            lessons=lessons,
        )
        archive = package_zip(
            self.safety.value(row.files),
            self.safety.text(readiness),
            self.safety.value(lessons),
        )
        return (
            archive,
            f"infraarch-{str(run_id)[:8]}-{variant.value}-{status.value}.zip",
        )

    async def download_all(self, run_id: UUID) -> tuple[bytes, str]:
        packages = {}
        async with self.sessions() as session:
            repository = ResultsRepository(session)
            snapshot = await repository.archive_snapshot(run_id)
            if snapshot is None:
                raise ReviewError(404, "not_found", "Run not found.")
            rows = {Variant(row.variant): row for row in snapshot.packages}
            if set(rows) != set(Variant) or any(
                not is_downloadable(PackageStatus(row.status)) for row in rows.values()
            ):
                raise ReviewError(
                    409,
                    "not_downloadable",
                    "All three variants must have readiness labels before downloading.",
                )
            for variant in Variant:
                row = rows[variant]
                label = await repository.label_event(
                    run_id, variant, PackageStatus(row.status)
                )
                retried = (
                    await repository.review_retry_before(run_id, variant, label.seq)
                    if label
                    else False
                )
                archive, filename = self._archive(
                    run_id, variant, snapshot, row, label, retried
                )
                packages[variant] = (archive, filename, row.status)
        return bundle_zip(
            run_id,
            packages,
            lessons=self.safety.value(run_lessons(snapshot)),
        ), f"infraarch-{str(run_id)[:8]}-all.zip"

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
                        retry_in_progress=item.review_retry_started_at is not None,
                        **self.safety.value(
                            {
                                "error": item.error,
                                "files": item.files,
                                "original_files": item.original_files,
                                "security_report": item.security_report,
                                "validation_report": item.validation_report,
                                "review_feedback": item.review_feedback,
                                "review_decision": {
                                    **item.review_decision,
                                    "category": item.review_decision.get("category"),
                                }
                                if item.review_decision
                                else None,
                                "profile_assessments": assess(
                                    {
                                        "security_report": item.security_report,
                                        "validation_report": item.validation_report,
                                        "files": item.files,
                                    }
                                ),
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
            telemetry=self.safety.value(safe_records(snapshot.telemetry)) or None,
            run=RunResult(
                lessons=self.safety.value(run_lessons(snapshot)),
                id=row.run_id,
                agent_models=self.safety.value(reported_selections(row.agent_models)),
                policy_profile="contextual-v1"
                if row.policy_profile == "contextual-v1"
                else "strict",
                status=run_status,
                input_text=self.safety.text(row.input_text),
                start_time=row.start_time,
                end_time=row.end_time,
                provider=LLMProvider(row.llm_provider),
                model=self.safety.value(row.model),
                max_iterations=row.max_iterations,
                error_message=self.safety.value(row.error_message),
            ),
            plan=DeploymentPlan.model_validate(self.safety.value(snapshot.plan))
            if snapshot.plan is not None
            else None,
            packages=packages,
            missing_variants=missing,
        )
