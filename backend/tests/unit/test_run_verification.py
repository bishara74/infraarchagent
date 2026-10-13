"""NFR-01: resolve operator settings without exposing them to verification."""

import os
import subprocess
import sys

import pytest

from app.core.config import Settings
from scripts import run_verification


def synthetic_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url="normal-app-canary",
        migration_database_url="normal-owner-canary",
        test_database_url="test-app-canary",
        test_migration_database_url="test-owner-canary",
        llm_provider="anthropic",
        llm_api_key="llm-secret-canary",
        api_key="api-secret-canary",
    )


@pytest.mark.req("NFR-01")
def test_child_receives_only_test_database_settings_and_stub_credentials(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "production-db-canary")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_API_KEY", "llm-env-canary")
    monkeypatch.setenv("API_KEY", "api-env-canary")
    monkeypatch.setenv("PYTHONPATH", "/synthetic-existing-path")
    before = os.environ.copy()
    env = run_verification.verification_environment(synthetic_settings())
    assert os.environ == before
    assert env["DATABASE_URL"] == env["TEST_DATABASE_URL"] == "test-app-canary"
    assert (
        env["MIGRATION_DATABASE_URL"]
        == env["TEST_MIGRATION_DATABASE_URL"]
        == "test-owner-canary"
    )
    assert env["INFRAARCH_TEST_BOOTSTRAP"] == "1"
    assert env["LLM_PROVIDER"] == "stub"
    assert env["LLM_API_KEY"] == env["API_KEY"] == ""
    assert env["PYTHONPATH"].split(os.pathsep) == [
        str(run_verification.BACKEND / "tests/bootstrap"),
        str(run_verification.BACKEND),
        "/synthetic-existing-path",
    ]
    assert not any("canary" in value for key, value in env.items() if "URL" not in key)


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("mode", ["pytest", "e2e"])
def test_launcher_executes_selected_process_in_isolated_environment(monkeypatch, mode):
    executed = []
    directories = []
    monkeypatch.setattr(run_verification, "get_settings", synthetic_settings)
    monkeypatch.setattr(sys, "argv", ["run_verification", mode, "--version"])
    monkeypatch.setattr(os, "chdir", directories.append)
    monkeypatch.setattr(os, "execvpe", lambda *args: executed.append(args))
    run_verification.main()
    executable, command, env = executed[0]
    assert env["INFRAARCH_TEST_BOOTSTRAP"] == "1"
    if mode == "pytest":
        assert executable == sys.executable
        assert command == [sys.executable, "-m", "pytest", "--version"]
        assert directories == []
    else:
        assert executable == "npm"
        assert command == ["npm", "run", "test:e2e", "--", "--version"]
        assert directories == [run_verification.BACKEND.parent / "frontend"]


@pytest.mark.req("NFR-01")
def test_launcher_configuration_failure_does_not_reveal_validation_input(monkeypatch):
    def invalid():
        return Settings(_env_file=None, llm_provider="validation-secret-canary")

    monkeypatch.setattr(run_verification, "get_settings", invalid)
    monkeypatch.setattr(sys, "argv", ["run_verification", "pytest"])
    with pytest.raises(SystemExit) as error:
        run_verification.main()
    assert str(error.value) == (
        "Verification settings unavailable; check the configured test database URLs."
    )


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("arguments", [[], ["unknown"]])
def test_launcher_requires_a_supported_command(monkeypatch, arguments):
    monkeypatch.setattr(sys, "argv", ["run_verification", *arguments])
    with pytest.raises(SystemExit, match="Usage:"):
        run_verification.main()


@pytest.mark.req("NFR-01")
def test_failing_launcher_subprocess_does_not_print_secret_input():
    backend = run_verification.BACKEND
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.run_verification", "pytest"],
        env={
            "PATH": os.defpath,
            "PYTHONPATH": f"{backend / 'tests/bootstrap'}:{backend}",
            "INFRAARCH_TEST_BOOTSTRAP": "1",
            "LLM_API_KEY": "subprocess-secret-canary",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    assert completed.stdout == ""
    assert completed.stderr.strip() == (
        "Verification settings unavailable; check the configured test database URLs."
    )


@pytest.mark.req("NFR-01")
def test_launcher_resolves_temporary_settings_before_disabling_child_dotenv(tmp_path):
    dotenv = tmp_path / "operator-settings.env"
    dotenv.write_text(
        "DATABASE_URL=production-app-canary\n"
        "MIGRATION_DATABASE_URL=production-owner-canary\n"
        "TEST_DATABASE_URL=test-app-canary\n"
        "TEST_MIGRATION_DATABASE_URL=test-owner-canary\n"
        "LLM_PROVIDER=anthropic\nLLM_API_KEY=llm-secret-canary\n"
        "API_KEY=api-secret-canary\n"
    )
    child_test = tmp_path / "test_child.py"
    child_test.write_text("""
def test_child():
    from app.core.config import Settings, get_settings
    assert Settings.model_config['env_file'] is None
    settings = get_settings()
    assert settings.database_url.get_secret_value() == 'test-app-canary'
    assert settings.migration_database_url.get_secret_value() == 'test-owner-canary'
    assert settings.llm_provider == 'stub'
    assert settings.llm_api_key is None and settings.api_key is None
""")
    script = """
import sys
from app.core.config import Settings
from pydantic_settings.sources import DotEnvSettingsSource
original = DotEnvSettingsSource._read_env_files
dotenv_path = sys.argv[1]
def guarded(self):
    assert str(self.env_file) == dotenv_path, 'Unexpected dotenv path'
    return original(self)
DotEnvSettingsSource._read_env_files = guarded
Settings.model_config['env_file'] = sys.argv[1]
from scripts.run_verification import main
sys.argv = ['run_verification', 'pytest', '-q', sys.argv[2]]
main()
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, str(dotenv), str(child_test)],
        cwd=tmp_path,
        env={"PATH": os.defpath, "PYTHONPATH": str(run_verification.BACKEND)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "1 passed" in completed.stdout
