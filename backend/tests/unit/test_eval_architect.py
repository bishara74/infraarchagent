from pathlib import Path

import pytest

from app.core.config import Settings
from app.domain.enums import LLMProvider
from scripts.eval_architect import CASES, run_evaluation


def settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://app:secret@localhost/db",
        migration_database_url="postgresql+asyncpg://owner:secret@localhost/db",
        test_database_url="postgresql+asyncpg://app:secret@localhost/test",
        test_migration_database_url="postgresql+asyncpg://owner:secret@localhost/test",
        llm_provider=LLMProvider.STUB,
        _env_file=None,
    )


@pytest.mark.req("FR-A-01", "FR-A-02", "FR-A-03")
async def test_offline_evaluation_passes_all_checks_and_correction(
    tmp_path: Path,
) -> None:
    output = await run_evaluation(
        settings(), provider=LLMProvider.STUB, output_root=tmp_path
    )
    summary = (output / "summary.md").read_text(encoding="utf-8")
    assert "FAIL" not in summary
    assert "correction diagnostic" in summary
    assert "Plan attempts: 2" in summary
    assert len(list(output.glob("*.json"))) == len(CASES) + 1
    assert "user_description" not in summary
