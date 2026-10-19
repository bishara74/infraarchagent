"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.agents.factory import AgentFactory
from app.api.auth import router as auth_router
from app.api.benchmark import router as benchmark_router
from app.api.frontend import DEFAULT_DIST, register_frontend
from app.api.health import router as health_router
from app.api.pipeline import router as pipeline_router
from app.core.auth import AuthService
from app.core.bind import check_open_bind
from app.core.config import Settings, get_settings
from app.core.errors import (
    ForbiddenError,
    UnauthorizedError,
    forbidden_error_handler,
    internal_error_handler,
    unauthorized_error_handler,
)
from app.core.logging import configure_logging
from app.core.safety import PublicDataSafety
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider, RunStatus
from app.events.broker import InMemoryBroker
from app.events.log import EventLog
from app.pipeline.runner import PipelineRunner
from app.pipeline.state import PipelineStateWriter
from app.scanners.runner import scanner_versions
from app.validation.tools import mirror_present, validator_versions

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
    *,
    frontend_dist: Path | None = None,
) -> FastAPI:
    configured = settings or get_settings()
    configure_logging(configured)
    owns_engine = engine is None
    app_engine = engine or create_async_engine(
        configured.database_url.get_secret_value(), echo=False
    )
    session_factory = make_session_factory(app_engine)
    broker = InMemoryBroker(configured.broker_queue_size)
    event_log = EventLog(session_factory, broker, safety=PublicDataSafety(configured))
    writer = PipelineStateWriter(session_factory, event_log)
    scanner_info = scanner_versions()
    factory = AgentFactory(
        configured,
        pipeline_demo_stub=True,
        session_factory=session_factory,
        scanner_versions={
            tool: details["version"] if isinstance(details["version"], str) else None
            for tool, details in scanner_info.items()
        },
    )
    runner = PipelineRunner(
        capacity=configured.max_concurrent_runs,
        factory=factory,
        session_factory=session_factory,
        writer=writer,
        security_stage=None,
        validation_stage=factory.create_validator_agent(),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        check_open_bind(configured.api_key)
        app.state.engine = app_engine
        if (
            configured.pipeline_demo_scenario == "review"
            and configured.llm_provider != LLMProvider.STUB
        ):
            logger.warning("PIPELINE_DEMO_SCENARIO=review is ignored for non-stub runs")
        if configured.api_key is None:
            logger.warning(
                "API_KEY is unset; pipeline API is open for local development"
            )
        for tool, details in scanner_info.items():
            if not details["available"]:
                logger.warning("%s is not installed", tool)
        async with session_factory() as session:
            interrupted = await RunRepository(session).list_interrupted()
        for run_id in interrupted:
            try:
                await writer.run_transition(
                    run_id,
                    RunStatus.FAILED,
                    message="interrupted by server restart",
                    error_message="interrupted by server restart",
                )
            except Exception:
                # A concurrent recovery or database outage is surfaced in logs.
                import logging

                logging.getLogger(__name__).exception(
                    "recovery failed for run %s", run_id
                )
        async with session_factory() as session:
            review_retries = await PackageRepository(session).list_review_retries()
        for run_id, variant in review_retries:
            try:
                await writer.abort_review_retry(
                    run_id, variant, reason="review retry interrupted by server restart"
                )
            except Exception:
                logger.exception(
                    "review retry recovery failed for run %s variant %s",
                    run_id,
                    variant,
                )
        try:
            yield
        finally:
            await runner.shutdown()
            if owns_engine:
                await app_engine.dispose()

    app = FastAPI(lifespan=lifespan)
    app.state.engine = app_engine
    app.state.broker = broker
    app.state.event_log = event_log
    app.state.writer = writer
    app.state.runner = runner
    app.state.settings = configured
    app.state.session_factory = session_factory
    app.state.auth = AuthService(session_factory, configured)
    app.state.scanners = scanner_info
    app.state.validators = validator_versions()
    app.state.provider_mirror_present = mirror_present()
    app.add_exception_handler(Exception, internal_error_handler)
    app.add_exception_handler(UnauthorizedError, unauthorized_error_handler)
    app.add_exception_handler(ForbiddenError, forbidden_error_handler)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(benchmark_router)
    app.include_router(pipeline_router)
    register_frontend(app, frontend_dist if frontend_dist is not None else DEFAULT_DIST)
    return app


app = create_app()
