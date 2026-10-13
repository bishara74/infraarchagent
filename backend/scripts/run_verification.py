"""Launch isolated verification using test URLs from normal operator settings.

The parent resolves settings normally. Only test database credentials cross into
the dotenv-disabled child; configured LLM/API credentials are never forwarded.
"""

import os
import sys
from pathlib import Path

from pydantic import ValidationError

from app.core.config import Settings, get_settings

BACKEND = Path(__file__).resolve().parents[1]


def verification_environment(settings: Settings) -> dict[str, str]:
    env = os.environ.copy()
    for normal, test, value in (
        ("DATABASE_URL", "TEST_DATABASE_URL", settings.test_database_url),
        (
            "MIGRATION_DATABASE_URL",
            "TEST_MIGRATION_DATABASE_URL",
            settings.test_migration_database_url,
        ),
    ):
        env[normal] = env[test] = value.get_secret_value()
    env.update(
        INFRAARCH_TEST_BOOTSTRAP="1",
        LLM_PROVIDER="stub",
        LLM_MODEL="",
        LLM_API_KEY="",
        API_KEY="",
        LLM_REASONING_EFFORT="",
        LLM_RESPONSE_FORMAT="",
        LLM_PROMPT_CACHE="off",
        LLM_BASE_URL="",
        SECURITY_FIX_PROVIDER="",
        SECURITY_FIX_MODEL="",
        SECURITY_FIX_REASONING_EFFORT="",
    )
    env["PYTHONPATH"] = os.pathsep.join(
        [str(BACKEND / "tests/bootstrap"), str(BACKEND)]
        + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])
    )
    return env


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"pytest", "e2e"}:
        raise SystemExit(
            "Usage: python -m scripts.run_verification {pytest|e2e} [args]"
        )
    try:
        env = verification_environment(get_settings())
    except (ValidationError, OSError):
        raise SystemExit(
            "Verification settings unavailable; "
            "check the configured test database URLs."
        ) from None
    if sys.argv[1] == "pytest":
        command = [sys.executable, "-m", "pytest", *sys.argv[2:]]
    else:
        command = ["npm", "run", "test:e2e", "--", *sys.argv[2:]]
        os.chdir(BACKEND.parent / "frontend")
    os.execvpe(command[0], command, env)


if __name__ == "__main__":
    main()
