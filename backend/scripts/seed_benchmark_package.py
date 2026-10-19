"""Create an explicitly synthetic, rejected PR-04 package in the dev database."""

import argparse
import asyncio
import base64
import random
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_database_engine, make_session_factory
from app.domain.archive import package_zip, readiness_document
from app.domain.enums import AgentName, LLMProvider, PackageStatus, RunStatus, Variant
from app.events.kinds import package_status_payload, run_status_payload
from app.events.log import EventLog
from app.events.publisher import NullPublisher
from app.pipeline.state import PipelineStateWriter
from scripts.phase9_common import evidence_directory, safe_main, write_json
from scripts.phase9_report import summary

SYNTHETIC = "benchmark synthetic package"


class SeedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")
    database_url: SecretStr


class SeedConfigurationError(ValueError):
    """Fixed safe prerequisite message, never validation input or credentials."""


def load_seed_settings() -> SeedSettings:
    try:
        settings = SeedSettings()
    except ValidationError:
        raise SeedConfigurationError(
            "PR-04 seed requires exported DATABASE_URL for the development app role."
        ) from None
    require_dev_database(settings)
    return settings


def require_dev_database(settings: SeedSettings) -> None:
    url = urlparse(settings.database_url.get_secret_value())
    if url.path != "/infraarch" or url.username != "infraarch_app":
        raise SeedConfigurationError(
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
    decision = {
        "action": "reject",
        "reviewer_name": None,
        "reason": (
            "Synthetic fixture; no human review, scanner, validation or LLM executed."
        ),
        "decided_at": datetime.now(UTC).isoformat(),
        "identity_basis": "synthetic benchmark fixture",
    }
    readiness = readiness_document(
        run_id=run_id,
        variant=Variant.COST,
        status=PackageStatus.REJECTED,
        model="stub",
        labelled_at=datetime.now(UTC),
        review_action="reject",
        feedback=SYNTHETIC,
        security_report=None,
        validation_report=None,
        decision=decision,
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
            row = await PackageRepository(session).get_for_update(run_id, Variant.COST)
            assert row is not None
            row.review_decision = decision
    await log.append(
        run_id,
        AgentName.ORCHESTRATOR,
        PackageStatus.REJECTED,
        previous,
        message=SYNTHETIC,
        payload={
            **package_status_payload(Variant.COST),
            "review_action": "reject",
            "review_decision": decision,
            "review_reasons": ["synthetic_fixture"],
        },
    )
    await writer.run_transition(run_id, RunStatus.PARTIAL_SUCCESS, message=SYNTHETIC)
    return {
        "run_id": str(run_id),
        "synthetic": True,
        "label": "rejected",
        "seed": seed,
        "file_count": len(files),
        "source_bytes": sum(len(value.encode()) for value in files.values()),
        "calibrated_archive_bytes": len(package_zip(files, readiness)),
        "target_archive_bytes": archive_bytes,
        "measurement": "Synthetic fixture; no scanner, validation or LLM executed.",
    }


async def run(args) -> None:
    settings = load_seed_settings()
    directory = evidence_directory(
        "seed", args.output_dir, mode="synthetic", provider="stub", model="stub"
    )
    summary(
        directory / "summary.md",
        "Synthetic PR-04 package",
        "INCOMPLETE",
        ["Seeding started."],
    )
    engine = make_database_engine(settings.database_url)
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
                "Synthetic rejected label; no successful scan claim.",
            ],
        )
        print(report["run_id"])
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=704)
    parser.add_argument("--output-dir", type=Path)
    try:
        asyncio.run(run(parser.parse_args()))
    except SeedConfigurationError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    safe_main(main)
