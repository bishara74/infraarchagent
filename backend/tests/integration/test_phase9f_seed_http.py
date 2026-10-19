"""PR-04: real PostgreSQL fixture creation and rejected synthetic HTTP download."""

from io import BytesIO
from zipfile import ZipFile

import httpx
import pytest

from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus, Variant
from app.main import create_app
from scripts.seed_benchmark_package import seed_package


@pytest.mark.req("PR-04", "FR-S-10", "NFR-01")
async def test_full_size_seed_and_download_against_real_postgres(db_engines):
    from uuid import UUID

    sessions = make_session_factory(db_engines[0])
    report = await seed_package(sessions)
    async with sessions() as session:
        row = await PackageRepository(session).get(UUID(report["run_id"]), Variant.COST)
    assert row.status == PackageStatus.REJECTED
    assert row.security_report is None and row.validation_report is None
    assert row.review_feedback == "benchmark synthetic package"
    assert 9_940_050 <= report["calibrated_archive_bytes"] <= 9_990_000
    settings = get_settings().model_copy(update={"api_key": None, "llm_api_key": None})
    app = create_app(settings, db_engines[0])
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/pipeline/{report['run_id']}/download/cost")
    assert response.status_code == 200
    assert len(response.content) <= 10_000_000
    with ZipFile(BytesIO(response.content)) as archive:
        label = archive.read("INFRAARCHAGENT_READINESS.md").decode()
    assert "REJECTED" in label
    assert "Scan outcome: unavailable" in label
    assert (
        "synthetic benchmark fixture (no engineer decision or executed checks)" in label
    )
    assert row.review_decision["identity_basis"] == "synthetic benchmark fixture"
