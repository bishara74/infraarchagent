import importlib.util
from pathlib import Path
from types import ModuleType

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
