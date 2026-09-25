"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.api.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.errors import internal_error_handler
from app.core.logging import configure_logging


def create_app(
    settings: Settings | None = None, engine: AsyncEngine | None = None
) -> FastAPI:
    configured = settings or get_settings()
    configure_logging(configured)
    owns_engine = engine is None
    app_engine = engine or create_async_engine(
        configured.database_url.get_secret_value(), echo=False
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.engine = app_engine
        try:
            yield
        finally:
            if owns_engine:
                await app_engine.dispose()

    app = FastAPI(lifespan=lifespan)
    app.state.engine = app_engine
    app.add_exception_handler(Exception, internal_error_handler)
    app.include_router(health_router)
    return app


app = create_app()
