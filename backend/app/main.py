"""FastAPI application factory."""

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
from app.pipeline.stages import UnavailableSecurityStage, UnavailableValidationStage
from app.pipeline.state import PipelineStateWriter


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
    runner = PipelineRunner(
        capacity=configured.max_concurrent_runs,
        factory=AgentFactory(configured, pipeline_demo_stub=True),
        session_factory=session_factory,
        writer=writer,
        security_stage=UnavailableSecurityStage(),
        validation_stage=UnavailableValidationStage(),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.engine = app_engine
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
    app.add_exception_handler(Exception, internal_error_handler)
    app.include_router(health_router)
    app.include_router(pipeline_router)
    return app


app = create_app()
