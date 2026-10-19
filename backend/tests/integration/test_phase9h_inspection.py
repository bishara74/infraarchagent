"""NFR-01 real PostgreSQL grants: inspection cannot mutate application data."""

import pytest
from sqlalchemy import text


@pytest.mark.req("NFR-01")
async def test_inspection_select_only(db_engines):
    async with db_engines[1].connect() as connection:
        for table in (
            "pipeline_runs",
            "generated_packages",
            "agent_events",
            "users",
            "auth_sessions",
            "provider_credentials",
            "user_preferences",
            "user_recent_runs",
            "llm_settings",
        ):
            assert await connection.scalar(
                text(
                    "SELECT has_table_privilege('infraarch_readonly', :table, 'SELECT')"
                ),
                {"table": table},
            )
            for privilege in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
                assert not await connection.scalar(
                    text(
                        "SELECT has_table_privilege('infraarch_readonly', :table, :privilege)"
                    ),
                    {"table": table, "privilege": privilege},
                )
        assert not await connection.scalar(
            text("SELECT has_table_privilege('infraarch_app','pipeline_runs','DELETE')")
        )
        assert not await connection.scalar(
            text("SELECT has_table_privilege('infraarch_app','agent_events','UPDATE')")
        )
