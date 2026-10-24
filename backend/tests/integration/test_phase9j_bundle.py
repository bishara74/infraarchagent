"""FR-UI-06 / NFR-01: unchanged labelled payloads in an atomic all-three bundle."""

import asyncio
import hashlib
import json
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

import pytest
from pydantic import SecretStr

from app.db.repositories.packages import PackageRepository
from app.db.repositories.results import ResultsRepository
from app.domain.enums import PackageStatus, Variant
from tests.integration.test_pipeline_review import (
    client_for,
    pending_app,
    review_url,
    validation_report,
)


async def all_labelled(engine, *, approve_cost=True):
    app, run = await pending_app(engine)
    for variant in (Variant.PERFORMANCE, Variant.SECURITY):
        async with app.state.session_factory() as session, session.begin():
            repo = PackageRepository(session)
            await repo.create(run, variant)
            await repo.save_files(
                run,
                variant,
                {
                    "terraform/main.tf": f"# {variant.value}\nterraform {{}}\n",
                    "INFRAARCHAGENT_READINESS.md": "User-provided collision\n",
                },
            )
        for target in (
            PackageStatus.GENERATED,
            PackageStatus.SCANNING,
            PackageStatus.SCAN_CLEAN,
            PackageStatus.VALIDATING,
        ):
            await app.state.writer.package_transition(
                run, variant, target, message="fixture"
            )
        async with app.state.session_factory() as session, session.begin():
            await PackageRepository(session).save_validation_results(
                run,
                variant,
                validation_report(
                    "valid" if variant == Variant.PERFORMANCE else "invalid"
                ),
            )
        for target in (
            (PackageStatus.VALID, PackageStatus.CHECKS_PASSED)
            if variant == Variant.PERFORMANCE
            else (PackageStatus.INVALID, PackageStatus.PENDING_REVIEW)
        ):
            await app.state.writer.package_transition(
                run, variant, target, message="fixture"
            )
    async with client_for(app) as client:
        rejected = await client.post(
            review_url(run, "security"),
            json={
                "action": "reject",
                "reviewer_name": "Engineer",
                "category": "other",
                "reason": "Rejected remaining checks",
            },
        )
        assert rejected.status_code == 200
        if not approve_cost:
            return app, run
        approved = await client.post(
            review_url(run),
            json={
                "action": "approve",
                "reviewer_name": "Engineer",
                "category": "other",
                "reason": "Reviewed",
            },
        )
        assert approved.status_code == 200
    return app, run


@pytest.mark.req("FR-UI-06", "FR-S-10", "NFR-01")
async def test_bundle_payload_hashes_and_readiness_match_individual_zip_bytes(
    db_engines,
):
    app, run = await all_labelled(db_engines[0])
    canary = "synthetic-bundle-secret-canary"
    app.state.settings = app.state.settings.model_copy(
        update={"llm_api_key": SecretStr(canary)}
    )
    # Seed a hostile legacy payload; both archive surfaces must redact it.
    async with app.state.session_factory() as session, session.begin():
        await PackageRepository(session).save_files(
            run,
            Variant.COST,
            {"terraform/main.tf": "terraform {}\n", "README.txt": canary},
        )
    async with client_for(app) as client:
        singles = {
            variant.value: await client.get(
                f"/api/pipeline/{run}/download/{variant.value}"
            )
            for variant in Variant
        }
        response = await client.get(f"/api/pipeline/{run}/download-all")
        assert response.status_code == 200
        assert (
            response.content
            == (await client.get(f"/api/pipeline/{run}/download-all")).content
        )
        assert response.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(response.content)) as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        assert manifest["run_id"] == str(run) and manifest["schema_version"] == 1
        assert set(manifest["files"]) == set(bundle.namelist()) - {"manifest.json"}
        for path, digest in manifest["files"].items():
            assert hashlib.sha256(bundle.read(path)).hexdigest() == digest
            assert canary.encode() not in bundle.read(path)
        assert b"[REDACTED]" in bundle.read("cost/README.txt")
        for variant, single in singles.items():
            metadata = manifest["variants"][variant]
            assert (
                metadata["single_variant_zip"]["sha256"]
                == hashlib.sha256(single.content).hexdigest()
            )
            assert (
                metadata["single_variant_zip"]["filename"]
                in single.headers["content-disposition"]
            )
            with ZipFile(BytesIO(single.content)) as archive:
                assert {
                    path.removeprefix(variant + "/")
                    for path in bundle.namelist()
                    if path.startswith(variant + "/")
                } == set(archive.namelist())
                for path in archive.namelist():
                    assert bundle.read(f"{variant}/{path}") == archive.read(path)
        assert manifest["variants"]["cost"]["readiness_label"] == "engineer_approved"
        assert manifest["variants"]["security"]["readiness_label"] == "rejected"
        assert "performance/_infraarchagent/READINESS.md" in bundle.namelist()


@pytest.mark.req("FR-UI-06", "NFR-01")
async def test_bundle_errors_and_authentication_keep_existing_download_gates(
    db_engines,
):
    app, run = await pending_app(db_engines[0])
    async with client_for(app) as client:
        for target, status in (("bad", 400), (str(uuid4()), 404), (str(run), 409)):
            assert (
                await client.get(f"/api/pipeline/{target}/download-all")
            ).status_code == status
        app.state.settings = app.state.settings.model_copy(
            update={"api_key": SecretStr("bundle-auth-test-only")}
        )
        assert (
            await client.get(f"/api/pipeline/{run}/download-all")
        ).status_code == 401
        client.headers["X-API-Key"] = "bundle-auth-test-only"
        assert (
            await client.get(f"/api/pipeline/{run}/download-all")
        ).status_code == 409


@pytest.mark.req("FR-UI-06", "NFR-01")
async def test_bundle_uses_one_snapshot_even_if_files_change_during_label_reads(
    db_engines, monkeypatch
):
    app, run = await all_labelled(db_engines[0])
    ready, proceed = asyncio.Event(), asyncio.Event()
    original = ResultsRepository.label_event

    async def paused(self, *args):
        ready.set()
        await proceed.wait()
        return await original(self, *args)

    monkeypatch.setattr(ResultsRepository, "label_event", paused)
    async with client_for(app) as client:
        download = asyncio.create_task(client.get(f"/api/pipeline/{run}/download-all"))
        await asyncio.wait_for(ready.wait(), 5)
        try:
            async with app.state.session_factory() as session, session.begin():
                await PackageRepository(session).save_files(
                    run, Variant.COST, {"changed.tf": "changed\n"}
                )
        finally:
            proceed.set()
        response = await download
    assert response.status_code == 200
    with ZipFile(BytesIO(response.content)) as archive:
        assert "cost/terraform/main.tf" in archive.namelist()
        assert "cost/changed.tf" not in archive.namelist()


@pytest.mark.req("FR-UI-06", "FR-UI-07")
async def test_bundle_never_bypasses_one_pending_variant(db_engines):
    app, run = await all_labelled(db_engines[0], approve_cost=False)
    async with client_for(app) as client:
        assert (
            await client.get(f"/api/pipeline/{run}/download-all")
        ).status_code == 409
        assert (
            await client.get(f"/api/pipeline/{run}/download/performance")
        ).status_code == 200
