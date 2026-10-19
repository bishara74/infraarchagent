"""Pipeline API, durable ordering, SSE replay and real validation logic."""

import asyncio
import time
from io import BytesIO
from uuid import UUID
from zipfile import ZipFile

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.agents.validator import ValidatorAgent
from app.core.config import get_settings
from app.db.models import PipelineRun
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider, PackageStatus, RunStatus
from app.main import create_app
from app.pipeline.demo_stub import PipelineDemoStub
from app.scanners.runner import RecordedToolRunner, ToolResult
from app.scanners.scan import Scanner
from app.validation.engine import ValidationEngine
from tests.unit.test_validation_engine import Clean, mirror


def _empty_scanner(repeats: int = 32) -> Scanner:
    return Scanner(
        RecordedToolRunner(
            {
                "checkov": [
                    ToolResult('{"passed":0,"failed":0,"resource_count":0}', "", 0, 0)
                ]
                * repeats,
                "trivy": [ToolResult('{"Results":[]}', "", 0, 0)] * repeats,
                "terraform": [ToolResult('{"diagnostics":[]}', "", 0, 0)] * repeats,
            }
        )
    )


@pytest.mark.req("FR-I-01", "FR-I-02", "FR-I-04", "FR-P-04")
async def test_demo_run_persists_before_work_and_replays_full_stream(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    tmp_path,
) -> None:
    engine, _ = db_engines
    settings = get_settings().model_copy(
        update={"llm_provider": LLMProvider.STUB, "llm_model": None}
    )
    app = create_app(settings, engine)
    app.state.runner.factory.scanner = _empty_scanner()
    app.state.runner.validation_stage = ValidatorAgent(
        ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={}),
        make_session_factory(engine),
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/pipeline/run",
                json={
                    "text": "Deploy an AWS web service",
                    "config": {"max_iterations": 2},
                },
            )
            assert response.status_code == 202
            run_id = UUID(response.json()["run_id"])
            async with make_session_factory(engine)() as session:
                assert await RunRepository(session).get(run_id) is not None
            await asyncio.gather(*app.state.runner.tasks.values())
            async with make_session_factory(engine)() as session:
                run = await RunRepository(session).get(run_id)
                packages = await PackageRepository(session).list_for_run(run_id)
            assert run is not None and run.status == RunStatus.SUCCESS
            assert run.llm_provider == LLMProvider.STUB
            assert run.model == "stub"
            assert run.max_iterations == 2
            assert len(packages) == 3
            assert all(row.status == PackageStatus.CHECKS_PASSED for row in packages)
            assert all(row.files for row in packages)
            replay = await client.get(response.json()["stream_url"])
            assert replay.status_code == 200
            assert replay.headers["content-type"].startswith("text/event-stream")
            ids = [
                int(line[4:])
                for line in replay.text.splitlines()
                if line.startswith("id: ")
            ]
            assert ids == sorted(set(ids))
            assert "event: package_generated" in replay.text
            assert "validation summary" in replay.text
            assert "terraform/main.tf" in replay.text
            assert "required_version" not in replay.text
            last = await client.get(
                response.json()["stream_url"],
                headers={"Last-Event-ID": str(ids[-1])},
            )
            assert last.status_code == 200 and "id: " not in last.text


@pytest.mark.req("FR-I-01", "FR-I-02", "FR-I-03")
@pytest.mark.parametrize(
    "raw,status",
    [
        ("{", 400),
        ("{}", 400),
        ('{"text": 3}', 400),
        ('{"text":"hi"}', 400),
        ('{"text":"Deploy AWS ' + "x" * 2000 + '"}', 400),
        ('{"text":"Deploy AWS\\u0001 service"}', 400),
        ('{"text":"tell me a joke about cats"}', 422),
        ('{"text":"Deploy AWS service","config":{"max_iterations":0}}', 400),
        ('{"text":"Deploy AWS service","config":{"provider":"bad"}}', 400),
    ],
)
async def test_rejected_request_creates_no_run(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    raw: str,
    status: int,
) -> None:
    engine, _ = db_engines
    app = create_app(get_settings(), engine)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/pipeline/run",
            content=raw,
            headers={"content-type": "application/json"},
        )
    assert response.status_code == status
    async with make_session_factory(engine)() as session:
        assert await session.scalar(select(func.count()).select_from(PipelineRun)) == 0


async def test_stream_rejects_bad_and_unknown_ids(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    app = create_app(get_settings(), engine)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.get("/api/pipeline/not-a-uuid/stream")).status_code == 400
        assert (
            await client.get(
                "/api/pipeline/00000000-0000-0000-0000-000000000001/stream"
            )
        ).status_code == 404
        assert (
            await client.get(
                "/api/pipeline/00000000-0000-0000-0000-000000000001/stream",
                headers={"Last-Event-ID": "bad"},
            )
        ).status_code == 400


@pytest.mark.req("PR-03")
async def test_capacity_rejection_precedes_persistence(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    app = create_app(
        get_settings().model_copy(update={"max_concurrent_runs": 2}), engine
    )
    assert app.state.runner.reserve()
    assert app.state.runner.reserve()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/pipeline/run", json={"text": "Deploy an AWS web service"}
        )
    assert response.status_code == 429
    async with make_session_factory(engine)() as session:
        assert await session.scalar(select(func.count()).select_from(PipelineRun)) == 0
    app.state.runner.release()
    app.state.runner.release()


@pytest.mark.req("FR-P-03")
async def test_startup_recovery_settles_interrupted_run(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            run = await RunRepository(session).create(
                "Deploy an AWS web service", LLMProvider.STUB, 3
            )
            run_id = run.run_id
    async with sessions() as session:
        async with session.begin():
            await RunRepository(session).set_status(run_id, RunStatus.RUNNING)
    app = create_app(get_settings(), engine)
    async with app.router.lifespan_context(app):
        async with sessions() as session:
            recovered = await RunRepository(session).get(run_id)
        assert recovered is not None
        assert recovered.status == RunStatus.FAILED
        assert recovered.error_message == "interrupted by server restart"


@pytest.mark.req("FR-I-04", "FR-P-03")
async def test_architect_invocation_sees_committed_run(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, _ = db_engines
    app = create_app(
        get_settings().model_copy(update={"llm_provider": LLMProvider.STUB}), engine
    )
    app.state.runner.factory.scanner = _empty_scanner()
    observed: list[RunStatus] = []
    original = PipelineDemoStub.send_prompt

    async def probe(self: PipelineDemoStub, *args: object, **kwargs: object):
        if self.variant is None:
            async with make_session_factory(engine)() as session:
                rows = list(await session.scalars(select(PipelineRun)))
            assert len(rows) == 1
            observed.append(RunStatus(rows[0].status))
        return await original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(PipelineDemoStub, "send_prompt", probe)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/pipeline/run", json={"text": "Deploy an AWS web service"}
            )
            assert response.status_code == 202
            await asyncio.gather(*app.state.runner.tasks.values())
    assert observed == [RunStatus.RUNNING]


@pytest.mark.req("FR-I-04")
async def test_missing_real_provider_key_is_400_without_persistence(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    settings = get_settings().model_copy(update={"llm_api_key": None})
    app = create_app(settings, engine)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/pipeline/run",
            json={
                "text": "Deploy an AWS web service",
                "config": {"provider": "openai", "model": "test-model"},
            },
        )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"
    async with make_session_factory(engine)() as session:
        assert await session.scalar(select(func.count()).select_from(PipelineRun)) == 0


@pytest.mark.req("FR-I-04", "FR-UI-06", "FR-S-02", "NFR-01")
@pytest.mark.parametrize(
    "configured_provider,config,expected_model",
    [
        (LLMProvider.OPENAI, {"provider": "stub"}, "stub"),
        (LLMProvider.STUB, {}, "stub"),
        (LLMProvider.STUB, {"provider": "stub"}, "stub"),
        (
            LLMProvider.OPENAI,
            {"provider": "stub", "model": "fixture-model"},
            "stub",
        ),
    ],
)
async def test_stub_run_provenance_in_rows_results_reports_and_readiness(
    db_engines, tmp_path, monkeypatch, configured_provider, config, expected_model
):
    from app.llm import factory as llm_factory

    def forbidden(*args, **kwargs):
        raise AssertionError("a stub run must never build a network adapter")

    monkeypatch.setattr(llm_factory, "OpenAIAdapter", forbidden)
    monkeypatch.setattr(llm_factory, "AnthropicAdapter", forbidden)
    engine, _ = db_engines
    settings = get_settings().model_copy(
        update={
            "llm_provider": configured_provider,
            "llm_model": "deployment-model",
            "security_fix_provider": LLMProvider.ANTHROPIC,
            "security_fix_model": "paid-fixer-model",
            "security_fix_reasoning_effort": "high",
        }
    )
    app = create_app(settings, engine)
    app.state.runner.factory.scanner = _empty_scanner()
    app.state.runner.validation_stage = ValidatorAgent(
        ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={}),
        make_session_factory(engine),
    )
    body = {"text": "Deploy an AWS web service"}
    if config:
        body["config"] = config
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/pipeline/run", json=body)
            assert response.status_code == 202
            run_id = UUID(response.json()["run_id"])
            await asyncio.gather(*app.state.runner.tasks.values())
            async with app.state.session_factory() as session:
                run = await RunRepository(session).get(run_id)
            assert run is not None and run.model == expected_model
            assert run.llm_provider == LLMProvider.STUB
            assert run.status == RunStatus.SUCCESS
            results = await client.get(f"/api/pipeline/{run_id}/results")
            assert results.status_code == 200
            data = results.json()
            assert data["run"]["model"] == expected_model
            for package in data["packages"]:
                report = package["security_report"]
                assert report["fixing_provider"] == "stub"
                assert report["fixing_model"] == "stub"
                assert all(
                    item["fixing_model"] == "stub" for item in report["sessions"]
                )
                download = await client.get(
                    f"/api/pipeline/{run_id}/download/{package['variant']}"
                )
                assert download.status_code == 200
                with ZipFile(BytesIO(download.content)) as archive:
                    readiness = archive.read("INFRAARCHAGENT_READINESS.md").decode()
                assert f"Model: {expected_model}\n" in readiness
            events = await app.state.event_log.list_after(run_id, None)
            assert "paid-fixer-model" not in str(events)
            if expected_model == "stub":
                assert "deployment-model" not in str(events)
    factory = app.state.runner.factory
    from app.domain.run_config import RunConfig

    run_config = RunConfig.model_validate(config)
    assert factory.create_architect(run_config).llm_adapter.model == expected_model
    assert all(
        agent.llm_adapter.model == expected_model
        for agent in factory.create_generators(run_config)
    )


@pytest.mark.req("FR-I-04", "NFR-01")
@pytest.mark.parametrize("config", [None, {"provider": "openai"}])
async def test_api_inherits_configured_provider_and_model(
    db_engines, monkeypatch, config
):
    from pydantic import SecretStr

    app = create_app(
        get_settings().model_copy(
            update={
                "llm_provider": LLMProvider.OPENAI,
                "llm_model": "deployment-model",
                "llm_api_key": SecretStr("phase7b-CANARY"),
            }
        ),
        db_engines[0],
    )
    # Submission validates and persists, but never runs the real-provider pipeline.
    monkeypatch.setattr(app.state.runner, "start", lambda *args: None)
    body = {"text": "Deploy an AWS web service"}
    if config is not None:
        body["config"] = config
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/pipeline/run", json=body)
        assert response.status_code == 202
        run_id = UUID(response.json()["run_id"])
        results = await client.get(f"/api/pipeline/{run_id}/results")
    async with app.state.session_factory() as session:
        run = await RunRepository(session).get(run_id)
    assert run is not None
    assert (run.llm_provider, run.model) == ("openai", "deployment-model")
    assert results.json()["run"]["model"] == "deployment-model"
    app.state.runner.release()


@pytest.mark.req("FR-I-04", "NFR-01")
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
async def test_api_different_real_provider_without_model_is_400(
    db_engines, monkeypatch, provider
):
    from app.api import pipeline

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "invalid configuration must be rejected before building adapters"
        )

    monkeypatch.setattr(pipeline, "build_adapter", forbidden)
    app = create_app(
        get_settings().model_copy(
            update={"llm_provider": LLMProvider.STUB, "llm_model": "deployment-model"}
        ),
        db_engines[0],
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/pipeline/run",
            json={
                "text": "Deploy an AWS web service",
                "config": {"provider": provider},
            },
        )
    assert response.status_code == 400
    assert response.json() == {
        "error": "invalid_request",
        "message": "model is required when overriding the provider",
    }
    async with app.state.session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(PipelineRun)) == 0


@pytest.mark.req("PR-03", "FR-P-04")
async def test_three_runs_overlap_and_keep_events_isolated(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, _ = db_engines
    app = create_app(
        get_settings().model_copy(update={"llm_provider": LLMProvider.STUB}), engine
    )
    app.state.runner.factory.scanner = _empty_scanner(18)
    app.state.runner.validation_stage = ValidatorAgent(
        ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={}),
        make_session_factory(engine),
    )
    original = PipelineDemoStub.send_prompt
    architects: set[int] = set()
    all_started = asyncio.Event()
    release = asyncio.Event()

    async def blocked(self: PipelineDemoStub, *args: object, **kwargs: object):
        if self.variant is None:
            architects.add(id(self))
            if len(architects) == 3:
                all_started.set()
            await release.wait()
        return await original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(PipelineDemoStub, "send_prompt", blocked)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            try:
                responses = await asyncio.gather(
                    *(
                        client.post(
                            "/api/pipeline/run",
                            json={
                                "text": f"Deploy AWS web service number {index}",
                                "config": {"provider": "stub"},
                            },
                        )
                        for index in range(3)
                    )
                )
                assert all(item.status_code == 202 for item in responses)
                async with asyncio.timeout(30):
                    await all_started.wait()
                ids = {UUID(item.json()["run_id"]) for item in responses}
                assert len(ids) == 3 and len(architects) == 3
                async with app.state.session_factory() as session:
                    for run_id in ids:
                        row = await RunRepository(session).get(run_id)
                        assert row is not None and row.status == RunStatus.RUNNING
                assert len(app.state.runner.tasks) == 3
            finally:
                release.set()
            async with asyncio.timeout(30):
                await asyncio.gather(*app.state.runner.tasks.values())
            for run_id in ids:
                events = await app.state.event_log.list_after(run_id, None)
                assert events and all(item.run_id == run_id for item in events)
                assert events[-1].new_state == RunStatus.SUCCESS
                assert [item.seq for item in events] == sorted(
                    {item.seq for item in events}
                )


@pytest.mark.perf
@pytest.mark.req("PR-03")
async def test_three_runs_finish_within_fifty_percent_of_solo_time(
    db_engines: tuple[AsyncEngine, AsyncEngine],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, _ = db_engines
    app = create_app(
        get_settings().model_copy(update={"llm_provider": LLMProvider.STUB}), engine
    )
    app.state.runner.factory.scanner = _empty_scanner(24)
    original = PipelineDemoStub.send_prompt

    async def delayed(self: PipelineDemoStub, *args: object, **kwargs: object):
        await asyncio.sleep(1.0)
        return await original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(PipelineDemoStub, "send_prompt", delayed)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            started = time.monotonic()
            solo = await client.post(
                "/api/pipeline/run", json={"text": "Deploy an AWS web service"}
            )
            assert solo.status_code == 202
            await asyncio.gather(*app.state.runner.tasks.values())
            solo_elapsed = time.monotonic() - started

            started = time.monotonic()
            responses = await asyncio.gather(
                *(
                    client.post(
                        "/api/pipeline/run",
                        json={"text": f"Deploy AWS web service number {index}"},
                    )
                    for index in range(3)
                )
            )
            assert all(item.status_code == 202 for item in responses)
            await asyncio.gather(*app.state.runner.tasks.values())
            parallel_elapsed = time.monotonic() - started
            assert parallel_elapsed <= 1.5 * solo_elapsed
            ids = {UUID(item.json()["run_id"]) for item in responses}
            assert len(ids) == 3
            for run_id in ids:
                events = await app.state.event_log.list_after(run_id, None)
                assert events and all(item.run_id == run_id for item in events)
