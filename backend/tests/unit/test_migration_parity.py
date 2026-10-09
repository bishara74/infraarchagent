import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from app.domain.enums import AgentName, LLMProvider, PackageStatus, RunStatus, Variant


def _migration() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[2]
        / "app/db/migrations/versions/0001_initial_schema.py"
    )
    spec = importlib.util.spec_from_file_location("initial_schema", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_check_literals_match_domain_enums() -> None:
    migration = _migration()
    for name, enum in (
        ("RUN_STATUS_VALUES", RunStatus),
        ("PACKAGE_STATUS_VALUES", PackageStatus),
        ("VARIANT_VALUES", Variant),
        ("LLM_PROVIDER_VALUES", LLMProvider),
        ("AGENT_NAME_VALUES", AgentName),
    ):
        assert set(getattr(migration, name)) == {item.value for item in enum}


@pytest.mark.req("FR-S-09", "NFR-01")
def test_review_retry_migration_adds_nullable_timestamp_only(monkeypatch):
    path = (
        Path(__file__).resolve().parents[2]
        / "app/db/migrations/versions/0003_review_retry_started_at.py"
    )
    spec = importlib.util.spec_from_file_location("review_retry_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.down_revision == "0002_original_files"
    added = []
    monkeypatch.setattr(
        module.op, "add_column", lambda table, column: added.append((table, column))
    )
    module.upgrade()
    table, column = added[0]
    assert table == "generated_packages" and column.name == "review_retry_started_at"
    assert column.nullable and column.type.timezone and column.server_default is None
    dropped = []
    monkeypatch.setattr(module.op, "drop_column", lambda *args: dropped.append(args))
    module.downgrade()
    assert dropped == [("generated_packages", "review_retry_started_at")]
