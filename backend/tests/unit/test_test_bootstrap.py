import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.req("NFR-01")
def test_verification_bootstrap_disables_dotenv_before_settings() -> None:
    backend = Path(__file__).resolve().parents[2]
    env = {
        "PATH": os.defpath,
        "PYTHONPATH": f"{backend / 'tests/bootstrap'}:{backend}",
        "TEST_DATABASE_URL": "postgresql+asyncpg://app@localhost/test",
        "TEST_MIGRATION_DATABASE_URL": "postgresql+asyncpg://owner@localhost/test",
    }
    script = """
from app.core.config import Settings
assert Settings.model_config['env_file'] is None
from pydantic_settings.sources import DotEnvSettingsSource
original = DotEnvSettingsSource._read_env_files
def guarded(self):
    assert self.env_file is None, 'Verification attempted dotenv loading'
    return original(self)
DotEnvSettingsSource._read_env_files = guarded
s = Settings()
assert s.database_url.get_secret_value() == s.test_database_url.get_secret_value()
assert (s.migration_database_url.get_secret_value()
        == s.test_migration_database_url.get_secret_value())
assert s.llm_provider == 'stub'
assert s.llm_api_key is None and s.api_key is None
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
