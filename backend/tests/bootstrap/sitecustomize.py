"""Verification-only bootstrap: disable dotenv before settings instantiate.

Put this directory first on PYTHONPATH and set INFRAARCH_TEST_BOOTSTRAP=1
only for verification processes (including their Alembic subprocesses).
Explicit environment variables remain available to canary/configuration tests.
Production settings and normal operator startup are unchanged.
"""

import os

if os.environ.get("INFRAARCH_TEST_BOOTSTRAP") == "1":
    from app.core.config import Settings

    Settings.model_config["env_file"] = None

    # Verification can be configured with just the two explicit test URLs.
    for destination, source in (
        ("DATABASE_URL", "TEST_DATABASE_URL"),
        ("MIGRATION_DATABASE_URL", "TEST_MIGRATION_DATABASE_URL"),
    ):
        if os.environ.get(source):
            os.environ.setdefault(destination, os.environ[source])
