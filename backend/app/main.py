"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.agents.factory import AgentFactory
from app.api.health import router as health_router
from app.api.pipeline import router as pipeline_router
from app.core.config import Settings, get_settings
from app.core.errors import internal_error_handler
from app.core.logging import configure_logging
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import RunStatus
from app.events.broker import InMemoryBroker
from app.events.log import EventLog
from app.pipeline.runner import PipelineRunner
from app.pipeline.stages import UnavailableValidationStage
from app.pipeline.state import PipelineStateWriter
from app.scanners.runner import scanner_versions

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None, engine: AsyncEngine | None = None
) -> FastAPI:
    configured = settings or get_settings()
    configure_logging(configured)
    owns_engine = engine is None
    app_engine = engine or create_async_engine(
        configured.database_url.get_secret_value(), echo=False
    )
    session_factory = make_session_factory(app_engine)
    broker = InMemoryBroker(configured.broker_queue_size)
    event_log = EventLog(session_factory, broker)
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
        validation_stage=UnavailableValidationStage(),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.engine = app_engine
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
    app.state.scanners = scanner_info
    app.add_exception_handler(Exception, internal_error_handler)
    app.include_router(health_router)
    app.include_router(pipeline_router)
    return app


app = create_app()
