import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.llm.errors import ResponseStats
from scripts.spike_llm_timing import (
    GROUPS,
    call_record,
    markdown_summary,
    run_spike,
    summarize,
)


def settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        database_url="postgresql+asyncpg://app:secret@localhost/db",
        migration_database_url="postgresql+asyncpg://owner:secret@localhost/db",
        test_database_url="postgresql+asyncpg://app:secret@localhost/test",
        test_migration_database_url="postgresql+asyncpg://owner:secret@localhost/test",
        _env_file=None,
    )


@pytest.mark.req("PR-05", "NFR-01")
async def test_stub_spike_writes_safe_full_and_split_reports(tmp_path: Path) -> None:
    json_path, md_path = await run_spike(
        settings(),
        provider="stub",
        runs=2,
        max_output_tokens=77,
        output_dir=tmp_path,
    )
    report = json.loads(json_path.read_text())
    summary = md_path.read_text()
    assert report["max_output_tokens"] == 77
    assert len(report["runs"]) == 4
    assert len(report["runs"][1]["calls"]) == len(GROUPS) == 9
    assert [row["mode"] for row in report["summaries"]] == ["full", "split"]
    assert all(row["truncated"] == 0 for row in report["summaries"])
    assert "Truncated calls" in summary
    assert "truncated 0/" in summary
    assert "Three-tier AWS web app" not in json_path.read_text()
    assert "stub.txt" not in json_path.read_text()
    assert "stub.txt" not in summary


@pytest.mark.req("PR-05")
def test_truncation_blocks_fits_verdict() -> None:
    call = call_record(
        group="all",
        latency=0.5,
        stats=ResponseStats(10, 100, "max_tokens", 200),
        parsed=False,
        error="truncated",
    )
    row = summarize(
        [{"mode": "full", "run": 1, "wall_seconds": 0.5, "calls": [call]}], "full"
    )
    assert row["truncated"] == 1
    assert row["fits"] is False
    summary = markdown_summary(
        {"provider": "stub", "max_output_tokens": 100, "summaries": [row]}
    )
    assert "**1/1**" in summary
    assert "does not fit 30 s" in summary
    assert "truncated 1/1 calls" in summary


@pytest.mark.req("PR-05")
async def test_spike_rejects_nonpositive_output_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max output tokens"):
        await run_spike(
            settings(), provider="stub", max_output_tokens=0, output_dir=tmp_path
        )
