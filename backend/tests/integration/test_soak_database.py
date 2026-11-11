# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""The native soak detects other test clients, including idle connections."""

import pytest

from app.core.config import get_settings
from scripts.soak_native import SoakError, require_idle_database


async def test_soak_refuses_idle_test_client(db_engines):
    app_engine, _ = db_engines
    url = get_settings().test_migration_database_url.get_secret_value()
    async with app_engine.connect():
        with pytest.raises(SoakError, match="infraarch_test is in use"):
            await require_idle_database(url)
