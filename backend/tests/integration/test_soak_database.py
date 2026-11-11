# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""The native soak uses the real database and pipeline authentication path."""

import secrets
from unittest.mock import Mock

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import get_settings
from app.db.repositories.runs import RunRepository
from app.db.repositories.users import UserRepository
from app.domain.enums import LLMProvider
from app.main import create_app
from scripts.soak_native import (
    SoakError,
    error_redactor,
    require_idle_database,
    soak_client,
    submit,
)


async def test_soak_refuses_idle_test_client(db_engines):
    app_engine, _ = db_engines
    url = get_settings().test_migration_database_url.get_secret_value()
    async with app_engine.connect():
        with pytest.raises(SoakError, match="infraarch_test is in use"):
            await require_idle_database(url)


@pytest.mark.req("NFR-01", "FR-I-01", "FR-P-01")
async def test_soak_submission_authenticates_with_an_existing_account(
    db_engines, monkeypatch
):
    key = secrets.token_urlsafe(32)
    settings = get_settings().model_copy(
        update={"api_key": SecretStr(key), "llm_provider": LLMProvider.STUB}
    )
    app = create_app(settings, db_engines[0])
    async with app.state.session_factory() as session, session.begin():
        await UserRepository(session).create("existing-reviewer", "fixture", first=True)
    assert await app.state.auth.has_users()
    launch = Mock()
    monkeypatch.setattr(app.state.runner, "start", launch)
    row = {"run_id": None}
    async with (
        app.router.lifespan_context(app),
        soak_client(
            "http://test", key, 1, transport=httpx.ASGITransport(app=app)
        ) as client,
    ):
        await submit(client, "Deploy an AWS web service", row, error_redactor(key))
    assert row["submit_http_status"] == 202
    launch.assert_called_once()
    run_id = launch.call_args.args[0]
    assert row["run_id"] == str(run_id)
    async with app.state.session_factory() as session:
        run = await RunRepository(session).get(run_id)
        assert run is not None and run.user_id is None
