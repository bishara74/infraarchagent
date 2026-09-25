"""Async database connections and health probing."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def database_is_available(engine: AsyncEngine) -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        return False
    return True
