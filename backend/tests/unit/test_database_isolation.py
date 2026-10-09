"""NFR-01: synthetic development URLs must never escape into integration work."""

import pytest
from pydantic import SecretStr

from app.core.config import Settings
from tests.database_safety import (
    assert_test_database_settings,
    isolated_database_settings,
)


def settings():
    return Settings.model_construct(
        database_url=SecretStr(
            "postgresql+asyncpg://app:canary-key@localhost/infraarch"
        ),
        migration_database_url=SecretStr(
            "postgresql+asyncpg://owner:canary-key@localhost/infraarch"
        ),
        test_database_url=SecretStr(
            "postgresql+asyncpg://app@localhost/infraarch_test"
        ),
        test_migration_database_url=SecretStr(
            "postgresql+asyncpg://owner@localhost/infraarch_test"
        ),
    )


@pytest.mark.req("NFR-01")
def test_isolated_settings_replace_both_urls_and_leave_original_unchanged():
    original = settings()
    isolated = isolated_database_settings(original)
    assert_test_database_settings(isolated)
    assert isolated.database_url == original.test_database_url
    assert isolated.migration_database_url == original.test_migration_database_url
    with pytest.raises(AssertionError, match="test database URLs") as failure:
        assert_test_database_settings(original)
    assert "canary-key" not in str(failure.value)


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "field",
    [
        "database_url",
        "migration_database_url",
        "test_database_url",
        "test_migration_database_url",
    ],
)
def test_settings_guard_rejects_each_non_test_database_url(field):
    isolated = isolated_database_settings(settings())
    unsafe = isolated.model_copy(update={field: settings().database_url})
    with pytest.raises(AssertionError, match="test database URLs"):
        assert_test_database_settings(unsafe)
