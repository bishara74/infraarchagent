"""Create an explicitly synthetic, rejected PR-04 package in the dev database."""

import argparse
import asyncio
import base64
import random
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from app.core.config import Settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_app_engine, make_session_factory
from app.domain.archive import package_zip, readiness_document
from app.domain.enums import AgentName, LLMProvider, PackageStatus, RunStatus, Variant
from app.events.kinds import run_status_payload
from app.events.log import EventLog
from app.events.publisher import NullPublisher
from app.pipeline.state import PipelineStateWriter
from scripts.phase9_common import evidence_directory, safe_main, write_json
from scripts.phase9_report import summary

SYNTHETIC = "benchmark synthetic package"


def require_dev_database(settings: Settings) -> None:
    url = urlparse(settings.database_url.get_secret_value())
    if url.path != "/infraarch" or url.username != "infraarch_app":
        raise ValueError(
            "Seeding requires the development infraarch database and app role."
        )


def synthetic_files(seed: int, source: str, length: int) -> dict[str, str]:
    return {
        f"benchmark/data-{index:03}.txt": source[offset : min(offset + 200_000, length)]
        for index, offset in enumerate(range(0, length, 200_000))
    }


def calibrated_files(seed: int, target: int, readiness: str) -> dict[str, str]:
    source = base64.b64encode(random.Random(seed).randbytes(target)).decode("ascii")
    length = len(source)
    for _ in range(6):
        files = synthetic_files(seed, source, length)
        archive_size = len(package_zip(files, readiness))
        if target * 0.995 <= archive_size <= target:
            return files
        length = min(len(source), max(1, int(length * target / archive_size) - 128))
    raise RuntimeError("Synthetic archive calibration failed")


async def seed_package(
    session_factory, *, seed: int = 704, archive_bytes: int = 9_990_000
) -> dict:
    run_id = uuid4()
    readiness = readiness_document(
        run_id=run_id,
        variant=Variant.COST,
        status=PackageStatus.NOT_PRODUCTION_READY,
        model="stub",
        labelled_at=datetime.now(UTC),
        review_action="reject",
        feedback=SYNTHETIC,
        security_report=None,
        validation_report=None,
    )
    files = calibrated_files(seed, archive_bytes, readiness)
    async with session_factory() as session:
        async with session.begin():
            await RunRepository(session).create(
                SYNTHETIC, LLMProvider.STUB, 1, model="stub", run_id=run_id
            )
            repository = PackageRepository(session)
            await repository.create(run_id, Variant.COST)
            await repository.save_files(run_id, Variant.COST, files)
    log = EventLog(session_factory, NullPublisher())
    writer = PipelineStateWriter(session_factory, log)
    await log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        RunStatus.CREATED,
        message=SYNTHETIC,
        payload=run_status_payload(),
    )
    await writer.run_transition(run_id, RunStatus.RUNNING, message=SYNTHETIC)
    for status in (
        PackageStatus.GENERATED,
        PackageStatus.SCANNING,
        PackageStatus.REMEDIATING,
        PackageStatus.SCAN_EXHAUSTED,
        PackageStatus.VALIDATING,
        PackageStatus.VALIDATION_ERROR,
        PackageStatus.PENDING_REVIEW,
    ):
        await writer.package_transition(
            run_id,
            Variant.COST,
            status,
            message=SYNTHETIC,
            error=SYNTHETIC if status == PackageStatus.VALIDATION_ERROR else None,
        )
    async with session_factory() as session:
        async with session.begin():
            previous = await writer.review_action(
                session, run_id, Variant.COST, "reject", SYNTHETIC
            )
    await writer.review_event(
        run_id,
        Variant.COST,
        PackageStatus.NOT_PRODUCTION_READY,
        previous,
        action="reject",
        reasons=["validation_error"],
    )
    await writer.run_transition(run_id, RunStatus.PARTIAL_SUCCESS, message=SYNTHETIC)
    return {
        "run_id": str(run_id),
        "synthetic": True,
        "label": "not_production_ready",
        "seed": seed,
        "file_count": len(files),
        "source_bytes": sum(len(value.encode()) for value in files.values()),
        "calibrated_archive_bytes": len(package_zip(files, readiness)),
        "target_archive_bytes": archive_bytes,
        "measurement": "Synthetic fixture; no scanner, validation or LLM executed.",
    }


async def run(args) -> None:
    settings = Settings(_env_file=None)
    require_dev_database(settings)
    directory = evidence_directory(
        "seed", args.output_dir, mode="synthetic", provider="stub", model="stub"
    )
    summary(
        directory / "summary.md",
        "Synthetic PR-04 package",
        "INCOMPLETE",
        ["Seeding started."],
    )
    engine = make_app_engine(settings)
    try:
        report = await seed_package(make_session_factory(engine), seed=args.seed)
        write_json(directory / "seed.json", report)
        summary(
            directory / "summary.md",
            "Synthetic PR-04 package",
            "PASS",
            [
                report["measurement"],
                f"Run: {report['run_id']}; "
                f"archive bytes: {report['calibrated_archive_bytes']}.",
                "Synthetic not_production_ready label; no successful scan claim.",
            ],
        )
        print(report["run_id"])
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=704)
    parser.add_argument("--output-dir", type=Path)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    safe_main(main)
