"""Synthetic seeding uses the normal app role, repositories and state rules."""

from io import BytesIO
from uuid import UUID
from zipfile import ZipFile

import httpx
import pytest

from app.core.config import get_settings
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.main import create_app
from scripts.benchmark import Harness
from scripts.seed_benchmark_package import require_dev_database, seed_package


@pytest.mark.req("PR-04", "FR-UI-06", "NFR-01")
async def test_seed_and_download_through_http(db_engines, tmp_path):
    sessions = make_session_factory(db_engines[0])
    report = await seed_package(sessions, archive_bytes=100_000)
    async with sessions() as session:
        row = await RunRepository(session).get(UUID(report["run_id"]))
        assert row.input_text == "benchmark synthetic package"
    app = create_app(get_settings().model_copy(update={"api_key": None}), db_engines[0])
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        harness = Harness(client, base_url="http://test", output=tmp_path)
        await harness.pr04(report["run_id"], 2)
        response = await client.get(f"/api/pipeline/{report['run_id']}/download/cost")
    assert len(harness.rows) == 2 and all(row["complete"] for row in harness.rows)
    assert 99_000 < len(response.content) < 101_000
    with ZipFile(BytesIO(response.content)) as archive:
        assert (
            "NOT PRODUCTION READY"
            in archive.read("INFRAARCHAGENT_READINESS.md").decode()
        )
        assert (
            "benchmark synthetic package"
            in archive.read("INFRAARCHAGENT_READINESS.md").decode()
        )
        assert len(archive.namelist()) == report["file_count"] + 1
    events = await app.state.event_log.list_after(UUID(report["run_id"]), None)
    assert any(event.payload.get("review_action") == "reject" for event in events)


@pytest.mark.req("NFR-01", "PR-04")
def test_dev_guard_refuses_test_url():
    settings = get_settings().model_copy(
        update={"database_url": get_settings().test_database_url}
    )
    with pytest.raises(ValueError, match="development"):
        require_dev_database(settings)
