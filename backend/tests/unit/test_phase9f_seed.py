"""PR-04: seed configuration uses one exported URL, never dotenv or owner settings."""

import pytest

from scripts.seed_benchmark_package import (
    SeedConfigurationError,
    SeedSettings,
    load_seed_settings,
)


@pytest.mark.req("PR-04", "NFR-01")
def test_seed_needs_only_development_app_url(monkeypatch):
    for name in (
        "MIGRATION_DATABASE_URL",
        "TEST_DATABASE_URL",
        "TEST_MIGRATION_DATABASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://infraarch_app:placeholder@localhost/infraarch",
    )
    load_seed_settings()
    assert SeedSettings.model_fields.keys() == {"database_url"}


@pytest.mark.req("PR-04", "NFR-01")
@pytest.mark.parametrize(
    "url",
    [
        None,
        "postgresql+asyncpg://infraarch_owner:placeholder@localhost/infraarch",
        "postgresql+asyncpg://infraarch_app:placeholder@localhost/infraarch_test",
    ],
)
def test_seed_missing_or_wrong_role_database_has_safe_error(monkeypatch, url):
    if url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(SeedConfigurationError) as error:
        load_seed_settings()
    assert "placeholder" not in str(error.value)
    assert "postgresql" not in str(error.value)


@pytest.mark.req("PR-04")
async def test_stub_suite_preflights_seed_before_submitting_runs(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock

    from scripts import run_phase9_benchmarks as commands

    monkeypatch.delenv("DATABASE_URL", raising=False)
    harness = SimpleNamespace(stop_reason=None, flush=Mock())
    execute = AsyncMock()
    monkeypatch.setattr(commands, "evidence_directory", lambda *a, **kw: tmp_path)
    monkeypatch.setattr(commands, "configured_harness", AsyncMock(return_value=harness))
    monkeypatch.setattr(commands, "section_reports", lambda *a: None)
    monkeypatch.setattr(commands, "execute", execute)
    with pytest.raises(SystemExit) as error:
        await commands.run(SimpleNamespace(mode="stub", smoke=False))
    assert error.value.code == 2
    assert "DATABASE_URL" in harness.stop_reason
    execute.assert_not_awaited()
