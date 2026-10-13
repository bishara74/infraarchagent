"""Labelled persisted archives and measured PR-04 ASGI download."""

import base64
import random
import time
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

import pytest

from app.db.repositories.packages import PackageRepository
from app.domain.enums import PackageStatus, Variant
from tests.integration.test_pipeline_review import (
    client_for,
    pending_app,
    review_url,
    state,
)


@pytest.mark.req("FR-UI-06", "FR-S-08", "FR-S-10")
@pytest.mark.parametrize(
    "action,label",
    [
        ("approve", "PRODUCTION READY"),
        ("reject", "NOT PRODUCTION READY — rejected by the reviewing engineer"),
    ],
)
async def test_labelled_download_exact_files_and_repeat_bytes(
    db_engines, action, label
):
    app, run_id = await pending_app(db_engines[0])
    async with client_for(app) as client:
        assert (
            await client.get(f"/api/pipeline/{run_id}/download/cost")
        ).status_code == 409
        await client.post(
            review_url(run_id), json={"action": action, "feedback": "Engineer notes"}
        )
        first = await client.get(f"/api/pipeline/{run_id}/download/cost")
        second = await client.get(f"/api/pipeline/{run_id}/download/cost")
    assert first.status_code == 200 and first.content == second.content
    assert first.headers["content-type"] == "application/zip"
    expected_status = (
        "production_ready" if action == "approve" else "not_production_ready"
    )
    assert first.headers["content-disposition"] == (
        f'attachment; filename="infraarch-{str(run_id)[:8]}-cost-{expected_status}.zip"'
    )
    _, row = await state(app, run_id)
    events = await app.state.event_log.list_after(run_id, None)
    label_event = events[-1]
    with ZipFile(BytesIO(first.content)) as archive:
        assert set(archive.namelist()) == {*row.files, "INFRAARCHAGENT_READINESS.md"}
        for path, content in row.files.items():
            assert archive.read(path).decode() == content
        readiness = archive.read("INFRAARCHAGENT_READINESS.md").decode()
    assert readiness.startswith(f"# {label}")
    assert f"Labelled at: {label_event.timestamp.isoformat()}" in readiness
    assert (
        "engineer decision" in readiness
        and "Static validity does not prove deployability" in readiness
    )
    if action == "reject":
        assert "Engineer notes" in readiness


@pytest.mark.req("FR-UI-06")
async def test_download_errors_and_failed_generation(db_engines):
    app, run_id = await pending_app(db_engines[0])
    async with app.state.session_factory() as session:
        async with session.begin():
            await PackageRepository(session).create(run_id, Variant.PERFORMANCE)
    await app.state.writer.package_transition(
        run_id, Variant.PERFORMANCE, PackageStatus.FAILED, message="generation failed"
    )
    async with client_for(app) as client:
        for path, status in [
            ("bad/download/cost", 400),
            (f"{run_id}/download/wrong", 400),
            (f"{uuid4()}/download/cost", 404),
            (f"{run_id}/download/security", 404),
            (f"{run_id}/download/performance", 404),
            (f"{run_id}/download/cost", 409),
        ]:
            assert (await client.get(f"/api/pipeline/{path}")).status_code == status
    async with app.state.session_factory() as session:
        async with session.begin():
            await app.state.writer.review_action(
                session, run_id, Variant.COST, "retry", None
            )
    async with client_for(app) as client:
        assert (
            await client.get(f"/api/pipeline/{run_id}/download/cost")
        ).status_code == 409


@pytest.mark.req("FR-UI-06")
async def test_download_missing_label_event_has_stable_unavailable_time(db_engines):
    app, run_id = await pending_app(db_engines[0])
    async with app.state.session_factory() as session:
        async with session.begin():
            await app.state.writer.review_action(
                session, run_id, Variant.COST, "approve", None
            )
    async with client_for(app) as client:
        first = await client.get(f"/api/pipeline/{run_id}/download/cost")
        second = await client.get(f"/api/pipeline/{run_id}/download/cost")
    assert first.content == second.content
    with ZipFile(BytesIO(first.content)) as archive:
        assert (
            "Labelled at: unavailable"
            in archive.read("INFRAARCHAGENT_READINESS.md").decode()
        )


async def _ten_megabyte_download(db_engines):
    app, run_id = await pending_app(db_engines[0])
    rng = random.Random(704)
    files = {
        f"terraform/file-{index:02}.tf": base64.b64encode(
            rng.randbytes(150_000)
        ).decode("ascii")
        for index in range(50)
    }
    assert sum(len(value.encode()) for value in files.values()) == 10_000_000
    async with app.state.session_factory() as session:
        async with session.begin():
            await PackageRepository(session).save_files(run_id, Variant.COST, files)
    async with client_for(app) as client:
        await client.post(review_url(run_id), json={"action": "approve"})
        start = time.perf_counter()
        response = await client.get(f"/api/pipeline/{run_id}/download/cost")
        elapsed = time.perf_counter() - start
    assert (
        response.status_code == 200 and 7_000_000 < len(response.content) < 10_000_000
    )
    with ZipFile(BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {*files, "INFRAARCHAGENT_READINESS.md"}
        for path, content in files.items():
            assert archive.read(path).decode() == content
        assert archive.read("INFRAARCHAGENT_READINESS.md").startswith(
            b"# PRODUCTION READY"
        )
    return elapsed, len(response.content)


@pytest.mark.req("FR-UI-06")
async def test_ten_megabyte_package_download_contains_every_file(db_engines):
    await _ten_megabyte_download(db_engines)


@pytest.mark.perf
@pytest.mark.req("PR-04", "FR-UI-06")
async def test_ten_megabyte_package_download_under_two_seconds(
    db_engines, record_property
):
    elapsed, archive_bytes = await _ten_megabyte_download(db_engines)
    record_property("pr04_seconds", elapsed)
    print(f"PR-04: {elapsed:.6f}s; {archive_bytes} archive bytes")
    assert elapsed < 2


@pytest.mark.req("FR-UI-06", "FR-S-09")
async def test_retry_download_origin_uses_committed_review_event(
    db_engines, monkeypatch
):
    import asyncio

    from tests.integration.test_pipeline_review import install_retry

    app, run_id = await pending_app(db_engines[0])
    install_retry(app, monkeypatch)
    async with client_for(app) as client:
        response = await client.post(review_url(run_id), json={"action": "retry"})
        assert response.status_code == 202
        await asyncio.gather(*app.state.runner.tasks.values())
        first = await client.get(f"/api/pipeline/{run_id}/download/cost")
        second = await client.get(f"/api/pipeline/{run_id}/download/cost")
    assert first.status_code == 200 and first.content == second.content
    with ZipFile(BytesIO(first.content)) as archive:
        text = archive.read("INFRAARCHAGENT_READINESS.md").decode()
    assert "Label origin: automatic after an engineer-requested retry " in text
    assert "(clean scan and valid validation)" in text


@pytest.mark.req("FR-UI-06", "FR-S-09")
@pytest.mark.parametrize(
    "retry_variant,before_label,expected_retry",
    [
        (Variant.COST, True, True),
        (Variant.SECURITY, True, False),
        (Variant.COST, False, False),
    ],
)
async def test_origin_history_is_variant_scoped_and_precedes_label(
    db_engines, retry_variant, before_label, expected_retry
):
    app, run_id = await pending_app(db_engines[0], result="valid")

    async def record_retry():
        # State/event transactions are independent (D-19); this fixture isolates
        # history selection rather than executing another remediation pipeline.
        await app.state.writer.review_event(
            run_id,
            retry_variant,
            PackageStatus.REMEDIATING,
            PackageStatus.PENDING_REVIEW,
            action="retry",
            reasons=[],
        )

    if before_label:
        await record_retry()
    await app.state.writer.package_transition(
        run_id, Variant.COST, PackageStatus.PRODUCTION_READY, message="labelled"
    )
    if not before_label:
        await record_retry()
    async with client_for(app) as client:
        response = await client.get(f"/api/pipeline/{run_id}/download/cost")
    assert response.status_code == 200
    with ZipFile(BytesIO(response.content)) as archive:
        text = archive.read("INFRAARCHAGENT_READINESS.md").decode()
    origin = (
        "automatic after an engineer-requested retry (clean scan and valid validation)"
        if expected_retry
        else "automatic (clean scan and valid validation)"
    )
    assert f"Label origin: {origin}\n" in text
