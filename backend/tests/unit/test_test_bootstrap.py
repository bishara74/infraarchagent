import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("flag", [None, "0"])
def test_bootstrap_without_explicit_flag_is_inactive(flag) -> None:
    env = {
        "PATH": os.defpath,
        "PYTHONPATH": f"{BACKEND / 'tests/bootstrap'}:{BACKEND}",
        "TEST_DATABASE_URL": "test-only-canary",
    }
    if flag is not None:
        env["INFRAARCH_TEST_BOOTSTRAP"] = flag
    script = """
import os, sitecustomize, sys
assert 'app.core.config' not in sys.modules
from app.core.config import ROOT, Settings
assert Settings.model_config['env_file'] == ROOT / '.env'
assert 'DATABASE_URL' not in os.environ
"""
    completed = subprocess.run(
        [str(BACKEND / ".venv/bin/python"), "-c", script],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.req("NFR-01")
def test_normal_get_settings_loads_temporary_dotenv(tmp_path) -> None:
    dotenv = tmp_path / "settings.env"
    names = (
        "DATABASE_URL",
        "MIGRATION_DATABASE_URL",
        "TEST_DATABASE_URL",
        "TEST_MIGRATION_DATABASE_URL",
    )
    dotenv.write_text("".join(f"{name}=synthetic-{name}\n" for name in names))
    script = """
import sys
from app.core.config import ROOT, Settings, get_settings
assert Settings.model_config['env_file'] == ROOT / '.env'
from pydantic_settings.sources import DotEnvSettingsSource
original = DotEnvSettingsSource._read_env_files
def guarded(self):
    assert str(self.env_file) == sys.argv[1], 'Unexpected dotenv path'
    return original(self)
DotEnvSettingsSource._read_env_files = guarded
Settings.model_config['env_file'] = sys.argv[1]
settings = get_settings()
for name in ('database_url', 'migration_database_url',
             'test_database_url', 'test_migration_database_url'):
    assert getattr(settings, name).get_secret_value() == 'synthetic-' + name.upper()
"""
    completed = subprocess.run(
        [str(BACKEND / ".venv/bin/python"), "-c", script, str(dotenv)],
        env={
            "PATH": os.defpath,
            "PYTHONPATH": f"{BACKEND / 'tests/bootstrap'}:{BACKEND}",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "target",
    [
        "migrate",
        "migrate-test",
        "run",
        "eval-architect",
        "eval-generators",
        "eval-security",
        "eval-validation",
        "test",
        "test-perf",
    ],
)
def test_make_normal_commands_and_test_prerequisites_do_not_bootstrap(target, tmp_path):
    import shlex

    script = """
import os
from app.core.config import ROOT, Settings
assert Settings.model_config['env_file'] == ROOT / '.env'
assert 'INFRAARCH_TEST_BOOTSTRAP' not in os.environ
assert 'PYTHONPATH' not in os.environ
assert 'LLM_PROVIDER' not in os.environ
"""
    # Override only the recipes, retaining Make's target-specific environment
    # and dependency inheritance. No migrations or real services run here.
    quoted_script = shlex.quote("exec(" + repr(script) + ")")
    probe = f"@{BACKEND / '.venv/bin/python'} -c {quoted_script}"
    recipe = f"{target}:\n\t{probe}\n"
    if target in {"test", "test-perf"}:
        recipe += f"migrate-test:\n\t{probe}\n"
    override = tmp_path / "verification.mk"
    override.write_text(recipe)
    completed = subprocess.run(
        ["make", "-s", "-f", "Makefile", "-f", str(override), target],
        cwd=BACKEND.parent,
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.req("NFR-01")
def test_verification_bootstrap_disables_dotenv_before_settings() -> None:
    backend = Path(__file__).resolve().parents[2]
    env = {
        "PATH": os.defpath,
        "PYTHONPATH": f"{backend / 'tests/bootstrap'}:{backend}",
        "INFRAARCH_TEST_BOOTSTRAP": "1",
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
