"""Read migration compatibility without loading settings or running migrations."""

import asyncio
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine


@lru_cache(maxsize=1)
def migration_graph() -> ScriptDirectory:
    return ScriptDirectory(str(Path(__file__).with_name("migrations")))


@dataclass(frozen=True)
class SchemaStatus:
    current: str
    expected: str
    state: str

    @property
    def compatible(self) -> bool:
        return self.state == "current"

    @property
    def message(self) -> str:
        if self.state == "unavailable":
            return (
                "Database is unavailable. Check the database service "
                "and restart the server."
            )
        prefix = f"Database schema is at {self.current}, code expects {self.expected}"
        if self.state in {"behind", "missing", "unreadable"}:
            return prefix + " — run `make migrate`, then restart the server."
        return (
            prefix + " — use matching code and restart the server; "
            "do not downgrade automatically."
        )


def safe_revision(value: str) -> str:
    return value if re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", value) else "unknown"


async def schema_status(engine: AsyncEngine) -> SchemaStatus:
    graph = migration_graph()
    heads = tuple(sorted(graph.get_heads()))
    expected = ", ".join(heads) or "missing code migration"
    try:
        async with asyncio.timeout(5), engine.connect() as connection:
            revisions = tuple(
                sorted(
                    (
                        await connection.scalars(
                            text("SELECT version_num FROM alembic_version")
                        )
                    ).all()
                )
            )
    except (SQLAlchemyError, OSError, TimeoutError) as error:
        code = getattr(error.orig, "sqlstate", None) if hasattr(error, "orig") else None
        state = {"42P01": "missing", "42501": "unreadable"}.get(
            str(code), "unavailable"
        )
        return SchemaStatus(state, expected, state)
    current = ", ".join(safe_revision(value) for value in revisions) or "unversioned"
    if len(heads) == 1 and revisions == heads:
        return SchemaStatus(current, expected, "current")
    ancestors = {revision.revision for revision in graph.walk_revisions()}
    behind = len(revisions) <= 1 and (not revisions or revisions[0] in ancestors)
    return SchemaStatus(current, expected, "behind" if behind else "incompatible")
