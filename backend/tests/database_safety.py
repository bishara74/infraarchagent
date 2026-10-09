"""Test-only settings and connection guards; never expose database credentials."""

from sqlalchemy.engine import make_url

from app.core.config import Settings


def assert_test_database_settings(settings: Settings) -> None:
    for app, test in (
        (settings.database_url, settings.test_database_url),
        (settings.migration_database_url, settings.test_migration_database_url),
    ):
        target = make_url(test.get_secret_value())
        if (
            target.database != "infraarch_test"
            or make_url(app.get_secret_value()) != target
        ):
            raise AssertionError("Integration settings must use test database URLs")


def isolated_database_settings(settings: Settings) -> Settings:
    isolated = settings.model_copy(
        update={
            "database_url": settings.test_database_url,
            "migration_database_url": settings.test_migration_database_url,
        }
    )
    assert_test_database_settings(isolated)
    return isolated


def assert_test_connection(parameters: dict[str, object]) -> None:
    if parameters.get("database") != "infraarch_test":
        raise AssertionError("Integration tests must connect only to the test database")
