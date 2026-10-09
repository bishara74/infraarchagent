"""Reject non-test PostgreSQL connections before any DBAPI connection is made."""

import pytest
from sqlalchemy import Engine, event

from tests.database_safety import assert_test_connection


@pytest.fixture(autouse=True)
def forbid_non_test_database_connections():
    def guard(_dialect, _record, _args, parameters):
        try:
            assert_test_connection(parameters)
        except AssertionError:
            # pytest's failure escapes application Exception handlers as well.
            pytest.fail(
                "Integration tests must connect only to the test database",
                pytrace=False,
            )

    event.listen(Engine, "do_connect", guard)
    try:
        yield
    finally:
        event.remove(Engine, "do_connect", guard)
